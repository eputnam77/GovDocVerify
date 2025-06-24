from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DocumentValidationResults:
    """Keep track of an item's validation status."""

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
