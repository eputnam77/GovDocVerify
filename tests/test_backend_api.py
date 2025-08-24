from unittest import mock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from govdocverify.utils.security import RateLimiter, rate_limiter


def _mock_result():
    return {
        "has_errors": False,
        "rendered": "",
        "by_category": {},
        "severity": "LOW",
        "metadata": {},
    }


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    rate_limiter.requests.clear()
    yield
    rate_limiter.requests.clear()


def test_invalid_file_type(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("backend.api.process_document", lambda *args, **kwargs: _mock_result())
    with mock.patch("govdocverify.utils.security.filetype.guess") as guess:
        guess.return_value = None
        resp = client.post(
            "/process",
            files={"doc_file": ("x.txt", b"bad")},
            data={"doc_type": "AC"},
        )
    assert resp.status_code == 400


def test_rate_limiting(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("backend.api.process_document", lambda *args, **kwargs: _mock_result())
    with (
        mock.patch(
            "govdocverify.utils.security.rate_limiter",
            RateLimiter(max_requests=1, time_window=60),
        ) as rl,
        mock.patch("govdocverify.utils.security.filetype.guess") as guess,
    ):
        guess.return_value = mock.Mock(
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        rl.requests.clear()
        resp1 = client.post(
            "/process",
            files={"doc_file": ("x.docx", b"ok")},
            data={"doc_type": "AC"},
        )
        resp2 = client.post(
            "/process",
            files={"doc_file": ("x.docx", b"ok")},
            data={"doc_type": "AC"},
        )
    assert resp1.status_code == 200
    assert resp2.status_code == 429


def test_process_contract(monkeypatch):
    """API-01: /process returns expected JSON structure."""
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {
        "has_errors",
        "rendered",
        "by_category",
        "result_id",
        "severity",
        "metadata",
    }
    assert resp.headers["content-type"].startswith("application/json")


def test_process_validation_errors(monkeypatch):
    """API-02: oversized or wrong MIME yield 413/415."""
    client = TestClient(app)
    from fastapi import HTTPException

    def raise_413(*args, **kwargs):
        raise HTTPException(status_code=413, detail="too large")

    monkeypatch.setattr("backend.api.validate_file", raise_413)
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    assert resp.status_code == 413

    def raise_415(*args, **kwargs):
        raise HTTPException(status_code=415, detail="bad mime")

    monkeypatch.setattr("backend.api.validate_file", raise_415)
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    assert resp.status_code == 415


def test_invalid_visibility_json(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC", "visibility_json": "{bad json"},
    )
    assert resp.status_code == 400


def test_invalid_group_by(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC", "group_by": "unknown"},
    )
    assert resp.status_code == 400


def test_process_idempotent(monkeypatch):
    """API-03: same file + options produce identical results."""
    client = TestClient(app)

    def proc(tmp_path, doc_type, *_, **__):
        return {"has_errors": False, "rendered": "ok", "by_category": {}}

    monkeypatch.setattr("backend.api.process_document", proc)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)

    def send():
        return client.post(
            "/process",
            files={"doc_file": ("x.docx", b"ok")},
            data={"doc_type": "AC"},
        ).json()

    first = send()
    second = send()
    assert first == second


def test_process_concurrent_requests(monkeypatch):
    """API-04: concurrent requests finish successfully."""
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    monkeypatch.setattr(
        "govdocverify.utils.security.rate_limiter",
        RateLimiter(max_requests=100, time_window=60),
    )

    def send():
        return client.post(
            "/process",
            files={"doc_file": ("x.docx", b"ok")},
            data={"doc_type": "AC"},
        )

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=5) as ex:
        responses = list(ex.map(lambda _: send(), range(10)))

    assert all(r.status_code == 200 for r in responses)


def test_download_results(monkeypatch):
    """API-05: downloaded DOCX and PDF contain expected headers."""
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)

    def proc(tmp_path, doc_type, *_, **__):
        return {"has_errors": False, "rendered": "", "by_category": {"ok": 1}}

    monkeypatch.setattr("backend.api.process_document", proc)
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    result_id = resp.json()["result_id"]
    d_resp = client.get(f"/results/{result_id}.docx")
    assert d_resp.status_code == 200
    assert d_resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )
    assert d_resp.content.startswith(b"PK")
    p_resp = client.get(f"/results/{result_id}.pdf")
    assert p_resp.status_code == 200
    assert p_resp.headers["content-type"].startswith("application/pdf")
    assert p_resp.content.startswith(b"%PDF")


def test_download_missing_result():
    """API-06: requesting unknown result returns 404."""
    client = TestClient(app)
    resp = client.get("/results/does-not-exist.pdf")
    assert resp.status_code == 404


def test_download_unsupported_format(monkeypatch):
    """API-07: unsupported formats return 400."""
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    result_id = resp.json()["result_id"]
    bad = client.get(f"/results/{result_id}.txt")
    assert bad.status_code == 400


def test_download_from_disk(monkeypatch):
    """API-08: downloads work even if in-memory cache is cleared."""
    client = TestClient(app)
    monkeypatch.setattr("backend.api.validate_file", lambda *a, **k: None)
    monkeypatch.setattr("backend.api.process_document", lambda *a, **k: _mock_result())
    resp = client.post(
        "/process",
        files={"doc_file": ("x.docx", b"ok")},
        data={"doc_type": "AC"},
    )
    result_id = resp.json()["result_id"]
    # Simulate another worker by clearing in-memory cache.
    from backend import api as bapi

    with bapi._RESULTS_LOCK:
        bapi._RESULTS.clear()
    resp2 = client.get(f"/results/{result_id}.pdf")
    assert resp2.status_code == 200
