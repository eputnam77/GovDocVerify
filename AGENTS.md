# AGENTS.md — Coding and Debugging Guidelines

## Lint and Formatting
- **All code (new and modified) must fully comply with [ruff](https://github.com/astral-sh/ruff) and [black](https://github.com/psf/black).**
    - No warnings or errors for line length, complexity, or style.
    - Run `ruff .` and `black --check .` before every commit or pull request.

## Testing
- **Never break existing tests.**
- Add or update tests to maintain or improve coverage.
- Always re-run the full test suite after any code change.

## Security and Best Practices
- Always use the latest recommended Python and library best practices.
- Avoid deprecated or unsafe libraries, functions, or code patterns.
- Proactively check for and address security vulnerabilities.

## Code Quality
- Prioritize clarity, readability, and maintainability.
- Avoid unnecessary complexity, long lines, or convoluted logic.

## Fixes & Refactoring
- Any lint, test, or security fix must not introduce new issues elsewhere.
- Always recheck both lints and tests after every change.

## Before You Commit or Merge
1. Run `ruff .` and `black --check .` — fix any issues before proceeding.
2. Run all tests (`pytest` or equivalent) — ensure all pass.
3. Confirm no test or lint error is ignored or suppressed.
4. If you’re unsure, ask for a code review.

## Messages & Documentation
- Ensure all system messages intended for users are extremely clear and actionable. For example, "Replace {x} with {y}"
- Ensure all debug and logging messages intended to AI to debug provide what AI needs to debug correctly and efficiently the first time.
- Ensure all documentation, like README, are written for beginners. Ensure clarity and grace.


**Code will be reviewed and must meet these standards before it is merged.**

---

> **Remember:**
> Code as if your work is published and scrutinized for quality and security.

---

## **References**
- [OpenAI Codex Docs: AGENTS.md](https://platform.openai.com/docs/codex/overview#create-an-agents-md)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [black documentation](https://black.readthedocs.io/en/stable/)
