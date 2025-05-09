from typing import Any, Dict
from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.formatting import ResultFormatter
from ..utils.formatting import DocumentFormatter

class BaseChecker:
    """Base class for all document checkers."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        self._formatter = DocumentFormatter()
        self.formatter = ResultFormatter()

    def run_checks(self, document: Any, doc_type: str, results: DocumentCheckResult) -> None:
        """Base method to run all checks for this checker."""
        raise NotImplementedError("Subclasses must implement run_checks")

    def format_results(self, results: Dict[str, Any], doc_type: str) -> str:
        """Format check results using the unified formatter."""
        return self.formatter.format_results(results, doc_type)
