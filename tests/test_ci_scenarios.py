"""Tests for CI-related scenarios such as batch processing."""

from __future__ import annotations

import importlib.util
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

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


def test_ci_incremental_runs_skip_unchanged(tmp_path) -> None:
    """CI-02: CI run skips documents that have not changed."""
    module = _load_ci_batch()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo, check=True)

    file1 = repo / "a.docx"
    file2 = repo / "b.docx"
    file1.write_text("doc1")
    file2.write_text("doc2")
    subprocess.run(["git", "add", "a.docx", "b.docx"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)

    file1.write_text("doc1 updated")
    subprocess.run(["git", "commit", "-am", "update a"], cwd=repo, check=True)

    changed = module.get_changed_files("HEAD~1", ["*.docx"], repo)
    assert [Path(p).name for p in changed] == ["a.docx"]

    with patch.object(
        module,
        "process_document",
        return_value={"has_errors": False},
    ) as mock_process:
        exit_code = module.run_batch(changed, "ORDER")

    assert exit_code == 0
    processed = [Path(call.args[0]).name for call in mock_process.call_args_list]
    assert processed == ["a.docx"]


def _sleep_task(duration: float) -> None:
    """Helper task that simulates work by sleeping."""
    time.sleep(duration)


def test_parallel_ci_execution() -> None:
    """CI-03: CI processes documents in parallel for speed."""
    durations = [0.1] * 4

    start = time.perf_counter()
    for d in durations:
        _sleep_task(d)
    sequential = time.perf_counter() - start

    start = time.perf_counter()
    with ThreadPoolExecutor() as executor:
        list(executor.map(_sleep_task, durations))
    parallel = time.perf_counter() - start

    assert parallel < sequential * 0.75
