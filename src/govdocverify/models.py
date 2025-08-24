import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
    severity: Optional["Severity"] = None
    details: Optional[Dict[str, Any]] = None
    partial_failures: List[Dict[str, Any]] | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.issues is None:
            self.issues = []
        if self.partial_failures is None:
            self.partial_failures = []
        # ``severity`` may be supplied by the caller.  The previous
        # implementation always reset it to ``None`` here, discarding any
        # pre‑set value.  Only leave it as ``None`` when it wasn't provided.
        # It will still be updated when issues are added.

    def add_issue(
        self,
        message: str,
        severity: "Severity",
        line_number: int = None,
        category: str = None,
        **kwargs,
    ):
        """Add an issue to the result."""
        issue = {"message": message, "severity": severity, "line_number": line_number}
        if category is not None:
            issue["category"] = category
        issue.update(kwargs)
        self.issues.append(issue)
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
                html.append(f"<li>{issue['message']}</li>")
            html.append("</ul>")

        html.append("</div>")
        return "\n".join(html)


@dataclass
class VisibilitySettings:
    """Settings for controlling visibility of different check categories."""

    show_readability: bool = True
    show_analysis: bool = True
    show_paragraph_length: bool = True
    show_terminology: bool = True
    show_headings: bool = True
    show_structure: bool = True
    show_format: bool = True
    show_accessibility: bool = True
    show_document_status: bool = True
    show_acronym: bool = True
    _show_only_set: set[str] | None = None
    _hide_set: set[str] | None = None

    def to_dict(self) -> Dict[str, bool]:
        """Convert settings to dictionary format."""
        return {
            "readability": self.show_readability,
            "analysis": self.show_analysis,
            "paragraph_length": self.show_paragraph_length,
            "terminology": self.show_terminology,
            "headings": self.show_headings,
            "structure": self.show_structure,
            "format": self.show_format,
            "accessibility": self.show_accessibility,
            "document_status": self.show_document_status,
            "acronym": self.show_acronym,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "VisibilitySettings":
        """Create settings from dictionary format."""
        return cls(
            show_readability=data.get("readability", True),
            show_analysis=data.get("analysis", True),
            show_paragraph_length=data.get("paragraph_length", True),
            show_terminology=data.get("terminology", True),
            show_headings=data.get("headings", True),
            show_structure=data.get("structure", True),
            show_format=data.get("format", True),
            show_accessibility=data.get("accessibility", True),
            show_document_status=data.get("document_status", True),
            show_acronym=data.get("acronym", True),
        )

    @classmethod
    def from_dict_json(cls, json_str: str) -> "VisibilitySettings":
        """Create settings from a JSON string."""
        try:
            data = json.loads(json_str)
        except Exception:
            data = {}
        return cls.from_dict(data)
