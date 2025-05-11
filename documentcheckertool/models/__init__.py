from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

class Severity(Enum):
    """Enum for issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class DocumentType(Enum):
    ADVISORY_CIRCULAR = "Advisory Circular"
    AIRWORTHINESS_CRITERIA = "Airworthiness Criteria"
    DEVIATION_MEMO = "Deviation Memo"
    EXEMPTION = "Exemption"
    FEDERAL_REGISTER_NOTICE = "Federal Register Notice"
    ORDER = "Order"
    POLICY_STATEMENT = "Policy Statement"
    RULE = "Rule"
    SPECIAL_CONDITION = "Special Condition"
    TECHNICAL_STANDARD_ORDER = "Technical Standard Order"
    OTHER = "Other"

@dataclass
class DocumentCheckResult:
    success: bool = True
    severity: Severity = Severity.ERROR
    issues: List[Dict[str, Any]] = field(default_factory=list)
    details: Optional[Dict[str, Any]] = None

    def add_issue(self, message: str, severity: Severity, line_number: int = None) -> None:
        """Add an issue to the result."""
        self.issues.append({
            "message": message,
            "severity": severity,
            "line_number": line_number
        })
        self.success = False  # Set to False for any issue, not just errors
        self.severity = severity

    def add_detail(self, key: str, value: Any) -> None:
        if self.details is None:
            self.details = {}
        self.details[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'severity': self.severity.value,
            'issues': self.issues,
            'details': self.details
        }
