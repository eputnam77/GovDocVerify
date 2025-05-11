# pytest -v tests/test_headings.py --log-cli-level=DEBUG

import pytest
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

class TestHeadingChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.heading_checks = HeadingChecks(self.terminology_manager)

    def test_valid_heading_titles(self):
        content = [
            "PURPOSE.",
            "BACKGROUND.",
            "DEFINITIONS.",
            "APPLICABILITY.",
            "REQUIREMENTS."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0

    def test_invalid_heading_titles(self):
        content = [
            "INVALID HEADING.",
            "ANOTHER INVALID HEADING.",
            "YET ANOTHER INVALID HEADING."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert any("Invalid heading title" in issue['message'] for issue in result['warnings'])

    def test_heading_periods(self):
        content = [
            "PURPOSE",
            "BACKGROUND",
            "DEFINITIONS",
            "APPLICABILITY",
            "REQUIREMENTS"
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert any("Missing period" in issue['message'] for issue in result['warnings'])

    def test_heading_sequence(self):
        content = [
            "PURPOSE.",
            "BACKGROUND.",
            "DEFINITIONS.",
            "APPLICABILITY.",
            "REQUIREMENTS.",
            "PURPOSE.",  # Duplicate heading
            "BACKGROUND."  # Out of sequence
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert any("Duplicate heading" in issue['message'] for issue in result['warnings'])
        assert any("Out of sequence" in issue['message'] for issue in result['warnings'])

    def test_heading_case(self):
        content = [
            "Purpose.",
            "Background.",
            "Definitions.",
            "Applicability.",
            "Requirements."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert any("Heading should be uppercase" in issue['message'] for issue in result['warnings'])

    def test_heading_spacing(self):
        content = [
            "PURPOSE.",
            "This is some content.",
            "BACKGROUND.",
            "More content here.",
            "DEFINITIONS.",
            "Even more content."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No spacing issues

    def test_heading_with_content(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "The Federal Aviation Administration...",
            "DEFINITIONS.",
            "For the purpose of this document..."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No issues with headings and content

    def test_mixed_case_headings(self):
        content = [
            "PURPOSE.",
            "Background.",
            "DEFINITIONS.",
            "Applicability.",
            "REQUIREMENTS."
        ]
        result = self.heading_checks.check(content)
        assert not result['has_errors']
        assert any("Heading should be uppercase" in issue['message'] for issue in result['warnings'])