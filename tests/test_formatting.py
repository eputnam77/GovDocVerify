# python -m pytest tests/test_formatting.py -v

import unittest
from test_base import TestBase
try:
    from documentcheckertool.checks import FormattingChecker
except ImportError:
    from documentcheckertool.formatting.checker import FormattingChecker
from documentcheckertool.formatters.document_formatter import DocumentFormatter, FormatStyle

class TestFormatting(TestBase):
    """Test suite for formatting and style checks."""
    
    def setUp(self):
        super().setUp()
        self.formatter = DocumentFormatter()

    def test_format_styles(self):
        """Test different formatting styles."""
        issue = {
            'message': 'Test issue',
            'context': 'Test context'
        }
        result = DocumentCheckResult(success=False, issues=[issue])
        
        plain = DocumentFormatter.create('plain')
        markdown = DocumentFormatter.create('markdown')
        html = DocumentFormatter.create('html')
        
        self.assertIn('•', plain.format_issues(result)[0])
        self.assertIn('-', markdown.format_issues(result)[0])
        self.assertIn('<li>', html.format_issues(result)[0])

    def test_double_period_check_valid(self):
        """Test double period check with valid text."""
        content = [
            "This is a valid sentence.",
            "This is another valid sentence.",
            "This is a third valid sentence."
        ]
        result = self.formatting_checker.check_punctuation(content)
        self.assert_no_issues(result)
    
    def test_double_period_check_invalid(self):
        """Test double period check with invalid text."""
        content = [
            "This is a sentence with double periods..",
            "This is another sentence with double periods..",
            "This is a third sentence with double periods.."
        ]
        result = self.formatting_checker.check_punctuation(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "double periods")
    
    def test_spacing_check_valid(self):
        """Test spacing check with valid text."""
        content = [
            "This is a sentence with proper spacing.",
            "This is another sentence with proper spacing.",
            "This is a third sentence with proper spacing."
        ]
        result = self.formatting_checker.check_spacing(content)
        self.assert_no_issues(result)
    
    def test_spacing_check_invalid(self):
        """Test spacing check with invalid text."""
        content = [
            "This is a sentence with  extra  spacing.",
            "This is another sentence with  extra  spacing.",
            "This is a third sentence with  extra  spacing."
        ]
        result = self.formatting_checker.check_spacing(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "extra spaces")
    
    def test_parentheses_check_valid(self):
        """Test parentheses check with valid text."""
        content = [
            "This is a sentence with (proper) parentheses.",
            "This is another sentence with (proper) parentheses.",
            "This is a third sentence with (proper) parentheses."
        ]
        result = self.formatting_checker.check_parentheses(content)
        self.assert_no_issues(result)
    
    def test_parentheses_check_invalid(self):
        """Test parentheses check with invalid text."""
        content = [
            "This is a sentence with (unmatched parentheses.",
            "This is another sentence with unmatched) parentheses.",
            "This is a third sentence with (unmatched parentheses."
        ]
        result = self.formatting_checker.check_parentheses(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "unmatched parentheses")
    
    def test_section_symbol_check_valid(self):
        """Test section symbol check with valid text."""
        content = [
            "This is a sentence with § 1.1.",
            "This is another sentence with § 2.1.",
            "This is a third sentence with § 3.1."
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        self.assert_no_issues(result)
    
    def test_section_symbol_check_invalid(self):
        """Test section symbol check with invalid text."""
        content = [
            "This is a sentence with §1.1.",
            "This is another sentence with §2.1.",
            "This is a third sentence with §3.1."
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "section symbol")

    def test_list_formatting_valid(self):
        """Test list formatting with valid text."""
        content = [
            "1. First item",
            "2. Second item",
            "3. Third item"
        ]
        result = self.formatting_checker.check_list_formatting(content)
        self.assert_no_issues(result)

    def test_list_formatting_invalid(self):
        """Test list formatting with invalid text."""
        content = [
            "1.First item",  # Missing space
            "2.  Second item",  # Extra space
            "3 Third item"  # Missing period
        ]
        result = self.formatting_checker.check_list_formatting(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "inconsistent list formatting")

    def test_quotation_marks(self):
        """Test quotation marks consistency."""
        content = [
            'Using "straight quotes" instead of "curly quotes"',
            "Mix of 'single' and "double" quotes"
        ]
        result = self.formatting_checker.check_quotation_marks(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "inconsistent quotation marks")

    def test_bullet_list_formatting(self):
        """Test bullet list formatting."""
        content = [
            "• First bullet",
            "•Second bullet",  # Missing space
            "•  Third bullet"  # Extra space
        ]
        result = self.formatting_checker.check_list_formatting(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "inconsistent bullet spacing")

if __name__ == '__main__':
    unittest.main()