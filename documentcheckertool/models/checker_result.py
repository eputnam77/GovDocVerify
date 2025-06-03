from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentValidationResults:
    """Class for keeping track of an item's validation status."""
    is_valid: bool
    message: str
    found: Optional[str] = None
    expected: Optional[str] = None
    watermark_validation: Optional[dict] = None

    def add_watermark_result(self, is_valid: bool, message: str, found_watermark: str = None, expected_watermark: str = None):
        """Add watermark validation results."""
        self.watermark_validation = {
            'is_valid': is_valid,
            'message': message,
            'found': found_watermark,
            'expected': expected_watermark
        }
