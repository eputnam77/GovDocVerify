from typing import List, Dict, Optional
from documentcheckertool.models import Severity

class DocumentCheckResult:
    def __init__(self, success: bool, issues: List[Dict] = None, severity: Optional[Severity] = None):
        self.success = success
        self.issues = issues or []
        self.severity = severity