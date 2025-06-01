import sys
import logging
import argparse
import os
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import DocumentType, VisibilitySettings
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.logging_config import setup_logging

logger = logging.getLogger(__name__)

def process_document(file_path: str, doc_type: str, visibility_settings: VisibilitySettings, group_by: str = "category") -> str:
    print("[PROOF] process_document called")
    logger.debug(f"[DIAG] process_document called with file_path={file_path}, doc_type={doc_type}, group_by={group_by}")
    """Process a document and return formatted results."""
    try:
        logger.info(f"Processing document of type: {doc_type}, group_by: {group_by}")
        formatter = ResultFormatter(style=FormatStyle.PLAIN)

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

        # --- FILTER RESULTS BASED ON VISIBILITY SETTINGS ---
        # Only include categories where visibility_settings.<category> is True
        # If --show-only is used, only include those categories, even if others are present in results_dict
        if hasattr(visibility_settings, '_show_only_set') and visibility_settings._show_only_set:
            # Strict filtering: only show categories in show_only_set
            filtered_results_dict = {cat: checks for cat, checks in results_dict.items() if cat in visibility_settings._show_only_set}
        else:
            visibility_map = visibility_settings.to_dict()
            filtered_results_dict = {}
            for category, checks in results_dict.items():
                if category in visibility_map and not visibility_map[category]:
                    continue  # Skip hidden categories
                filtered_results_dict[category] = checks
        # ---------------------------------------------------

        formatted_results = formatter.format_results(filtered_results_dict, doc_type, group_by=group_by)
        logger.info("Document processing completed successfully")
        return formatted_results

    except FileNotFoundError:
        error_msg = f"❌ ERROR: File not found: {file_path}"
        logger.error(error_msg)
        return error_msg
    except PermissionError:
        error_msg = f"❌ ERROR: Permission denied: {file_path}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ ERROR: Error processing document: {str(e)}"
        logger.error(error_msg)
        return error_msg

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
    visibility_group.add_argument('--show-only', type=str, nargs='+', metavar='CATEGORY',
        help='Show only the specified categories (comma-separated or space-separated list). Mutually exclusive with --hide-* and --show-all. Categories: readability, paragraph_length, terminology, headings, structure, format, accessibility, document_status')
    visibility_group.add_argument('--hide', type=str, nargs='+', metavar='CATEGORY',
        help='Hide the specified categories (comma-separated or space-separated list). Mutually exclusive with --hide-* and --show-only/--show-all. Categories: readability, paragraph_length, terminology, headings, structure, format, accessibility, document_status')

    args = parser.parse_args()

    # Enforce mutual exclusivity
    if args.show_only:
        hide_flags = [args.hide_readability, args.hide_paragraph_length, args.hide_terminology, args.hide_headings,
                      args.hide_structure, args.hide_format, args.hide_accessibility, args.hide_document_status, args.show_all, args.hide]
        if any(hide_flags):
            parser.error('--show-only cannot be used with --hide-*, --hide, or --show-all')
    if args.hide:
        hide_flags = [args.hide_readability, args.hide_paragraph_length, args.hide_terminology, args.hide_headings,
                      args.hide_structure, args.hide_format, args.hide_accessibility, args.hide_document_status, args.show_all, args.show_only]
        if any(hide_flags):
            parser.error('--hide cannot be used with --hide-*, --show-only, or --show-all')

    # Set up logging based on debug flag
    setup_logging(debug=args.debug)

    if args.debug:
        logger.debug("Debug mode enabled")

    # --- Visibility logic ---
    categories = [
        'readability',
        'paragraph_length',
        'terminology',
        'headings',
        'structure',
        'format',
        'accessibility',
        'document_status',
    ]
    if args.show_only:
        # Support comma-separated or space-separated
        show_only_raw = []
        for val in args.show_only:
            show_only_raw.extend([v.strip() for v in val.split(',') if v.strip()])
        show_only_set = set(show_only_raw)
        # Validate
        invalid = [c for c in show_only_set if c not in categories]
        if invalid:
            parser.error(f"Invalid category in --show-only: {', '.join(invalid)}. Valid: {', '.join(categories)}")
        # Set only specified categories to True
        visibility_settings = VisibilitySettings(**{f'show_{cat}': (cat in show_only_set) for cat in categories})
        # Attach show_only_set for strict filtering in process_document
        visibility_settings._show_only_set = show_only_set
    elif args.hide:
        # Support comma-separated or space-separated
        hide_raw = []
        for val in args.hide:
            hide_raw.extend([v.strip() for v in val.split(',') if v.strip()])
        hide_set = set(hide_raw)
        # Validate
        invalid = [c for c in hide_set if c not in categories]
        if invalid:
            parser.error(f"Invalid category in --hide: {', '.join(invalid)}. Valid: {', '.join(categories)}")
        # Set specified categories to False, all others to True
        visibility_settings = VisibilitySettings(**{f'show_{cat}': (cat not in hide_set) for cat in categories})
        # Attach hide_set for possible future use
        visibility_settings._hide_set = hide_set
    else:
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
    # --- End visibility logic ---

    results = process_document(args.file, args.type, visibility_settings, group_by=args.group_by)
    print(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())