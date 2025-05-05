# python -m pytest tests/test_structure_checks.py -v

import unittest
from test_base import TestBase
from documentcheckertool.checks.structure_checks import StructureChecks

class TestStructureChecks(TestBase):
    """Test suite for structure-related checks."""
    
    def setUp(self):
        super().setUp()
        self.structure_checks = StructureChecks(self.checker.pattern_cache)
    
    def test_paragraph_length(self):
        """Test paragraph length checking."""
        content = [
            "Short paragraph.",
            "This is a very long paragraph that exceeds the recommended word count limit. "
            "It contains many words and sentences that make it too lengthy for optimal readability. "
            "The purpose of this test is to verify that the paragraph length checker correctly "
            "identifies paragraphs that are too long and need to be broken down into smaller, "
            "more manageable sections for better comprehension and readability."
        ]
        result = self.structure_checks.check_paragraph_length(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Paragraph too long")
    
    def test_sentence_length(self):
        """Test sentence length checking."""
        content = [
            "Short sentence.",
            "This is a very long sentence that exceeds the recommended word count limit and "
            "should be broken down into multiple shorter sentences for better readability."
        ]
        result = self.structure_checks.check_sentence_length(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Sentence too long")
    
    def test_parentheses(self):
        """Test parentheses checking."""
        content = [
            "Valid (balanced) parentheses.",
            "Invalid (unbalanced parentheses.",
            "Another invalid) parentheses."
        ]
        result = self.structure_checks.check_parentheses(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Mismatched parentheses")

if __name__ == '__main__':
    unittest.main()