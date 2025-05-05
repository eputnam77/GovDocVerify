# python -m pytest tests/test_formatting.py -v

import unittest
from test_base import TestBase

class TestFormattingChecks(TestBase):
    """Test suite for formatting and style checks."""
    
    def test_double_period_check_valid(self):
        """Test double period check with valid text."""
        content = [
            "This is a valid sentence.",
            "This is another valid sentence.",
            "This is a third valid sentence."
        ]
        doc_path = self.create_test_docx(content, "valid_periods.docx")
        result = self.checker.double_period_check(content)
        self.assert_no_issues(result)
    
    def test_double_period_check_invalid(self):
        """Test double period check with invalid text."""
        content = [
            "This is a sentence with double periods..",
            "This is another sentence with double periods..",
            "This is a third sentence with double periods.."
        ]
        doc_path = self.create_test_docx(content, "invalid_periods.docx")
        result = self.checker.double_period_check(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "double periods")
    
    def test_spacing_check_valid(self):
        """Test spacing check with valid text."""
        content = [
            "This is a sentence with proper spacing.",
            "This is another sentence with proper spacing.",
            "This is a third sentence with proper spacing."
        ]
        doc_path = self.create_test_docx(content, "valid_spacing.docx")
        result = self.checker.spacing_check(content)
        self.assert_no_issues(result)
    
    def test_spacing_check_invalid(self):
        """Test spacing check with invalid text."""
        content = [
            "This is a sentence with  extra  spacing.",
            "This is another sentence with  extra  spacing.",
            "This is a third sentence with  extra  spacing."
        ]
        doc_path = self.create_test_docx(content, "invalid_spacing.docx")
        result = self.checker.spacing_check(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "extra spaces")
    
    def test_parentheses_check_valid(self):
        """Test parentheses check with valid text."""
        content = [
            "This is a sentence with (proper) parentheses.",
            "This is another sentence with (proper) parentheses.",
            "This is a third sentence with (proper) parentheses."
        ]
        doc_path = self.create_test_docx(content, "valid_parentheses.docx")
        result = self.checker.check_parentheses(content)
        self.assert_no_issues(result)
    
    def test_parentheses_check_invalid(self):
        """Test parentheses check with invalid text."""
        content = [
            "This is a sentence with (unmatched parentheses.",
            "This is another sentence with unmatched) parentheses.",
            "This is a third sentence with (unmatched parentheses."
        ]
        doc_path = self.create_test_docx(content, "invalid_parentheses.docx")
        result = self.checker.check_parentheses(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "unmatched parentheses")
    
    def test_section_symbol_check_valid(self):
        """Test section symbol check with valid text."""
        content = [
            "This is a sentence with § 1.1.",
            "This is another sentence with § 2.1.",
            "This is a third sentence with § 3.1."
        ]
        doc_path = self.create_test_docx(content, "valid_section_symbols.docx")
        result = self.checker.check_section_symbol_usage(content)
        self.assert_no_issues(result)
    
    def test_section_symbol_check_invalid(self):
        """Test section symbol check with invalid text."""
        content = [
            "This is a sentence with §1.1.",
            "This is another sentence with §2.1.",
            "This is a third sentence with §3.1."
        ]
        doc_path = self.create_test_docx(content, "invalid_section_symbols.docx")
        result = self.checker.check_section_symbol_usage(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "section symbol")

if __name__ == '__main__':
    unittest.main() 