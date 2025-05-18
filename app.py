# python app.py
# python app.py --host 127.0.0.1 --port 7860 --debug
# python app.py --host 127.0.0.1 --port 7861 --debug

import argparse
import sys
import os
import logging
import traceback
from documentcheckertool.interfaces.gradio_ui import create_interface
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
import mimetypes
from documentcheckertool.models import DocumentCheckResult, Severity, DocumentType, VisibilitySettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('document_checker.log')
    ]
)
logger = logging.getLogger(__name__)

def process_document(file_path: str, doc_type: str, visibility_settings: VisibilitySettings) -> str:
    """Process a document and return formatted results."""
    try:
        logger.info(f"Processing document of type: {doc_type}")
        formatter = ResultFormatter(style=FormatStyle.HTML)

        # Initialize the document checker
        terminology_manager = TerminologyManager()
        checker = FAADocumentChecker(terminology_manager)

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

        # Create a dictionary with check results organized by category
        results_dict = {}

        # Define category mappings
        category_mappings = {
            'heading_checks': ['heading_title_check', 'heading_title_period_check'],
            'reference_checks': ['table_figure_reference_check', 'cross_references_check', 'document_title_check'],
            'acronym_checks': ['acronym_check', 'acronym_usage_check'],
            'terminology_checks': ['terminology_check', 'section_symbol_usage_check', 'double_period_check', 'spacing_check', 'date_formats_check', 'parentheses_check'],
            'structure_checks': ['paragraph_length_check', 'sentence_length_check', 'placeholders_check', 'boilerplate_check'],
            'accessibility_checks': ['508_compliance_check', 'hyperlink_check', 'accessibility'],
            'document_status_checks': ['watermark_check'],
            'readability_checks': ['readability_check']
        }

        # Organize results by category
        for category, checkers in category_mappings.items():
            category_results = {}
            for checker in checkers:
                if hasattr(results, checker):
                    result = getattr(results, checker)
                    logger.debug(f"Category {category}, Checker {checker}:")
                    logger.debug(f"  Result type: {type(result)}")
                    logger.debug(f"  Has issues attr: {hasattr(result, 'issues')}")
                    if hasattr(result, 'issues'):
                        logger.debug(f"  Number of issues: {len(result.issues)}")
                        # Convert DocumentCheckResult to dict format expected by formatter
                        category_results[checker] = {
                            'success': result.success,
                            'issues': result.issues,
                            'details': result.details if hasattr(result, 'details') else {}
                        }
            if category_results:
                results_dict[category] = category_results
                logger.debug(f"Added {len(category_results)} results for category {category}")

        # Use the ResultFormatter to format the results
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