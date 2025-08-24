"""Tests ensuring optional dependencies degrade gracefully."""

from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path


def test_formatter_without_colorama(monkeypatch):
    """Formatter works when colorama isn't installed."""
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "colorama":
            raise ModuleNotFoundError
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    orig_module = sys.modules.pop("govdocverify.utils.formatting", None)
    fmt_module = importlib.import_module("govdocverify.utils.formatting")
    formatter = fmt_module.ResultFormatter()
    assert fmt_module.Fore.RED == ""
    assert formatter._format_colored_text("hi", fmt_module.Fore.RED) == "hi"
    if orig_module is not None:
        sys.modules["govdocverify.utils.formatting"] = orig_module
    monkeypatch.setattr(builtins, "__import__", orig_import)


def test_format_checks_without_docx(monkeypatch):
    """Format checks run with a minimal document when python-docx is missing."""
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "docx":
            raise ModuleNotFoundError
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    orig_module = sys.modules.pop("govdocverify.checks.format_checks", None)
    fc_module = importlib.import_module("govdocverify.checks.format_checks")

    class DummyDoc:
        paragraphs: list[str] = []

    checker = fc_module.FormatChecks()
    results = fc_module.DocumentCheckResult()
    checker.run_checks(DummyDoc(), "AC", results)
    assert results.success
    if orig_module is not None:
        sys.modules["govdocverify.checks.format_checks"] = orig_module
    monkeypatch.setattr(builtins, "__import__", orig_import)


def test_save_results_as_pdf_without_fpdf(tmp_path: Path, monkeypatch):
    """PDF export writes a minimal file when fpdf isn't installed."""
    from govdocverify import export

    monkeypatch.setattr(export, "FPDF", None)
    output = tmp_path / "out.pdf"
    export.save_results_as_pdf({"a": 1}, str(output))
    assert output.read_bytes().startswith(b"%PDF-1.4")
