# python -m pytest tests/test_acronyms.py -v
# pytest -v tests/test_acronyms.py --log-cli-level=DEBUG

import unittest
import pytest
import logging
from documentcheckertool.checks.acronym_checks import AcronymChecker
from documentcheckertool.models import DocumentCheckResult

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        The EAP is responsible for something.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Acronym 'EAP' used without definition")

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
        # Add custom acronyms to the checker
        self.acronym_checker.add_custom_acronym("FOO", "Foo Object Oriented")
        self.acronym_checker.add_custom_acronym("BAR", "Bar Application Resource")
        # Reload the checker's configuration to recognize the new acronyms
        self.acronym_checker.reload_config()
        content = """
        The FOO system provides BAR services.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Custom acronym test issues: {result.issues}")
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

    def test_predefined_acronyms(self):
        """Test handling of predefined acronyms."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.
        The National Transportation Safety Board (NTSB) investigates accidents.

        The FAA and NASA are government agencies.
        The NTSB investigates accidents.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Predefined acronym test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_in_headings(self):
        """Test acronyms in document headings."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.
        The National Transportation Safety Board (NTSB) is a government agency.

        # FAA Regulations
        ## NASA Guidelines
        ### NTSB Requirements
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Headings test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_with_punctuation(self):
        """Test acronyms with various punctuation."""
        content = """
        The F.A.A. (Federal Aviation Administration) regulates aviation.
        The N.A.S.A. (National Aeronautics and Space Administration) explores space.
        The N.T.S.B. (National Transportation Safety Board) investigates accidents.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_in_tables(self):
        """Test acronyms in table-like structures."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.

        | Agency | Acronym |
        |--------|---------|
        | FAA | FAA |
        | NASA | NASA |
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Tables test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_in_footnotes(self):
        """Test acronyms in footnotes and references."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.

        The FAA regulates aviation safety[1].
        [1] FAA regulations.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_with_numbers(self):
        """Test acronyms that include numbers."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.

        The FAA-123 program is important.
        The NASA-456 mission is scheduled.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Numbers test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_in_different_sections(self):
        """Test acronyms across different document sections."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.

        # Introduction
        The FAA is responsible for aviation safety.

        # Background
        The FAA has been regulating aviation since 1958.

        # Current Status
        The FAA continues to ensure safety.

        # Conclusion
        The FAA's role is crucial.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_with_special_characters(self):
        """Test acronyms with special characters."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.

        The FAA's role is important.
        The NASA's mission is clear.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Special characters test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_acronyms_in_different_formats(self):
        """Test acronyms in different formatting styles."""
        # Define acronyms first
        content = """
        The Federal Aviation Administration (FAA) is a government agency.
        The National Aeronautics and Space Administration (NASA) is a government agency.
        The National Transportation Safety Board (NTSB) is a government agency.

        The *FAA* is important.
        The **NASA** is crucial.
        The `NTSB` is essential.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Different formats test issues: {result.issues}")
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def assert_issue_contains(self, result: DocumentCheckResult, message: str):
        """Helper method to check if result contains an issue with the given message."""
        self.assertTrue(
            any(message in issue.get('message', '') for issue in result.issues),
            f"No issue found containing message: {message}"
        )

if __name__ == '__main__':
    unittest.main()