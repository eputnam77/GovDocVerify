"""Tests for reliability and error resilience."""

import asyncio
import multiprocessing
import os
import signal
import time
from pathlib import Path

import httpx
import pytest

from govdocverify.document_checker import FAADocumentChecker
from govdocverify.processing import build_results_dict
from govdocverify.utils.network import fetch_url


def test_retry_transient_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """RE-01: operations are retried on transient errors before failing."""

    attempts = {"count": 0}

    def flaky_get(url: str, **_: object) -> httpx.Response:
        attempts["count"] += 1
        raise httpx.RequestError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", flaky_get)

    with pytest.raises(httpx.RequestError):
        fetch_url("https://example.com")

    assert attempts["count"] == 3


def test_partial_failure_reporting(monkeypatch: pytest.MonkeyPatch) -> None:
    """RE-02: partial failures should surface detailed reports."""

    checker = FAADocumentChecker()

    def boom(doc: object, doc_type: str | None) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        checker,
        "_get_check_modules",
        lambda: [(checker.readability_checks, "readability")],
    )
    monkeypatch.setattr(checker.readability_checks, "check_document", boom)

    result = checker.run_all_document_checks("content")
    assert result.partial_failures and result.partial_failures[0]["category"] == "readability"
    assert "boom" in result.partial_failures[0]["error"]

    out = build_results_dict(result)
    assert out["partial_failures"][0]["category"] == "readability"


def test_graceful_shutdown_under_load(tmp_path: Path) -> None:
    """RE-03: system shuts down gracefully during high load."""

    port = 8765

    def _run_server() -> None:
        from fastapi import FastAPI  # noqa: E402,I001
        from backend.graceful import run  # noqa: E402

        app = FastAPI()

        @app.get("/slow")
        async def slow() -> dict[str, str]:
            await asyncio.sleep(0.5)
            return {"status": "ok"}

        @app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        run(app, host="127.0.0.1", port=port)

    proc = multiprocessing.Process(target=_run_server)
    proc.start()

    base_url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            httpx.get(f"{base_url}/health", timeout=0.2)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.fail("server failed to start")

    async def _hammer() -> list[httpx.Response]:
        async with httpx.AsyncClient() as client:
            tasks = [asyncio.create_task(client.get(f"{base_url}/slow")) for _ in range(5)]
            await asyncio.sleep(0.1)
            os.kill(proc.pid, signal.SIGTERM)
            return await asyncio.gather(*tasks)

    responses = asyncio.run(_hammer())

    proc.join(timeout=30)
    assert proc.exitcode == 0
    assert all(r.status_code == 200 for r in responses)
