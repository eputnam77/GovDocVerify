# python -m unittest discover tests to run all tests

import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document

from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.terminology_utils import TerminologyManager


class TestBase(unittest.TestCase):
    """Base class for all document checker tests."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(__file__).parent / "test_files"
        self.test_dir.mkdir(exist_ok=True)
        self.terminology_manager = TerminologyManager()
        self.checker = FAADocumentChecker()

    def tearDown(self):
        """Clean up after tests."""
        self.cleanup_test_files()

    def create_test_file(self, content: str, filename: str) -> Path:
        """Create a test file with the given content."""
        file_path = self.test_dir / filename
        file_path.write_text(content)
        return file_path

    def cleanup_test_files(self):
        """Clean up test files."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*"):
                file.unlink()

    def assert_check_result(
        self,
        result: DocumentCheckResult,
        expected_issues: Optional[List[Dict]] = None,
        expected_score: Optional[float] = None,
    ):
        """Assert that the check result matches expectations."""
        if expected_issues is not None:
            self.assertEqual(len(result.issues), len(expected_issues))
            for actual, expected in zip(result.issues, expected_issues):
                self.assertEqual(actual["message"], expected["message"])
                self.assertEqual(actual["line_number"], expected["line_number"])
                self.assertEqual(actual["severity"], expected["severity"])

        if expected_score is not None:
            self.assertAlmostEqual(result.score, expected_score, places=2)

    def create_test_docx(self, content: List[str], filename: str) -> str:
        """Create a temporary DOCX file with given content."""
        doc = Document()
        for paragraph in content:
            doc.add_paragraph(paragraph)

        temp_path = os.path.join(tempfile.gettempdir(), filename)
        doc.save(temp_path)
        return temp_path

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
        self.assertTrue(
            any(text in issue.get("message", "") for issue in result.issues),
            f"Expected to find issue containing '{text}' but found: {result.issues}",
        )
