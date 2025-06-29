from typing import List, Dict, Annotated, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import json
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from prompts import ASSESSMENT_PROMPT, SUBJECT_MAPPING_PROMPT, SYNTHESIS_PROMPT, MULTI_PARSER_EXTRACTION_PROMPT
from grade_reader import get_grade_data
from model import get_llm_core, get_extraction_llm
from tools import calculate_all_metrics
from datetime import datetime
from report_formatter import format_sections_to_report
from user_input_parser import parse_pdf_to_text, SubjectPerformance

# --- Pydantic Models ---
class PerformanceInfo(BaseModel):
    """Tool for extracting performance information from student data."""
    subjects: List[SubjectPerformance] = Field(description="List of subjects, their scores, and any recommended skills.")

class PerformanceTableRow(BaseModel):
    """Structured representation of a single row in the performance dashboard table."""
    subject_name: str = Field(description="The subject name (e.g., 'Math: Overall', 'ELA: Reading')")
    score: int = Field(description="The student's numeric score (e.g., 450, 520)")
    performance_band: str = Field(description="Performance band: 'Above Grade Level', 'On Grade Level', or 'Below Grade Level'")
    percentile: str = Field(description="Percentile with emoji (e.g., '🎉 95th percentile')")
    next_grade_threshold: int = Field(description="Numeric threshold for next grade level")
    performing_grade: str = Field(description="Grade level text (e.g., '3rd grade', '4th grade')")
    recommended_skills: List[str] = Field(description="List of recommended skills for this subject")

class PerformanceDashboard(BaseModel):
    """Structured representation of the complete performance dashboard table."""
    table_rows: List[PerformanceTableRow] = Field(description="All subject rows in the performance dashboard")

class SubjectMapping(BaseModel):
    """A mapping from a raw subject name to the official subject name."""
    raw_subject: str = Field(description="The subject name as extracted from the PDF report.")
    official_subject: str = Field(description="The corresponding official subject name from the provided list. Must be an exact match from the list.")

class SubjectMappings(BaseModel):
    """A list of subject mappings to ensure all subjects from the PDF are correctly matched."""
    mappings: List[SubjectMapping]

class AssessmentReport(BaseModel):
    """Structured output for the synthesis node to ensure all sections are present."""
    key_findings: str = Field(description="Key findings section with above/on/below grade level subjects")
    overview: str = Field(description="2-3 sentence overview of overall performance")
    performance_dashboard: PerformanceDashboard = Field(description="Structured performance dashboard data")
    summary: str = Field(description="Summary section with key strengths, areas for improvement, and readiness assessment")
    methodology: str = Field(description="Methodology section explaining data sources")

# --- State Management ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    grade: str
    student_name: str
    pdf_path: str  # PDF path for the user_input_parser node
    student_performance_data: List[SubjectPerformance] #Raw subjects + student scores and recommended skills from PDF
    subject_mapping: Dict[str, str]  # Definitive mapping from raw -> official
    subjects_json: str  # JSON string of mapped subjects with scores and recommended skills

# --- Agent Class ---
class StudentAssessment(BaseModel):
    """An agent that assesses student performance based on diagnostic reports."""
    graph: Any = Field(default=None, init=False)
    llm_with_tools: Any = Field(default=None, init=False)
    mapping_llm: Any = Field(default=None, init=False)
    synthesis_llm: Any = Field(default=None, init=False)
    tools: List = Field(default_factory=list, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    async def setup_graph(self):
        """Initializes the LLMs and builds the graph."""
        print("--- Setting up agent graph ---")
        print(f"--- Agent setup called at {id(self)} ---")
        self.tools = [calculate_all_metrics]  # Use the combined tool instead of three separate tools
        llm = get_llm_core()
        self.llm_with_tools = llm.bind_tools(self.tools)
        self.mapping_llm = llm.with_structured_output(SubjectMappings)
        self.synthesis_llm = llm.with_structured_output(AssessmentReport)
        self.graph = await self.build_graph()
        
        return self.graph

    def user_input_parser_node(self, state: AgentState) -> dict:
        """
        Orchestrates the end-to-end process of parsing a PDF and extracting
        structured subject and score data using multiple strategies.

        Args:
            state: AgentState containing the pdf_path and other information.

        Returns:
            A dict with student_performance_data populated.
        """
        print("=" * 50)
        print("🔍 USER INPUT PARSER NODE")
        print("=" * 50)
        
        pdf_path = state["pdf_path"]
        
        # 1. Get raw text using the parsing function from user_input_parser.py
        result = parse_pdf_to_text(pdf_path)
        if not result:
            print("--- PDF parsing failed, returning empty list ---")
            return {"student_performance_data": []}
        pymupdf_text, llamaparse_text = result

        # 2. Use a structured LLM call to extract subjects and scores from the parsed text
        print("--- Extracting subjects and scores from parsed text ---")
        extraction_llm = get_extraction_llm().with_structured_output(PerformanceInfo)

        prompt = MULTI_PARSER_EXTRACTION_PROMPT.format(
            pymupdf_text=pymupdf_text,
            llamaparse_text=llamaparse_text
        )

        try:
            extraction_result = extraction_llm.invoke(prompt)
            print(f"--- Extraction complete. Found {len(extraction_result.subjects)} subjects. ---")
            return {"student_performance_data": extraction_result.subjects}
        except Exception as e:
            print(f"--- Error during subject extraction: {e} ---")
            return {"student_performance_data": []}

    def subject_mapping_node(self, state: AgentState) -> dict:
        """Uses the mapping_llm to map raw subjects to official subjects."""
        print("=" * 50)
        print("🔍 SUBJECT MAPPING NODE")
        print("=" * 50)
        raw_subjects = [s.subject for s in state["student_performance_data"]]
        official_subjects = get_grade_data()['Subject'].unique().tolist()        
        prompt = SUBJECT_MAPPING_PROMPT.format(raw_subjects=raw_subjects, official_subjects=official_subjects)
        mapping_result = self.mapping_llm.invoke(prompt)
        mapping_dict = {m.raw_subject: m.official_subject for m in mapping_result.mappings}
        
        # Create mapped subjects JSON
        mapped_subjects = []
        for s in state["student_performance_data"]:
            official_name = mapping_dict.get(s.subject)
            if official_name:
                mapped_subjects.append({
                    "subject": official_name,
                    "score": s.score,
                    "recommended_skills": s.recommended_skills,
                })
        
        subjects_json = json.dumps(mapped_subjects, indent=2)
        
        return {"subject_mapping": mapping_dict, "subjects_json": subjects_json}

    def assessment_node(self, state: AgentState) -> dict:
        """
        Prepares the assessment data and invokes the LLM with the current state to decide on the next action,
        which is either calling a tool or concluding the analysis.
        """
        print("=" * 50)
        print("📊 ASSESSMENT NODE")
        print(f"Messages count: {len(state['messages'])}")
        print("=" * 50)

        # If this is the first pass, create the initial human message to kick things off.
        if not state["messages"]:
            assessment_prompt_str = ASSESSMENT_PROMPT.format(
                grade=state["grade"],
                student_name=state["student_name"],
                subjects_json=state["subjects_json"],
            )            
            messages_to_invoke = [HumanMessage(content=assessment_prompt_str)]
            response = self.llm_with_tools.invoke(messages_to_invoke)            
            # On the first run, we must return both the human prompt and the AI's response
            # to properly initialize the conversation history.
            return {"messages": [messages_to_invoke[0], response]}

        # For subsequent calls, the message history is already populated with tool responses.
        response = self.llm_with_tools.invoke(state["messages"])
        # print ('Subsequent calls: state["messages"]', state["messages"])
        # Append the new response to the existing messages instead of replacing them
        return {"messages": state["messages"] + [response]}

    def synthesis_node(self, state: AgentState) -> dict:
        """
        Generates the final student report after all tool calls are complete.
        """
        print("=" * 50)
        print("🎯 SYNTHESIS NODE")
        print("=" * 50)
        
        # Get student information for the synthesis prompt
        grade = state["grade"]
        student_name = state["student_name"]
        current_date = datetime.now().strftime("%B %d, %Y")
        
        synthesis_prompt_str = SYNTHESIS_PROMPT.format(
            grade=grade,
            student_name=student_name,
            current_date=current_date,
        )        
        synthesis_prompt = HumanMessage(content=synthesis_prompt_str)
        # Get structured output from the LLM
        structured_report = self.synthesis_llm.invoke(state["messages"] + [synthesis_prompt])
        # Convert structured output to formatted HTML report
        formatted_report = format_sections_to_report(structured_report, student_name, grade, current_date)
        # Create a proper AIMessage with the formatted content
        from langchain_core.messages import AIMessage
        response = AIMessage(content=formatted_report)
        # Return only the new message
        return {"messages": [response]}
    
    async def build_graph(self) -> StateGraph:
        """Builds the LangGraph agent."""
        graph_builder = StateGraph(AgentState)
        tool_node = ToolNode(self.tools)

        graph_builder.add_node("user_input_parser", self.user_input_parser_node)
        graph_builder.add_node("map_subjects", self.subject_mapping_node)
        graph_builder.add_node("assessment", self.assessment_node)
        graph_builder.add_node("execute_tools", tool_node)
        graph_builder.add_node("synthesis", self.synthesis_node)

        graph_builder.set_entry_point("user_input_parser")
        
        # Conditional edge from user_input_parser - if subjects found, go to map_subjects, else END
        graph_builder.add_conditional_edges(
            "user_input_parser",
            lambda output: "map_subjects" if output and output.get("student_performance_data") and len(output["student_performance_data"]) > 0 else END,
        )
        
        # Direct edge from map_subjects to assessment
        graph_builder.add_edge("map_subjects", "assessment")
        
        # Conditional edge from assessment - if tools needed, go to execute_tools, else synthesis
        graph_builder.add_conditional_edges(
            "assessment",
            tools_condition,
            {
                "tools": "execute_tools",
                END: "synthesis",
            },
        )
        graph_builder.add_edge("execute_tools", "assessment")
        graph_builder.add_edge("synthesis", END)

        # Set recursion limit when compiling the graph (removed, not supported)
        return graph_builder.compile(checkpointer=None, interrupt_before=None, interrupt_after=None, debug=False)

    async def run_from_pdf(self, pdf_path: str, grade: str, student_name: str):
        """Runs the agent starting from a PDF path, letting the graph handle parsing internally."""
        if self.graph is None:
            await self.setup_graph()

        # Start with just the PDF path - the user_input_parser node will handle the rest
        initial_state: AgentState = {
            "pdf_path": pdf_path,  # Add PDF path to state
            "grade": grade, 
            "student_name": student_name, 
            "messages": [],
            "student_performance_data": [],  # Will be populated by user_input_parser node
            "subject_mapping": {}, 
            "subjects_json": ""
        }
        
        print(f"--- Starting agent run from PDF: {pdf_path} ---")
        print(f"--- Setting recursion limit to 300 ---")
        
        # Increased recursion limit to allow for all tool calls
        final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": 100})
        return final_state

# --- Main Function ---
async def main():
    """Main function to run the agent from the command line for testing."""
    load_dotenv(override=True)
    
    student_grade = "4"
    student_name = "Daniel S."
    
    try:
        # Use the new run_from_pdf method for testing
        pdf_path = "assets/IXL-Diagnostic-Report_2025-06-20_Daniel.pdf"
        
        print(f"Testing with PDF: {pdf_path}")
        
        # Run the agent with the PDF path - it will handle everything internally
        agent = StudentAssessment()
        await agent.setup_graph()
        result = await agent.run_from_pdf(pdf_path=pdf_path, grade=student_grade, student_name=student_name)
    
        if result and "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                print("\n--- Final Assessment ---\n")
                print(final_message.content)
            else:
                print("No result generated")
                
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())