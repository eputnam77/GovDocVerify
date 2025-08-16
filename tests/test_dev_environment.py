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


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit not installed")
def test_lint_staged_integration(tmp_path: Path) -> None:
    """DEV-03: lint-staged checks staged files during commit."""
    repo = tmp_path
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "lint_staged.py"

    (repo / ".pre-commit-config.yaml").write_text(
        f"""
repos:
  - repo: local
    hooks:
      - id: lint-staged
        name: lint-staged
        entry: python {script_path}
        language: system
        pass_filenames: false
"""
    )

    (repo / "package.json").write_text(
        """
{
  "lint-staged": {
    "*.txt": "python -c \"import sys; print('linted', *sys.argv[1:])\""
  }
}
"""
    )

    (repo / "staged.txt").write_text("data\n")
    (repo / "unstaged.txt").write_text("other\n")

    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["pre-commit", "install"], cwd=repo, check=True)
    subprocess.run(["git", "add", "staged.txt"], cwd=repo, check=True)
    result = subprocess.run(
        ["git", "commit", "-m", "test"], cwd=repo, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "linted staged.txt" in result.stdout
    assert "unstaged.txt" not in result.stdout


def test_task_runner_integration(tmp_path: Path) -> None:
    """DEV-04: task runner executes defined development tasks."""
    repo_root = Path(__file__).resolve().parents[1]

    lint_result = subprocess.run(["make", "lint"], cwd=repo_root, capture_output=True, text=True)
    assert lint_result.returncode == 0

    temp_repo = tmp_path / "repo"
    shutil.copytree(repo_root, temp_repo)
    fmt_result = subprocess.run(["make", "format"], cwd=temp_repo, capture_output=True, text=True)
    assert fmt_result.returncode == 0

    env = os.environ.copy()
    env["PYTEST_ADDOPTS"] = '-k "test_dev_environment and not task_runner_integration"'
    test_result = subprocess.run(
        ["make", "test"], cwd=repo_root, env=env, capture_output=True, text=True
    )
    assert test_result.returncode == 0
