# Run test: pytest -v

import unittest
from pathlib import Path
from tests.test_base import TestBase
from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.models import DocumentCheckResult

class TestAccessibilityChecks(TestBase):
    """Test cases for accessibility checking functionality."""
    
    def setUp(self):
        super().setUp()
        self.accessibility_checks = AccessibilityChecks(self.checker.pattern_cache)
    
    def test_readability(self):
        """Test readability checking."""
        content = [
            "Short sentence.",
            "This is a very long sentence that exceeds the recommended word count limit and "
            "should be broken down into multiple shorter sentences for better readability.",
            "Another short sentence with a total word count of exactly twenty-five words here."
        ]
        result = self.accessibility_checks.check_readability(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Sentence too long")
        self.assert_issue_contains(result, "Word count exceeds")

    def test_section_508_compliance(self):
        """Test Section 508 compliance checking."""
        content = [
            "Document with proper structure.",
            "Content with appropriate formatting.",
            "Accessible document elements."
        ]
        result = self.accessibility_checks.check_section_508_compliance(content)
        self.assertTrue(result.success)
    
    def test_complex_sentences(self):
        """Test handling of complex sentences."""
        content = [
            "The Federal Aviation Administration (FAA), which is responsible for overseeing "
            "civil aviation in the United States, including the regulation and oversight of "
            "aircraft operations, air traffic control, and the certification of personnel "
            "and aircraft, plays a crucial role in ensuring the safety and efficiency of "
            "the national airspace system."
        ]
        result = self.accessibility_checks.check_readability(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Sentence too long")

    def test_heading_structure(self):
        """Test heading structure checking."""
        content = """
        # Main Heading
        ## Subheading
        ### Skip level heading
        # Another Main
        #### Too deep
        """
        result = self.accessibility_checks.check_heading_structure(content.split('\n'))
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Inconsistent heading structure")

    def test_image_alt_text(self):
        """Test checking for image alt text."""
        content = """
        ![Descriptive alt text](image.png "Image title")
        ![Another image](photo.jpg "Photo description")
        """
        result = self.accessibility_checks.check_image_accessibility(content.split('\n'))
        self.assertTrue(result.success)
        
    def test_missing_alt_text(self):
        """Test detection of missing alt text."""
        content = """
        ![](image.png)
        """
        file_path = self.create_test_file(content, "test_accessibility.md")
        checker = AccessibilityChecks(pattern_cache=self.checker.pattern_cache)
        result = checker.check_document(file_path)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Missing alt text")

    def test_color_contrast(self):
        """Test color contrast checking."""
        content = """
        <span style="color: #777777">Low contrast text</span>
        <div style="background-color: #FFFF00; color: #FFFFFF">Poor contrast background</div>
        """
        results = DocumentCheckResult()
        self.accessibility_checks._check_color_contrast(content.split('\n'), results)
        self.assertFalse(results.success)
        self.assert_issue_contains(results, "Insufficient color contrast")

if __name__ == '__main__':
    unittest.main()