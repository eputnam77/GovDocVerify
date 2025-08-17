"""Tests for non-goals guardrails to ensure irrelevant docs are rejected."""

import pytest

from govdocverify.document_checker import FAADocumentChecker


def test_rejects_non_government_docs() -> None:
    """NG-01: system should reject documents outside scope."""
    checker = FAADocumentChecker()
    result = checker.run_all_document_checks("https://example.com/doc.docx")
    assert not result.success
    assert any("Non-government" in issue["message"] for issue in result.issues)


@pytest.mark.parametrize("path", ["document.pdf", "document.doc"])
def test_exclude_legacy_formats(path: str) -> None:
    """NG-02: legacy document formats are ignored."""
    checker = FAADocumentChecker()
    result = checker.run_all_document_checks(path)
    assert not result.success
    assert any("Legacy file format" in issue["message"] for issue in result.issues)
