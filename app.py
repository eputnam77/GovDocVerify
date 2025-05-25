# python app.py
# python app.py --host 127.0.0.1 --port 7860 --debug
# python app.py --host 127.0.0.1 --port 7861 --debug

import argparse
import sys
import os
import logging
import traceback
import logging.config
from documentcheckertool.interfaces.gradio_ui import create_interface
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
import mimetypes
from documentcheckertool.models import DocumentCheckResult, Severity, DocumentType, VisibilitySettings
from documentcheckertool.checks.check_registry import CheckRegistry  # Added for registry-driven category mapping

log_path = os.path.abspath("document_checker.log")

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': log_path,
            'mode': 'w',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.debug("[UI DEBUG] Logging is active at module import time.")

def process_document(file_path: str, doc_type: str, visibility_settings: VisibilitySettings) -> str:
    """Process a document and return formatted results."""
    try:
        logger.info(f"Processing document of type: {doc_type}")
        formatter = ResultFormatter(style=FormatStyle.HTML)

        # Initialize the document checker
        terminology_manager = TerminologyManager()
        checker = FAADocumentChecker()

        # Detect file type using mimetypes and file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        logger.info(f"Detected MIME type: {mime_type}")

        # If DOCX, pass file path directly to checker
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_path.lower().endswith('.docx'):
            logger.info("Processing as DOCX file")
            results = checker.run_all_document_checks(file_path, doc_type)
        else:
            logger.info(f"Reading file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.warning("UTF-8 decode failed, trying with different encoding")
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            logger.info("Running document checks (text file)")
            results = checker.run_all_document_checks(content, doc_type)

        logger.info("Formatting results")
        logger.debug(f"Raw results type: {type(results)}")
        logger.debug(f"Raw results dir: {dir(results)}")

        # Use per_check_results if available
        results_dict = getattr(results, 'per_check_results', None)
        if not results_dict:
            results_dict = {"all": {"all": {
                "success": results.success,
                "issues": results.issues,
                "details": getattr(results, "details", {})
            }}}

        logger.info(f"Results dict before formatting: {results_dict}")
        formatted_results = formatter.format_results(results_dict, doc_type)
        logger.info("Document processing completed successfully")
        return formatted_results

    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    except PermissionError:
        error_msg = f"Permission denied: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"

def main() -> int:
    """Main entry point for the application."""
    try:
        logger.info("Starting Document Checker Tool")
        parser = argparse.ArgumentParser(description='FAA Document Checker')
        parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
        parser.add_argument('--file', type=str, help='Path to document file')
        parser.add_argument('--type', type=str, help='Document type')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host')
        parser.add_argument('--port', type=int, default=7860, help='Server port')

        # Add visibility control flags
        visibility_group = parser.add_argument_group('Visibility Controls')
        visibility_group.add_argument('--show-all', action='store_true', help='Show all sections (default)')
        visibility_group.add_argument('--hide-readability', action='store_true', help='Hide readability metrics')
        visibility_group.add_argument('--hide-paragraph-length', action='store_true', help='Hide paragraph and sentence length checks')
        visibility_group.add_argument('--hide-terminology', action='store_true', help='Hide terminology checks')
        visibility_group.add_argument('--hide-headings', action='store_true', help='Hide heading checks')
        visibility_group.add_argument('--hide-structure', action='store_true', help='Hide structure checks')
        visibility_group.add_argument('--hide-format', action='store_true', help='Hide format checks')
        visibility_group.add_argument('--hide-accessibility', action='store_true', help='Hide accessibility checks')
        visibility_group.add_argument('--hide-document-status', action='store_true', help='Hide document status checks')

        args = parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

        if args.cli:
            if not args.file or not args.type:
                logger.error("Missing required arguments in CLI mode")
                print("Error: --file and --type are required in CLI mode")
                return 1

            try:
                # Create visibility settings from CLI arguments
                visibility_settings = VisibilitySettings(
                    show_readability=not args.hide_readability,
                    show_paragraph_length=not args.hide_paragraph_length,
                    show_terminology=not args.hide_terminology,
                    show_headings=not args.hide_headings,
                    show_structure=not args.hide_structure,
                    show_format=not args.hide_format,
                    show_accessibility=not args.hide_accessibility,
                    show_document_status=not args.hide_document_status
                )

                results = process_document(args.file, args.type, visibility_settings)
                print(results)
                return 0
            except Exception as e:
                logger.error(f"Error in CLI mode: {str(e)}")
                return 1
        else:
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
                share=not is_spaces
            )
            return 0

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())