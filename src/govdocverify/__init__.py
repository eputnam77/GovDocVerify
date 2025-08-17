"""Top-level package for the GovDocVerify Python API.

The module exposes a very small, intentionally curated public surface. Everything
else in the repository is internal and may change without notice.  The exported
symbols are re-imported here for convenience and documented in
``docs/api-reference.md``.

Example
-------
>>> from govdocverify import DocumentChecker
>>> checker = DocumentChecker()
>>> result = checker.run_all_document_checks("path/to.docx")
>>> result.success
True
"""

# Import lightweight items only so tests do not pull heavy optional dependencies.
from .document_checker import FAADocumentChecker as DocumentChecker
from .export import save_results_as_docx, save_results_as_pdf
from .models import DocumentCheckResult, Severity, VisibilitySettings

__all__ = [
    "DocumentChecker",
    "DocumentCheckResult",
    "VisibilitySettings",
    "Severity",
    "save_results_as_docx",
    "save_results_as_pdf",
]
