# python -m pytest tests/test_heading_checks.py -v

import unittest
from test_base import TestBase
from documentcheckertool.checks.heading_checks import HeadingChecker

class TestHeadingChecks(TestBase):
    """Test suite for heading-related checks."""
    
    def setUp(self):
        super().setUp()
        self.heading_checker = HeadingChecker()

    def test_heading_hierarchy(self):
        """Test heading hierarchy checking."""
        content = [
            "# Main Heading",
            "## Subheading 1",
            "### Section 1.1",
            "## Subheading 2",
            "#### Invalid Skip Level"  # Should trigger warning
        ]
        result = self.heading_checker.check_hierarchy(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Heading level skipped")

    def test_custom_heading_format(self):
        """Test custom heading format checking."""
        self.heading_checker.set_heading_format(r"^\d+\.\d*\s+[A-Z]")
        content = [
            "1. INTRODUCTION",
            "1.1 BACKGROUND",
            "1.2 SCOPE",
            "2. REQUIREMENTS"
        ]
        result = self.heading_checker.check_format(content)
        self.assert_no_issues(result)

    def test_heading_consistency(self):
        """Test heading format consistency."""
        content = [
            "1. Introduction",
            "2) Background",  # Inconsistent format
            "3. Requirements"
        ]
        result = self.heading_checker.check_format(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Inconsistent heading format")

    def test_duplicate_headings(self):
        """Test duplicate heading detection."""
        content = [
            "# Introduction",
            "## Overview",
            "## Overview"  # Duplicate
        ]
        result = self.heading_checker.check_duplicates(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Duplicate heading")

if __name__ == '__main__':
    unittest.main()