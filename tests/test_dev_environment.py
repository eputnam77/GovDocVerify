"""Tests for developer environment and tooling."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit not installed")
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


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit not installed")
def test_env_setup_script(tmp_path: Path) -> None:
    """DEV-02: setup script provisions local environment."""
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
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "setup_env.sh"
    env = os.environ.copy()
    env.update({"SKIP_POETRY": "1", "SKIP_FRONTEND": "1"})
    subprocess.run([str(script_path)], cwd=repo, env=env, check=True)
    assert (repo / ".venv").exists()
    assert (repo / ".git" / "hooks" / "pre-commit").exists()


@pytest.mark.skip("DEV-03: lint staged integration not implemented")
def test_lint_staged_integration() -> None:
    """DEV-03: lint-staged checks staged files during commit."""
    ...


@pytest.mark.skip("DEV-04: task runner integration not implemented")
def test_task_runner_integration() -> None:
    """DEV-04: task runner executes defined development tasks."""
    ...
