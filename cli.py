import sys
import logging
import argparse
import os
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import DocumentType, VisibilitySettings
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
from documentcheckertool.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)

# For structured logging with timestamps and levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

def process_document(file_path: str, doc_type: str, visibility_settings: VisibilitySettings, group_by: str = "category") -> str:
    """Process a document and return formatted results."""
    try:
        logger.info(f"Processing document of type: {doc_type}, group_by: {group_by}")
        formatter = ResultFormatter(style=FormatStyle.HTML)

        # Initialize the document checker
        terminology_manager = TerminologyManager()
        checker = FAADocumentChecker()

        # Detect file type using mimetypes and file extension
        import mimetypes
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
                "details": getattr(results, "details", {{}})
            }}}
        formatted_results = formatter.format_results(results_dict, doc_type, group_by=group_by)
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
        logger.error(error_msg)
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"

def main() -> int:
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(description='FAA Document Checker CLI')
    parser.add_argument('--file', type=str, required=True, help='Path to document file')
    parser.add_argument('--type', type=str, required=True, help='Document type')
    parser.add_argument('--group-by', type=str, choices=['category', 'severity'], default='category', help='Group results by category or severity')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

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

    results = process_document(args.file, args.type, visibility_settings, group_by=args.group_by)
    print(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())