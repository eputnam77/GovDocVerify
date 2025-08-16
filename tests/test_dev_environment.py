"""Placeholder tests for developer environment and tooling."""

import subprocess
from pathlib import Path

import pytest


def test_pre_commit_enforced(tmp_path: Path) -> None:
    """DEV-01: pre-commit hooks run before commits."""
    repo = tmp_path

    (repo / ".pre-commit-config.yaml").write_text(
        """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
"""
    )

    # Create a file with trailing whitespace to trigger the hook
    (repo / "bad.txt").write_text("oops! \n")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["pre-commit", "install"], cwd=repo, check=True)
    subprocess.run(["git", "add", "bad.txt"], cwd=repo, check=True)
    result = subprocess.run(
        ["git", "commit", "-m", "test"], cwd=repo, capture_output=True, text=True
    )

    assert result.returncode != 0
    assert "trailing-whitespace" in result.stdout


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
