"""Ensure coverage thresholds are enforced."""

from __future__ import annotations

import subprocess
import sys
from textwrap import dedent

import pytest

pytest.importorskip("pytest_cov")


def _run_pytest(tmp_path, threshold: int, source: str) -> subprocess.CompletedProcess[str]:
    """Run pytest in *tmp_path* with the given coverage *threshold*."""
    module = tmp_path / "module.py"
    module.write_text(dedent(source))
    test_file = tmp_path / "test_module.py"
    test_file.write_text("from module import func\n\n" "def test_func() -> None:\n" "    func()\n")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=.",
        "--cov-branch",
        f"--cov-fail-under={threshold}",
    ]
    return subprocess.run(cmd, cwd=tmp_path, text=True, capture_output=True)


def test_coverage_threshold_enforced(tmp_path):
    """Pytest exits with non-zero status when coverage is too low."""
    source = """
    from typing import NoReturn

    def func() -> None:
        if False:  # pragma: no cover
            _unreachable()

    def _unreachable() -> NoReturn:
        raise RuntimeError
    """
    result = _run_pytest(tmp_path, 100, source)
    assert result.returncode != 0
    assert "required test coverage of 100%" in result.stdout


def test_coverage_threshold_met(tmp_path):
    """Pytest passes when coverage requirement is satisfied."""
    source = """
    def func() -> None:
        pass
    """
    result = _run_pytest(tmp_path, 50, source)
    assert result.returncode == 0
