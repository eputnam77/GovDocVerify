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

class DocumentType(Enum):
    """Enumeration of supported document types."""
    ADVISORY_CIRCULAR = auto()
    AIRWORTHINESS_CRITERIA = auto()
    DEVIATION_MEMO = auto()
    EXEMPTION = auto()
    FEDERAL_REGISTER_NOTICE = auto()
    ORDER = auto()
    POLICY_STATEMENT = auto()
    RULE = auto()
    SPECIAL_CONDITION = auto()
    TECHNICAL_STANDARD_ORDER = auto()
    OTHER = auto()

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

class DocumentCheckResult(BaseModel):
    """Represents the result of a document check."""
    success: bool
    issues: List[Dict] = []
    score: float = 0.0

class DocumentType(BaseModel):
    """Represents a document type with its associated rules."""
    name: str
    description: str
    rules: List[str] 