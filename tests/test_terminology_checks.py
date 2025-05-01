import unittest
from test_base import TestBase
from checks.terminology_checks import TerminologyChecks

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

if __name__ == '__main__':
    unittest.main() 