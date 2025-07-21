# Getting Started

This guide walks you through installing dependencies and running the application.

## Requirements
- Python 3.11+
- Node 18+ for the React frontend

## Prerequisites

Install [`uv`](https://github.com/astral-sh/uv) and [`Poetry`](https://python-poetry.org/) with `pip` or `pipx`:

```bash
pip install uv poetry
# or
pipx install uv poetry
```

1. **Create and activate a virtual environment**

  ```bash
  python -m venv venv
  source venv/bin/activate
  ```

2. **Install the backend and web server**

  ```bash
  pip install -r requirements-dev.txt
  pre-commit install  # optional git hooks
  ```


## Frontend Setup
```bash
cd frontend/faa-doc-checker
npm install
```

## Running the Application
Start the backend in one terminal:
```bash
cd backend
python -m uvicorn backend.main:app --reload
```
Start the frontend in another terminal:
```bash
cd frontend/faa-doc-checker
npm run dev
```

## Command Line Usage
The CLI accepts a file and document type:
```bash
python cli.py --file mydoc.docx --type "Advisory Circular" --group-by category
```
See `--help` for all options.
