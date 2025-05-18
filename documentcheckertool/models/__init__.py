from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re

class Severity(Enum):
    """Enum for issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

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
    def from_string(cls, doc_type: str) -> 'DocumentType':
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
        normalized = re.sub(r'\s+', ' ', doc_type.strip()).title()

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
    def from_dict(cls, settings: Dict[str, bool]) -> 'VisibilitySettings':
        """Create settings from dictionary format."""
        return cls(
            show_readability=settings.get('readability', True),
            show_paragraph_length=settings.get('paragraph_length', True),
            show_terminology=settings.get('terminology', True),
            show_headings=settings.get('headings', True),
            show_structure=settings.get('structure', True),
            show_format=settings.get('format', True),
            show_accessibility=settings.get('accessibility', True),
            show_document_status=settings.get('document_status', True)
        )
