# AGENTS.md — Coding and Debugging Guidelines

This document describes the rules and expectations for AI coding and debugging agents in this repository. Follow these instructions to ensure all code contributions are correct, secure, and production-ready on the first pass.

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

## Security Scanning (NEW)
* **All commits must pass `Snyk` vulnerability scanning.**
  * Run `snyk test` (via the `snyk-security` MCP server) over the full repo.
  * Any **high** or **critical** issue blocks the merge; the agent must fix or document why a false-positive.
  * Re-run the scan after every change that adds dependencies or alters build scripts.

## External Tools & MCP Servers
Agents may (and should) call these servers when relevant:

| Tool | Purpose |
|------|---------|
|`exa`|Codebase search & structural queries|
|`collaborative-reasoning`|Deep reflective reasoning on complex tasks|
|`mem0-memory-mcp`|Recall decisions, design notes, or historical context|
|`mcp-obsidian`|Write or update docs/ADRs in the linked Obsidian vault|
|`snyk-security`|Static dependency & code-level security scanning|

Calls are made through OpenAI function-calling; results must be acted on or surfaced to reviewers.

---

## Security and Best Practices

* Use the latest recommended Python and library best practices.
* Avoid deprecated, unmaintained, or insecure libraries and patterns.
* Actively check for and address security vulnerabilities.
* Never commit code with known security issues or technical debt.
* Do not introduce new dependencies unless required and reviewed.

---

## Code Quality

* Prioritize clarity, readability, and maintainability at all times.
* Avoid unnecessary complexity, convoluted logic, long functions, or long lines.
* Structure code so that it is easy to understand and maintain by others.

---

## Fixes & Refactoring

* Any fix for lint, test, or security issues must **not** introduce new problems elsewhere.
* Always re-run all lints and tests after any change.
* Refactor only as necessary to resolve problems or improve code quality.
* Do not introduce unrelated changes in a single commit.

---

## System Messages, Debugging, and Documentation

* **User-facing messages** must be clear and actionable.
  *Example: “Replace {x} with {y}.”*
* **Debug and log messages** (for agents) must provide all needed context for troubleshooting efficiently.
* **Documentation** (including README and docstrings) must be written for beginners.
  Aim for clarity and grace—explain concepts simply.

---

## First-Pass Correctness

* All code must be correct, complete, and production-ready on the first submission.
* Never propose partial, incomplete, or “fix later” code.
* If code cannot be made to pass all lints and tests, stop and explain the issue for human review.

---

## Multi-Language Projects

* Only modify code in Python unless specifically instructed otherwise.
* If asked to code in another stack (e.g., JS/TS), apply the equivalent linting and testing discipline (e.g., ESLint, TypeScript, pnpm, Vitest).
* For environment or workflow setup, see CONTRIBUTING.md.

---

## Before You Commit or Merge

**Agents must:**

1. Run `ruff .` and `black --check .` and resolve any issues before committing.
2. Run all tests (`pytest` or project equivalent) and ensure all pass.
3. Confirm no test or lint error is ignored, suppressed, or skipped.
4. Ensure all user and debug messages are clear and useful.
5. If uncertain, prompt for a code review or highlight specific questions in the commit.

---

**All code will be reviewed and must meet these standards before it is merged. Code as if your work is immediately published and scrutinized for quality and security.**

---

## References

* [OpenAI Codex Docs: AGENTS.md](https://platform.openai.com/docs/codex/overview#create-an-agents-md)
* [ruff documentation](https://docs.astral.sh/ruff/)
* [black documentation](https://black.readthedocs.io/en/stable/)
