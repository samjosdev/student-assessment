import gradio as gr
from dotenv import load_dotenv
from build_graph import StudentAssessment
from user_input_parser import extract_subjects_from_pdf
import asyncio

load_dotenv(override=True)

# Global variable to store the agent instance
agent = None
# Debug counter
call_counter = 0

async def setup_agent():
    """Initialize the agent once when the app starts."""
    global agent
    if agent is None:
        agent = StudentAssessment()
    return agent

async def process_pdf(pdf_path, grade_input, student_name_input):
    """Process the uploaded PDF and generate assessment, yielding status updates."""
    global call_counter
    call_counter += 1
    print(f"=== process_pdf called #{call_counter} ===")
    
    if not pdf_path:
        yield "Please upload a PDF file."
        return
    
    if not grade_input:
        yield "Please enter the student's grade level."
        return

    if not student_name_input:
        yield "Please enter the student's name."
        return
    
    try:
        yield "⏳ Parsing PDF and extracting subject data..."
        
        # This is now the pre-processing step, handled by the front-end
        subjects = await extract_subjects_from_pdf(pdf_path)

        if not subjects:
            yield "Could not process the PDF. Please ensure it contains valid data and subject scores."
            return
        
        yield f"✅ Extracted {len(subjects)} subjects. Initializing assessment agent..."
        
        # The agent is now initialized with clean data
        agent = StudentAssessment()
        
        yield "🔄 **Processing Assessment:** This may take a moment as we analyze performance data and generate your comprehensive report..."
        
        result = await agent.run(student_performance_data=subjects, grade=grade_input, student_name=student_name_input)
        
        if result and "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                yield final_message.content
            else:
                yield "Assessment complete, but no content was generated."
        else:
            yield "The assessment could not be completed."
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"An error occurred: {str(e)}"

def lock_ui():
    """Disables input controls and shows the stop button."""
    return [
        gr.File(interactive=False),
        gr.Dropdown(interactive=False),
        gr.Textbox(interactive=False),
        gr.Button(interactive=False),
        gr.Button("Stop", variant="stop", visible=True, interactive=True),
    ]

def unlock_ui():
    """Re-enables input controls and hides the stop button."""
    return [
        gr.File(interactive=True),
        gr.Dropdown(interactive=True),
        gr.Textbox(interactive=True),
        gr.Button(interactive=True),
        gr.Button("Stop", variant="stop", visible=False, interactive=False),
    ]

def create_interface():
    """Creates the Gradio interface."""
    grade_levels = [str(i) for i in range(1, 13)]
    grade_levels.insert(0, "K")
    grade_levels.append("HS")

    with gr.Blocks(title="Student Assessment Analyzer", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 📊 Student Assessment Analyzer")
        gr.Markdown("Upload a student's IXL Diagnostic Report PDF and select their grade to get a comprehensive assessment analysis.")
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="1. Upload PDF Report", file_types=[".pdf"], type="filepath")
                grade_input = gr.Dropdown(grade_levels, label="2. Select Student Grade", info="Please select the student's grade level.")
                student_name_input = gr.Textbox(label="3. Enter Student Name", info="e.g., Daniel S.")
                with gr.Row():
                    analyze_btn = gr.Button("Analyze Report", variant="primary", interactive=False)
                    stop_btn = gr.Button("Stop", variant="stop", visible=False, interactive=False)
                
                gr.Markdown("""
                **Instructions:**
                The "Analyze Report" button will activate once you upload a PDF, select a grade, and enter a name.
                """)
            
            with gr.Column(scale=2):
                output = gr.Markdown(label="Assessment Results", value="Upload a PDF and select a grade to see the assessment results.")
        
        interactive_comps = [pdf_input, grade_input, student_name_input, analyze_btn, stop_btn]

        def update_analyze_button_state(pdf, grade, name):
            return gr.Button(interactive=(pdf is not None and grade is not None and name))

        pdf_input.upload(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)
        grade_input.change(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)
        student_name_input.change(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)

        analysis_run = analyze_btn.click(fn=lock_ui, outputs=interactive_comps).then(
            fn=process_pdf,
            inputs=[pdf_input, grade_input, student_name_input],
            outputs=[output]
        ).then(
            fn=unlock_ui, outputs=interactive_comps
        )
        
        stop_btn.click(fn=lambda: unlock_ui(), outputs=interactive_comps, cancels=[analysis_run])

        gr.Examples(
            examples=[["assets/IXL-Diagnostic-Report_2025-06-20_Daniel.pdf", "4", "Daniel S."]],
            inputs=[pdf_input, grade_input, student_name_input],
            cache_examples=False,
            label="Example Reports"
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()