import pytest
from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

class TestFormatChecks:
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

    def test_phone_number_format_check_valid(self):
        """Test phone number format check with valid formats."""
        content = [
            "Contact us at (202) 267-1000.",
            "For emergencies, call (800) 555-1212.",
            "The office number is (703) 123-4567."
        ]
        doc_path = self.create_test_docx(content, "valid_phone_numbers.docx")
        result = self.checker.check_phone_number_format(content)
        self.assert_no_issues(result)

    def test_phone_number_format_check_invalid(self):
        """Test phone number format check with invalid formats."""
        content = [
            "Contact us at 202-267-1000.",
            "For emergencies, call 800.555.1212.",
            "The office number is 7031234567."
        ]
        doc_path = self.create_test_docx(content, "invalid_phone_numbers.docx")
        result = self.checker.check_phone_number_format(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "phone number format")

    def test_date_format_check_valid(self):
        """Test date format check with valid formats."""
        content = [
            "The document was issued on January 1, 2023.",
            "The meeting is scheduled for December 31, 2023.",
            "The deadline is March 15, 2023."
        ]
        doc_path = self.create_test_docx(content, "valid_dates.docx")
        result = self.checker.check_date_formats(content)
        self.assert_no_issues(result)

    def test_date_format_check_invalid(self):
        """Test date format check with invalid formats."""
        content = [
            "The document was issued on 1/1/2023.",
            "The meeting is scheduled for 12-31-2023.",
            "The deadline is 03.15.2023."
        ]
        doc_path = self.create_test_docx(content, "invalid_dates.docx")
        result = self.checker.check_date_formats(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "date format")

    def test_placeholder_check_valid(self):
        """Test placeholder check with valid text."""
        content = [
            "This is a document without placeholders.",
            "This is another sentence without placeholders.",
            "This is a third sentence without placeholders."
        ]
        doc_path = self.create_test_docx(content, "valid_placeholders.docx")
        result = self.checker.check_placeholders(content)
        self.assert_no_issues(result)

    def test_placeholder_check_invalid(self):
        """Test placeholder check with invalid text."""
        content = [
            "This is a document with [PLACEHOLDER].",
            "This is another sentence with <PLACEHOLDER>.",
            "This is a third sentence with {PLACEHOLDER}."
        ]
        doc_path = self.create_test_docx(content, "invalid_placeholders.docx")
        result = self.checker.check_placeholders(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "placeholder")

    def test_phone_number_format_usage(self):
        """Test phone number format usage check."""
        content = ["Call (123) 456-7890 for support", "Contact us at 123-456-7890"]
        result = self.checker.check_phone_number_format_usage(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_phone_number_format_usage_inconsistent(self):
        """Test phone number format usage check with inconsistent formats."""
        content = ["Call (123) 456-7890 for support", "Contact us at 123.456.7890"]
        result = self.checker.check_phone_number_format_usage(content)
        self.assertFalse(result.success)
        self.assertGreater(len(result.issues), 0)

    def test_date_format_usage(self):
        """Test date format usage check."""
        content = ["The meeting is on January 1, 2023", "Deadline: 01/01/2023"]
        result = self.checker.check_date_format_usage(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_date_format_usage_inconsistent(self):
        """Test date format usage check with inconsistent formats."""
        content = ["The meeting is on January 1, 2023", "Deadline: 1/1/23"]
        result = self.checker.check_date_format_usage(content)
        self.assertFalse(result.success)
        self.assertGreater(len(result.issues), 0)

    def test_placeholder_usage(self):
        """Test placeholder usage check."""
        content = ["This is a complete sentence.", "No placeholders here."]
        result = self.checker.check_placeholder_usage(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.issues), 0)

    def test_placeholder_usage_with_placeholders(self):
        """Test placeholder usage check with placeholders."""
        content = ["This is a complete sentence.", "TBD: Add more content here."]
        result = self.checker.check_placeholder_usage(content)
        self.assertFalse(result.success)
        self.assertGreater(len(result.issues), 0)

if __name__ == '__main__':
    pytest.main()