# Student Assessment Analyzer 📊

An intelligent web application that analyzes student diagnostic reports (specifically IXL Diagnostic Reports) and generates comprehensive assessment summaries with percentile rankings, performance bands, and actionable recommendations.

## Features ✨

- **Multi-Strategy PDF Parsing**: Uses PyMuPDF, OCR (PaddleOCR), and LlamaParse for maximum accuracy
- **Intelligent Subject Mapping**: Automatically maps extracted subjects to standardized categories
- **Percentile Calculations**: Accurate percentile rankings based on national grade-level benchmarks
- **Performance Dashboard**: Visual HTML table showing scores, performance bands, and recommendations
- **Grade-Level Analysis**: Determines actual performing grade level vs. current grade
- **Actionable Insights**: Specific skill recommendations and next steps

## Architecture 🏗️

The application uses a **LangGraph-based agent system** with the following components:

### Core Components

- **Web Interface** (`app.py`): Gradio-based UI for file upload and results display
- **PDF Parser** (`pdf_parser.py`): Multi-strategy PDF text extraction
- **Agent Graph** (`build_graph.py`): LangGraph workflow for assessment processing
- **Assessment Tools** (`tools.py`): Calculation functions for percentiles and grade levels
- **Benchmark Data Provider** (`grade_reader.py`): **Critical component** that loads and processes national grade-level benchmark data used by LLM tools for accurate calculations

### Agent Workflow

1. **Subject Mapping Node**: Maps extracted subjects to official categories
2. **Assessment Node**: Processes student data and decides on tool usage
3. **Tool Execution**: Calculates percentiles, performing grades, and thresholds using **benchmark data from `grade_reader.py`**
4. **Synthesis Node**: Generates the final comprehensive report

### Data Flow & LLM Tool Integration

The application follows this critical data flow:

```
PDF → Parser → Subject Extraction → LLM Agent → Tools → grade_reader.py → Benchmark Data → Calculations → Report
```

**Key Integration Points:**
- **`tools.py`** contains calculation functions (`calculate_percentile`, `calculate_performing_grade`, `calculate_next_grade_threshold`)
- **These tools are bound to the LLM** and called automatically during assessment
- **Each tool function calls `get_grade_data()`** from `grade_reader.py` to access benchmark data
- **`grade_reader.py` provides the single source of truth** for all national grade-level standards used in calculations

## Installation 🚀

### Prerequisites

- Python 3.8+
- OpenAI API key or Google Gemini API key
- LlamaParse API key (optional, for fallback parsing)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd student-assessment-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Choose one of the following:
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   
   # Optional (for LlamaParse fallback)
   LLAMA_CLOUD_API_KEY=your_llamaparse_api_key_here
   ```

4. **Ensure assets directory exists**
   ```bash
   mkdir -p assets
   ```
   Place your `EOY_Grade_levels.json` benchmark data file in the `assets/` directory.

## Usage 💻

### Web Interface

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open your browser** to the displayed URL (typically `http://localhost:7860`)

3. **Upload and analyze**:
   - Upload an IXL Diagnostic Report PDF
   - Select the student's grade level
   - Enter the student's name
   - Click "Analyze Report"

### Command Line Testing

For development and testing:

```bash
python build_graph.py
```

This will run the agent with the example PDF in the `assets/` directory.

## File Structure 📁

```
student-assessment-analyzer/
├── app.py                      # Gradio web interface
├── build_graph.py             # Main agent and LangGraph workflow
├── pdf_parser.py              # Multi-strategy PDF parsing
├── user_input_parser.py       # Subject extraction from parsed text
├── tools.py                   # LLM-bound calculation tools (percentiles, grades)
├── grade_reader.py            # **CRITICAL**: Benchmark data provider for LLM tools
├── model.py                   # LLM configuration
├── prompts.py                 # System prompts and templates
├── assets/
│   ├── EOY_Grade_levels.json  # **REQUIRED**: National benchmark data
│   └── *.pdf                  # Sample diagnostic reports
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

## Key Technologies 🛠️

- **[LangGraph](https://langchain-ai.github.io/langgraph/)**: Agent workflow orchestration
- **[Gradio](https://gradio.app/)**: Web interface
- **[PyMuPDF](https://pymupdf.readthedocs.io/)**: Primary PDF text extraction
- **[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)**: OCR for image-based PDFs
- **[LlamaParse](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/)**: Fallback PDF parsing
- **[OpenAI](https://openai.com/) / [Google Gemini](https://deepmind.google/technologies/gemini/)**: LLM providers
- **[Pandas](https://pandas.pydata.org/)**: Data manipulation and analysis

## Configuration ⚙️

### Model Selection

Edit `model.py` to change the LLM provider:

```python
# For OpenAI
model = ChatOpenAI(model="gpt-4o-mini")

# For Google Gemini (default)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20")
```

### Benchmark Data & LLM Tool Integration

The application's accuracy depends on the critical relationship between `grade_reader.py` and the LLM tools:

#### How It Works:
1. **`grade_reader.py`** loads `EOY_Grade_levels.json` and converts it to a clean Pandas DataFrame
2. **LLM tools in `tools.py`** call `get_grade_data()` to access this standardized data
3. **The LLM automatically invokes these tools** during assessment to perform calculations
4. **All percentile and grade-level determinations** use this authoritative dataset

#### Data Structure:
The `get_grade_data()` function returns a DataFrame with columns:
- `Subject`: Official subject names (e.g., "End-of-Year Math: Overall (K-8)")
- `Grade`: Grade levels (K, 1, 2, ..., 12)  
- `Percentile`: Performance percentiles (10th, 20th, ..., 99th)
- `Score`: Benchmark scores for each grade/percentile combination

#### Critical Dependencies:
- **`calculate_percentile`** → Uses benchmark scores to determine student percentile ranking
- **`calculate_performing_grade`** → Uses 85th percentile thresholds to find actual performing grade
- **`calculate_next_grade_threshold`** → Uses 70th percentile scores for advancement criteria

**⚠️ Important**: The LLM tools will fail if `EOY_Grade_levels.json` is missing or malformed, as they depend on `grade_reader.py` for all calculations.

#### Required JSON Structure:

```json
[
  {
    "title": "End-of-Year Math: Overall (K-8)",
    "data": [
      {
        "Percentile": 10,
        "K": 200,
        "1": 250,
        "2": 300,
        ...
      },
      ...
    ]
  },
  ...
]
```

## Example Output 📋

The application generates comprehensive reports including:

- **Key Findings**: Above/On/Below grade level subjects
- **Overview**: Performance summary
- **Current Performing Grade**: Overall grade level assessment
- **Performance Dashboard**: Detailed HTML table with:
  - Subject scores
  - Performance bands (color-coded)
  - Percentile rankings
  - Next grade thresholds
  - Specific skill recommendations
- **Summary**: Strengths, improvements, and readiness assessment

## Development 🔧

### Adding New Tools

1. Create tool functions in `tools.py`
2. Add them to the `tools` list in `StudentAssessment.__init__()`
3. Update prompts in `prompts.py` to reference new tools

### Extending PDF Parsing

The `EnhancedPDFParser` class supports multiple parsing strategies. To add new methods:

1. Add parsing method to `pdf_parser.py`
2. Integrate into the parsing pipeline
3. Update adequacy checks as needed

### Customizing Reports

Modify `ASSESSMENT_PROMPT` in `prompts.py` to change report format, styling, or content structure.

## Troubleshooting 🔍

### Common Issues

1. **PDF parsing fails**: Ensure PDFs contain text or clear images for OCR
2. **Missing benchmark data**: Verify `EOY_Grade_levels.json` is in `assets/` directory
3. **API errors**: Check your API keys in `.env` file
4. **Tool calculation errors**: Verify subject names match benchmark data exactly

### Debug Mode

Enable verbose logging by adding debug prints or running:

```bash
python build_graph.py
```

This runs the agent directly and shows detailed processing steps.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

[Add your license information here]

## Support 💬

For issues, questions, or contributions, please [create an issue](link-to-issues) or [contact the development team](contact-info).

---

**Note**: This application is designed specifically for IXL Diagnostic Reports. For other assessment formats, you may need to modify the parsing and extraction logic.