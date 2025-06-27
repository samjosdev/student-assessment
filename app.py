import gradio as gr
from build_graph import StudentAssessment
import asyncio
import tempfile
import os


# Global variable to store the agent instance
agent = None
# Debug counter
call_counter = 0

async def setup_agent():
    """Initialize the agent once when the app starts."""
    global agent
    if agent is None:
        agent = StudentAssessment()
        await agent.setup_graph()
    return agent

def save_html_report(html_content, input_pdf_path):
    base = os.path.splitext(os.path.basename(input_pdf_path))[0]
    out_name = f"{base}_studentassessmentreport.html"
    out_path = os.path.join(tempfile.gettempdir(), out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return out_path

async def process_pdf(pdf_path, grade_input, student_name_input):
    """Process the uploaded PDF and generate assessment, yielding status updates."""
    global call_counter
    call_counter += 1
    print(f"=== process_pdf called #{call_counter} ===")
    
    if not pdf_path:
        yield "Please upload a PDF file.", gr.update(visible=False)
        return
    
    if not grade_input:
        yield "Please enter the student's grade level.", gr.update(visible=False)
        return
    
    if not student_name_input:
        yield "Please enter the student's name.", gr.update(visible=False)
        return
    
    try:
        yield "⏳ Initializing assessment agent...", gr.update(visible=False)
        
        # The agent will handle PDF parsing internally via the user_input_parser node
        agent = StudentAssessment()
        await agent.setup_graph()
        
        yield "🔄 **Processing Assessment:** This may take a moment as we parse the PDF and analyze performance data...", gr.update(visible=False)
        
        # Pass the PDF path directly to the agent - it will handle parsing internally
        result = await agent.run_from_pdf(pdf_path=pdf_path, grade=grade_input, student_name=student_name_input)
        
        if result and "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                html_report = final_message.content
                html_file_path = save_html_report(html_report, pdf_path)
                # Yield the HTML report and the file path for gr.File (download button)
                yield html_report, gr.update(value=html_file_path, visible=True)
            else:
                yield "Assessment complete, but no content was generated.", gr.update(visible=False)
        else:
            yield "The assessment could not be completed.", gr.update(visible=False)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"An error occurred: {str(e)}", gr.update(visible=False)

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
    grade_levels = [str(i) for i in range(1, 9)]
    custom_css = """
    body { background: linear-gradient(135deg, #f8fafc 0%, #e3e9f3 100%); font-family: 'Inter', Arial, sans-serif; }
    .gradio-container { background: none !important; }
    .gr-box, .gr-panel, .gr-form, .gr-form-section, .gr-form-row, .gr-form-col, .gr-form-group, .gr-form-input, .gr-form-output {
        background: #fff !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 24px 0 rgba(80, 80, 120, 0.08) !important;
        padding: 32px 32px 24px 32px !important;
        margin-bottom: 32px !important;
        border: none !important;
    }
    .gr-button, button, input[type="submit"] {
        background: linear-gradient(135deg, #667eea 0%, #7ed957 100%) !important;
        color: #fff !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        padding: 12px 28px !important;
        border: none !important;
        box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.08) !important;
        transition: background 0.2s;
    }
    .gr-button:hover, button:hover, input[type="submit"]:hover {
        background: linear-gradient(135deg, #7ed957 0%, #667eea 100%) !important;
    }
    .gr-upload, .gr-file, .gr-input, .gr-output {
        border-radius: 12px !important;
        box-shadow: 0 2px 8px 0 rgba(80, 80, 120, 0.04) !important;
        background: #f8f9fa !important;
        border: 1px solid #e3e9f3 !important;
    }
    .gr-markdown, .gr-html, .gr-output-html {
        background: none !important;
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
    }
    .gr-input-label, .gr-form-label {
        color: #667eea !important;
        font-weight: 700 !important;
        font-size: 1.08em !important;
        background: none !important;
        margin-bottom: 4px !important;
        letter-spacing: 0.01em;
    }
    .gr-info {
        color: #888fd6 !important;
        font-size: 0.98em !important;
        font-weight: 500 !important;
        background: none !important;
    }
    """

    with gr.Blocks(title="Student Assessment Analyzer", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("# Student Assessment Analyzer")
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
                output_html = gr.HTML(label="Assessment Results")
                # Use gr.File for download, label as 'Download Report', and make visible only when ready
                download_html = gr.File(label="Download Report", visible=False)
        
        interactive_comps = [pdf_input, grade_input, student_name_input, analyze_btn, stop_btn]

        def update_analyze_button_state(pdf, grade, name):
            return gr.Button(interactive=(pdf is not None and grade is not None and name))

        pdf_input.upload(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)
        grade_input.change(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)
        student_name_input.change(update_analyze_button_state, [pdf_input, grade_input, student_name_input], analyze_btn)

        analysis_run = analyze_btn.click(
            fn=process_pdf,
            inputs=[pdf_input, grade_input, student_name_input],
            outputs=[output_html, download_html]
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

def html_to_pdf(html_content):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        HTML(string=html_content).write_pdf(tmpfile.name)
        return tmpfile.name

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()