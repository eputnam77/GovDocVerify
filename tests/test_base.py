# python -m unittest discover tests to run all tests

import unittest
import os
import tempfile
from typing import List, Dict, Any
from docx import Document
from document_checker import FAADocumentChecker
from models import DocumentType, DocumentCheckResult

class TestBase(unittest.TestCase):
    """Base test class with common test functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.checker = FAADocumentChecker()
        self.temp_files = []
    
    def tearDown(self):
        """Clean up test environment."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_test_docx(self, content: List[str], filename: str) -> str:
        """Create a temporary DOCX file with given content."""
        doc = Document()
        for paragraph in content:
            doc.add_paragraph(paragraph)
        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        doc.save(temp_path)
        self.temp_files.append(temp_path)
        return temp_path
    
    def assert_check_result(self, result: DocumentCheckResult, expected_success: bool, 
                          expected_issue_count: int = 0):
        """Assert that a check result matches expectations."""
        self.assertEqual(result.success, expected_success)
        self.assertEqual(len(result.issues), expected_issue_count)
    
    def assert_no_issues(self, result: DocumentCheckResult):
        """Assert that a check result has no issues."""
        self.assertTrue(result.success, f"Expected no issues but found: {result.issues}")
        self.assertEqual(len(result.issues), 0, f"Expected no issues but found: {result.issues}")
    
    def assert_has_issues(self, result: DocumentCheckResult):
        """Assert that a check result has issues."""
        self.assertFalse(result.success, "Expected issues but found none")
        self.assertGreater(len(result.issues), 0, "Expected issues but found none")
    
    def assert_issue_contains(self, result: DocumentCheckResult, text: str):
        """Assert that a check result contains an issue with the given text."""
        self.assertFalse(result.success, "Expected issues but found none")
        self.assertTrue(any(text in issue.get('message', '') for issue in result.issues),
                       f"Expected to find issue containing '{text}' but found: {result.issues}") 