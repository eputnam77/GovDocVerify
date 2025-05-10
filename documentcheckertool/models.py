from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DocumentCheckError(Exception):
    """Base exception for document checking errors."""
    pass

class ConfigurationError(DocumentCheckError):
    """Exception for configuration-related errors."""
    pass

class DocumentTypeError(DocumentCheckError):
    """Exception for document type-related errors."""
    pass

@dataclass
class PatternConfig:
    """Configuration for pattern matching."""
    pattern: str
    description: str
    is_error: bool
    replacement: Optional[str] = None
    keep_together: bool = False
    format_name: Optional[str] = None

class DocumentType(str, Enum):
    """Supported document types."""
    AC = "Advisory Circular"
    ORDER = "Order"
    NOTICE = "Notice"
    NPRM = "Notice of Proposed Rulemaking"
    FR = "Federal Register Notice"

    @classmethod
    def from_string(cls, doc_type: str) -> 'DocumentType':
        """Convert string to DocumentType enum."""
        try:
            return cls[doc_type.upper().replace(' ', '_')]
        except KeyError:
            raise DocumentTypeError(f"Invalid document type: {doc_type}")

class Issue(BaseModel):
    """Represents an issue found during document checking."""
    message: str
    line_number: Optional[int] = None
    severity: str = "warning"
    suggestion: Optional[str] = None

@dataclass
class DocumentCheckResult:
    """Result of a document check."""
    success: bool
    issues: List[Dict[str, Any]]
    checker_name: Optional[str] = None
    score: float = 1.0

    def __post_init__(self):
        """Calculate score based on issues."""
        if self.issues:
            self.score = max(0.0, 1.0 - (len(self.issues) * 0.1))

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def to_color(self) -> str:
        return {
            "LOW": "blue",
            "MEDIUM": "orange",
            "HIGH": "red"
        }[self.value]

class DocumentCheckResult:
    def __init__(self, success: bool = True, issues: List[Dict[str, Any]] = None):
        self.success = success
        self.issues = issues or []

    def add_issue(self, message: str, severity: Severity, line_number: int = None):
        self.issues.append({
            "message": message,
            "severity": severity,
            "line_number": line_number
        })
        if severity in [Severity.MEDIUM, Severity.HIGH]:
            self.success = False

    def to_html(self) -> str:
        if not self.issues:
            return "<div style='color: green;'>✓ No issues found</div>"

        html = ["<div style='padding: 10px;'>"]

        # Group issues by severity
        by_severity = {}
        for issue in self.issues:
            sev = issue["severity"]
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(issue)

        # Generate HTML for each severity group
        for severity in sorted(by_severity.keys(), key=lambda x: x.value):
            issues = by_severity[severity]
            color = severity.to_color()

            html.append(f"<h3 style='color: {color};'>{severity.value} Severity Issues:</h3>")
            html.append("<ul>")
            for issue in issues:
                line_info = f" (line {issue['line_number']})" if issue.get('line_number') else ""
                html.append(f"<li>{issue['message']}{line_info}</li>")
            html.append("</ul>")

        html.append("</div>")
        return "\n".join(html)

class DocumentType(BaseModel):
    """Represents a document type with its associated rules."""
    name: str
    description: str
    rules: List[str]