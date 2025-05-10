# python -m pytest tests/test_heading_checks.py -v

import pytest
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager
from docx import Document

class TestHeadingChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.heading_checks = HeadingChecks(self.terminology_manager)

    def test_validate_input(self):
        # Test valid input
        valid_doc = ["1. PURPOSE.", "2. BACKGROUND."]
        assert self.heading_checks.validate_input(valid_doc) is True

        # Test invalid input
        invalid_doc = ["1. PURPOSE.", 123]
        assert self.heading_checks.validate_input(invalid_doc) is False

    def test_check_heading_title(self):
        doc = [
            "1. PURPOSE.",
            "2. BACKGROUND.",
            "3. DEFINITIONS."
        ]
        result = self.heading_checks.check_heading_title(doc, "ADVISORY_CIRCULAR")
        assert result.success is True
        assert len(result.issues) == 0

    def test_check_heading_period(self):
        doc = [
            "1. PURPOSE",
            "2. BACKGROUND.",
            "3. DEFINITIONS"
        ]
        result = self.heading_checks.check_heading_period(doc, "ADVISORY_CIRCULAR")
        assert result.success is False
        assert len(result.issues) > 0

    def test_check_heading_structure(self):
        doc = Document()
        doc.add_paragraph("1. PURPOSE.")
        doc.add_paragraph("2. BACKGROUND.")
        doc.add_paragraph("2.1. History.")
        doc.add_paragraph("2.2. Current Status.")
        doc.add_paragraph("3. DEFINITIONS.")

        issues = self.heading_checks.check_heading_structure(doc)
        assert len(issues) == 0

    def test_invalid_heading_structure(self):
        doc = Document()
        doc.add_paragraph("1. PURPOSE.")
        doc.add_paragraph("2. BACKGROUND.")
        doc.add_paragraph("2.1. History.")
        doc.add_paragraph("2.3. Current Status.")  # Skipped 2.2

        issues = self.heading_checks.check_heading_structure(doc)
        assert len(issues) > 0
        assert any("skipped level" in issue["message"] for issue in issues)

if __name__ == '__main__':
    pytest.main()