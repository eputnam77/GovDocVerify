"""Placeholder tests for developer environment and tooling."""

import pytest


@pytest.mark.skip("DEV-01: pre-commit enforcement not implemented")
def test_pre_commit_enforced() -> None:
    """DEV-01: pre-commit hooks run before commits."""
    ...


@pytest.mark.skip("DEV-02: environment setup script not implemented")
def test_env_setup_script() -> None:
    """DEV-02: setup script provisions local environment."""
    ...


@pytest.mark.skip("DEV-03: lint staged integration not implemented")
def test_lint_staged_integration() -> None:
    """DEV-03: lint-staged checks staged files during commit."""
    ...


@pytest.mark.skip("DEV-04: task runner integration not implemented")
def test_task_runner_integration() -> None:
    """DEV-04: task runner executes defined development tasks."""
    ...
