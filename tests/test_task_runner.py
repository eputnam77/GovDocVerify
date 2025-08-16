"""Tests for the Makefile task runner."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_make_lint_runs_successfully() -> None:
    result = subprocess.run(["make", "lint"], cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0


def test_make_format_runs_successfully(tmp_path: Path) -> None:
    tmp_repo = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, tmp_repo)
    result = subprocess.run(["make", "format"], cwd=tmp_repo, capture_output=True, text=True)
    assert result.returncode == 0


def test_make_test_runs_subset() -> None:
    env = os.environ.copy()
    env["PYTEST_ADDOPTS"] = "-k test_task_runner_dummy"
    result = subprocess.run(
        ["make", "test"], cwd=REPO_ROOT, env=env, capture_output=True, text=True
    )
    assert result.returncode == 0


def test_task_runner_dummy() -> None:
    assert True
