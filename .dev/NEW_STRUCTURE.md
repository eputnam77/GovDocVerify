# Repository structure

- `src/` and `govdocverify/` contain the application code.
- `tests/` holds unit and integration tests.
- `docs/` provides documentation built with MkDocs.
- `scripts/` stores helper scripts such as `next-agent.sh`.
- `migrations/` will store future database migration files.
- `ADR/` captures architecture decision records like `20250721-ci-skeleton.md`.
- Dependency versions are locked via `pyproject.toml` and `poetry.lock`.
- GitHub Actions workflows reside under `.github/workflows/`.
