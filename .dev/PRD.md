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

## Architecture
The project is composed of a reusable Python package, a FastAPI service,
and a React frontend. Core checking logic lives under
`documentcheckertool/` and is shared by all interfaces:

- **CLI** – entry point `cli.py` lets users run checks locally.
- **API** – `backend/` packages the FastAPI application and routes.
- **Frontend** – `frontend/faa-doc-checker` provides the React interface.

All interfaces call `process_document` which invokes the
`FAADocumentChecker` to run category-specific checks. Export utilities
convert results to HTML, DOCX or PDF.

## Usage Scenarios
Typical ways to use the tool include:

- Single document analysis via `python cli.py --file mydoc.docx --type "Order"`.
- Batch checking through the `/process` API for integration with other systems.
- Continuous integration jobs that fail on high severity issues.

## Non-Goals
- Editing documents directly
- Supporting formats other than DOCX and plain text

## Development Environment
Python 3.11+ is required for the backend. The frontend relies on Node 18.
Install dependencies with one command such as `pip install -r
requirements-dev.txt` or `poetry install --with dev`. Pre-commit hooks run
Ruff, Black, MyPy and the Pytest suite on each commit.

## Repository Structure
Key folders include:

- `documentcheckertool/` – core package and checks
- `backend/` – FastAPI service
- `frontend/` – React application
- `docs/` – MkDocs site with guides and API reference
- `.dev/` – product docs, ADRs and task tracking

## Dependency Options
Use **one** of the following methods to install Python dependencies:

- `pip install -r requirements-dev.txt` for development (includes
  `requirements.txt`).
- `pip install -r requirements.txt` for runtime-only environments.
- `poetry install` (add `--with dev` for development extras) which reads
  `pyproject.toml`.

Installing from multiple files is unnecessary.

