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
            "Valid until 2023-12-31",
            "Due by March 15, 2024"
        ]
        result = self.format_checks.check_date_format_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Inconsistent date format")
    
    def test_custom_date_format(self):
        """Test custom date format patterns."""
        self.format_checks.set_date_format("DD-MMM-YYYY")
        content = [
            "Date: 31-Dec-2023",
            "Due: 15-Jan-2024"
        ]
        result = self.format_checks.check_date_format_usage(content)
        self.assertTrue(result.success)

    def test_phone_number_format_usage(self):
        """Test phone number format checking."""
        content = [
            "Call +1 (123) 456-7890",
            "Phone: +44 20 7123 4567",
            "Contact: 123.456.7890"
        ]
        result = self.format_checks.check_phone_number_format_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Inconsistent phone number format")

    def test_url_format(self):
        """Test URL format checking."""
        content = [
            "Visit https://example.com",
            "See: http://invalid..com",
            "Web: example.com"
        ]
        result = self.format_checks.check_url_format(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Invalid URL format")

    def test_email_format(self):
        """Test email format checking."""
        content = [
            "Email: user@example.com",
            "Contact: invalid@email",
            "Send to: @domain.com"
        ]
        result = self.format_checks.check_email_format(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Invalid email format")

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