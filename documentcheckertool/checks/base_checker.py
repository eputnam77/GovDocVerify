from typing import Any
from documentcheckertool.models import DocumentCheckResult

class BaseChecker:
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache

    def run_checks(self, document: Any, doc_type: str, results: DocumentCheckResult) -> None:
        """Base method to run all checks for this checker."""
        raise NotImplementedError("Subclasses must implement run_checks")
