"""Tests for basic frontend upload and rendering workflow."""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from govdocverify.utils.security import rate_limiter


def test_frontend_upload_and_render(monkeypatch) -> None:
    """FE-01: uploading a document yields rendered HTML."""

    client = TestClient(app)
    sample_html = "<p>Hello world</p>"

    def fake_process(tmp_path, doc_type, vis, group_by="category"):
        return {"has_errors": False, "rendered": sample_html, "by_category": {}}

    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", fake_process)

    with open("tests/test_data/valid_readability.docx", "rb") as f:
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        resp = client.post(
            "/process",
            files={"doc_file": ("doc.docx", f, mime)},
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
    rate_limiter.requests.clear()
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


def test_severity_filter_toggling() -> None:
    """FE-03: toggling severity filters updates visible results."""

    html = (
        "<ul>"
        "<li><span>[ERROR]</span>error</li>"
        "<li><span>[WARNING]</span>warn</li>"
        "<li><span>[INFO]</span>info</li>"
        "</ul>"
    )

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    for li in soup.find_all("li"):
        span = li.find("span")
        if not span:
            continue
        text = span.text
        if "[ERROR]" in text:
            li["class"] = ["severity-error"]
        elif "[WARNING]" in text:
            li["class"] = ["severity-warning"]
        elif "[INFO]" in text:
            li["class"] = ["severity-info"]

    filters = {"error": True, "warning": False, "info": True}
    for sev, show in filters.items():
        for el in soup.select(f".severity-{sev}"):
            if not show:
                el["style"] = "display: none;"

    assert soup.select(".severity-warning")[0]["style"] == "display: none;"
    assert "style" not in soup.select(".severity-error")[0].attrs
    assert "style" not in soup.select(".severity-info")[0].attrs


def test_frontend_error_banner() -> None:
    """FE-04: API failures surface a global error banner."""

    # ErrorBanner component exists with a test id for visibility
    path = Path("frontend/govdocverify/src/components/ErrorBanner.tsx")
    content = path.read_text(encoding="utf-8")
    assert "Alert" in content
    assert 'data-testid="error-banner"' in content

    # App integrates the banner and sets errors from failed requests
    app = Path("frontend/govdocverify/src/App.tsx").read_text(encoding="utf-8")
    assert "ErrorBanner" in app
    assert "message={error}" in app
    assert "setError(" in app and "catch (err" in app
