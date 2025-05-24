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

def process_document(file_path: str, doc_type: str) -> Dict[str, Any]:
    """
    Process a document using FAADocumentChecker and return a result dict.
    Includes detailed logging and error handling.
    """
    logger.info(f"Processing document: {file_path} with type: {doc_type}")
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
        errors = [issue for issue in result.issues if issue.get('severity', 'error') == 'error']
        warnings = [issue for issue in result.issues if issue.get('severity', 'error') == 'warning']
        logger.info(f"Check complete. Errors: {len(errors)}, Warnings: {len(warnings)}")
        return {
            'has_errors': not result.success,
            'errors': errors,
            'warnings': warnings
        }
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
    logger.debug(f"CLI arguments: {sys.argv}")
    if len(sys.argv) != 3:
        logger.error("Usage: script.py <file_path> <doc_type>")
        return 1
    file_path = sys.argv[1]
    doc_type = sys.argv[2]
    try:
        result = process_document(file_path, doc_type)
    except Exception as e:
        logger.error(f"Exception in process_document: {e}")
        return 1
    if not isinstance(result, dict) or 'has_errors' not in result:
        logger.error("process_document did not return a valid result dict.")
        return 1
    if result['has_errors']:
        logger.error(f"Errors found: {result.get('errors', [])}")
        return 1
    logger.info("Document processed successfully with no errors.")
    return 0

# For direct CLI usage
if __name__ == "__main__":
    sys.exit(main())