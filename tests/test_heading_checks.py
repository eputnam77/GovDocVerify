# python -m pytest tests/test_heading_checks.py -v

import unittest
from test_base import TestBase
from documentcheckertool.checks.heading_checks import HeadingChecks

class TestHeadingChecks(TestBase):
    """Test suite for heading-related checks."""
    
    def setUp(self):
        super().setUp()
        self.heading_checks = HeadingChecks(self.checker.pattern_cache)
    
    def test_heading_title(self):
        """Test heading title checking."""
        content = [
            "1. Introduction",
            "2. Background",
            "3. Requirements"
        ]
        result = self.heading_checks.check_heading_title(content)
        self.assertTrue(result.success)
    
    def test_heading_period(self):
        """Test heading period checking."""
        content = [
            "1. Introduction.",
            "2. Background.",
            "3. Requirements."
        ]
        result = self.heading_checks.check_heading_period(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Heading ends with period")
    
    def test_heading_format(self):
        """Test heading format checking."""
        content = [
            "1. Introduction",
            "2. Background",
            "3. Requirements",
            "4. Implementation",
            "5. Conclusion"
        ]
        result = self.heading_checks.check_heading_title(content)
        self.assertTrue(result.success)
    
    def test_invalid_headings(self):
        """Test handling of invalid headings."""
        content = [
            "1. Introduction",
            "2. Background",
            "3. Requirements",
            "4. Implementation",
            "5. Conclusion",
            "6. References",
            "7. Appendix",
            "8. Glossary",
            "9. Index",
            "10. About"
        ]
        result = self.heading_checks.check_heading_title(content)
        self.assertTrue(result.success)

if __name__ == '__main__':
    unittest.main()