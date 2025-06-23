---
title: wiki_google_chatbot
app_file: app.py
sdk: gradio
sdk_version: 5.34.2
---
# Augmented LLM Agent

A powerful AI assistant built using the Anthropic agents framework with web search, Wikipedia integration, and push notification capabilities. This project demonstrates effective agent construction following [Anthropic's guide to building effective agents](https://www.anthropic.com/engineering/building-effective-agents).

## Features

- **AI Chat Interface**: Interactive text-based chat powered by Google's Gemini 2.5 Flash model
- **Web Search Integration**: Real-time web search capabilities using Google Serper API
- **Wikipedia Access**: Comprehensive knowledge retrieval from Wikipedia
- **Push Notifications**: Send notifications via Pushover service
- **Session Management**: Per-session conversation tracking in web interface
- **Web Interface**: Beautiful Gradio-based chat interface with markdown support
- **Command Line Interface**: Terminal-based chat for development and testing

## Architecture

The project uses LangGraph to create a stateful agent with:
- **State Management**: Maintains conversation context across interactions
- **Tool Integration**: Seamlessly switches between different tools based on user needs
- **Memory Persistence**: Stores conversation history in SQLite database (CLI only)
- **Async Processing**: Built with async/await for optimal performance

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/samjosdev/augmented_llm.git
   cd augmented_llm
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   PUSHOVER_TOKEN=your_pushover_token_here
   PUSHOVER_USER=your_pushover_user_key_here
   ```

## Required API Keys

- **Google API Key**: For Gemini 2.5 Flash model access
  - Get it from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Serper API Key**: For web search functionality
  - Get it from [Serper.dev](https://serper.dev/)
- **Pushover Credentials**: For push notifications (optional)
  - Get them from [Pushover.net](https://pushover.net/)

## Usage

### Web Interface (Recommended)

Launch the Gradio web interface:
```bash
python augumented_llm_chat.py
```

Then open your browser to `http://localhost:7860`

*Note: The web interface uses in-session memory only - conversations are not persisted between browser sessions.*

### Command Line Interface

For development or terminal-based usage with persistent memory:
```bash
python app.py
```

*The CLI version maintains conversation history across sessions using SQLite.*

## Example Interactions

- **General Knowledge**: "What is quantum computing?"
- **Current Events**: "What are the latest developments in renewable energy?"
- **Sports**: "When is the next India Australia test series?"
- **Research**: "Tell me about the history of artificial intelligence"
- **Notifications**: "Send me a notification with today's weather"

## Project Structure

```
augmented_llm/
├── app.py                    # Main application with CLI interface
├── augumented_llm_chat.py    # Gradio web interface
├── model.py                  # LLM model configuration
├── tools.py                  # Tool definitions and implementations
├── prompts.py                # System prompts and instructions
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
├── session.json             # Session persistence (auto-generated)
└── agent_memory.sqlite      # Conversation memory (auto-generated)
```

## Key Components

### Agent Architecture (`app.py`)
- **Augmented_Agent**: Main agent class with tool binding and graph construction
- **State Management**: Handles conversation context and message flow
- **Memory Integration**: Persistent storage using AsyncSqliteSaver

### Tools (`tools.py`)
- **Web Search**: Google Serper API integration for current information
- **Wikipedia**: Knowledge base access for general information
- **Push Notifications**: Pushover integration for user alerts

### Web Interface (`augumented_llm_chat.py`)
- **Gradio Integration**: Beautiful, responsive chat interface
- **Markdown Rendering**: Proper formatting for complex responses
- **Session Management**: Per-session conversation tracking (no persistence between sessions)

## Customization

### Adding New Tools

1. Define your tool function in `tools.py`
2. Create a Pydantic model for input validation
3. Add the tool to the `other_tools()` function
4. Update the system prompt in `prompts.py`

### Changing the LLM Model

Modify `model.py` to use different models:
```python
# For OpenAI
model = ChatOpenAI(model="gpt-4o-mini")

# For Google Gemini (current)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20")
```

### Customizing System Prompts

Edit `prompts.py` to modify the agent's behavior and instructions.

## Dependencies

Main dependencies include:
- `langgraph`: Agent framework and state management
- `langchain`: LLM integration and tool utilities
- `gradio`: Web interface framework
- `sqlite3`: Database for persistent memory
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built following [Anthropic's guide to building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Uses LangGraph for agent orchestration
- Powered by Google's Gemini 2.5 Flash model
- Web search via Serper.dev API
- Push notifications via Pushover

## Support

For issues and questions, please open an issue on GitHub or contact the maintainer.

---

**Note**: This is an educational project demonstrating agent construction patterns. Always follow best practices for API key management and never commit sensitive credentials to version control.