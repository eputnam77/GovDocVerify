from unittest import mock

from fastapi.testclient import TestClient

from backend.main import app
from govdocverify.utils.security import RateLimiter


def _mock_result():
    return {"has_errors": False, "rendered": "", "by_category": {}}


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
        guess.return_value = mock.Mock(mime="application/msword")
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
    assert set(data) == {"has_errors", "rendered", "by_category"}
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
