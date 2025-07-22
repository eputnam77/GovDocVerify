# Document Checker Tool

Validate FAA documents for style, terminology and accessibility issues. The project includes a React frontend and a FastAPI backend.

Full documentation is available in the `docs/` directory and on the generated site. See [Getting Started](docs/getting-started.md) for installation instructions.

## Features
- Automated checks for headings, formatting, terminology and more
- Displays document metadata (Title, Author, Last Modified By, Created and Modified)
- FastAPI endpoint for programmatic access
- Modern React interface with live preview
- Command line interface for local use

## Quickstart
```bash
python -m venv venv
source venv/bin/activate
# Install either from requirements-dev.txt or using Poetry
pip install -r requirements-dev.txt
# poetry install --with dev
python cli.py --file mydoc.docx --type "Advisory Circular"
```

For additional scenarios, API details and developer info, browse the docs.

## API Usage

Interact with the FastAPI backend directly using `curl`:

```bash
curl -F "doc_file=@mydoc.docx" -F "doc_type=Advisory Circular" \
  http://localhost:8000/process
```
