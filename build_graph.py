from typing import List, Dict, Annotated, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import json
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from prompts import ASSESSMENT_PROMPT, SUBJECT_MAPPING_PROMPT, SYNTHESIS_PROMPT
from grade_reader import get_grade_data
from model import get_llm_core
from tools import calculate_percentile, calculate_performing_grade, calculate_next_grade_threshold
from datetime import datetime
from report_formatter import format_sections_to_report

# --- Pydantic Models ---
class SubjectPerformance(BaseModel):
    """Represents a student's performance in a single subject."""
    subject: str = Field(description="The subject, e.g., 'Math' or 'ELA'")
    score: int = Field(description="The student's score in the subject.")
    recommended_skills: List[str] = Field(default_factory=list, description="A list of recommended skills for the subject, if any.")

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
        self.tools = [calculate_percentile, calculate_performing_grade, calculate_next_grade_threshold]
        llm = get_llm_core()
        self.llm_with_tools = llm.bind_tools(self.tools)
        self.mapping_llm = llm.with_structured_output(SubjectMappings)
        self.synthesis_llm = llm.with_structured_output(AssessmentReport)
        self.graph = await self.build_graph()
        
        return self.graph

    def subject_mapping_node(self, state: AgentState) -> dict:
        """Uses the mapping_llm to map raw subjects to official subjects."""
        print("--- In subject_mapping_node ---")
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
        print("--- In assessment_node ---")

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
        print("--- In synthesis_node ---")
        
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

        graph_builder.add_node("map_subjects", self.subject_mapping_node)
        graph_builder.add_node("assessment", self.assessment_node)
        graph_builder.add_node("execute_tools", tool_node)
        graph_builder.add_node("synthesis", self.synthesis_node)

        graph_builder.set_entry_point("map_subjects")
        graph_builder.add_edge("map_subjects", "assessment")

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

        return graph_builder.compile()

    async def run(self, student_performance_data: List[SubjectPerformance], grade: str, student_name: str):
        """Runs the agent with the provided student performance data and grade."""
        if self.graph is None:
            # This should not happen if setup is called in __init__
            await self.setup_graph()

        initial_state: AgentState = {
            "student_performance_data": student_performance_data, 
            "grade": grade, 
            "student_name": student_name, 
            "messages": [],
            "subject_mapping": {},  # Initialize empty mapping
            "subjects_json": ""  # Initialize empty subjects_json
        }
        # Increased recursion limit to allow for all tool calls
        final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": 50})
        return final_state

# --- Main Function ---
async def main():
    """Main function to run the agent from the command line for testing."""
    from user_input_parser import extract_subjects_from_pdf
    
    load_dotenv(override=True)
    
    student_grade = "4"
    student_name = "Daniel S."
    
    try:
        # Use the new extraction function to get structured data
        pdf_path = "assets/IXL-Diagnostic-Report_2025-06-20_Daniel.pdf"
        subjects = await extract_subjects_from_pdf(pdf_path)
        
        if not subjects:
            print("Could not extract subjects from PDF")
            return

        print(f"Extracted {len(subjects)} subjects: {[s.subject for s in subjects]}")
        # Log extracted skills for debugging
        for s in subjects:
            if s.recommended_skills:
                print(f"  - {s.subject}: {len(s.recommended_skills)} skills")

        # Run the agent with the extracted data
        agent = StudentAssessment()
        await agent.setup_graph()
        result = await agent.run(student_performance_data=subjects, grade=student_grade, student_name=student_name)
    
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