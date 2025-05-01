# python -m pytest tests/test_acronyms.py -v

import unittest
from test_base import TestBase

class TestAcronymChecks(TestBase):
    """Test suite for acronym and terminology checks."""
    
    def test_acronym_check_valid(self):
        """Test acronym check with valid usage."""
        content = [
            "The Federal Aviation Administration (FAA) is responsible for aviation safety.",
            "The FAA oversees all aspects of civil aviation."
        ]
        doc_path = self.create_test_docx(content, "valid_acronyms.docx")
        result = self.checker.acronym_check(content)
        self.assert_no_issues(result)
    
    def test_acronym_check_invalid(self):
        """Test acronym check with invalid usage."""
        content = [
            "The FAA is responsible for aviation safety.",
            "The FAA oversees all aspects of civil aviation."
        ]
        doc_path = self.create_test_docx(content, "invalid_acronyms.docx")
        result = self.checker.acronym_check(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "FAA")
    
    def test_acronym_usage_check_valid(self):
        """Test acronym usage check with valid usage."""
        content = [
            "The Federal Aviation Administration (FAA) is responsible for aviation safety.",
            "The FAA oversees all aspects of civil aviation.",
            "The FAA's mission is to provide the safest, most efficient aerospace system in the world."
        ]
        doc_path = self.create_test_docx(content, "valid_acronym_usage.docx")
        result = self.checker.acronym_usage_check(content)
        self.assert_no_issues(result)
    
    def test_acronym_usage_check_invalid(self):
        """Test acronym usage check with invalid usage."""
        content = [
            "The Federal Aviation Administration (FAA) is responsible for aviation safety.",
            "The FAA oversees all aspects of civil aviation.",
            "The Federal Aviation Administration's mission is to provide the safest system."
        ]
        doc_path = self.create_test_docx(content, "invalid_acronym_usage.docx")
        result = self.checker.acronym_usage_check(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Federal Aviation Administration")
    
    def test_terminology_check_valid(self):
        """Test terminology check with valid usage."""
        content = [
            "The aircraft must meet the requirements specified in this advisory circular.",
            "The pilot must maintain visual contact with the runway."
        ]
        doc_path = self.create_test_docx(content, "valid_terminology.docx")
        result = self.checker.check_terminology(content)
        self.assert_no_issues(result)
    
    def test_terminology_check_invalid(self):
        """Test terminology check with invalid usage."""
        content = [
            "The plane must meet the requirements specified in this advisory circular.",
            "The driver must maintain visual contact with the runway."
        ]
        doc_path = self.create_test_docx(content, "invalid_terminology.docx")
        result = self.checker.check_terminology(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "plane")
        self.assert_issue_contains(result, "driver")

if __name__ == '__main__':
    unittest.main() 