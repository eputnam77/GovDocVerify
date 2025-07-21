# ADR: CI skeleton and dependency locking

Date: 2025-07-21

## Status
Accepted

## Context
The project previously used requirements files without a lock file and had a basic CI workflow. To support reproducible builds and align with the tooling defined in `.dev/AGENTS.md`, we adopt Poetry as the dependency manager and add a GitHub Actions workflow that caches dependencies using the `poetry.lock` hash.

## Decision
- Maintain `pyproject.toml` as the single source of dependencies with `requires-python = ">=3.11,<4.0"`.
- Generate and commit `poetry.lock`.
- Add a `migrations/` directory for future database changes.
- Implement a `ci.yml` workflow caching `~/.cache/pypoetry` and `~/.cache/pip` keyed by `hashFiles('poetry.lock')`.

## Consequences
- Development environments can be reproduced reliably using `poetry install` and `uv pip sync`.
- CI runs faster due to dependency caching.
- Future schema migrations will live under `migrations/`.

