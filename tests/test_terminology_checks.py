# python -m pytest tests/test_terminology_checks.py -v

import unittest
from test_base import TestBase
from documentcheckertool.checks.terminology_checks import TerminologyChecks

class TestTerminologyChecks(TestBase):
    """Test suite for terminology-related checks."""
    
    def setUp(self):
        super().setUp()
        self.terminology_checks = TerminologyChecks(self.checker.pattern_cache)
    
    def test_abbreviation_usage(self):
        """Test abbreviation usage checking."""
        content = [
            "The FAA (Federal Aviation Administration) is responsible.",
            "FAA regulations require compliance.",
            "The Federal Aviation Administration (FAA) oversees operations."
        ]
        result = self.terminology_checks.check_abbreviation_usage(content)
        # Note: This test will need to be updated once the implementation is complete
        self.assertTrue(result.success)
    
    def test_cross_reference_usage(self):
        """Test cross-reference checking."""
        content = [
            "As mentioned above",
            "See below for details",
            "Refer to section 25.1309"
        ]
        result = self.terminology_checks.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'above'")
        self.assert_issue_contains(result, "Avoid using 'below'")
    
    def test_required_language(self):
        """Test required language checking."""
        content = [
            "This document contains required language.",
            "Standard disclaimer text.",
            "Regulatory compliance statement."
        ]
        result = self.terminology_checks.check_required_language(content, "Advisory Circular")
        # Note: This test will need to be updated once the implementation is complete
        self.assertTrue(result.success)
    
    def test_invalid_references(self):
        """Test various invalid reference patterns."""
        content = [
            "The former section",
            "The latter paragraph",
            "As stated earlier",
            "The aforementioned requirements"
        ]
        result = self.terminology_checks.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'former'")
        self.assert_issue_contains(result, "Avoid using 'latter'")
        self.assert_issue_contains(result, "Avoid using 'earlier'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

    def test_additionally_usage(self):
        """Test checking for sentences beginning with 'Additionally' per DOT OGC Style Guide."""
        content = [
            "Additionally, the FAA requires compliance.",
            "The FAA requires compliance. Additionally, it must be documented.",
            "In addition, the FAA requires compliance.",  # Correct usage
            "The FAA requires compliance. In addition, it must be documented."  # Correct usage
        ]
        result = self.terminology_checks.check_abbreviation_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'Additionally'")
        self.assert_issue_contains(result, "Replace with 'In addition'")

    def test_split_infinitives(self):
        """Test checking for split infinitives."""
        content = [
            "The FAA needs to completely review the application.",
            "The applicant must to thoroughly document the process.",
            "The inspector will to carefully examine the evidence.",
            "The regulation requires to properly maintain records.",
            "The FAA needs to review the application completely.",  # Correct usage
            "The applicant must document the process thoroughly."  # Correct usage
        ]
        result = self.terminology_checks.check_split_infinitives(content)
        self.assertTrue(result.success)  # Should be True since these are style suggestions
        self.assert_issue_contains(result, "Split infinitive detected")
        self.assert_issue_contains(result, "style choice rather than a grammatical error")

    def test_multi_word_split_infinitives(self):
        """Test checking for split infinitives with multi-word phrases."""
        content = [
            "The FAA needs to more than double its efforts.",
            "The applicant must to as well as document the process.",
            "The inspector will to in addition to examine the evidence.",
            "The regulation requires to in order to maintain records.",
            "The FAA needs to double its efforts more than.",  # Correct usage
            "The applicant must document the process as well as."  # Correct usage
        ]
        result = self.terminology_checks.check_split_infinitives(content)
        self.assertTrue(result.success)  # Should be True since these are style suggestions
        self.assert_issue_contains(result, "Split infinitive detected")
        self.assert_issue_contains(result, "style choice rather than a grammatical error")

if __name__ == '__main__':
    unittest.main()