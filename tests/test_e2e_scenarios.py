"""Placeholder tests for end-to-end scenarios."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from govdocverify.utils.security import rate_limiter


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


def test_api_frontend_integration(monkeypatch) -> None:
    """E2E-B: API upload and frontend rendering with downloadable exports."""

    client = TestClient(app)
    rate_limiter.requests.clear()

    sample_html = "<p>Hello world</p>"

    # Stub out the heavy document processing and file validation.
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)

    def fake_process(tmp_path, doc_type, vis, group_by="category"):
        return {"has_errors": False, "rendered": sample_html, "by_category": {}}

    monkeypatch.setattr("backend.api.process_document", fake_process)

    with open("tests/test_data/valid_readability.docx", "rb") as f:
        resp = client.post(
            "/process",
            files={
                "doc_file": (
                    "doc.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"doc_type": "AC", "visibility_json": "{}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["rendered"] == sample_html
    assert "result_id" in data

    rid = data["result_id"]

    docx = client.get(f"/results/{rid}.docx")
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")

    pdf = client.get(f"/results/{rid}.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")

    # Ensure the frontend wires the API response to the viewer
    app_src = Path("frontend/govdocverify/src/App.tsx").read_text(encoding="utf-8")
    assert "axios.post" in app_src
    assert "ResultsPane" in app_src


@pytest.mark.skip("E2E-C: batch gate under STRICT_MODE not implemented")
def test_batch_gate_strict_mode() -> None:
    """E2E-C: batch processing fails build on High severity under STRICT_MODE=1."""
    ...
