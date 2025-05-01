import unittest
from test_base import TestBase

class TestCrossReferenceChecks(TestBase):
    """Test suite for cross-reference formatting and usage checks."""
    
    def test_cross_reference_formatting(self):
        """Test cross-reference formatting."""
        content = [
            "As mentioned above",
            "See below for details",
            "Per the preceding section"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'above' for references")
        self.assert_issue_contains(result, "Avoid using 'below' for references")
        self.assert_issue_contains(result, "Avoid using 'preceding' for references")
    
    def test_cross_reference_edge_cases(self):
        """Test edge cases in cross-references."""
        content = [
            "The former and latter sections",
            "As stated earlier in this document",
            "The aforementioned requirements"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'former'")
        self.assert_issue_contains(result, "Avoid using 'latter'")
        self.assert_issue_contains(result, "Avoid using 'earlier'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")
    
    def test_valid_cross_references(self):
        """Test valid cross-reference formats."""
        content = [
            "See section 25.1309",
            "Refer to paragraph (a)",
            "Under subsection (1)"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)
    
    def test_nested_references(self):
        """Test nested cross-references."""
        content = [
            "See section 25.1309(a)(1)",
            "Refer to paragraph (a) of section 25.1309",
            "Under subsection (1) of paragraph (a)"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)
    
    def test_ambiguous_references(self):
        """Test ambiguous cross-references."""
        content = [
            "As mentioned in the previous section",
            "See the following paragraph",
            "Per the next section"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'previous'")
        self.assert_issue_contains(result, "Avoid using 'following'")
        self.assert_issue_contains(result, "Avoid using 'next'")
    
    def test_relative_references(self):
        """Test relative position references."""
        content = [
            "The above-mentioned requirements",
            "The below-listed items",
            "The herein contained provisions"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using relative position references")
    
    def test_compound_references(self):
        """Test compound reference phrases."""
        content = [
            "As mentioned earlier in this document",
            "As stated above in this section",
            "As discussed below in this chapter"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using compound reference phrases")
    
    def test_aviation_references(self):
        """Test aviation-specific references."""
        content = [
            "See AC 25-7D",
            "Refer to FAA Order 8900.1",
            "Under TSO-C23d"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)
    
    def test_regulatory_references(self):
        """Test regulatory document references."""
        content = [
            "See 14 CFR part 25",
            "Refer to 49 U.S.C. 44701",
            "Under 14 CFR § 25.1309"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)
    
    def test_mixed_references(self):
        """Test mixed valid and invalid references."""
        content = [
            "See section 25.1309",
            "As mentioned above",
            "Refer to paragraph (a)",
            "The aforementioned requirements"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'above'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

if __name__ == '__main__':
    unittest.main() 