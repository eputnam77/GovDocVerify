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

logger = logging.getLogger(__name__)

class FAADocumentChecker:
    """Main document checker class that coordinates various checks."""

    def __init__(self, terminology_manager=None, config_path: Optional[str] = None):
        self.pattern_cache = PatternCache()
        self.terminology_manager = terminology_manager or TerminologyManager()

        # Initialize all check modules
        self.heading_checks = HeadingChecks(self.terminology_manager)
        self.accessibility_checks = AccessibilityChecks(self.terminology_manager)
        self.format_checks = FormatChecks(self.terminology_manager)
        self.structure_checks = StructureChecks(self.terminology_manager)
        self.terminology_checks = TerminologyChecks(self.terminology_manager)
        self.readability_checks = ReadabilityChecks(self.terminology_manager)
        self.acronym_checker = AcronymChecker()
        self.table_figure_checks = TableFigureReferenceCheck()

        # Load configuration if provided
        self.config = self._load_config(config_path) if config_path else {}

    def run_all_document_checks(self, document_path: str, doc_type: str = None) -> DocumentCheckResult:
        """Run all document checks."""
        try:
            doc = Document(document_path)
            results = DocumentCheckResult()

            # Get all standard check modules
            check_modules = [
                self.heading_checks,
                self.accessibility_checks,
                self.format_checks,
                self.structure_checks,
                self.terminology_checks,
                self.readability_checks
            ]

            # Run all standard checks
            for check_module in check_modules:
                try:
                    logger.info(f"Running {check_module.__class__.__name__}")
                    check_module.run_checks(doc, doc_type, results)
                except Exception as e:
                    logger.error(f"Error in {check_module.__class__.__name__}: {str(e)}")
                    results.issues.append({
                        'error': f"Error in {check_module.__class__.__name__}: {str(e)}"
                    })
                    results.success = False

            # Run acronym checks (special case due to different interface)
            try:
                logger.info("Running AcronymChecker")
                acronym_result = self.acronym_checker.check_text(doc.text)
                if not acronym_result.success:
                    results.issues.extend(acronym_result.issues)
                    results.success = False
            except Exception as e:
                logger.error(f"Error in AcronymChecker: {str(e)}")
                results.issues.append({
                    'error': f"Error in AcronymChecker: {str(e)}"
                })
                results.success = False

            # Run table/figure reference check (special case due to different interface)
            try:
                logger.info("Running TableFigureReferenceCheck")
                table_figure_result = self.table_figure_checks.check_text(doc.text)
                if not table_figure_result.success:
                    results.issues.extend(table_figure_result.issues)
                    results.success = False
            except Exception as e:
                logger.error(f"Error in TableFigureReferenceCheck: {str(e)}")
                results.issues.append({
                    'error': f"Error in TableFigureReferenceCheck: {str(e)}"
                })
                results.success = False

            return results

        except Exception as e:
            logger.error(f"Error running document checks: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{'error': f"Error running document checks: {str(e)}"}]
            )