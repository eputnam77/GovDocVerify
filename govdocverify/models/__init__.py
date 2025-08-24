import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, ClassVar, Dict, List, Optional


class Severity(IntEnum):
    """Enum for issue severity levels."""

    ERROR = 0
    WARNING = 1
    INFO = 2

    def to_color(self) -> str:
        """Return a color name for the severity."""
        return ["red", "orange", "blue"][self]

    @property
    def value_str(self) -> str:
        return ["error", "warning", "info"][self]


class DocumentTypeError(Exception):
    """Raised when an invalid document type is provided."""

    pass


class DocumentType(str, Enum):
    """Supported document types for FAA documents."""

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

    def __str__(self) -> str:
        """Return the value of the enum member."""
        return self.value

    @classmethod
    def from_string(cls, doc_type: str) -> "DocumentType":
        """Convert string to DocumentType enum.

        Args:
            doc_type: String representation of document type

        Returns:
            DocumentType enum member

        Raises:
            DocumentTypeError: If the document type is invalid
        """
        if not doc_type or not isinstance(doc_type, str):
            raise DocumentTypeError(f"Invalid document type: {doc_type}")

        # Normalize the input string:
        # 1. Strip leading/trailing whitespace
        # 2. Replace multiple spaces/newlines/tabs with single space
        # 3. Title case the string
        normalized = re.sub(r"\s+", " ", doc_type.strip()).title()

        # Try direct value match first
        for member in cls:
            if member.value == normalized:
                return member

        # Try case-insensitive match
        for member in cls:
            if member.value.lower() == normalized.lower():
                return member

        raise DocumentTypeError(f"Invalid document type: {doc_type}")

    @classmethod
    def values(cls) -> List[str]:
        """Get list of document type values.

        Returns:
            List of string values for all document types
        """
        return [doc_type.value for doc_type in cls]


@dataclass
class DocumentCheckResult:
    """Result of a document check."""

    SERIALIZATION_VERSION: ClassVar[int] = 1

    success: bool = True
    issues: List[Dict[str, Any]] = field(default_factory=list)
    checker_name: Optional[str] = None
    score: float = 1.0
    severity: Optional["Severity"] = None
    details: Optional[Dict[str, Any]] = None
    partial_failures: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize default values and ensure all issues have a category."""
        # Defensive: ensure all issues have a category
        for issue in self.issues:
            if "category" not in issue or not issue["category"]:
                issue["category"] = getattr(self, "checker_name", None) or "general"
                logging.warning(
                    "[DEFENSIVE] Issue missing category. "
                    f"Assigned category: '{issue['category']}'. "
                    f"Issue details: {issue}"
                )
        # ``severity`` might be provided by callers that already know the
        # overall state.  The previous implementation unconditionally reset it
        # to ``None`` here, discarding that information.  Preserve the supplied
        # value and leave it unchanged until issues are added.

    def add_issue(
        self,
        message: str,
        severity: "Severity",
        line_number: int | None = None,
        category: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Add an issue to the result."""
        if category is None:
            category = getattr(self, "checker_name", None) or "general"
        issue = {
            "message": message,
            "severity": severity,
            "line_number": line_number,
            "category": category,
        }
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
        by_severity: Dict[Severity, List[Dict[str, Any]]] = {}
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

    # ---- Serialization helpers -------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result to a dictionary with version metadata."""
        issues: List[Dict[str, Any]] = []
        for issue in self.issues:
            new_issue = issue.copy()
            sev = new_issue.get("severity")
            if isinstance(sev, Severity):
                new_issue["severity"] = sev.value
            issues.append(new_issue)

        return {
            "version": self.SERIALIZATION_VERSION,
            "success": self.success,
            "issues": issues,
            "checker_name": self.checker_name,
            "score": self.score,
            "severity": self.severity.value if self.severity is not None else None,
            "details": self.details,
            "partial_failures": self.partial_failures,
        }

    def to_json(self) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentCheckResult":
        """Deserialize a result from a dictionary.

        Data without explicit version metadata is treated as version 0 for
        backward compatibility.
        """

        version = int(data.get("version", 0))
        if version > cls.SERIALIZATION_VERSION:
            raise ValueError(f"Unsupported DocumentCheckResult version: {version}")

        issues: List[Dict[str, Any]] = []
        for issue in data.get("issues", []):
            new_issue = issue.copy()
            sev = new_issue.get("severity")
            if isinstance(sev, int):
                new_issue["severity"] = Severity(sev)
            issues.append(new_issue)

        severity = data.get("severity")
        if isinstance(severity, int):
            severity = Severity(severity)

        return cls(
            success=data.get("success", True),
            issues=issues,
            checker_name=data.get("checker_name"),
            score=data.get("score", 1.0),
            severity=severity,
            details=data.get("details"),
            partial_failures=data.get("partial_failures", []),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentCheckResult":
        """Deserialize a result from a JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class VisibilitySettings:
    """Settings for controlling visibility of different check categories."""

    SERIALIZATION_VERSION: ClassVar[int] = 1

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

    def to_dict(self) -> Dict[str, bool | int]:
        """Convert settings to dictionary format with version metadata."""
        data: Dict[str, bool | int] = {
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
        data["version"] = self.SERIALIZATION_VERSION
        return data

    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> "VisibilitySettings":
        """Create settings from dictionary format.

        Data without explicit version metadata is treated as version 0 for
        backward compatibility.
        """

        version = int(settings.get("version", 0))
        if version > cls.SERIALIZATION_VERSION:
            raise ValueError(f"Unsupported VisibilitySettings version: {version}")

        return cls(
            show_readability=settings.get("readability", True),
            show_analysis=settings.get("analysis", True),
            show_paragraph_length=settings.get("paragraph_length", True),
            show_terminology=settings.get("terminology", True),
            show_headings=settings.get("headings", True),
            show_structure=settings.get("structure", True),
            show_format=settings.get("format", True),
            show_accessibility=settings.get("accessibility", True),
            show_document_status=settings.get("document_status", True),
            show_acronym=settings.get("acronym", True),
        )

    @classmethod
    def from_dict_json(cls, json_str: str) -> "VisibilitySettings":
        """Create settings from a JSON string."""
        try:
            data = json.loads(json_str)
        except Exception:
            data = {}
        return cls.from_dict(data)
