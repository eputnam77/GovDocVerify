# python -m pytest tests/test_acronyms.py -v
# pytest -v tests/test_acronyms.py --log-cli-level=DEBUG

import logging
import unittest

import pytest

from govdocverify.checks.acronym_checks import AcronymChecker
from govdocverify.models import DocumentCheckResult
from govdocverify.utils.terminology_utils import TerminologyManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAcronyms(unittest.TestCase):
    """Test cases for acronym checking functionality."""

    def setUp(self):
        """Set up test cases."""
        self.acronym_checker = AcronymChecker()
        self.terminology_manager = TerminologyManager()
        logger.info("Initialized test fixtures")

    def test_valid_acronym_definition(self):
        """Test that valid acronym definitions pass when used."""
        content = """
        The Federal Aviation Administration (FAA) is responsible for aviation safety.
        The FAA regulates aviation.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)
        logger.debug("Valid acronym definition test passed")

    def test_missing_acronym_definition(self):
        """Test that missing acronym definitions are caught."""
        content = """
        The EAP is responsible for something.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Confirm 'EAP' was defined at its first use")
        logger.debug("Missing acronym definition test passed")

    def test_unused_acronym_definition(self):
        """Test that unused acronym definitions are caught."""
        content = """
        The Environmental Protection Agency (EPA) is a federal agency.
        The Department of Transportation (DOT) oversees transportation safety.
        The FAA regulates aviation.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success, "Should detect unused acronyms")
        # Both EPA and DOT should be reported as unused
        self.assert_issue_contains(result, "Acronym 'EPA' is defined but never used")
        self.assert_issue_contains(result, "Acronym 'DOT' is defined but never used")
        logger.debug("Unused acronym definition test passed")

    def test_multiple_acronym_definitions(self):
        """Test that multiple acronym definitions are caught."""
        content = """
        The National Aeronautics and Space Administration (NASA) is responsible for space
        exploration.
        The National Aeronautics and Space Agency (NASA) regulates space activities.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Acronym 'NASA' defined with non-standard definition")
        logger.debug("Multiple acronym definitions test passed")

    def test_multiple_unused_acronyms(self):
        """Test detection of multiple unused acronyms."""
        content = """
        The Federal Aviation Administration (FAA) regulates aviation.
        The Environmental Protection Agency (EPA) protects the environment.
        The Department of Transportation (DOT) oversees transportation.
        The FAA issues regulations.
        """
        result = self.acronym_checker.check_text(content)
        self.assertFalse(result.success, "Should detect unused acronyms")
        issues = [issue for issue in result.issues if issue["type"] == "acronym_usage"]
        # Both EPA and DOT should be reported as unused
        self.assertEqual(len(issues), 2, "Should detect both EPA and DOT as unused")
        self.assertTrue(
            any("EPA" in issue["message"] for issue in issues), "Should detect EPA as unused"
        )
        self.assertTrue(
            any("DOT" in issue["message"] for issue in issues), "Should detect DOT as unused"
        )
        logger.debug("Multiple unused acronyms test passed")

    def test_used_acronym_not_reported(self):
        """Test that used acronyms are not reported as unused."""
        content = """
        The Federal Aviation Administration (FAA) regulates aviation.
        The FAA issues regulations.
        """
        result = self.acronym_checker.check_text(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)
        logger.debug("Used acronym not reported test passed")

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
        logger.debug("Custom acronym list test passed")

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
            self.assertNotIn("faa", issue.get("message", ""))
        logger.debug("Case sensitivity test passed")

    def test_acronym_dictionary_validation(self):
        """Test validation of acronym dictionary format."""
        with pytest.raises(ValueError):
            self.acronym_checker.add_custom_acronym(None, "Invalid definition")
        with pytest.raises(ValueError):
            self.acronym_checker.add_custom_acronym(123, "Not a string")
        logger.debug("Dictionary validation test passed")

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
        logger.debug("Predefined acronyms test passed")

    def test_acronyms_in_headings(self):
        """Test acronyms in document headings."""
        content = """
        PURPOSE
        This document contains FAA requirements.
        """
        result = self.acronym_checker.check_text(content)
        logger.debug(f"Headings test issues: {result.issues}")
        self.assertTrue(result.success)  # Headings are now ignored
        self.assertEqual(len(result.issues), 0)
        logger.debug("Headings test passed")

    def test_ignored_patterns(self):
        """Test that ignored patterns are not flagged."""
        test_cases = [
            "See FAA-2023-1234 for details.",
            "Refer to 12-34-56-SC for more information.",
            "Check AC 25.1309-1A for guidance.",
            "Review AD 2023-12-34 for requirements.",
            "See 12-ABC for details.",
            "Check XYZ-123 for information.",
            "Refer to § 25.1309 for requirements.",
            "See Part 25 for details.",
        ]
        for text in test_cases:
            result = self.acronym_checker.check_text(text)
            self.assertTrue(result.success)
            self.assertEqual(len(result.issues), 0)
        logger.debug("Ignored patterns test passed")

    def test_length_limit(self):
        """Test that acronyms longer than 10 characters are ignored."""
        text = "The Very Long Acronym (VERYLONGACRONYM) is used."
        logger.debug(f"Testing length limit with text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit test issues: {result.issues}")
        # VERYLONGACRONYM should be ignored due to length > 10
        self.assertTrue(result.success, "Long acronyms should be ignored")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit test passed")

    def test_length_limit_with_usage(self):
        """Test that acronyms longer than 10 characters are ignored even when used."""
        text = """
        The Very Long Acronym (VLACRONYM) is used.
        The VLACRONYM is important.
        """
        logger.debug(f"Testing length limit with usage text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit with usage test issues: {result.issues}")
        # VLACRONYM should be ignored due to length > 10
        self.assertTrue(result.success, "Long acronyms should be ignored even when used")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit with usage test passed")

    def test_length_limit_with_multiple(self):
        """Test that multiple acronyms longer than 10 characters are ignored."""
        text = """
        The Very Long Acronym (VERYLONGACRONYM) is used.
        The Extremely Long Acronym (EXTREMELONGACRONYM) is also used.
        The FAA regulates aviation.
        """
        logger.debug(f"Testing length limit with multiple text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit with multiple test issues: {result.issues}")
        # Both VERYLONGACRONYM and EXTREMELONGACRONYM should be ignored due to length > 10
        # FAA should be processed normally
        self.assertTrue(result.success, "Multiple long acronyms should be ignored")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit with multiple test passed")

    def test_length_limit_edge_case(self):
        """Test that acronyms exactly 10 characters are not ignored."""
        text = """
        The Ten Letter Acronym (TENLETTERS) is used.
        The TENLETTERS is important.
        """
        logger.debug(f"Testing length limit edge case text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit edge case test issues: {result.issues}")
        # TENLETTERS should not be ignored as it's exactly 10 characters
        self.assertTrue(result.success, "10-character acronyms should not be ignored")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit edge case test passed")

    def test_length_limit_mixed(self):
        """Test mixing long and short acronyms."""
        text = """
        The Very Long Acronym (VLACRONYM) is used.
        The FAA regulates aviation.
        The VLACRONYM is important.
        """
        logger.debug(f"Testing length limit mixed text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit mixed test issues: {result.issues}")
        # VLACRONYM should be ignored due to length > 10
        # FAA should be processed normally
        self.assertTrue(result.success, "Mixed length acronyms should be handled correctly")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit mixed test passed")

    def test_length_limit_with_definition(self):
        """Test that long acronyms are ignored even when defined."""
        text = """
        The Very Long Acronym (VLACRONYM) is used.
        The VLACRONYM is important.
        The FAA regulates aviation.
        """
        logger.debug(f"Testing length limit with definition text: {text}")
        result = self.acronym_checker.check_text(text)
        logger.debug(f"Length limit with definition test issues: {result.issues}")
        # VLACRONYM should be ignored due to length > 10
        # FAA should be processed normally
        self.assertTrue(result.success, "Long acronyms should be ignored even when defined")
        self.assertEqual(len(result.issues), 0, "No issues should be found")
        logger.debug("Length limit with definition test passed")

    def test_non_alphabetic(self):
        """Test that non-alphabetic acronyms are ignored."""
        text = "The A1B2 is used."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)
        logger.debug("Non-alphabetic test passed")

    def test_valid_words(self):
        """Test that valid words are not flagged as acronyms."""
        text = "The API and REST are used."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)
        logger.debug("Valid words test passed")

    def test_standard_ac_definition(self):
        """Ensure AC defined with the standard term is accepted."""
        text = "The advisory circular (AC) provides guidance. The AC applies."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_standard_tso_definition(self):
        """Ensure TSO defined with the standard term is accepted."""
        text = (
            "The Technical Standard Order (TSO) provides requirements. "
            "Compliance with the TSO is required."
        )
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_dc_location_not_acronym(self):
        """Ensure location references like Washington, DC are ignored."""
        text = "The meeting will be held in Washington, DC next week."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_ignore_usc_without_periods(self):
        """Ensure USC without periods is not treated as an acronym."""
        text = "According to 49 USC 106(g), actions are authorized."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_all_caps_word_not_acronym(self):
        """Ensure uppercase words in valid_words are ignored."""
        text = "The process is GOOD and meets standards."
        result = self.acronym_checker.check_text(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_complex_document(self):
        """Test a complex document with multiple acronyms and edge cases."""
        text = """
        PURPOSE
        This document contains requirements.

        The Federal Aviation Administration (FAA) is an agency.
        The FAA regulates aviation.
        See FAA-2023-1234 for details.
        The API and REST are used.
        The Very Long Acronym (VLACRONYM) is used.
        The A1B2 is used.
        """
        result = self.acronym_checker.check_text(text)
        # VLACRONYM is defined but never used and should be reported
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Acronym 'VLACRONYM' is defined but never used")
        logger.debug("Complex document test passed")

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
        logger.debug("Punctuation test passed")

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
        logger.debug("Tables test passed")

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
        logger.debug("Footnotes test passed")

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
        logger.debug("Numbers test passed")

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
        logger.debug("Different sections test passed")

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
        logger.debug("Special characters test passed")

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
        logger.debug("Different formats test passed")

    def test_sample_acronym_findings(self):
        """Ensure acronyms are flagged when not defined at first use."""

        text = """
        SC requirements apply.
        EPA oversees regulations.
        EASA issues guidance.
        EO mandates action.
        SE documents exist.
        USC provides authority.
        DRS handles data.
        DOD policies apply.
        PS references documents.
        AMACC procedures follow.
        NASA explores space.
        ISO sets standards.
        EMI occurs frequently.
        HIRF affects equipment.

        The National Transportation Safety Board (NTSB) investigates.
        """
        result = self.acronym_checker.check_text(text)

        self.assertFalse(result.success)

        expected_missing = [
            "EPA",
            "EO",
            "SE",
            "DRS",
            "DOD",
            "PS",
            "AMACC",
            "HIRF",
        ]
        for acro in expected_missing:
            self.assert_issue_contains(result, f"Confirm '{acro}' was defined at its first use")

        self.assert_issue_contains(result, "Acronym 'NTSB' is defined but never used")

    def assert_issue_contains(self, result: DocumentCheckResult, message: str):
        """Helper method to check if result contains an issue with the given message."""
        self.assertTrue(
            any(message in issue.get("message", "") for issue in result.issues),
            f"No issue found containing message: {message}",
        )


if __name__ == "__main__":
    unittest.main()
