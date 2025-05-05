# Developer Documentation

## Running the Document Checker Tool

The Document Checker Tool can be run in two ways:
1. Web Interface (Gradio UI)
2. Command Line Interface (CLI)

## Prerequisites

Before running the tool, ensure you have:
1. Python 3.9 or higher installed
2. pip (Python package installer)
3. All dependencies installed via `pip install -r requirements.txt`

## Web Interface (Gradio)

### Starting the Web Server

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Gradio server:
```bash
python app.py
```

The server will start at `http://0.0.0.0:7860` by default.

### Web Interface Features

- **Document Upload**: Supports .docx, .pdf, and .txt files
- **Check Selection**: Choose which checks to run
- **Results Display**: Interactive results panel showing:
  - Check results categorized by severity
  - Suggested fixes
  - Line numbers and context
  - Export options for results

### Advanced Gradio UI Options

The web interface supports additional options when starting the server:

```bash
# Enable debugging and detailed logging
python app.py --debug

# Start with specific checks enabled
python app.py --enabled-checks readability,spelling

# Set custom check configurations
python app.py --config path/to/config.yaml

# Enable development mode with hot-reloading
python app.py --dev

# Set maximum file size (in MB)
python app.py --max-file-size 50

# Run in CLI mode with specific file
python app.py --cli --file path/to/document.docx --type "Advisory Circular"

# Run web interface with custom host and port
python app.py --host 0.0.0.0 --port 8000

# Enable debug mode
python app.py --debug
```

### Gradio UI Debugging

For troubleshooting the web interface:

```bash
# Enable verbose logging
export GRADIO_DEBUG=True
export DOC_CHECKER_LOG_LEVEL=DEBUG
python app.py --debug

# Save server logs to file
python app.py --log-file ui_debug.log

# Enable performance profiling
python app.py --profile
```

### Browser Console Debugging

The web interface exposes debugging information in the browser console:
- Network requests and responses
- Check execution times
- Memory usage statistics
- Error traces

Access these by opening your browser's developer tools (F12) and checking the console tab.

### Configuration Options

The web interface can be configured via environment variables:

```bash
export DOC_CHECKER_PORT=8000       # Change default port
export DOC_CHECKER_HOST=0.0.0.0    # Allow external access
export DOC_CHECKER_DEBUG=True      # Enable debug mode
```

## Command Line Interface

### Basic Usage

Run checks on a single file:
```bash
python app.py --cli --file path/to/document.docx --type "Advisory Circular"
```

### Advanced CLI Options

```bash
# Run specific checks only
python app.py --cli --file path/to/document.docx --checks readability,acronyms

# Output results in different formats
python app.py --cli --file path/to/document.docx --format json
python app.py --cli --file path/to/document.docx --format csv

# Generate a detailed report
python app.py --cli --file path/to/document.docx --report detailed

# Process multiple files
python app.py --cli --file path/to/doc1.docx path/to/doc2.docx

# Exclude specific checks
python app.py --cli --file path/to/document.docx --exclude heading,spacing

# Set custom severity levels
python app.py --cli --file path/to/document.docx --min-severity WARNING
```

### Configuration File

Create a `.doc-checker.yaml` in your project root to set default options:

```yaml
checks:
  enabled:
    - readability
    - acronyms
    - headings
  disabled:
    - spacing

output:
  format: json
  report_type: detailed
  min_severity: WARNING

paths:
  exclude:
    - "**/draft/*"
    - "**/archive/*"
```

### Exit Codes

- 0: All checks passed
- 1: Some checks failed
- 2: Configuration error
- 3: File access error

### Batch Processing

For batch processing multiple documents:

```bash
# Process all documents in a directory
python app.py --batch ./docs/

# Process with specific patterns
python app.py --batch --pattern "*.docx" ./docs/

# Generate summary report
python app.py --batch --summary-only ./docs/
```

## API Usage

The checker can be used programmatically:

```python
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import format_results_to_html

# Initialize the checker
checker = FAADocumentChecker()

# Run checks on a document
results = checker.run_all_document_checks(
    document_path="document.docx",
    doc_type="Advisory Circular"
)

# Format results as HTML
html_output = format_results_to_html(results)

# Access individual issues
for issue in results.issues:
    print(f"{issue['severity']}: {issue['message']} at line {issue.get('line_number', 'unknown')}")
```

## Development Notes

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_readability.py
pytest tests/test_acronyms.py

# Run with coverage
pytest --cov=document_checker
```

### Debug Mode

For detailed logging during development:

```bash
export DOC_CHECKER_DEBUG=True
python app.py --verbose --file path/to/document.docx
```

### Contributing

1. Create a new branch for your feature
2. Ensure all tests pass
3. Add new tests for new functionality
4. Update documentation
5. Submit a pull request

For more information, see CONTRIBUTING.md