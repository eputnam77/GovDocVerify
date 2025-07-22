import logging
import mimetypes
from typing import Any, Dict

from govdocverify.document_checker import FAADocumentChecker
from govdocverify.models import DocumentCheckResult
from govdocverify.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)


def _read_file_content(file_path: str) -> str:
    """Read file content with fallback encoding."""
    logger.info(f"Reading file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed, trying with different encoding")
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def process_document(file_path: str, doc_type: str) -> DocumentCheckResult:
    """Run all checks on the given document and return a result object."""
    TerminologyManager()
    checker = FAADocumentChecker()

    mime_type, _ = mimetypes.guess_type(file_path)
    logger.info(f"Detected MIME type: {mime_type}")

    if (
        mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or file_path.lower().endswith(".docx")
    ):
        logger.info("Processing as DOCX file")
        return checker.run_all_document_checks(file_path, doc_type)

    content = _read_file_content(file_path)
    logger.info("Running document checks (text file)")
    return checker.run_all_document_checks(content, doc_type)


def _check_results_have_issues(results_dict: Dict[str, Dict[str, Any]]) -> bool:
    """Return True if any issue exists in the results dictionary."""
    for checks in results_dict.values():
        for res in checks.values():
            issues = getattr(res, "issues", []) if hasattr(res, "issues") else res.get("issues", [])
            if issues:
                return True
    return False


def _create_fallback_results_dict(results: DocumentCheckResult) -> Dict[str, Dict[str, Any]]:
    """Create fallback results dictionary when per_check_results is unavailable."""
    return {
        "all": {
            "all": {
                "success": results.success,
                "issues": results.issues,
                "details": getattr(results, "details", {}),
            }
        }
    }


def build_results_dict(results: DocumentCheckResult) -> Dict[str, Dict[str, Any]]:
    """Return a normalized results dictionary from a check result."""
    results_dict = getattr(results, "per_check_results", None)
    logger.debug("[DIAG] per_check_results present: %s", results_dict is not None)

    if results_dict:
        logger.debug("[DIAG] per_check_results keys: %s", list(results_dict.keys()))
    else:
        logger.debug("[DIAG] per_check_results is None")

    if not results_dict:
        logger.warning(
            "[DIAG] Fallback triggered: per_check_results is None. Using 'ALL' grouping."
        )
        return _create_fallback_results_dict(results)

    has_issues = _check_results_have_issues(results_dict)

    if not has_issues and results.issues:
        logger.warning(
            "[DIAG] Fallback triggered: per_check_results has no issues, "
            "but results.issues is non-empty (len=%d). Using 'ALL' grouping.",
            len(results.issues),
        )
        logger.debug("[DIAG] per_check_results content: %s", results_dict)
        return _create_fallback_results_dict(results)

    return results_dict
