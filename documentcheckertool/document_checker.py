import logging
from typing import List, Dict, Any, Optional
from docx import Document
from documentcheckertool.models import DocumentCheckResult, DocumentType
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.checks.reference_checks import TableFigureReferenceCheck
from documentcheckertool.checks.readability_checks import ReadabilityChecks
from documentcheckertool.checks.acronym_checks import AcronymChecker
from documentcheckertool.utils.text_utils import split_sentences, count_words, normalize_reference
from documentcheckertool.utils.pattern_cache import PatternCache
from documentcheckertool.utils.terminology_utils import TerminologyManager
from .utils.check_discovery import validate_check_registration

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

            # Load the document
            if isinstance(document_path, str) and (document_path.lower().endswith('.docx') or document_path.lower().endswith('.doc')):
                doc = Document(document_path)
                # Extract text from the document
                doc.text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                logger.debug(f"Loaded document from file: {document_path}, extracted text length: {len(doc.text)}")
            else:
                # For text content, create a simple document structure
                doc = Document()
                if isinstance(document_path, list):
                    doc.text = '\n'.join(document_path)
                    logger.debug(f"Created document from list of strings, length: {len(document_path)}")
                else:
                    doc.text = document_path
                    logger.debug(f"Created document from raw string, length: {len(document_path)}")

            # Define all check modules with their names for logging
            check_modules = [
                (self.heading_checks, "Heading Checks"),
                (self.accessibility_checks, "Accessibility Checks"),
                (self.format_checks, "Format Checks"),
                (self.structure_checks, "Structure Checks"),
                (self.terminology_checks, "Terminology Checks"),
                (self.readability_checks, "Readability Checks"),
                (self.acronym_checker, "Acronym Checks"),
                (self.table_figure_checks, "Table/Figure Reference Checks")
            ]

            # Run all checks
            for check_module, check_name in check_modules:
                try:
                    logger.info(f"Running {check_name}...")
                    if hasattr(check_module, 'check_text'):
                        # Special case for modules with check_text interface
                        result = check_module.check_text(doc.text)
                        if not result.success:
                            combined_results.issues.extend(result.issues)
                    else:
                        # Standard interface
                        check_module.run_checks(doc, doc_type, combined_results)
                except Exception as e:
                    logger.error(f"Error in {check_name}: {str(e)}")
                    combined_results.issues.append({
                        'error': f"Error in {check_name}: {str(e)}"
                    })

            # Set success based on whether any issues were found
            combined_results.success = len(combined_results.issues) == 0

            logger.info(f"Completed all checks. Found {len(combined_results.issues)} issues.")
            return combined_results

        except Exception as e:
            logger.error(f"Error running document checks: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{'error': f"Error running document checks: {str(e)}"}]
            )