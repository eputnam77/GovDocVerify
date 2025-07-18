# ADR 1: Standard Python toolchain

Date: 2024-06-14

## Status
Accepted

## Context
The project started as an experimental sandbox. We now need a consistent development toolchain and CI approach.

## Decision
- Python 3.12 is the primary target with 3.11 kept for compatibility.
- Dependency management uses **Poetry** together with **uv** for creating virtual environments and syncing the lock file.
- Code quality tools are **Black**, **Ruff**, **MyPy**, **Bandit**, **Semgrep**, and **Pytest**.
- Pre‑commit hooks run these tools automatically.
- GitHub Actions will run the same gates and a Codex router workflow when enabled.

## Consequences
- A `poetry.lock` file becomes the single source of dependency versions.
- Developers run `poetry install && poetry sync && uv pip sync pyproject.toml` to replicate the environment.
- The repository includes `.github/workflows/agents.yml.disabled` and `scripts/next-agent.sh` to integrate with the multi‑agent pipeline.
