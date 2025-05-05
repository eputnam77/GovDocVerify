# python -m unittest tests/test_headings.py -v

import unittest
from .test_base import TestBase
from documentcheckertool.app import DOCUMENT_TYPES
from docx import Document
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.utils.pattern_cache import PatternCache

class TestHeadingChecks(TestBase):
    """Test suite for heading and title checks."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.pattern_cache = PatternCache()
        self.heading_checks = HeadingChecks(self.pattern_cache)
    
    def test_heading_title_check_valid(self):
        """Test heading title check with valid headings."""
        content = [
            "1. Purpose",
            "2. Applicability",
            "3. Background",
            "4. Discussion"
        ]
        doc_path = self.create_test_docx(content, "valid_headings.docx")
        result = self.heading_checks.check_heading_title(content, "Advisory Circular")
        self.assert_no_issues(result)
    
    def test_heading_title_check_invalid(self):
        """Test heading title check with invalid headings."""
        content = [
            "1. Invalid Heading",
            "2. Another Invalid Heading",
            "3. Yet Another Invalid Heading"
        ]
        doc_path = self.create_test_docx(content, "invalid_headings.docx")
        result = self.heading_checks.check_heading_title(content, "Advisory Circular")
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Heading formatting issue")
    
    def test_heading_title_period_check_valid(self):
        """Test heading title period check with valid headings."""
        content = [
            "1. Purpose.",
            "2. Applicability.",
            "3. Background.",
            "4. Discussion."
        ]
        doc_path = self.create_test_docx(content, "valid_period_headings.docx")
        result = self.heading_checks.check_heading_period(content, "Advisory Circular")
        self.assert_no_issues(result)
    
    def test_heading_title_period_check_invalid(self):
        """Test heading title period check with invalid headings."""
        content = [
            "1. Purpose",
            "2. Applicability",
            "3. Background",
            "4. Discussion"
        ]
        doc_path = self.create_test_docx(content, "invalid_period_headings.docx")
        result = self.heading_checks.check_heading_period(content, "Advisory Circular")
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Heading missing required period")
    
    def test_heading_sequence_check_valid(self):
        """Test heading sequence check with valid sequence."""
        content = [
            "1. First Level",
            "1.1 Second Level",
            "1.1.1 Third Level",
            "2. First Level",
            "2.1 Second Level"
        ]
        doc_path = self.create_test_docx(content, "valid_sequence.docx")
        result = self.heading_checks.check_heading_structure(Document(doc_path))
        self.assertEqual(len(result), 0)
    
    def test_heading_sequence_check_invalid(self):
        """Test heading sequence check with invalid sequence."""
        content = [
            "1. First Level",
            "1.1 Second Level",
            "1.1.1 Third Level",
            "1.1.1.1 Fourth Level",  # Invalid: skipped level
            "2. First Level"
        ]
        doc_path = self.create_test_docx(content, "invalid_sequence.docx")
        result = self.heading_checks.check_heading_structure(Document(doc_path))
        self.assertGreater(len(result), 0)
        self.assertTrue(any("skipped level" in issue.get('message', '') for issue in result))

if __name__ == '__main__':
    unittest.main()