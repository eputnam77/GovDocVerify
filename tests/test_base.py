# python -m unittest discover tests to run all tests

import unittest
import os
from typing import List, Dict, Any
from docx import Document
from app import FAADocumentChecker, DocumentType, DocumentCheckResult

class TestBase(unittest.TestCase):
    """Base class for all document checker tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.checker = FAADocumentChecker()
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(cls.test_data_dir, exist_ok=True)
    
    def create_test_docx(self, content: List[str], filename: str) -> str:
        """Create a test DOCX file with the given content."""
        doc = Document()
        for paragraph in content:
            doc.add_paragraph(paragraph)
        filepath = os.path.join(self.test_data_dir, filename)
        doc.save(filepath)
        return filepath
    
    def assert_check_result(self, result: DocumentCheckResult, expected_success: bool, 
                          expected_issue_count: int = 0):
        """Assert that a check result matches expectations."""
        self.assertEqual(result.success, expected_success)
        self.assertEqual(len(result.issues), expected_issue_count)
    
    def assert_issue_contains(self, result: DocumentCheckResult, expected_text: str):
        """Assert that at least one issue contains the expected text."""
        issue_texts = [issue.get('text', '') for issue in result.issues]
        self.assertTrue(any(expected_text in text for text in issue_texts),
                       f"Expected text '{expected_text}' not found in issues: {issue_texts}")
    
    def assert_no_issues(self, result: DocumentCheckResult):
        """Assert that there are no issues in the result."""
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)
    
    def assert_has_issues(self, result: DocumentCheckResult, min_issues: int = 1):
        """Assert that there are at least the minimum number of issues."""
        self.assertFalse(result.success)
        self.assertGreaterEqual(len(result.issues), min_issues) 