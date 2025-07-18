---
title: Document Checker Tool
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.27.0
app_file: app.py
pinned: false
---

# Document Checker Tool

Validate FAA documents for style, terminology and accessibility issues. The project includes a React frontend, a FastAPI backend and a simple Gradio interface.

Full documentation is available in the `docs/` directory and on the generated site. See [Getting Started](docs/getting-started.md) for installation instructions.

## Features
- Automated checks for headings, formatting, terminology and more
- FastAPI endpoint for programmatic access
- Modern React interface with live preview
- Command line interface for local use

## Quickstart
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
python cli.py --file mydoc.docx --type "Advisory Circular"
```

For additional scenarios, API details and developer info, browse the docs.
