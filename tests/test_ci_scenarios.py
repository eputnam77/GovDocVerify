"""Tests for CI-related scenarios such as batch processing."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

CI_BATCH_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ci_batch.py"


def _load_ci_batch():
    """Dynamically load the CI batch script as a module."""
    spec = importlib.util.spec_from_file_location("ci_batch", CI_BATCH_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_batch_mode_processing(tmp_path):
    """CI-01: multiple files are processed in one batch run."""
    module = _load_ci_batch()
    file1 = tmp_path / "a.docx"
    file2 = tmp_path / "b.docx"
    file1.write_text("doc1")
    file2.write_text("doc2")
    pattern = str(tmp_path / "*.docx")

    with patch.object(
        module,
        "process_document",
        return_value={"has_errors": False},
    ) as mock_process:
        exit_code = module.run_batch([pattern], "ORDER")

    assert exit_code == 0
    processed = [call.args[0] for call in mock_process.call_args_list]
    assert processed == [str(file1), str(file2)]


@pytest.mark.skip("CI-02: incremental CI runs not implemented")
def test_ci_incremental_runs_skip_unchanged() -> None:
    """CI-02: CI run skips documents that have not changed."""
    ...


@pytest.mark.skip("CI-03: parallel CI execution not implemented")
def test_ci_parallel_execution() -> None:
    """CI-03: CI processes documents in parallel for speed."""
    ...
