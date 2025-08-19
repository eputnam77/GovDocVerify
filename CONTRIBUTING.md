# Contributing to GovDocVerify Sandbox

Thank you for your interest in contributing to the GovDocVerify Sandbox! This guide will help you get started with the development process.

## Code Formatting and Pre-commit

We use [Black](https://black.readthedocs.io/) for code formatting and
[pre-commit](https://pre-commit.com/) to run formatting, linting, and security
checks before each commit.

**Setup:**

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```
2. Install the git hooks:
   ```bash
   pre-commit install
   ```
3. Run all checks (optional but recommended before committing):
   ```bash
   pre-commit run --all-files
   ```

Pre-commit will now run automatically on `git commit` and block the commit if
any check fails. Re-run the commit after fixing the reported issues.

## Development Setup

1. Clone the repository
2. Set up a Python 3.11–3.13 environment (3.12 recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies (choose **one** approach):
   ```bash
   pip install --upgrade pip
   pip install -r requirements-dev.txt  # includes requirements.txt
   ```
   Or with Poetry:
   ```bash
   poetry install --with dev
   ```
   Either method installs the same packages—no need to run both.
4. Install the project in editable mode:
   ```bash
   pip install -e .
   ```
5. Install pre-commit hooks:
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
pytest --cov=govdocverify
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Ensure pre-commit hooks pass
6. Submit a pull request

## Project Structure

- `govdocverify/`: Main package code
- `tests/`: Test files
- `frontend/`: React frontend application
- `backend/`: Backend API code

## Questions?

If you have questions about contributing, please open an issue for discussion.