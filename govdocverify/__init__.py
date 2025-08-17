"""Top-level package for the GovDocVerify Python API.

The module exposes a **very** small and well defined public surface.  Everything
else in the repository should be considered internal and may change without
notice.  The exported names are re-imported here for convenience and documented
in :ref:`docs/api-reference.md`.

Example
-------
>>> from govdocverify import DocumentChecker
>>> checker = DocumentChecker()
>>> result = checker.run_all_document_checks("path/to.docx")
>>> result.success
True
"""

# Only import lightweight items at module import time so that unit tests can run
# without pulling in heavy optional dependencies (e.g. ``docx`` or ``uvicorn``).
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
