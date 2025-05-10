# NOTE: Refactored to use ReadabilityChecks and TerminologyChecks, as content_checks.py does not exist.
import pytest
from documentcheckertool.checks.readability_checks import ReadabilityChecks
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

# Mock or stub for testing purposes
READABILITY_CONFIG = {
    'max_sentence_length': 20,
    'max_paragraph_length': 100
}

class TestContentChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.readability_checks = ReadabilityChecks(self.terminology_manager)
        self.terminology_checks = TerminologyChecks(self.terminology_manager)

    def test_plain_language(self):
        content = "Pursuant to the regulations, the following requirements are established."
        result = self.terminology_checks.check(content)
        assert any("Use simpler alternatives" in issue['message'] for issue in result['warnings'])

    def test_active_voice(self):
        content = "The requirements are established by this document."
        result = self.readability_checks.check(content)
        assert any("active voice" in issue['message'] for issue in result['warnings'])

    def test_clear_definitions(self):
        content = "Aircraft means a device that is used or intended to be used for flight."
        result = self.terminology_checks.check(content)
        assert len(result['warnings']) == 0

    def test_consistent_terminology(self):
        content = "The aircraft must be maintained. The airplane shall be inspected."
        result = self.terminology_checks.check(content)
        assert any("Inconsistent terminology" in issue['message'] for issue in result['warnings'])

    def test_clear_requirements(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "REQUIREMENTS.",
            "The operator should maintain records.",
            "The operator may conduct inspections.",
            "The operator might need to submit reports."
        ]
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Use clear requirement language" in issue['message'] for issue in result['warnings'])

    def test_proper_citations(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As per 14 CFR Part 25",
            "According to 49 USC 106(g)",
            "Under 14 CFR part 121"
        ]
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Incorrect citation format" in issue['message'] for issue in result['warnings'])

    def test_clear_procedures(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "PROCEDURES.",
            "The operator shall do the following:",
            "1. First step",
            "2. Second step",
            "3. Third step"
        ]
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No issues with procedures
