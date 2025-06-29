# Student Assessment Analyzer

A comprehensive web application that analyzes IXL Diagnostic Report PDFs and generates detailed student performance assessments with grade-level comparisons, percentile rankings, and actionable recommendations.

## 🌟 Features

- **PDF Processing**: Automated parsing of IXL Diagnostic Report PDFs using multiple extraction methods
- **Performance Analysis**: Calculates percentiles, performing grade levels, and next grade thresholds
- **Interactive Dashboard**: Clean, responsive web interface built with Gradio
- **Comprehensive Reports**: HTML reports with performance dashboards, key findings, and recommendations
- **Grade-Level Benchmarking**: Compares student performance against national grade-level standards
- **Downloadable Reports**: Export assessment reports as HTML files

## 🏗️ Architecture

The application uses a graph-based agent architecture powered by LangGraph:

1. **User Input Parser**: Extracts text from PDF using PyMuPDF and LlamaParse
2. **Subject Mapping**: Maps extracted subjects to official benchmark subjects
3. **Assessment Node**: Coordinates performance calculations using tools
4. **Tool Execution**: Calculates percentiles, performing grades, and thresholds
5. **Synthesis**: Generates comprehensive HTML assessment reports

## 📋 Requirements

### Python Dependencies
```
gradio>=4.0.0
langchain-openai
langchain-google-genai
langchain-core
langgraph
pandas
pydantic
python-dotenv
PyMuPDF
llama-parse
asyncio
```

### Environment Variables
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_google_gemini_api_key
LLAMA_CLOUD_API_KEY=your_llama_parse_api_key
```

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd student-assessment-analyzer
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Add your API keys for Google Gemini and LlamaParse

5. **Prepare benchmark data**:
   - Ensure `assets/EOY_Grade_levels.json` contains the grade-level benchmark data
   - Add sample PDFs to the `assets/` directory for testing

## 🎯 Usage

### Web Interface

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to the provided URL (typically `http://localhost:7860`)

3. **Upload and analyze**:
   - Upload an IXL Diagnostic Report PDF
   - Select the student's grade level (1-8)
   - Enter the student's name
   - Click "Analyze Report"

4. **View results**:
   - Review the comprehensive assessment in the web interface
   - Download the HTML report for offline viewing

### Command Line Testing

Run the assessment engine directly:
```bash
python build_graph.py
```

## 📁 Project Structure

```
├── app.py                 # Gradio web interface
├── build_graph.py         # Main agent logic and graph construction
├── grade_reader.py        # Benchmark data loading and processing
├── model.py              # LLM model configuration
├── pdf_parser.py         # PDF text extraction utilities
├── prompts.py            # System prompts for different nodes
├── report_formatter.py   # HTML report generation
├── tools.py              # Performance calculation tools
├── user_input_parser.py  # PDF parsing and subject extraction
├── assets/
│   ├── EOY_Grade_levels.json    # Grade-level benchmark data
│   └── *.pdf                    # Sample diagnostic reports
└── README.md
```

## 🔧 Key Components

### Agent Nodes

- **`user_input_parser_node`**: Extracts and structures data from PDF reports
- **`subject_mapping_node`**: Maps extracted subjects to official benchmark subjects
- **`assessment_node`**: Coordinates performance analysis using available tools
- **`synthesis_node`**: Generates final structured HTML reports

### Tools

- **`calculate_all_metrics`**: Unified tool that calculates percentile, performing grade, and next grade threshold for any subject

### Data Models

- **`SubjectPerformance`**: Individual subject scores and recommendations
- **`PerformanceDashboard`**: Structured table data for report generation
- **`AssessmentReport`**: Complete structured assessment output

## 📊 Performance Metrics

The application calculates three key metrics for each subject:

1. **Percentile Ranking**: Student's position relative to national norms
2. **Performing Grade Level**: Highest grade level where student meets 70th percentile
3. **Next Grade Threshold**: Score needed to be "on track" for next grade

### Percentile Bands
- 🎉 90-100th: Outstanding!
- ⭐ 80-89th: Excellent!
- 🏆 70-79th: Great job!
- 👍 60-69th: Good work!
- 📈 50-59th: On track!
- 💪 40-49th: Keep going!
- 📚 30-39th: More practice needed
- 🔧 20-29th: Needs support
- 💡 10-19th: Let's work on this
- 🌱 1-9th: Starting fresh

## 🎨 Report Features

Generated reports include:

- **Key Findings**: Color-coded performance bands (Above/On/Below grade level)
- **Overview**: 2-3 sentence performance summary
- **Performance Dashboard**: Detailed table with scores, percentiles, and recommendations
- **Summary**: Strengths, areas for improvement, and readiness assessment
- **Methodology**: Data sources and calculation methods

## 🔍 Data Sources

Performance benchmarks are based on:
- IXL's National Norms for Diagnostic Assessment
- End-of-year grade-level expectations
- National percentile rankings for grades K-12

**Citation**: IXL's ELO score rating system [National Norms for IXL's Diagnostic in Grades K-12](https://www.ixl.com/materials/us/research/National_Norms_for_IXL_s_Diagnostic_in_Grades_K-12.pdf)

## 🛠️ Development

### Adding New Features

1. **New Assessment Metrics**: Add functions to `tools.py`
2. **Additional PDF Parsers**: Extend `pdf_parser.py`
3. **Custom Report Sections**: Modify `report_formatter.py`
4. **New Agent Nodes**: Add to `build_graph.py`

### Testing

```bash
# Test PDF parsing
python user_input_parser.py

# Test grade data loading
python grade_reader.py

# Test full assessment pipeline
python build_graph.py
```

### Configuration

- **Models**: Configure LLM models in `model.py`
- **Prompts**: Customize system prompts in `prompts.py`
- **UI Styling**: Modify CSS in `app.py`

## 📈 Performance Considerations

- **Caching**: Grade data is loaded once and reused
- **Async Processing**: PDF parsing and analysis run asynchronously
- **Error Handling**: Comprehensive error handling with fallbacks
- **Memory Management**: Efficient PDF processing with cleanup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions, issues, or feature requests:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include sample files and error messages when applicable

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
- Configure environment variables securely
- Use a production WSGI server (e.g., Gunicorn)
- Set up proper logging and monitoring
- Consider containerization with Docker

## ⚠️ Important Notes

- **API Keys**: Never commit API keys to version control
- **PDF Privacy**: Ensure student data privacy and compliance
- **Rate Limits**: Be aware of API rate limits for LLM services
- **Data Validation**: Always validate input data before processing

---

Built with ❤️ for educational assessment and student success.