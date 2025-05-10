from typing import List, Dict, Any, Optional
from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.formatting import ResultFormatter
from ..utils.formatting import DocumentFormatter

class BaseChecker:
    """Base class for all document checkers."""

    def __init__(self):
        self.name = self.__class__.__name__
        self.pattern_cache = None
        self._formatter = DocumentFormatter()
        self.formatter = ResultFormatter()

    def run_checks(self, document: Any, doc_type: str, results: DocumentCheckResult) -> None:
        """Base method to run all checks for this checker."""
        raise NotImplementedError("Subclasses must implement run_checks")

    def format_results(self, results: Dict[str, Any], doc_type: str) -> str:
        """Format check results using the unified formatter."""
        return self.formatter.format_results(results, doc_type)

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content and return results."""
        raise NotImplementedError("Subclasses must implement check_text")

    def check_document(self, file_path: str) -> DocumentCheckResult:
        """Check a document file and return results."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.check_text(content)

    def create_issue(self, message: str, line_number: int = 0, severity: str = "warning") -> Dict[str, Any]:
        """Create a standardized issue dictionary."""
        return {
            "message": message,
            "line_number": line_number,
            "severity": severity,
            "checker": self.name
        }

    def create_result(self, issues: List[Dict[str, Any]], success: bool = True) -> DocumentCheckResult:
        """Create a standardized check result."""
        return DocumentCheckResult(
            success=success,
            issues=issues,
            checker_name=self.name
        )
