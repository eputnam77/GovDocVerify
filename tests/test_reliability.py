"""Tests for reliability and error resilience."""

import httpx
import pytest

from govdocverify.document_checker import FAADocumentChecker
from govdocverify.processing import build_results_dict
from govdocverify.utils.network import fetch_url


def test_retry_transient_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """RE-01: operations are retried on transient errors before failing."""

    attempts = {"count": 0}

    def flaky_get(url: str) -> httpx.Response:
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


@pytest.mark.skip("RE-03: graceful shutdown under load not implemented")
def test_graceful_shutdown_under_load() -> None:
    """RE-03: system shuts down gracefully during high load."""
    ...
