import gradio as gr
from dotenv import load_dotenv
import asyncio
import json
import os
from backend import Augumented_Agent
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env if it exists
load_dotenv(override=True)

# Global dictionary to store user states and agents
user_states = {}

def blank_state():
    return {
        "agent": None,
    }

async def chat(message, history, request: gr.Request):
    session_hash = request.session_hash
    
    # Initialize user state if not exists
    if session_hash not in user_states:
        user_states[session_hash] = blank_state()
        
        # Initialize the agent without memory (stateless)
        agent = Augumented_Agent()
        await agent.setup()
        
        user_states[session_hash]["agent"] = agent
    
    state = user_states[session_hash]
    agent = state["agent"]
    
    try:
        # Convert history to messages format
        messages = []
        if history:
            for entry in history:
                if isinstance(entry, (list, tuple)) and len(entry) == 2:
                    human, ai = entry
                    if human:
                        messages.append(HumanMessage(content=human))
                    if ai:
                        messages.append(AIMessage(content=ai))
                elif isinstance(entry, dict):
                    if entry.get('role') == 'user':
                        messages.append(HumanMessage(content=entry.get('content', '')))
                    elif entry.get('role') == 'assistant':
                        messages.append(AIMessage(content=entry.get('content', '')))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        # Collect the complete response first
        complete_response = ""
        async for event in agent.graph.astream(
            {'messages': messages}
        ):
            for step_key, step_value in event.items():
                if isinstance(step_value, dict) and "messages" in step_value:
                    latest_message = step_value['messages'][-1]
                    if hasattr(latest_message, 'content') and latest_message.content:
                        complete_response = latest_message.content
        
        # Only yield the final, complete response
        if complete_response:
            yield complete_response
        else:
            yield "I couldn't generate a response. Please try again."
            
    except Exception as e:
        yield f"Sorry, I encountered an error: {str(e)}"
    
    return

# Set up the theme
theme = gr.themes.Soft(
    primary_hue="green",
    secondary_hue="green",
    neutral_hue="gray",
    font=gr.themes.GoogleFont("Open Sans")
)

# Create the Gradio interface with markdown enabled
with gr.Blocks(theme=theme) as demo:
    gr.ChatInterface(
        fn=chat,
        title="AI Assistant",
        description="AI assistant with web search, Wikipedia, and memory. Ask me anything!",
        examples=[
            "What's the latest news about artificial intelligence?",
            "Tell me about quantum computing",
            "What's the weather like in New York?",
            "Who is Elon Musk?",
            "What are the benefits of meditation?"
        ],
        chatbot=gr.Chatbot(
            render_markdown=True,
            height=600,
            show_copy_button=True,
            latex_delimiters=[],
            type="messages"
        ),
        css=".examples-table {border-radius: 8px !important; border: 1px solid rgba(128, 128, 128, 0.2) !important; padding: 10px !important; margin: 10px 0 !important;} .examples-table button {background-color: #2c2c2c !important; border: 1px solid #404040 !important; border-radius: 4px !important; margin: 4px !important; padding: 8px 16px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;}"
    )

if __name__ == "__main__":
    # Check if running on Hugging Face Spaces
    if os.environ.get("SPACE_ID"):
        demo.launch()
    else:
        # Local development settings
        demo.launch(
            server_name="0.0.0.0",  # Allows external access
            server_port=7860,       # Default Gradio port
            share=False,            # Set to True if you want to generate a public link
            debug=True
        )