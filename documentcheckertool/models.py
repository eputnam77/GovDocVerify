from dataclasses import dataclass
from enum import Enum, auto, IntEnum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from documentcheckertool.models import DocumentType, DocumentTypeError
import json

class DocumentCheckError(Exception):
    """Base exception for document checking errors."""
    pass

class ConfigurationError(DocumentCheckError):
    """Exception for configuration-related errors."""
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

class Severity(IntEnum):
    """Severity levels for issues."""
    ERROR = 0
    WARNING = 1
    INFO = 2

    def to_color(self) -> str:
        """Convert severity to color."""
        return ["red", "orange", "blue"][self]

    @property
    def value_str(self) -> str:
        """Get the string representation of the severity."""
        return ["error", "warning", "info"][self]

@dataclass
class DocumentCheckResult:
    """Result of a document check."""
    success: bool = True
    issues: List[Dict[str, Any]] = None
    checker_name: Optional[str] = None
    score: float = 1.0
    severity: Optional['Severity'] = None
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.issues is None:
            self.issues = []
        self.severity = None  # Will be set on first issue

    def add_issue(self, message: str, severity: 'Severity', line_number: int = None):
        """Add an issue to the result."""
        self.issues.append({
            "message": message,
            "severity": severity,
            "line_number": line_number
        })
        # Any issue marks the run as unsuccessful
        self.success = False

        # Keep track of the most severe issue (ERROR < WARNING < INFO)
        if self.severity is None or severity < self.severity:
            self.severity = severity

    def to_html(self) -> str:
        """Convert the result to HTML."""
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

            html.append(f"<h3 style='color: {color};'>{severity.value_str} Severity Issues:</h3>")
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

@dataclass
class VisibilitySettings:
    """Settings for controlling visibility of different check categories."""
    show_readability: bool = True
    show_paragraph_length: bool = True
    show_terminology: bool = True
    show_headings: bool = True
    show_structure: bool = True
    show_format: bool = True
    show_accessibility: bool = True
    show_document_status: bool = True

    def to_dict(self) -> Dict[str, bool]:
        """Convert settings to dictionary format."""
        return {
            'readability': self.show_readability,
            'paragraph_length': self.show_paragraph_length,
            'terminology': self.show_terminology,
            'headings': self.show_headings,
            'structure': self.show_structure,
            'format': self.show_format,
            'accessibility': self.show_accessibility,
            'document_status': self.show_document_status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'VisibilitySettings':
        """Create settings from dictionary format."""
        return cls(
            show_readability=data.get('readability', True),
            show_paragraph_length=data.get('paragraph_length', True),
            show_terminology=data.get('terminology', True),
            show_headings=data.get('headings', True),
            show_structure=data.get('structure', True),
            show_format=data.get('format', True),
            show_accessibility=data.get('accessibility', True),
            show_document_status=data.get('document_status', True)
        )

    @classmethod
    def from_dict_json(cls, json_str: str) -> 'VisibilitySettings':
        """Create settings from a JSON string."""
        try:
            data = json.loads(json_str)
        except Exception:
            data = {}
        return cls.from_dict(data)