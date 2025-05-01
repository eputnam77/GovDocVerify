import unittest
from test_base import TestBase
from app import DocumentType

class TestTerminologyChecks(TestBase):
    """Test suite for terminology and style guide compliance checks."""
    
    def test_usc_formatting(self):
        """Test USC/U.S.C. formatting rules."""
        content = [
            "According to 49 USC 106(g)",
            "As per 49 U.S.C 106(g)",
            "Under 49 U.S.C. 106(g)"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "USC should be U.S.C.")
        self.assert_issue_contains(result, "U.S.C should have a final period")
    
    def test_cfr_formatting(self):
        """Test CFR formatting rules."""
        content = [
            "Under 14 C.F.R. Part 25",
            "According to 14 CFR Part 25",
            "Per 14 CFR part 25"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "C.F.R. should be CFR")
        self.assert_issue_contains(result, "CFR Part should be CFR part")
    
    def test_gendered_terms(self):
        """Test replacement of gendered terms."""
        content = [
            "The chairman will preside",
            "The flagman will signal",
            "The manpower is needed"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "chairman should be chair")
        self.assert_issue_contains(result, "flagman should be flagperson")
        self.assert_issue_contains(result, "manpower should be labor force")
    
    def test_plain_language(self):
        """Test plain language requirements."""
        content = [
            "Pursuant to the regulations",
            "In accordance with the rules",
            "In compliance with the standards"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Use simpler alternatives like 'under' or 'following'")
    
    def test_aviation_terminology(self):
        """Test aviation-specific terminology."""
        content = [
            "The flight crew will perform",
            "The cockpit is equipped with",
            "Notice to air missions is required"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "flight crew should be flightcrew")
        self.assert_issue_contains(result, "cockpit should be flight deck")
        self.assert_issue_contains(result, "notice to air missions should be notice to airmen")
    
    def test_legalese_terms(self):
        """Test replacement of legalese terms."""
        content = [
            "The aforementioned requirements",
            "The herein contained provisions",
            "The thereto attached documents"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid archaic or legalese terms")
    
    def test_qualifiers(self):
        """Test unnecessary qualifiers."""
        content = [
            "This is very important",
            "The system is extremely reliable",
            "The process is quite efficient"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid unnecessary qualifiers")
    
    def test_plural_usage(self):
        """Test singular/plural consistency."""
        content = [
            "The data are available",
            "The criteria is met",
            "The phenomena is observed"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Ensure consistent singular/plural usage")
    
    def test_document_type_specific_terms(self):
        """Test document type specific terminology."""
        content = [
            "This is an Advisory Circular",
            "This is a Policy Statement",
            "This is a Special Condition"
        ]
        result = self.checker.check_terminology(content)
        self.assertTrue(result.success)  # These should be valid
    
    def test_authority_citations(self):
        """Test authority citation formatting."""
        content = [
            "Authority: 49 U.S.C. 106(g)",
            "Authority: 49 U.S.C. 106(f), 40113, 44701, 44702, and 44704"
        ]
        result = self.checker.check_terminology(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "49 U.S.C. 106(g) should not be included")

if __name__ == '__main__':
    unittest.main() 