import unittest
from test_base import TestBase

class TestFormatChecks(TestBase):
    """Test suite for phone number and date format checks."""
    
    def test_phone_number_format_check_valid(self):
        """Test phone number format check with valid formats."""
        content = [
            "Contact us at (202) 267-1000.",
            "For emergencies, call (800) 555-1212.",
            "The office number is (703) 123-4567."
        ]
        doc_path = self.create_test_docx(content, "valid_phone_numbers.docx")
        result = self.checker.check_phone_number_format(content)
        self.assert_no_issues(result)
    
    def test_phone_number_format_check_invalid(self):
        """Test phone number format check with invalid formats."""
        content = [
            "Contact us at 202-267-1000.",
            "For emergencies, call 800.555.1212.",
            "The office number is 7031234567."
        ]
        doc_path = self.create_test_docx(content, "invalid_phone_numbers.docx")
        result = self.checker.check_phone_number_format(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "phone number format")
    
    def test_date_format_check_valid(self):
        """Test date format check with valid formats."""
        content = [
            "The document was issued on January 1, 2023.",
            "The meeting is scheduled for December 31, 2023.",
            "The deadline is March 15, 2023."
        ]
        doc_path = self.create_test_docx(content, "valid_dates.docx")
        result = self.checker.check_date_formats(content)
        self.assert_no_issues(result)
    
    def test_date_format_check_invalid(self):
        """Test date format check with invalid formats."""
        content = [
            "The document was issued on 1/1/2023.",
            "The meeting is scheduled for 12-31-2023.",
            "The deadline is 03.15.2023."
        ]
        doc_path = self.create_test_docx(content, "invalid_dates.docx")
        result = self.checker.check_date_formats(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "date format")
    
    def test_placeholder_check_valid(self):
        """Test placeholder check with valid text."""
        content = [
            "This is a document without placeholders.",
            "This is another sentence without placeholders.",
            "This is a third sentence without placeholders."
        ]
        doc_path = self.create_test_docx(content, "valid_placeholders.docx")
        result = self.checker.check_placeholders(content)
        self.assert_no_issues(result)
    
    def test_placeholder_check_invalid(self):
        """Test placeholder check with invalid text."""
        content = [
            "This is a document with [PLACEHOLDER].",
            "This is another sentence with <PLACEHOLDER>.",
            "This is a third sentence with {PLACEHOLDER}."
        ]
        doc_path = self.create_test_docx(content, "invalid_placeholders.docx")
        result = self.checker.check_placeholders(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "placeholder")

if __name__ == '__main__':
    unittest.main() 