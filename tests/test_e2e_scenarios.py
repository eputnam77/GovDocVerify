"""Placeholder tests for end-to-end scenarios."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_cli_single_file_run(tmp_path: Path) -> None:
    """E2E-A: CLI single-file run with exports and fail-on flag."""
    sample = tmp_path / "sample.txt"
    sample.write_text("simple content")

    script = (
        "import json, sys\n"
        "from govdocverify import cli\n"
        "def stub_process_document(file_path, doc_type, visibility_settings=None, group_by='category'):\n"
        "    return {'has_errors': True, 'rendered': 'stub', 'by_category': {}, 'metadata': {}}\n"
        "cli.process_document = stub_process_document\n"
        "sys.argv = ['cli.py', '--file', sys.argv[1], '--type', 'ORDER', '--json']\n"
        "raise SystemExit(cli.main())\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(sample)], capture_output=True, text=True
    )

    assert completed.returncode == 1
    last_line = completed.stdout.strip().splitlines()[-1]
    result = json.loads(last_line)
    assert {
        "has_errors",
        "rendered",
        "by_category",
        "metadata",
    } <= result.keys()
    assert result["has_errors"] is True


@pytest.mark.skip("E2E-B: API + frontend integration not implemented")
def test_api_frontend_integration() -> None:
    """E2E-B: API upload and frontend rendering with downloadable exports."""
    ...


@pytest.mark.skip("E2E-C: batch gate under STRICT_MODE not implemented")
def test_batch_gate_strict_mode() -> None:
    """E2E-C: batch processing fails build on High severity under STRICT_MODE=1."""
    ...
