"""Tests for non-goals guardrails to ensure irrelevant docs are rejected."""

from govdocverify.document_checker import FAADocumentChecker


def test_rejects_non_government_docs() -> None:
    """NG-01: system should reject documents outside scope."""
    checker = FAADocumentChecker()
    result = checker.run_all_document_checks("https://example.com/doc.docx")
    assert not result.success
    assert any("Non-government" in issue["message"] for issue in result.issues)


def test_excludes_legacy_formats() -> None:
    """NG-02: legacy document formats are ignored."""
    checker = FAADocumentChecker()
    result = checker.run_all_document_checks("document.pdf")
    assert not result.success
    assert any("Disallowed file format" in issue["message"] for issue in result.issues)
