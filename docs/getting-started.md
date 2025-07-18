# Getting Started

This guide walks you through installing dependencies and running the application.

## Requirements
- Python 3.11+
- Node 18+ for the React frontend

## Backend Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```
Or with Poetry:
```bash
poetry install --with dev
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
uvicorn backend.main:app --reload
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
