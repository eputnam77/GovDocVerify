# pytest -v tests/test_formatting.py --log-cli-level=DEBUG

# NOTE: Refactored to use FormatChecks, as formatting_checks.py does not exist.
import pytest

from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager


class TestFormattingChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.format_checks = FormatChecks(self.terminology_manager)

    def test_font_consistency(self):
        content = [
            "This is normal text.",
            "This is BOLD text.",
            "This is italic text.",
            "This is normal text again."
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert any("Inconsistent font usage" in issue['message'] for issue in result['warnings'])

    def test_spacing_consistency(self):
        content = [
            "This is a paragraph with single spacing.",
            "This is a paragraph with  double  spacing.",
            "This is a paragraph with   triple   spacing.",
            "This is a paragraph with single spacing again."
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert any("Inconsistent spacing" in issue['message'] for issue in result['warnings'])

    def test_margin_consistency(self):
        content = [
            "This is a paragraph with normal margins.",
            "    This is a paragraph with indented margins.",
            "This is a paragraph with normal margins again.",
            "        This is another paragraph with indented margins."
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert any("Inconsistent margins" in issue['message'] for issue in result['warnings'])

    def test_list_formatting(self):
        content = [
            "The following items are required:",
            "1. First item",
            "2. Second item",
            "a. Sub-item",
            "b. Another sub-item",
            "3. Third item"
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No formatting issues

    def test_table_formatting(self):
        content = [
            "Table 1. Sample Table",
            "Column 1 | Column 2 | Column 3",
            "---------|----------|----------",
            "Data 1   | Data 2   | Data 3",
            "Data 4   | Data 5   | Data 6"
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No formatting issues

    def test_heading_formatting(self):
        content = [
            "PURPOSE.",
            "This is the purpose section.",
            "BACKGROUND.",
            "This is the background section.",
            "DEFINITIONS.",
            "This is the definitions section."
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No formatting issues

    def test_reference_formatting(self):
        content = [
            "See paragraph 5.2.3 for more information.",
            "Refer to section 4.1.2 for details.",
            "As discussed in paragraph 3.4.5"
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert any("Inconsistent reference format" in issue['message'] for issue in result['warnings'])

    def test_figure_formatting(self):
        content = [
            "Figure 1. Sample Figure",
            "This is a figure caption.",
            "Figure 2. Another Sample Figure",
            "This is another figure caption."
        ]
        result = self.format_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No formatting issues
