#!/usr/bin/env bash
set -euo pipefail

# Helper script to provision the local development environment.
# Creates a Python virtual environment, installs dependencies, and enables tooling.

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

if [[ "${SKIP_VENV:-0}" != "1" ]]; then
  if [[ ! -d ".venv" ]]; then
    echo "Creating Python ${PYTHON_VERSION} virtual environment..."
    uv venv "${PYTHON_VERSION}"
  fi
fi

if [[ "${SKIP_POETRY:-0}" != "1" ]]; then
  echo "Installing Python dependencies via Poetry..."
  poetry install
  poetry sync
  uv pip sync pyproject.toml
fi

if [[ "${SKIP_PRECOMMIT:-0}" != "1" ]]; then
  echo "Installing pre-commit hooks..."
  pre-commit install
fi

if [[ -d "frontend" && "${SKIP_FRONTEND:-0}" != "1" ]]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm ci --legacy-peer-deps)
fi

echo "Development environment ready."
