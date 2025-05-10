# python -m pytest tests/test_acronyms.py -v

import pytest
from pathlib import Path
from documentcheckertool.checks.acronym_checks import AcronymChecker
from tests.test_base import TestBase
from documentcheckertool.models import DocumentCheckResult

class TestAcronyms(TestBase):
    """Test cases for acronym checking functionality."""

    def setUp(self):
        super().setUp()
        self.acronym_checker = AcronymChecker()

    def test_valid_acronym_definition(self):
        """Test that valid acronym definitions pass."""
        content = """
        The Federal Aviation Administration (FAA) is responsible for aviation safety.
        """
        result = self.acronym_checker.check_text(content)
        self.assert_no_issues(result)

    def test_missing_acronym_definition(self):
        """Test that missing acronym definitions are caught."""
        content = """
        The FAA is responsible for aviation safety.
        """
        result = self.acronym_checker.check_text(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Acronym 'FAA' used without definition")

    def test_multiple_acronym_definitions(self):
        """Test that multiple acronym definitions are caught."""
        content = """
        The FAA (Federal Aviation Administration) is responsible for aviation safety.
        The FAA (Federal Aviation Administration) regulates air traffic.
        """
        result = self.acronym_checker.check_text(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Acronym 'FAA' defined multiple times")

    def test_custom_acronym_list(self):
        """Test checking against custom acronym list."""
        self.acronym_checker.load_custom_acronyms({
            "API": "Application Programming Interface",
            "REST": "Representational State Transfer"
        })
        content = """
        The API follows REST principles.
        """
        result = self.acronym_checker.check_text(content)
        self.assert_no_issues(result)

    def test_case_sensitive_acronyms(self):
        """Test case sensitivity in acronym checking."""
        content = """
        The Federal Aviation Administration (FAA) oversees aviation.
        Later in the document: The faa continues its work.
        """
        result = self.acronym_checker.check_text(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Incorrect case used for acronym 'faa'")

    def test_acronym_dictionary_validation(self):
        """Test validation of acronym dictionary format."""
        with pytest.raises(ValueError):
            self.acronym_checker.load_custom_acronyms({
                "BAD": None,  # Invalid definition
                123: "Not a string"  # Invalid acronym type
            })

if __name__ == '__main__':
    pytest.main()