import logging
from functools import lru_cache
from types import SimpleNamespace
from typing import Any, cast

from docx import Document

from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.checks.acronym_checks import AcronymChecker
from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.checks.readability_checks import ReadabilityChecks
from documentcheckertool.checks.reference_checks import (
    DocumentTitleFormatCheck,
    TableFigureReferenceCheck,
)
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.pattern_cache import PatternCache
from documentcheckertool.utils.terminology_utils import TerminologyManager

from .utils.check_discovery import validate_check_registration


@lru_cache(maxsize=8)
def _load_docx_cached(path: str) -> Document:
    """Return a cached ``Document`` instance for the given path."""
    return Document(path)


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
        logger.debug(
            f"HeadingChecks initialized with pattern_cache: {self.heading_checks.pattern_cache}"
        )
        # Pass the terminology manager for API consistency, even though the
        # current implementation does not use it.
        self.format_checks = FormatChecks(self.terminology_manager)
        self.structure_checks = StructureChecks()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)
        logger.debug(
            f"TerminologyChecks initialized with terminology_manager: {self.terminology_manager}"
        )
        self.readability_checks = ReadabilityChecks(self.terminology_manager)
        logger.debug(
            f"ReadabilityChecks initialized with terminology_manager: {self.terminology_manager}"
        )
        self.acronym_checker = AcronymChecker(self.terminology_manager)
        logger.debug(
            f"AcronymChecker initialized with terminology_manager: {self.terminology_manager}"
        )
        self.accessibility_checks = AccessibilityChecks(self.terminology_manager)
        logger.debug(
            f"AccessibilityChecks initialized with terminology_manager: {self.terminology_manager}"
        )
        self.table_figure_checks = TableFigureReferenceCheck()
        logger.debug(f"TableFigureReferenceCheck initialized: {self.table_figure_checks}")
        self.document_title_checks = DocumentTitleFormatCheck()
        logger.debug(f"DocumentTitleFormatCheck initialized: {self.document_title_checks}")

        # Validate check registration
        validation_results = validate_check_registration()
        if validation_results["missing_categories"] or validation_results["missing_checks"]:
            logger.warning("Some checks are not properly registered:")
            if validation_results["missing_categories"]:
                logger.warning(f"Missing categories: {validation_results['missing_categories']}")
            if validation_results["missing_checks"]:
                logger.warning(f"Missing checks: {validation_results['missing_checks']}")
        if validation_results["extra_checks"]:
            logger.warning(f"Extra registered checks: {validation_results['extra_checks']}")
        logger.debug("FAADocumentChecker initialized successfully")

    def run_all_document_checks(
        self, document_path: str, doc_type: str = None
    ) -> DocumentCheckResult:
        """Run all document checks."""
        try:
            combined_results = DocumentCheckResult()
            per_check_results = {}

            # Load the document
            doc = self._load_document(document_path)

            # Define all check modules with their names for logging
            check_modules = self._get_check_modules()

            # Run all checks
            self._run_checks(check_modules, doc, doc_type, combined_results, per_check_results)

            # Ensure per_check_results is populated with all issues
            self._populate_check_results(combined_results, per_check_results)

            combined_results.per_check_results = per_check_results
            combined_results.success = len(combined_results.issues) == 0
            logger.info(f"Completed all checks. Found {len(combined_results.issues)} issues.")
            return combined_results

        except Exception as e:
            logger.error(f"Error running document checks: {str(e)}")
            return DocumentCheckResult(
                success=False, issues=[{"error": f"Error running document checks: {str(e)}"}]
            )

    def _load_document(self, document_path: str) -> SimpleNamespace:
        """Load document from path or create a lightweight representation."""
        if isinstance(document_path, str) and (
            document_path.lower().endswith(".docx") or document_path.lower().endswith(".doc")
        ):
            doc_obj = _load_docx_cached(document_path)
            paragraphs = list(doc_obj.paragraphs)
            text = "\n".join(p.text for p in paragraphs)
            logger.debug(
                "Loaded document from file: %s, extracted text length: %d",
                document_path,
                len(text),
            )
            return SimpleNamespace(paragraphs=paragraphs, text=text)

        if isinstance(document_path, list):
            lines = document_path
            logger.debug(f"Creating document from list of strings, count: {len(document_path)}")
        else:
            lines = str(document_path).splitlines()
            logger.debug(f"Creating document from raw string, line count: {len(lines)}")

        paragraphs = [SimpleNamespace(text=line) for line in lines]
        text = "\n".join(lines)
        return SimpleNamespace(paragraphs=paragraphs, text=text)

    def _get_check_modules(self):
        """Get all check modules with their category names."""
        return [
            (self.heading_checks, "heading"),
            (self.accessibility_checks, "accessibility"),
            (self.format_checks, "format"),
            (self.structure_checks, "structure"),
            (self.terminology_checks, "terminology"),
            (self.readability_checks, "readability"),
            (self.acronym_checker, "acronym"),
            (self.table_figure_checks, "formatting"),
            (self.document_title_checks, "formatting"),
        ]

    def _run_checks(self, check_modules, doc, doc_type, combined_results, per_check_results):
        """Run all check modules and collect results."""
        for check_module, category in check_modules:
            try:
                logger.info(f"Running {category} checks...")
                result = check_module.check_document(doc, doc_type)
                self._process_check_result(result, category, per_check_results)

                # Collect issues from the result
                if hasattr(result, "issues") and result.issues:
                    combined_results.issues.extend(result.issues)

                if not result.success:
                    combined_results.success = False
            except Exception as e:
                self._handle_check_error(e, category, per_check_results, combined_results)

    def _process_check_result(self, result, category, per_check_results):
        """Process individual check result."""
        per_check_results.setdefault(category, {})
        for check_func in CheckRegistry.get_checks_for_category(category):
            if hasattr(result, "checker_name") and result.checker_name == check_func:
                per_check_results[category][check_func] = result
            elif hasattr(result, check_func):
                per_check_results[category][check_func] = getattr(result, check_func)

    def _handle_check_error(self, error, category, per_check_results, combined_results):
        """Handle errors that occur during check execution."""
        logger.error(f"Error in {category} checks: {str(error)}")
        per_check_results.setdefault(category, {})
        for check_func in CheckRegistry.get_checks_for_category(category):
            dcr = DocumentCheckResult(
                success=False,
                issues=[{"error": f"Error in {category} checks: {str(error)}"}],
            )
            per_check_results[category][check_func] = dcr
        combined_results.issues.append(
            {"error": f"Error in {category} checks: {str(error)}", "category": category}
        )

    def _populate_check_results(
        self,
        combined_results: DocumentCheckResult,
        per_check_results: dict[str, dict[str, Any]],
    ) -> None:
        """Ensure per_check_results is populated with all issues."""
        if (
            not per_check_results or not self._has_any_issues(per_check_results)
        ) and combined_results.issues:
            # Group issues by category if possible
            grouped = {}
            for issue in combined_results.issues:
                category = issue.get("category")
                if not category:
                    # Try to infer from checker_name if present
                    category = issue.get("checker") or "general"
                if category not in grouped:
                    grouped[category] = {"success": False, "issues": [], "details": {}}
                grouped[category]["issues"].append(issue)
            # Convert to per_check_results structure
            per_check_results.update({cat: {"general": res} for cat, res in grouped.items()})

    def _has_any_issues(self, per_check_results: dict[str, dict[str, Any]]) -> bool:
        """Check if any results contain issues."""
        for cat in per_check_results.values():
            for check in cat.values():
                if hasattr(check, "issues") and check.issues:
                    return True
                if isinstance(check, dict) and check.get("issues"):
                    return True
        return False

    def check_paragraph_length(
        self,
        content: str | list[str],
        max_sentences: int = 6,
        max_lines: int = 8,
    ) -> DocumentCheckResult:
        """Check paragraph length for given content."""
        logger.debug(f"Checking paragraph length for {len(content)} items")
        results = DocumentCheckResult()

        if isinstance(content, list):
            # Join list content into paragraphs
            for paragraph_text in content:
                if paragraph_text.strip():
                    self.structure_checks._check_paragraph_length(
                        paragraph_text,
                        results,
                        max_sentences,
                        max_lines,
                    )
        else:
            # Handle single string content
            self.structure_checks._check_paragraph_length(
                content, results, max_sentences, max_lines
            )

        results.success = len(results.issues) == 0
        return results

    def check_sentence_length(
        self, content: str | list[str], max_words: int = 30
    ) -> DocumentCheckResult:
        """Check sentence length for given content."""
        logger.debug(f"Checking sentence length for {len(content)} items")
        results = DocumentCheckResult()

        if isinstance(content, list):
            # Join list content and check sentences
            full_text = " ".join(content)
            self.structure_checks._check_sentence_length(full_text, results, max_words)
        else:
            # Handle single string content
            self.structure_checks._check_sentence_length(content, results, max_words)

        results.success = len(results.issues) == 0
        return results

    def check_readability(self, content: str | list[str]) -> DocumentCheckResult:
        """Check readability for given content."""
        logger.debug(f"Checking readability for {len(content)} items")

        if isinstance(content, list):
            # Convert list to text format expected by readability checker
            full_text = "\n".join(content)
        else:
            full_text = content

        # Use the readability checker's check_text method
        return self.readability_checks.check_text(full_text)

    def check_section_508_compliance(self, doc_path: str) -> DocumentCheckResult:
        """Check Section 508 compliance for a document."""
        logger.debug(f"Checking Section 508 compliance for: {doc_path}")

        try:
            # Load the document
            doc = self._load_document(doc_path)

            # Use accessibility checker for 508 compliance
            return cast(
                DocumentCheckResult,
                self.accessibility_checks.check_document(doc, "508_compliance"),
            )

        except Exception as e:
            logger.error(f"Error checking Section 508 compliance: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{"error": f"Error checking Section 508 compliance: {str(e)}"}],
            )
