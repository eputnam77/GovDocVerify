# Developer Guide

This project uses standard Python tooling with a React frontend.

## Project Structure
```
project-root/
├── backend/            # FastAPI backend
├── govdocverify/ # Core package (to be moved under src/)
├── frontend/           # React + Vite app
├── docs/               # MkDocs documentation
├── tests/              # Unit tests
```

## Development Environment
Install dev requirements and pre-commit hooks:
```bash
pip install -r requirements-dev.txt
pre-commit install
```
Run the test suite with:
```bash
pytest
```
Lint and type-check:
```bash
ruff check .
mypy --strict govdocverify tests
```

## Contributing
See `CONTRIBUTING.md` for full guidelines.
