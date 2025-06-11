# python app.py
# python app.py --host 127.0.0.1 --port 7860 --debug
# python app.py --host 127.0.0.1 --port 7861 --debug

import argparse
import logging
import logging.config
import mimetypes
import os
import sys
import traceback

from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.interfaces.gradio_ui import create_interface
from documentcheckertool.logging_config import setup_logging
from documentcheckertool.models import (
    VisibilitySettings,
)
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter
from documentcheckertool.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)


def _create_error_div(error_msg: str) -> str:
    """Create a styled error div for display."""
    return (
        f"<div style='color: #721c24; background-color: #f8d7da; "
        f"padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    )


def _read_file_content(file_path: str) -> str:
    """Read file content with encoding fallback."""
    logger.info(f"Reading file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed, trying with different encoding")
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def _process_document_checks(file_path: str, doc_type: str, checker: FAADocumentChecker):
    """Process document checks based on file type."""
    mime_type, _ = mimetypes.guess_type(file_path)
    logger.info(f"Detected MIME type: {mime_type}")

    # If DOCX, pass file path directly to checker
    if (
        mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or file_path.lower().endswith(".docx")
    ):
        logger.info("Processing as DOCX file")
        return checker.run_all_document_checks(file_path, doc_type)
    else:
        content = _read_file_content(file_path)
        logger.info("Running document checks (text file)")
        return checker.run_all_document_checks(content, doc_type)


def _check_results_have_issues(results_dict: dict) -> bool:
    """Check if results dictionary contains any issues."""
    for cat, checks in results_dict.items():
        for check, res in checks.items():
            issues = getattr(res, "issues", []) if hasattr(res, "issues") else res.get("issues", [])
            if issues:
                return True
    return False


def _create_fallback_results_dict(results):
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


def _process_results_dict(results):
    """Process and validate results dictionary."""
    results_dict = getattr(results, "per_check_results", None)
    logger.debug(f"[DIAG] per_check_results present: {results_dict is not None}")

    if results_dict:
        logger.debug(f"[DIAG] per_check_results keys: {list(results_dict.keys())}")
    else:
        logger.debug("[DIAG] per_check_results is None")

    if not results_dict:
        logger.warning(
            "[DIAG] Fallback triggered: per_check_results is None. Using 'ALL' grouping."
        )
        return _create_fallback_results_dict(results)

    # Check if all sub-dicts are empty or only contain empty sub-dicts
    has_issues = _check_results_have_issues(results_dict)

    if not has_issues and results.issues:
        logger.warning(
            "[DIAG] Fallback triggered: per_check_results has no issues, "
            f"but results.issues is non-empty (len={len(results.issues)}). "
            "Using 'ALL' grouping."
        )
        logger.debug(f"[DIAG] per_check_results content: {results_dict}")
        return _create_fallback_results_dict(results)

    return results_dict


def process_document(
    file_path: str,
    doc_type: str,
    visibility_settings: VisibilitySettings,
    group_by: str = "category",
) -> str:
    """Process a document and return formatted results."""
    logger.debug("[PROOF] process_document called")
    logger.debug(
        "[DIAG] process_document called with "
        f"file_path={file_path}, "
        f"doc_type={doc_type}, "
        f"group_by={group_by}"
    )

    try:
        logger.info(f"Processing document of type: {doc_type}, group_by: {group_by}")
        formatter = ResultFormatter(style=FormatStyle.HTML)

        # Initialize the document checker
        TerminologyManager()
        checker = FAADocumentChecker()

        # Process document checks
        results = _process_document_checks(file_path, doc_type, checker)

        logger.info("Formatting results")
        logger.debug(f"Raw results type: {type(results)}")
        logger.debug(f"Raw results dir: {dir(results)}")

        # Process and validate results dictionary
        results_dict = _process_results_dict(results)
        logger.debug(f"[DIAG] Final results_dict keys: {list(results_dict.keys())}")

        logger.info(f"Results dict before formatting: {results_dict}")
        formatted_results = formatter.format_results(results_dict, doc_type, group_by=group_by)
        logger.info("Document processing completed successfully")
        return formatted_results

    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return _create_error_div(error_msg)
    except PermissionError:
        error_msg = f"Permission denied: {file_path}"
        logger.error(error_msg)
        return _create_error_div(error_msg)
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return _create_error_div(error_msg)


def main() -> int:
    """Main entry point for the application (web/Gradio only)."""
    try:
        logger.info("Starting Document Checker Tool (web/Gradio mode)")
        parser = argparse.ArgumentParser(description="FAA Document Checker (Web/Gradio)")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
        parser.add_argument("--port", type=int, default=7860, help="Server port")
        args = parser.parse_args()

        # Set up logging based on debug flag
        setup_logging(debug=args.debug)

        if args.debug:
            logger.debug("Debug mode enabled")

        logger.info("Starting Gradio interface")
        interface = create_interface()

        # Determine if we're running in Hugging Face Spaces
        is_spaces = os.environ.get("SPACE_ID") is not None
        logger.info(f"Running in Hugging Face Spaces: {is_spaces}")

        interface.launch(
            debug=args.debug,
            server_name="0.0.0.0" if is_spaces else args.host,
            server_port=args.port,
            show_error=True,
            share=not is_spaces,
        )
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
