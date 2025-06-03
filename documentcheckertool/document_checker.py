import logging
from typing import List, Dict, Any, Optional
from docx import Document
from documentcheckertool.models import DocumentCheckResult, DocumentType
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.checks.reference_checks import TableFigureReferenceCheck, DocumentTitleFormatCheck
from documentcheckertool.checks.readability_checks import ReadabilityChecks
from documentcheckertool.checks.acronym_checks import AcronymChecker
from documentcheckertool.utils.text_utils import split_sentences, count_words, normalize_reference
from documentcheckertool.utils.pattern_cache import PatternCache
from documentcheckertool.utils.terminology_utils import TerminologyManager
from .utils.check_discovery import validate_check_registration
from documentcheckertool.checks.check_registry import CheckRegistry

logger = logging.getLogger(__name__)

class FAADocumentChecker:
    """Main document checker class that coordinates various checks."""

    def __init__(self):
        """Initialize the document checker with all check modules."""
        logger.debug("Initializing FAADocumentChecker")

        # Initialize pattern cache for heading checks
        self.pattern_cache = PatternCache()
        logger.debug(f"PatternCache initialized: {self.pattern_cache}")

        # Initialize terminology manager for terminology-based checks
        self.terminology_manager = TerminologyManager()
        logger.debug(f"TerminologyManager initialized: {self.terminology_manager}")

        # Initialize all check modules
        self.heading_checks = HeadingChecks(self.pattern_cache)
        logger.debug(f"HeadingChecks initialized with pattern_cache: {self.heading_checks.pattern_cache}")
        self.format_checks = FormatChecks()
        self.structure_checks = StructureChecks()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)
        logger.debug(f"TerminologyChecks initialized with terminology_manager: {self.terminology_manager}")
        self.readability_checks = ReadabilityChecks(self.terminology_manager)
        logger.debug(f"ReadabilityChecks initialized with terminology_manager: {self.terminology_manager}")
        self.acronym_checker = AcronymChecker(self.terminology_manager)
        logger.debug(f"AcronymChecker initialized with terminology_manager: {self.terminology_manager}")
        self.accessibility_checks = AccessibilityChecks(self.terminology_manager)
        logger.debug(f"AccessibilityChecks initialized with terminology_manager: {self.terminology_manager}")
        self.table_figure_checks = TableFigureReferenceCheck()
        logger.debug(f"TableFigureReferenceCheck initialized: {self.table_figure_checks}")
        self.document_title_checks = DocumentTitleFormatCheck()
        logger.debug(f"DocumentTitleFormatCheck initialized: {self.document_title_checks}")

        # Validate check registration
        validation_results = validate_check_registration()
        if validation_results['missing_categories'] or validation_results['missing_checks']:
            logger.warning("Some checks are not properly registered:")
            if validation_results['missing_categories']:
                logger.warning(f"Missing categories: {validation_results['missing_categories']}")
            if validation_results['missing_checks']:
                logger.warning(f"Missing checks: {validation_results['missing_checks']}")
        if validation_results['extra_checks']:
            logger.warning(f"Extra registered checks: {validation_results['extra_checks']}")
        logger.debug("FAADocumentChecker initialized successfully")

    def run_all_document_checks(self, document_path: str, doc_type: str = None) -> DocumentCheckResult:
        """Run all document checks."""
        try:
            # Create a new DocumentCheckResult to store combined results
            combined_results = DocumentCheckResult()
            per_check_results = {}

            # Load the document
            if isinstance(document_path, str) and (document_path.lower().endswith('.docx') or document_path.lower().endswith('.doc')):
                doc = Document(document_path)
                doc.text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                logger.debug(f"Loaded document from file: {document_path}, extracted text length: {len(doc.text)}")
            else:
                doc = Document()
                if isinstance(document_path, list):
                    doc.text = '\n'.join(document_path)
                    logger.debug(f"Created document from list of strings, length: {len(document_path)}")
                else:
                    doc.text = document_path
                    logger.debug(f"Created document from raw string, length: {len(document_path)}")

            # Define all check modules with their names for logging
            check_modules = [
                (self.heading_checks, "heading"),
                (self.accessibility_checks, "accessibility"),
                (self.format_checks, "format"),
                (self.structure_checks, "structure"),
                (self.terminology_checks, "terminology"),
                (self.readability_checks, "readability"),
                (self.acronym_checker, "acronym"),
                (self.table_figure_checks, "reference"),
                (self.document_title_checks, "reference")
            ]

            # Run all checks
            for check_module, category in check_modules:
                try:
                    logger.info(f"Running {category} checks...")
                    # Always pass the Document object to check_document
                    result = check_module.check_document(doc, doc_type)
                    per_check_results.setdefault(category, {})
                    for check_func in CheckRegistry.get_checks_for_category(category):
                        if hasattr(result, 'checker_name') and result.checker_name == check_func:
                            per_check_results[category][check_func] = result
                        elif hasattr(result, check_func):
                            per_check_results[category][check_func] = getattr(result, check_func)

                    # Collect issues from the result (these should be properly formatted from add_issue calls)
                    if hasattr(result, 'issues') and result.issues:
                        combined_results.issues.extend(result.issues)

                    if not result.success:
                        combined_results.success = False
                except Exception as e:
                    logger.error(f"Error in {category} checks: {str(e)}")
                    per_check_results.setdefault(category, {})
                    for check_func in CheckRegistry.get_checks_for_category(category):
                        dcr = DocumentCheckResult(
                            success=False,
                            issues=[{'error': f"Error in {category} checks: {str(e)}"}]
                        )
                        per_check_results[category][check_func] = dcr
                    combined_results.issues.append({
                        'error': f"Error in {category} checks: {str(e)}",
                        'category': category
                    })

            # Always ensure per_check_results is populated with all issues
            # If per_check_results is empty or contains only empty sub-dicts, but there are issues, group them by category
            def _has_any_issues(per_check_results):
                for cat in per_check_results.values():
                    for check in cat.values():
                        if hasattr(check, 'issues') and check.issues:
                            return True
                        if isinstance(check, dict) and check.get('issues'):
                            return True
                return False

            if (not per_check_results or not _has_any_issues(per_check_results)) and combined_results.issues:
                # Group issues by category if possible
                grouped = {}
                for issue in combined_results.issues:
                    category = issue.get('category')
                    if not category:
                        # Try to infer from checker_name if present
                        category = issue.get('checker') or 'general'
                    if category not in grouped:
                        grouped[category] = {'success': False, 'issues': [], 'details': {}}
                    grouped[category]['issues'].append(issue)
                # Convert to per_check_results structure
                per_check_results = {cat: {'general': res} for cat, res in grouped.items()}
            combined_results.per_check_results = per_check_results
            combined_results.success = len(combined_results.issues) == 0
            logger.info(f"Completed all checks. Found {len(combined_results.issues)} issues.")
            return combined_results

        except Exception as e:
            logger.error(f"Error running document checks: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{'error': f"Error running document checks: {str(e)}"}]
            )