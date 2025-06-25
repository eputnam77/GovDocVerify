# AGENTS.md — Coding and Debugging Guidelines

This document defines the rules and expectations for AI coding and debugging agents in this repository. **Follow these instructions to ensure all code contributions are correct, secure, and production-ready on the first pass.** Code as if your work will be immediately published and scrutinized for quality and security.

---

## Linting and Formatting

* **All code (new or modified) must fully comply with [ruff](https://docs.astral.sh/ruff/) and [black](https://black.readthedocs.io/en/stable/).**

  * There must be **no warnings or errors** for line length, complexity, style, or formatting.
  * Run `ruff .` and `black --check .` before any commit or pull request.
  * **Never ignore or suppress** linting errors or warnings. Treat warnings as errors.
  * Code must be ready for publication on the first pass—do not defer fixes.

---

## Testing

* **Never break existing tests.**

  * Always maintain or improve test coverage. Add or update tests for any code changes.
  * Re-run the entire test suite (`pytest` or project equivalent) after any code or test modification.
  * If a test fails, halt and correct the issue immediately. Do not suppress or skip failing tests.
  * **Maintain 90%+ test coverage**; fail CI if coverage drops below threshold.
  * Use `pytest-cov` and `coverage.py` for coverage reporting.
  * Include property-based tests with `hypothesis` for data validation and edge cases.

---

## Security Scanning and Best Practices

* Use the latest recommended Python and library best practices.
* Avoid deprecated, unmaintained, or insecure libraries and patterns.
* **Run security scans before every commit:**

  * `bandit -r src/` for Python-specific security issues
  * `pip-audit -r requirements.txt` for dependency vulnerabilities
  * `semgrep` for custom security rules (if configured)
* **Never commit API keys, tokens, or secrets**—use environment variables.
* Never commit code with known security issues or technical debt.
* Do not introduce new dependencies unless required and reviewed.
* Actively check for and address security vulnerabilities.
* **All commits must pass `Snyk` vulnerability scanning** (`snyk test` via the `snyk-security` MCP server). Any **high** or **critical** issue blocks the merge; false-positives must be documented. Re-scan after any dependency or build script changes.

---

## Dependency Management

* **Use modern tools:**

  * Prefer [`uv`](https://docs.astral.sh/uv/) for faster package installation.
  * Use `pyproject.toml` over `requirements.txt` when possible.
  * Pin dependencies appropriately; only set upper bounds when necessary.
  * Use lockfiles for reproducible builds.
* **Before adding new dependencies:**

  * Check if existing dependencies can solve the problem.
  * Verify packages are actively maintained and secure.
  * Add to the appropriate group (dev, test, security, etc.).
* **Run dependency audits regularly:**

  * `pip-audit` for vulnerabilities.
  * `uv pip compile` for dependency resolution.
  * Update dependencies when security issues are found.

---

## Code Quality

* Prioritize clarity, readability, and maintainability at all times.
* Avoid unnecessary complexity, convoluted logic, long functions, or long lines.
* Structure code for ease of understanding and maintenance.
* **Use static type checking with [MyPy](https://mypy.readthedocs.io/):**

  * Enable strict type checking mode.
  * Add type hints to all public functions and methods.
  * Use `mypy --strict` to catch type errors before runtime.
* **Python best practices:**

  * Use f-strings, comprehensions, `pathlib`, `dataclasses`, and/or `Pydantic` where appropriate.

---

## Pre-commit Requirements

**Agents must run the complete pre-commit pipeline before any commit:**

1. **Formatting and Linting:**

   ```bash
   ruff --fix .
   black --check .
   ```
2. **Type Checking:**

   ```bash
   mypy src/ --strict
   ```
3. **Testing:**

   ```bash
   pytest --cov=src --cov-report=term-missing
   coverage report --fail-under=90
   ```
4. **Security Scanning:**

   ```bash
   bandit -r src/ -f json -o bandit-report.json
   pip-audit -r requirements.txt
   ```
5. **Pre-commit Hooks:**

   ```bash
   pre-commit run --all-files
   ```

**All checks must pass before committing. Never bypass or suppress any failures.**

---

## External Tools & MCP Servers

Agents may (and should) call these servers when relevant:

| Tool                      | Purpose                                                |
| ------------------------- | ------------------------------------------------------ |
| `exa`                     | Codebase search & structural queries                   |
| `collaborative-reasoning` | Deep reflective reasoning on complex tasks             |
| `mem0-memory-mcp`         | Recall decisions, design notes, or historical context  |
| `mcp-obsidian`            | Write or update docs/ADRs in the linked Obsidian vault |
| `snyk-security`           | Static dependency & code-level security scanning       |

*Calls are made through OpenAI function-calling; results must be acted on or surfaced to reviewers.*

---

## Fixes & Refactoring

* Any fix for lint, test, or security issues must **not** introduce new problems elsewhere.
* Always re-run all lints and tests after any change.
* Refactor only as necessary to resolve problems or improve code quality.
* Do not introduce unrelated changes in a single commit.
* **Use conventional commits** with `commitizen` or `cz-git` for consistent commit messages.

---

## System Messages, Debugging, and Documentation

* **User-facing messages** must be clear and actionable.

  * Example: “Replace {x} with {y}.”
* **Debug/log messages** must provide context for troubleshooting.
* **Documentation** (README, docstrings) must be beginner-friendly—aim for clarity and grace.
* **Use structured logging** with Python’s `logging` or Pydantic.
* **Include meaningful log messages** at key execution points with unique identifiers and timestamps.

---

## First-Pass Correctness

* All code must be correct, complete, and production-ready on the first submission.
* Never propose partial, incomplete, or “fix later” code.
* If code cannot be made to pass all lints and tests, stop and explain the issue for human review.

---

## Multi-Language Projects

* Only modify Python code unless otherwise instructed.
* For other stacks (JS/TS), apply equivalent linting and testing discipline (ESLint, TypeScript, pnpm, Vitest, etc.).
* For environment or workflow setup, see CONTRIBUTING.md.

---

## Environment Setup Requirements

* **Python 3.11+** with virtual environment isolation
* **Essential tools installed:**

  * `ruff>=0.5.0`, `black>=24.4.2`, `mypy>=1.10.0`, `pytest>=8.0.0`, `pytest-cov>=5.0.0`
  * `hypothesis>=6.0.0`, `bandit>=1.9.0`, `pre-commit>=3.7.0`
* **Pre-commit hooks configured and installed**
* **CI/CD pipeline compatible** (GitHub Actions or equivalent)
* **For containerized environments** (Docker, Codespaces):

  * Include all development dependencies in the container.
  * Set up proper Python path, environment variables, and pre-commit hooks at container initialization.

---

## Performance and Optimization

* **Use fast development tools:**

  * `uv` for package install speed
  * `ruff` for fast linting
  * Parallel testing with `pytest-xdist`
* **Optimize for time and space complexity** in algorithms.
* **Handle edge cases and exceptions robustly.**
* **Implement proper error handling and secure sensitive data.**
* **Use caching strategies** where appropriate for performance.

---

## Before You Commit or Merge

**Agents must:**

1. Run `ruff .` and `black --check .` and resolve any issues before committing.
2. Run all tests (`pytest` or project equivalent) and ensure all pass.
3. Confirm no test or lint error is ignored, suppressed, or skipped.
4. Ensure all user and debug messages are clear and useful.
5. Run a complete security scan with bandit and pip-audit.
6. Verify test coverage meets 90%+ threshold.
7. Check type safety with MyPy strict mode.
8. Run pre-commit hooks on all files.
9. If uncertain, prompt for a code review or highlight specific questions in the commit.
