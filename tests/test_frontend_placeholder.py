"""Tests for basic frontend upload and rendering workflow."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app


def test_frontend_upload_and_render(monkeypatch) -> None:
    """FE-01: uploading a document yields rendered HTML."""

    client = TestClient(app)
    sample_html = "<p>Hello world</p>"

    def fake_process(tmp_path, doc_type, vis, group_by="category"):
        return {"has_errors": False, "rendered": sample_html, "by_category": {}}

    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", fake_process)

    with open("tests/test_data/valid_readability.docx", "rb") as f:
        resp = client.post(
            "/process",
            files={"doc_file": ("doc.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"doc_type": "AC", "visibility_json": "{}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["rendered"] == sample_html
    assert "result_id" in data


def test_frontend_viewer_uses_iframe() -> None:
    """FE-02: rendered HTML is displayed via an iframe viewer."""

    path = Path("frontend/govdocverify/src/components/ResultsPane.tsx")
    content = path.read_text(encoding="utf-8")
    assert "iframe" in content
    assert "srcDoc" in content


def test_download_actions(monkeypatch) -> None:
    """FE-05: users can download DOCX and PDF results."""

    # Ensure frontend exposes download links
    path = Path("frontend/govdocverify/src/components/DownloadButtons.tsx")
    content = path.read_text(encoding="utf-8")
    assert "Download DOCX" in content
    assert "Download PDF" in content

    # Simulate a processing request and verify downloads
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr(
        "backend.api.process_document",
        lambda *a, **k: {"has_errors": False, "rendered": "", "by_category": {"ok": 1}},
    )

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
    rid = resp.json()["result_id"]

    docx = client.get(f"/results/{rid}.docx")
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")

    pdf = client.get(f"/results/{rid}.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


@pytest.mark.skip("FE-03: severity filter toggling not implemented")
def test_frontend_severity_filters() -> None:
    """Placeholder for FE-03."""
    ...


@pytest.mark.skip("FE-04: error banner not implemented")
def test_frontend_error_banner() -> None:
    """Placeholder for FE-04."""
    ...
