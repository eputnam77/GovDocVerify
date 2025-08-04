"""Export utility tests covering multiple report formats."""

from __future__ import annotations

from docx import Document

from govdocverify import export
from govdocverify.models import DocumentCheckResult, Severity
from govdocverify.utils.formatting import FormatStyle, ResultFormatter


def _make_result(issues=None, details=None) -> DocumentCheckResult:
    """Create a DocumentCheckResult helper for formatting tests."""
    return DocumentCheckResult(success=not issues, issues=issues or [], details=details)


def test_save_results_as_docx(tmp_path) -> None:
    output = tmp_path / "out.docx"
    export.save_results_as_docx({}, str(output))
    assert output.exists()


def test_save_results_as_pdf(tmp_path) -> None:
    output = tmp_path / "out.pdf"
    export.save_results_as_pdf({}, str(output))
    assert output.exists()


def test_html_report_contains_expected_markup() -> None:
    """EX-01: HTML output contains metadata and issues."""
    result = _make_result(issues=[{"message": "Problem", "severity": Severity.ERROR}])
    data = {"section": {"check": result}}
    formatter = ResultFormatter(style=FormatStyle.HTML)
    html = formatter.format_results(data, "ORDER", metadata={"title": "Doc"})
    assert "Doc" in html
    assert "Problem" in html


def test_docx_export_contains_unicode(tmp_path) -> None:
    """EX-02/EX-05: DOCX export preserves heading and non-ASCII text."""
    results = {"issues": ["§ Section symbol present"]}
    output = tmp_path / "out.docx"
    export.save_results_as_docx(results, str(output))
    doc = Document(str(output))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Document Check Results" in text
    assert "§ Section symbol present" in text


def test_pdf_export_has_pdf_header(tmp_path) -> None:
    """EX-03/EX-04: PDF export writes a valid header and non-empty content."""
    results = {"issues": ["Line one"]}
    output = tmp_path / "out.pdf"
    export.save_results_as_pdf(results, str(output))
    data = output.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 10
    
