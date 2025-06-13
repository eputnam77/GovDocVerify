from typing import Any, Dict, List

from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter

from ..utils.formatting import DocumentFormatter
from .check_registry import CheckRegistry


class BaseChecker:
    """Base class for all document checkers."""

    def __init__(self, terminology_manager=None):
        self.name = self.__class__.__name__
        self.pattern_cache = None
        self._formatter = DocumentFormatter()
        self.formatter = ResultFormatter(style=FormatStyle.HTML)
        self.terminology_manager = terminology_manager

    def run_checks(self, document: Any, doc_type: str, results: DocumentCheckResult) -> None:
        """Base method to run all checks for this checker."""
        raise NotImplementedError("Subclasses must implement run_checks")

    def format_results(
        self, results: Dict[str, Any], doc_type: str, metadata: Dict[str, Any] | None = None
    ) -> str:
        """Format check results using the unified formatter."""
        return self.formatter.format_results(results, doc_type, metadata=metadata)

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content and return results."""
        raise NotImplementedError("Subclasses must implement check_text")

    def check_document(self, document: Any, doc_type: str = None) -> DocumentCheckResult:
        """Check a document and return results."""
        # If document is a file path string, read the file
        if isinstance(document, str):
            with open(document, "r", encoding="utf-8") as f:
                content = f.read()
            return self.check_text(content)

        # If document has text attribute, use it
        if hasattr(document, "text"):
            return self.check_text(document.text)

        # If document is already text content
        if isinstance(document, (str, list)):
            return self.check_text(document)

        # Default fallback
        return self.check_text(str(document))

    def create_issue(
        self, message: str, line_number: int = 0, severity: str = "warning", category: str = None
    ) -> Dict[str, Any]:
        """Create a standardized issue dictionary."""
        return {
            "message": message,
            "line_number": line_number,
            "severity": severity,
            "checker": self.name,
            "category": category or getattr(self, "category", None),
        }

    def create_result(
        self, issues: List[Dict[str, Any]], success: bool = True
    ) -> DocumentCheckResult:
        """Create a standardized check result."""
        return DocumentCheckResult(success=success, issues=issues, checker_name=self.name)

    @classmethod
    def get_registered_checks(cls) -> Dict[str, List[str]]:
        """Get all registered checks for this checker class.

        Returns:
            Dictionary mapping categories to lists of check function names
        """
        return CheckRegistry.get_category_mappings()

    @classmethod
    def register_check(cls, category: str):
        """Decorator to register a check function.

        Args:
            category: The category to register the check under

        Returns:
            Decorator function
        """
        return CheckRegistry.register(category)
