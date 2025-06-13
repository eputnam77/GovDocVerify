# python app.py
# python app.py --host 127.0.0.1 --port 7860 --debug
# python app.py --host 127.0.0.1 --port 7861 --debug

import argparse
import logging
import logging.config
import os
import sys
import traceback

from documentcheckertool.interfaces.gradio_ui import create_interface
from documentcheckertool.logging_config import setup_logging
from documentcheckertool.models import (
    VisibilitySettings,
)
from documentcheckertool.processing import build_results_dict
from documentcheckertool.processing import process_document as _run_checks
from documentcheckertool.utils import extract_docx_metadata
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter

logger = logging.getLogger(__name__)


def _create_error_div(error_msg: str) -> str:
    """Create a styled error div for display."""
    return (
        f"<div style='color: #721c24; background-color: #f8d7da; "
        f"padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    )


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
        metadata = extract_docx_metadata(file_path)

        # Run the document checks using the shared processing module
        results = _run_checks(file_path, doc_type)

        logger.info("Formatting results")
        logger.debug(f"Raw results type: {type(results)}")
        logger.debug(f"Raw results dir: {dir(results)}")

        # Process and validate results dictionary
        results_dict = build_results_dict(results)
        logger.debug(f"[DIAG] Final results_dict keys: {list(results_dict.keys())}")

        logger.info(f"Results dict before formatting: {results_dict}")
        formatted_results = formatter.format_results(
            results_dict,
            doc_type,
            group_by=group_by,
            metadata=metadata,
        )
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
