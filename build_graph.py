from typing import List, Dict, Annotated
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

# --- Pydantic Models ---
class SubjectPerformance(BaseModel):
    """Represents a student's performance in a single subject."""
    subject: str = Field(description="The subject, e.g., 'Math' or 'ELA'")
    score: int = Field(description="The student's score in the subject.")
    recommended_skills: List[str] = Field(default_factory=list, description="A list of recommended skills for the subject, if any.")

class SubjectMapping(BaseModel):
    """A mapping from a raw subject name to the official subject name."""
    raw_subject: str = Field(description="The subject name as extracted from the PDF report.")
    official_subject: str = Field(description="The corresponding official subject name from the provided list. Must be an exact match from the list.")

class SubjectMappings(BaseModel):
    """A list of subject mappings to ensure all subjects from the PDF are correctly matched."""
    mappings: List[SubjectMapping]

# --- State Management ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    grade: str
    student_name: str
    student_performance_data: List[SubjectPerformance] # Raw subjects + student scores and recommended skills from PDF
    subject_mapping: Dict[str, str]  # Definitive mapping from raw -> official

# --- Agent Class ---
class StudentAssessment(BaseModel):
    """An agent that assesses student performance based on diagnostic reports."""
    graph: any = Field(default=None, init=False)
    llm_with_tools: any = Field(default=None, init=False)
    mapping_llm: any = Field(default=None, init=False)
    synthesis_llm: any = Field(default=None, init=False)
    synthesis_llm_with_tools: any = Field(default=None, init=False)
    tools: List = Field(default_factory=list, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self.graph = self.setup_graph()

    def setup_graph(self):
        """Initializes the LLMs and builds the graph."""
        print("--- Setting up agent graph ---")
        print(f"--- Agent setup called at {id(self)} ---")
        self.tools = [calculate_percentile, calculate_performing_grade, calculate_next_grade_threshold]
        llm = get_llm_core()
        self.llm_with_tools = llm.bind_tools(self.tools)
        self.mapping_llm = llm.with_structured_output(SubjectMappings)
        self.synthesis_llm = llm
        
        return self.build_graph()

    def subject_mapping_node(self, state: AgentState) -> dict:
        """Uses the mapping_llm to map raw subjects to official subjects."""
        print("--- In subject_mapping_node ---")
        raw_subjects = [s.subject for s in state["student_performance_data"]]
        official_subjects = get_grade_data()['Subject'].unique().tolist()        
        prompt = SUBJECT_MAPPING_PROMPT.format(raw_subjects=raw_subjects, official_subjects=official_subjects)
        mapping_result = self.mapping_llm.invoke(prompt)
        mapping_dict = {m.raw_subject: m.official_subject for m in mapping_result.mappings}
        # print(f"--- Subject mapping complete: {mapping_dict} ---")
        return {"subject_mapping": mapping_dict}

    def assessment_node(self, state: AgentState) -> dict:
        """
        Prepares the assessment data and invokes the LLM with the current state to decide on the next action,
        which is either calling a tool or concluding the analysis.
        """
        print("--- In assessment_node ---")

        # If this is the first pass, create the initial human message to kick things off.
        if not state["messages"]:
            grade = state["grade"]
            student_name = state["student_name"]
            
            mapped_subjects = []
            for s in state["student_performance_data"]:
                official_name = state["subject_mapping"].get(s.subject)
                if official_name:
                    mapped_subjects.append(
                        {
                            "subject": official_name,
                            "score": s.score,
                            "recommended_skills": s.recommended_skills,
                        }
                    )
            
            subjects_json = json.dumps(mapped_subjects, indent=2)

            assessment_prompt_str = ASSESSMENT_PROMPT.format(
                grade=grade,
                student_name=student_name,
                subjects_json=subjects_json,
            )
            
            messages_to_invoke = [HumanMessage(content=assessment_prompt_str)]
            response = self.llm_with_tools.invoke(messages_to_invoke)
            
            # On the first run, we must return both the human prompt and the AI's response
            # to properly initialize the conversation history.
            return {"messages": [messages_to_invoke[0], response]}

        # For subsequent calls, the message history is already populated with tool responses.
        response = self.llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def synthesis_node(self, state: AgentState) -> dict:
        """
        Generates the final student report after all tool calls are complete.
        """
        print("--- In synthesis_node ---")
        synthesis_prompt = HumanMessage(content=SYNTHESIS_PROMPT)
        response = self.synthesis_llm.invoke(state["messages"] + [synthesis_prompt])
        return {"messages": [response]}

    def build_graph(self) -> StateGraph:
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
            self.setup_graph()

        initial_state: AgentState = {
            "student_performance_data": student_performance_data, 
            "grade": grade, 
            "student_name": student_name, 
            "messages": [],
            "subject_mapping": {}  # Initialize empty mapping
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