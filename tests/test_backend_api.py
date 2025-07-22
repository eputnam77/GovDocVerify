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
