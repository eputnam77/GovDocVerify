"""Helpers for exporting check results to various formats."""

from typing import Any


def save_results_as_docx(results: dict[str, Any], path: str) -> None:
    """Save results as a DOCX file."""
    raise NotImplementedError("DOCX export not implemented yet")


def save_results_as_pdf(results: dict[str, Any], path: str) -> None:
    """Save results as a PDF file."""
    raise NotImplementedError("PDF export not implemented yet")
