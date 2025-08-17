import json
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Optional


@dataclass
class DocumentValidationResults:
    """Keep track of an item's validation status."""

    SERIALIZATION_VERSION: ClassVar[int] = 1

    is_valid: bool
    message: str
    found: Optional[str] = None
    expected: Optional[str] = None
    watermark_validation: Optional[Dict[str, Any]] = None

    def add_watermark_result(
        self,
        is_valid: bool,
        message: str,
        found_watermark: Optional[str] = None,
        expected_watermark: Optional[str] = None,
    ) -> None:
        """Add watermark validation results."""

        self.watermark_validation = {
            "is_valid": is_valid,
            "message": message,
            "found": found_watermark,
            "expected": expected_watermark,
        }

    # ---- Serialization helpers -------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the validation results to a dictionary."""
        return {
            "version": self.SERIALIZATION_VERSION,
            "is_valid": self.is_valid,
            "message": self.message,
            "found": self.found,
            "expected": self.expected,
            "watermark_validation": self.watermark_validation,
        }

    def to_json(self) -> str:
        """Serialize the validation results to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentValidationResults":
        """Deserialize validation results from a dictionary."""
        version = int(data.get("version", 0))
        if version > cls.SERIALIZATION_VERSION:
            raise ValueError(f"Unsupported DocumentValidationResults version: {version}")
        return cls(
            is_valid=data.get("is_valid", False),
            message=data.get("message", ""),
            found=data.get("found"),
            expected=data.get("expected"),
            watermark_validation=data.get("watermark_validation"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentValidationResults":
        """Deserialize validation results from a JSON string."""
        return cls.from_dict(json.loads(json_str))
