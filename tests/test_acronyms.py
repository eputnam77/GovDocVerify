# python -m pytest tests/test_acronyms.py -v
# pytest -v tests/test_acronyms.py --log-cli-level=DEBUG

import unittest
import pytest
from documentcheckertool.checks.acronym_checks import AcronymChecker
from documentcheckertool.models import DocumentCheckResult

class TestAcronyms(unittest.TestCase):
    """Test cases for acronym checking functionality."""

    def setUp(self):
        """Set up test cases."""
        self.acronym_checker = AcronymChecker()

    def test_valid_acronym_definition(self):
        """Test that valid acronym definitions pass."""
        content = """
        The Federal Aviation Administration (FAA) is responsible for aviation safety.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_missing_acronym_definition(self):
        """Test that missing acronym definitions are caught."""
        content = """
        The NASA is responsible for space exploration.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Acronym 'NASA' used without definition")

    def test_multiple_acronym_definitions(self):
        """Test that multiple acronym definitions are caught."""
        content = """
        The FAA (Federal Aviation Administration) is responsible for aviation safety.
        The FAA (Federal Aviation Administration) regulates air traffic.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Acronym 'FAA' defined multiple times")

    def test_custom_acronym_list(self):
        """Test checking against custom acronym list."""
        # Add custom acronyms one by one
        self.acronym_checker.add_custom_acronym("API", "Application Programming Interface")
        self.acronym_checker.add_custom_acronym("REST", "Representational State Transfer")

        content = """
        The API provides REST services.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_case_sensitive_acronyms(self):
        """Test case sensitivity in acronym checking."""
        content = """
        The Federal Aviation Administration (FAA) oversees aviation.
        Later in the document: The faa continues its work.
        """
        result = self.acronym_checker.check_text(content)
        # Lowercase 'faa' should NOT be flagged as an acronym
        self.assertTrue(result.success)
        # Optionally, check that no issues mention 'faa'
        for issue in result.issues:
            self.assertNotIn("faa", issue.get('message', ''))

    def test_acronym_dictionary_validation(self):
        """Test validation of acronym dictionary format."""
        with pytest.raises(ValueError):
            self.acronym_checker.add_custom_acronym(None, "Invalid definition")
        with pytest.raises(ValueError):
            self.acronym_checker.add_custom_acronym(123, "Not a string")

    def assert_issue_contains(self, result: DocumentCheckResult, message: str):
        """Helper method to check if result contains an issue with the given message."""
        self.assertTrue(
            any(message in issue.get('message', '') for issue in result.issues),
            f"No issue found containing message: {message}"
        )

if __name__ == '__main__':
    unittest.main()