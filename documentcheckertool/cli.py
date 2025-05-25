import sys
import logging
from typing import Dict, Any
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import DocumentType

# Export for test patching compatibility
DocumentChecker = FAADocumentChecker

logger = logging.getLogger(__name__)

# For structured logging with timestamps and levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

def process_document(file_path: str, doc_type: str, group_by: str = "category") -> Dict[str, Any]:
    """
    Process a document using FAADocumentChecker and return a result dict.
    Includes detailed logging and error handling.
    """
    logger.info(f"Processing document: {file_path} with type: {doc_type}, group_by: {group_by}")
    checker = FAADocumentChecker()
    try:
        # Validate document type
        if doc_type not in DocumentType.__members__:
            logger.error(f"Invalid document type: {doc_type}")
            return {
                'has_errors': True,
                'errors': [f'Invalid document type: {doc_type}'],
                'warnings': []
            }
        result = checker.run_all_document_checks(file_path, doc_type)

        # ── keep category structure intact ────────────────────────────────
        results_dict = getattr(result, "per_check_results", None) or {
            "all": {"all": {'success': result.success,
                                'issues': result.issues,
                                'details': getattr(result, 'details', {})}}
        }

        from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
        formatter = ResultFormatter(style=FormatStyle.MARKDOWN)
        rendered = formatter.format_results(results_dict, doc_type, group_by=group_by)

        logger.info("Check complete. Results grouped by %s.", group_by)
        return {"has_errors": not result.success,
                "rendered": rendered,
                "by_category": results_dict}
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {
            'has_errors': True,
            'errors': [f'File not found: {file_path}'],
            'warnings': []
        }
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return {
            'has_errors': True,
            'errors': [f'Permission denied: {file_path}'],
            'warnings': []
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            'has_errors': True,
            'errors': [f'Unexpected error: {str(e)}'],
            'warnings': []
        }

def main() -> int:
    """
    CLI entry point. Parses sys.argv and runs process_document.
    Returns 0 on success, 1 on error. Logs all actions.
    Handles exceptions robustly for test compatibility.
    """
    import argparse
    parser = argparse.ArgumentParser(description='FAA Document Checker CLI')
    parser.add_argument('file_path', type=str, help='Path to document file')
    parser.add_argument('doc_type', type=str, help='Document type')
    parser.add_argument('--group-by', type=str, choices=['category', 'severity'], default='category', help='Group results by category or severity')
    args = parser.parse_args()
    try:
        print("Checking document...", flush=True)
        result = process_document(args.file_path, args.doc_type, group_by=args.group_by)
    except Exception as e:
        logger.error(f"Exception in process_document: {e}")
        print(f"Error: {e}", flush=True)
        return 1
    if not isinstance(result, dict) or 'has_errors' not in result:
        logger.error("process_document did not return a valid result dict.")
        print("Error: Invalid result from document checker.", flush=True)
        return 1
    if result['has_errors']:
        logger.error(f"Errors found: {result.get('rendered', '')}")
        print("Check complete. Errors found.", flush=True)
        return 1
    logger.info("Document processed successfully with no errors.")
    print(result['rendered'])
    print("Check complete. No errors found.", flush=True)
    return 0

# For direct CLI usage
if __name__ == "__main__":
    sys.exit(main())