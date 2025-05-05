# Developer Documentation

## Running the Document Checker Tool

The Document Checker Tool can be run in two ways:
1. Web Interface (Gradio UI)
2. Command Line Interface (CLI)

## Prerequisites

Before running the tool, ensure you have:
1. Python 3.8 or higher installed
2. Poetry package manager installed
3. All dependencies installed via `poetry install`

## Web Interface (Gradio)

### Starting the Web Server

1. Set up and activate the conda environment:
```bash
conda create -n doc-checker python=3.10
conda activate doc-checker
pip install -r requirements.txt
```

2. Start the Gradio server:
```bash
python -m documentcheckertool.interfaces
```

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
poetry run python -m documentcheckertool.interfaces.gradio_ui --debug

# Start with specific checks enabled
poetry run python -m documentcheckertool.interfaces.gradio_ui --enabled-checks readability,spelling

# Set custom check configurations
poetry run python -m documentcheckertool.interfaces.gradio_ui --config path/to/config.yaml

# Enable development mode with hot-reloading
poetry run python -m documentcheckertool.interfaces.gradio_ui --dev

# Set maximum file size (in MB)
poetry run python -m documentcheckertool.interfaces.gradio_ui --max-file-size 50
```

### Gradio UI Debugging

For troubleshooting the web interface:

```bash
# Enable verbose logging
export GRADIO_DEBUG=True
export DOC_CHECKER_LOG_LEVEL=DEBUG
poetry run python -m documentcheckertool.interfaces.gradio_ui

# Save server logs to file
poetry run python -m documentcheckertool.interfaces.gradio_ui --log-file ui_debug.log

# Enable performance profiling
poetry run python -m documentcheckertool.interfaces.gradio_ui --profile
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
poetry run doc-checker check path/to/document.docx
```

### Advanced CLI Options

```bash
# Run specific checks only
poetry run doc-checker check --checks readability,acronyms path/to/document.docx

# Output results in different formats
poetry run doc-checker check --format json path/to/document.docx
poetry run doc-checker check --format csv path/to/document.docx

# Generate a detailed report
poetry run doc-checker check --report detailed path/to/document.docx

# Process multiple files
poetry run doc-checker check path/to/doc1.docx path/to/doc2.docx

# Exclude specific checks
poetry run doc-checker check --exclude heading,spacing path/to/document.docx

# Set custom severity levels
poetry run doc-checker check --min-severity WARNING path/to/document.docx
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
poetry run doc-checker batch ./docs/

# Process with specific patterns
poetry run doc-checker batch --pattern "*.docx" ./docs/

# Generate summary report
poetry run doc-checker batch --summary-only ./docs/
```

## API Usage

The checker can also be used programmatically:

```python
from document_checker import DocumentChecker

checker = DocumentChecker()
results = checker.check_file("document.docx")

# Access results
for issue in results.issues:
    print(f"{issue.severity}: {issue.message} at line {issue.line_number}")
```

## Development Notes

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/test_readability.py
poetry run pytest tests/test_acronyms.py

# Run with coverage
poetry run pytest --cov=document_checker
```

### Debug Mode

For detailed logging during development:

```bash
export DOC_CHECKER_DEBUG=True
poetry run doc-checker check --verbose path/to/document.docx
```

### Contributing

1. Create a new branch for your feature
2. Ensure all tests pass
3. Add new tests for new functionality
4. Update documentation
5. Submit a pull request

For more information, see CONTRIBUTING.md