# Document Checker Tool PRD

## Overview
This product validates Word documents against FAA style standards and now
extracts document metadata for display.

## Key Features
- Automated checks for formatting, headings, and accessibility
- Metadata extraction (Title, Author, Last Modified By, Created, Modified)
  displayed at the start of each report
- React UI page allows users to upload a document, view the results on screen,
  and download a DOCX or PDF of those results
- FastAPI backend exposes an API endpoint for document processing

## Non-Goals
- Editing documents directly
- Supporting formats other than DOCX and plain text

## Dependency Options
Use **one** of the following methods to install Python dependencies:

- `pip install -r requirements-dev.txt` for development (includes
  `requirements.txt`).
- `pip install -r requirements.txt` for runtime-only environments.
- `poetry install` (add `--with dev` for development extras) which reads
  `pyproject.toml`.

Installing from multiple files is unnecessary.

