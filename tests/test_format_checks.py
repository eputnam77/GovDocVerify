# python -m pytest tests/test_format_checks.py -v

import unittest
from test_base import TestBase
from documentcheckertool.checks.format_checks import FormatChecks

class TestFormatChecks(TestBase):
    """Test suite for format-related checks."""
    
    def setUp(self):
        super().setUp()
        self.format_checks = FormatChecks(self.checker.pattern_cache)
    
    def test_date_format_usage(self):
        """Test date format checking."""
        content = [
            "Date: 12/31/2023",
            "Effective: 1/1/24",
            "Valid until 2023-12-31"
        ]
        result = self.format_checks.check_date_format_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Incorrect date format")
    
    def test_phone_number_format_usage(self):
        """Test phone number format checking."""
        content = [
            "Call 123-456-7890",
            "Phone: 123.456.7890",
            "Contact: (123) 456-7890"
        ]
        result = self.format_checks.check_phone_number_format_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Incorrect phone number format")
    
    def test_placeholder_usage(self):
        """Test placeholder detection."""
        content = [
            "This section is TBD",
            "To be determined later",
            "Content to be added"
        ]
        result = self.format_checks.check_placeholder_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Placeholder found")

if __name__ == '__main__':
    unittest.main()