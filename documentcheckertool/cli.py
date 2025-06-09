"""CLI module for the document checker tool."""

import argparse
import logging
import sys

from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.logging_config import setup_logging
from documentcheckertool.models import VisibilitySettings
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter
from documentcheckertool.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)


def process_document(
    file_path: str,
    doc_type: str,
    visibility_settings: VisibilitySettings = None,
    group_by: str = "category",
) -> dict:
    """Process a document and return results as a dictionary."""
    print("[PROOF] process_document called")
    logger.debug(
        "[DIAG] process_document called with "
        f"file_path={file_path}, "
        f"doc_type={doc_type}, "
        f"group_by={group_by}"
    )

    try:
        logger.info(f"Processing document of type: {doc_type}, group_by: {group_by}")

        # Use default visibility settings if none provided
        if visibility_settings is None:
            visibility_settings = VisibilitySettings()

        formatter = ResultFormatter(style=FormatStyle.PLAIN)

        # Initialize the document checker
        TerminologyManager()
        checker = FAADocumentChecker()

        # Detect file type using mimetypes and file extension
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path)
        logger.info(f"Detected MIME type: {mime_type}")

        # If DOCX, pass file path directly to checker
        if (
            mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or file_path.lower().endswith(".docx")
        ):
            logger.info("Processing as DOCX file")
            results = checker.run_all_document_checks(file_path, doc_type)
        else:
            logger.info(f"Reading file: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.warning("UTF-8 decode failed, trying with different encoding")
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            logger.info("Running document checks (text file)")
            results = checker.run_all_document_checks(content, doc_type)

        logger.info("Formatting results")
        logger.debug(f"Raw results type: {type(results)}")
        logger.debug(f"Raw results dir: {dir(results)}")

        # Use per_check_results if available
        results_dict = getattr(results, "per_check_results", None)
        if not results_dict:
            results_dict = {
                "all": {
                    "all": {
                        "success": results.success,
                        "issues": results.issues,
                        "details": getattr(results, "details", {}),
                    }
                }
            }

        # --- FILTER RESULTS BASED ON VISIBILITY SETTINGS ---
        # Only include categories where visibility_settings.<category> is True
        # If --show-only is used, only include those categories,
        # even if others are present in results_dict
        if hasattr(visibility_settings, "_show_only_set") and visibility_settings._show_only_set:
            # Strict filtering: only show categories in show_only_set
            filtered_results_dict = {
                cat: checks
                for cat, checks in results_dict.items()
                if cat in visibility_settings._show_only_set
            }
        else:
            visibility_map = visibility_settings.to_dict()
            filtered_results_dict = {}
            for category, checks in results_dict.items():
                if category in visibility_map and not visibility_map[category]:
                    continue  # Skip hidden categories
                filtered_results_dict[category] = checks
        # ---------------------------------------------------

        formatted_results = formatter.format_results(
            filtered_results_dict, doc_type, group_by=group_by
        )
        logger.info("Document processing completed successfully")

        # Return a dictionary with the expected structure for tests
        has_errors = not results.success if hasattr(results, 'success') else False
        return {
            "has_errors": has_errors,
            "rendered": formatted_results,
            "by_category": filtered_results_dict
        }

    except FileNotFoundError:
        error_msg = f"❌ ERROR: File not found: {file_path}"
        logger.error(error_msg)
        raise
    except PermissionError:
        error_msg = f"❌ ERROR: Permission denied: {file_path}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"❌ ERROR: Error processing document: {str(e)}"
        logger.error(error_msg)
        raise


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="FAA Document Checker CLI")
    parser.add_argument("--file", type=str, required=True, help="Path to document file")
    parser.add_argument("--type", type=str, required=True, help="Document type")
    parser.add_argument(
        "--group-by",
        type=str,
        choices=["category", "severity"],
        default="category",
        help="Group results by category or severity",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Add visibility control flags
    visibility_group = parser.add_argument_group("Visibility Controls")
    visibility_group.add_argument(
        "--show-all", action="store_true", help="Show all sections (default)"
    )
    visibility_group.add_argument(
        "--hide-readability", action="store_true", help="Hide readability metrics"
    )
    visibility_group.add_argument(
        "--hide-paragraph-length",
        action="store_true",
        help="Hide paragraph and sentence length checks",
    )
    visibility_group.add_argument(
        "--hide-terminology", action="store_true", help="Hide terminology checks"
    )
    visibility_group.add_argument(
        "--hide-headings", action="store_true", help="Hide heading checks"
    )
    visibility_group.add_argument(
        "--hide-structure", action="store_true", help="Hide structure checks"
    )
    visibility_group.add_argument("--hide-format", action="store_true", help="Hide format checks")
    visibility_group.add_argument(
        "--hide-accessibility", action="store_true", help="Hide accessibility checks"
    )
    visibility_group.add_argument(
        "--hide-document-status", action="store_true", help="Hide document status checks"
    )
    visibility_group.add_argument(
        "--show-only",
        type=str,
        nargs="+",
        metavar="CATEGORY",
        help=(
            "Show only the specified categories. Accepts a comma- or space-separated list. "
            "Cannot be used with --hide-* or --show-all. "
            "Categories: readability, paragraph_length, terminology, headings, structure, "
            "format, accessibility, document_status."
        ),
    )
    visibility_group.add_argument(
        "--hide",
        type=str,
        nargs="+",
        metavar="CATEGORY",
        help=(
            "Hide the specified categories. Accepts a comma- or space-separated list. "
            "Cannot be used with --hide-* or --show-only/--show-all. "
            "Categories: readability, paragraph_length, terminology, headings, structure, "
            "format, accessibility, document_status."
        ),
    )
    return parser


def _validate_argument_exclusivity(args, parser: argparse.ArgumentParser) -> None:
    """Validate that mutually exclusive arguments are not used together."""
    if args.show_only:
        hide_flags = [
            args.hide_readability,
            args.hide_paragraph_length,
            args.hide_terminology,
            args.hide_headings,
            args.hide_structure,
            args.hide_format,
            args.hide_accessibility,
            args.hide_document_status,
            args.show_all,
            args.hide,
        ]
        if any(hide_flags):
            parser.error("--show-only cannot be used with --hide-*, --hide, or --show-all")

    if args.hide:
        hide_flags = [
            args.hide_readability,
            args.hide_paragraph_length,
            args.hide_terminology,
            args.hide_headings,
            args.hide_structure,
            args.hide_format,
            args.hide_accessibility,
            args.hide_document_status,
            args.show_all,
            args.show_only,
        ]
        if any(hide_flags):
            parser.error("--hide cannot be used with --hide-*, --show-only, or --show-all")


def _get_valid_categories() -> list[str]:
    """Get the list of valid category names."""
    return [
        "readability",
        "paragraph_length",
        "terminology",
        "headings",
        "structure",
        "format",
        "accessibility",
        "document_status",
    ]


def _parse_category_list(category_args: list[str]) -> set[str]:
    """Parse comma- or space-separated category arguments into a set."""
    category_raw = []
    for val in category_args:
        category_raw.extend([v.strip() for v in val.split(",") if v.strip()])
    return set(category_raw)


def _create_visibility_settings(args, parser: argparse.ArgumentParser) -> VisibilitySettings:
    """Create visibility settings based on parsed arguments."""
    categories = _get_valid_categories()

    if args.show_only:
        show_only_set = _parse_category_list(args.show_only)
        # Validate categories
        invalid = [c for c in show_only_set if c not in categories]
        if invalid:
            parser.error(
                "Invalid category in --show-only: "
                f"{', '.join(invalid)}. "
                "Valid categories are: "
                f"{', '.join(categories)}"
            )
        # Set only specified categories to True
        visibility_settings = VisibilitySettings(
            **{f"show_{cat}": (cat in show_only_set) for cat in categories}
        )
        # Attach show_only_set for strict filtering in process_document
        visibility_settings._show_only_set = show_only_set
        return visibility_settings

    if args.hide:
        hide_set = _parse_category_list(args.hide)
        # Validate categories
        invalid = [c for c in hide_set if c not in categories]
        if invalid:
            parser.error(
                f"Invalid category in --hide: {', '.join(invalid)}. Valid: {', '.join(categories)}"
            )
        # Set specified categories to False, all others to True
        visibility_settings = VisibilitySettings(
            **{f"show_{cat}": (cat not in hide_set) for cat in categories}
        )
        # Attach hide_set for possible future use
        visibility_settings._hide_set = hide_set
        return visibility_settings

    # Default visibility settings based on individual hide flags
    return VisibilitySettings(
        show_readability=not args.hide_readability,
        show_paragraph_length=not args.hide_paragraph_length,
        show_terminology=not args.hide_terminology,
        show_headings=not args.hide_headings,
        show_structure=not args.hide_structure,
        show_format=not args.hide_format,
        show_accessibility=not args.hide_accessibility,
        show_document_status=not args.hide_document_status,
    )


def main() -> int:
    """Main entry point for the CLI application."""
    try:
        # Handle case where no arguments are provided
        if len(sys.argv) < 3:
            print("Usage: script.py <file_path> <doc_type>")
            return 1

        # Simple argument parsing for basic usage
        if len(sys.argv) >= 3:
            file_path = sys.argv[1]
            doc_type = sys.argv[2]

            # Validate document type
            valid_doc_types = ["ADVISORY_CIRCULAR", "POLICY", "ORDER", "NOTICE"]
            if doc_type not in valid_doc_types:
                print(f"Invalid document type: {doc_type}")
                return 1

            # Set up basic logging
            setup_logging(debug=False)

            # Process document with default settings
            result = process_document(file_path, doc_type)

            # Return appropriate exit code
            return 1 if result.get("has_errors", False) else 0

        # If we have more arguments, use the full argument parser
        parser = _create_argument_parser()
        args = parser.parse_args()

        # Validate argument exclusivity
        _validate_argument_exclusivity(args, parser)

        # Set up logging based on debug flag
        setup_logging(debug=args.debug)

        if args.debug:
            logger.debug("Debug mode enabled")

        # Create visibility settings
        visibility_settings = _create_visibility_settings(args, parser)

        # Process document and display results
        result = process_document(args.file, args.type, visibility_settings, group_by=args.group_by)
        print(result["rendered"])
        return 1 if result.get("has_errors", False) else 0

    except FileNotFoundError:
        print("File not found")
        return 1
    except PermissionError:
        print("Permission denied")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
