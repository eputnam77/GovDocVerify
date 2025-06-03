# Contributing to Document Checker Tool Sandbox

Thank you for your interest in contributing to the Document Checker Tool Sandbox! This guide will help you get started with the development process.

## Code Formatting

We use [Black](https://black.readthedocs.io/) for code formatting.
A pre-commit hook is set up to automatically format code before each commit.

**Setup:**
1. Install pre-commit:
   `pip install pre-commit`
2. Install the hooks:
   `pre-commit install`

This ensures your code is formatted with Black before every commit.

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Bandit**: Security linting
- **Pre-commit hooks**: Automated checks before commits

## Running Tests

Run the test suite with:
```bash
pytest
```

For coverage reports:
```bash
pytest --cov=documentcheckertool
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Ensure pre-commit hooks pass
6. Submit a pull request

## Project Structure

- `documentcheckertool/`: Main package code
- `tests/`: Test files
- `frontend/`: React frontend application
- `backend/`: Backend API code

## Questions?

If you have questions about contributing, please open an issue for discussion.