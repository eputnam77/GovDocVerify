# pytest -v tests/test_format_checks.py --log-cli-level=DEBUG

import pytest
import logging
from documentcheckertool.checks.format_checks import FormatChecks, FormattingChecker
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.models import DocumentCheckResult, Severity

logger = logging.getLogger(__name__)

class TestFormatChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        logger.info("Setting up test fixtures")
        self.terminology_manager = TerminologyManager()
        self.format_checks = FormatChecks(self.terminology_manager)
        self.formatting_checker = FormattingChecker(self.terminology_manager)
        logger.debug("Initialized test with FormatChecks")
        logger.debug(f"Available Severity values: {[s.value for s in Severity]}")

    @pytest.mark.parametrize("content,expected_issues", [
        (
            ["Date: 01/01/2023", "Date: May 11, 2025"],
            [{"message": "Incorrect date format. Use Month Day, Year format (e.g., May 11, 2025)", "severity": Severity.ERROR, "line_number": 1}]
        ),
        (
            ["Date: 12/31/2023", "Date: December 31, 2023"],
            [{"message": "Incorrect date format. Use Month Day, Year format (e.g., May 11, 2025)", "severity": Severity.ERROR, "line_number": 1}]
        ),
        (
            ["Date: May 11, 2025", "Date: December 31, 2023"],
            []
        ),
    ])
    def test_check_date_formats(self, content, expected_issues):
        """Test date format checking with various inputs."""
        result = DocumentCheckResult()
        logger.debug(f"Testing date formats with content: {content}")
        self.format_checks._check_date_formats(content, result)
        logger.debug(f"Date format test result: {result}")
        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)
        if expected_issues:
            assert result.issues[0]["message"] == expected_issues[0]["message"]
            assert result.issues[0]["severity"] == expected_issues[0]["severity"]
            assert result.issues[0]["line_number"] == expected_issues[0]["line_number"]

    @pytest.mark.parametrize("content,expected_issues", [
        (
            ["Phone: (123) 456-7890", "Phone: 123-456-7890"],
            [
                {"message": "Inconsistent phone number format", "severity": Severity.WARNING, "line_number": 1},
                {"message": "Inconsistent phone number format", "severity": Severity.WARNING, "line_number": 2}
            ]
        ),
        (
            ["Phone: 123.456.7890", "Phone: 1234567890"],
            [
                {"message": "Inconsistent phone number format", "severity": Severity.WARNING, "line_number": 1},
                {"message": "Inconsistent phone number format", "severity": Severity.WARNING, "line_number": 2}
            ]
        ),
        (
            ["Phone: 123-456-7890", "Phone: 123-456-7890"],
            []
        ),
    ])
    def test_check_phone_numbers(self, content, expected_issues):
        """Test phone number format checking with various inputs."""
        result = DocumentCheckResult()
        logger.debug(f"Testing phone numbers with content: {content}")
        self.format_checks._check_phone_numbers(content, result)
        logger.debug(f"Phone number test result: {result}")
        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)
        if expected_issues:
            for i, issue in enumerate(expected_issues):
                assert result.issues[i]["message"] == issue["message"]
                assert result.issues[i]["severity"] == issue["severity"]
                assert result.issues[i]["line_number"] == issue["line_number"]

    @pytest.mark.parametrize("content,expected_issues", [
        (
            ["Lorem ipsum dolor sit amet", "TODO: Add content here"],
            [{"message": "Placeholder text found", "severity": Severity.ERROR, "line_number": 2}]
        ),
        (
            ["FIXME: Update this", "DRAFT: Review needed"],
            [
                {"message": "Placeholder text found", "severity": Severity.ERROR, "line_number": 1},
                {"message": "Placeholder text found", "severity": Severity.ERROR, "line_number": 2}
            ]
        ),
        (
            ["Regular content", "More content"],
            []
        ),
    ])
    def test_check_placeholders(self, content, expected_issues):
        """Test placeholder text checking with various inputs."""
        result = DocumentCheckResult()
        logger.debug(f"Testing placeholders with content: {content}")
        self.format_checks._check_placeholders(content, result)
        logger.debug(f"Placeholders test result: {result}")
        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)
        if expected_issues:
            for i, issue in enumerate(expected_issues):
                assert result.issues[i]["message"] == issue["message"]
                assert result.issues[i]["severity"] == issue["severity"]
                assert result.issues[i]["line_number"] == issue["line_number"]

    @pytest.mark.parametrize("content,expected_issues", [
        (
            ["This is a test - with incorrect spacing", "This is a test-without-spaces"],
            [{"message": "Remove spaces around dash: ' - '", "severity": Severity.WARNING, "line_number": 1}]
        ),
        (
            ["Text -no space after", "No space before- text"],
            [
                {"message": "Remove space before dash: ' -'", "severity": Severity.WARNING, "line_number": 1},
                {"message": "Remove space after dash: '- '", "severity": Severity.WARNING, "line_number": 2}
            ]
        ),
        (
            ["Text-without-spaces", "More-text-without-spaces"],
            []
        ),
    ])
    def test_check_dash_spacing(self, content, expected_issues):
        """Test dash spacing checking with various inputs."""
        result = DocumentCheckResult()
        logger.debug(f"Testing dash spacing with content: {content}")
        self.format_checks._check_dash_spacing(content, result)
        logger.debug(f"Dash spacing test result: {result}")
        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)
        if expected_issues:
            for i, issue in enumerate(expected_issues):
                assert result.issues[i]["message"] == issue["message"]
                assert result.issues[i]["severity"] == issue["severity"]
                assert result.issues[i]["line_number"] == issue["line_number"]

    def test_empty_input(self):
        """Test behavior with empty input."""
        logger.info("Testing empty input")
        content = ""
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Empty input test result: {result}")
        assert result.success
        assert len(result.issues) == 0

    def test_multiple_issues_single_line(self):
        """Test detection of multiple issues in a single line."""
        logger.info("Testing multiple issues in single line")
        content = "text..  text"  # Double period and extra spaces
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Multiple issues test result: {result}")
        assert not result.success
        assert len(result.issues) >= 2
        assert any("Double periods" in issue["message"] for issue in result.issues)
        assert any("Extra spaces" in issue["message"] for issue in result.issues)

    @pytest.mark.parametrize("content,expected_issues", [
        (
            "text..",
            [{"message": "Double periods found in line 1", "severity": Severity.WARNING, "line_number": 1}]
        ),
        (
            "text  text",
            [{"message": "Extra spaces found in line 1", "severity": Severity.WARNING, "line_number": 1}]
        ),
        (
            "(unmatched parentheses",
            [{"message": "Unmatched parentheses in line 1", "severity": Severity.WARNING, "line_number": 1}]
        ),
        (
            "§ 123",
            []
        ),
        (
            "§123",
            [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]
        ),
    ])
    def test_formatting_checker_individual_checks(self, content, expected_issues):
        """Test individual formatting checks with various inputs."""
        logger.info(f"Testing formatting checker with content: {content}")
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Formatting checker test result: {result}")
        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)
        if expected_issues:
            for i, issue in enumerate(expected_issues):
                assert result.issues[i]["message"] == issue["message"]
                assert result.issues[i]["severity"] == issue["severity"]
                assert result.issues[i]["line_number"] == issue["line_number"]

    def test_severity_levels(self):
        """Test that issues are assigned correct severity levels."""
        logger.info("Testing severity levels")
        test_cases = [
            ("TODO: Add content here", Severity.ERROR),  # Placeholder text
            ("text  text", Severity.WARNING),  # Extra spaces
            ("text..", Severity.WARNING),  # Double periods
        ]

        for content, expected_severity in test_cases:
            logger.debug(f"Testing content: {content}")
            result = self.formatting_checker.check_text(content)
            logger.debug(f"Severity test result: {result}")
            assert not result.success
            assert any(issue["severity"] == expected_severity for issue in result.issues)

    def test_long_line_handling(self):
        """Test handling of very long lines."""
        logger.info("Testing long line handling")
        long_line = "x" * 1000  # Create a very long line
        content = f"{long_line}\n{long_line}"
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Long line test result: {result}")
        # Should not crash or timeout
        assert isinstance(result, DocumentCheckResult)

    def test_special_characters(self):
        """Test handling of special characters."""
        logger.info("Testing special characters")
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        content = f"Testing {special_chars}"
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Special characters test result: {result}")
        # Should not crash or produce false positives
        assert isinstance(result, DocumentCheckResult)

    def test_mixed_formatting_issues(self):
        """Test detection of multiple different formatting issues."""
        logger.info("Testing mixed formatting issues")
        content = """
        •Inconsistent bullet spacing
        "Mixed" quotation marks"
        text..  text
        (unmatched parentheses
        §123
        """
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Mixed issues test result: {result}")
        assert not result.success
        assert len(result.issues) >= 5  # Should detect multiple issues
        # Verify different types of issues are detected
        issue_types = {issue["message"].split(" in line")[0] for issue in result.issues}
        assert len(issue_types) >= 5  # Should have at least 5 different types of issues

class TestSectionSymbolUsage:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        logger.info("Setting up test fixtures")
        self.terminology_manager = TerminologyManager()
        self.formatting_checker = FormattingChecker(self.terminology_manager)
        logger.debug("Initialized test with FormattingChecker")

    @pytest.mark.parametrize("content,expected_issues", [
        # Basic valid cases
        (["§ 123"], []),
        (["§ 123.45"], []),
        (["§ 123(a)"], []),
        (["§ 123.45(a)(1)"], []),

        # Invalid spacing cases
        (["§123"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§  123"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§\t123"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),

        # Multiple section symbols
        (["§ 123 and § 456"], []),
        (["§ 123 and §456"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),

        # Section symbols with text
        (["See § 123 for more details"], []),
        (["See §123 for more details"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),

        # Complex section references
        (["§§ 123-456"], []),
        (["§§ 123.45-456.78"], []),
        (["§§ 123(a)-456(b)"], []),

        # Edge cases
        (["§ 0"], []),  # Zero section number
        (["§ 999999"], []),  # Large section number
        (["§ 123.456.789"], []),  # Multiple decimal points
        (["§ 123(a)(1)(i)"], []),  # Deeply nested subsections

        # Invalid cases
        (["§"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§ "], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§ abc"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§ 123abc"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),

        # Multiple lines
        (["§ 123", "§ 456"], []),
        (["§ 123", "§456"], [{"message": "Incorrect section symbol usage in line 2", "severity": Severity.WARNING, "line_number": 2}]),
        (["§123", "§ 456"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),

        # Special characters and formatting
        (["§ 123-456"], []),
        (["§ 123(a)(1)(i)"], []),
        (["§ 123.45(a)(1)(i)"], []),
        (["§ 123(a)(1)(i)(A)"], []),

        # Mixed content
        (["Regular text § 123 more text"], []),
        (["Regular text §123 more text"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
        (["§ 123 and some text § 456"], []),
        (["§ 123 and some text §456"], [{"message": "Incorrect section symbol usage in line 1", "severity": Severity.WARNING, "line_number": 1}]),
    ])
    def test_section_symbol_usage(self, content, expected_issues):
        """Test section symbol usage with various inputs."""
        logger.debug(f"Testing section symbol usage with content: {content}")
        result = self.formatting_checker.check_section_symbol_usage(content)
        logger.debug(f"Section symbol test result: {result}")

        assert result.success == (len(expected_issues) == 0)
        assert len(result.issues) == len(expected_issues)

        if expected_issues:
            for i, issue in enumerate(expected_issues):
                assert result.issues[i]["message"] == issue["message"]
                assert result.issues[i]["severity"] == issue["severity"]
                assert result.issues[i]["line_number"] == issue["line_number"]

    def test_section_symbol_with_special_characters(self):
        """Test section symbol usage with special characters."""
        content = [
            "§ 123§ 456",  # Multiple section symbols without space
            "§ 123§456",   # Multiple section symbols without space and number
            "§ 123 § 456", # Multiple section symbols with space
            "§ 123 §456",  # Multiple section symbols with space and no space
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        assert not result.success
        assert len(result.issues) == 2  # Should flag the incorrect usages

    def test_section_symbol_with_unicode(self):
        """Test section symbol usage with Unicode characters."""
        content = [
            "§ 123 § 456",  # Regular section symbols
            "§ 123 § 456",  # Unicode section symbols
            "§ 123 § 456",  # Mixed section symbols
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        assert result.success
        assert len(result.issues) == 0

    def test_section_symbol_with_line_breaks(self):
        """Test section symbol usage with line breaks."""
        content = [
            "§ 123\n§ 456",  # Line break between section symbols
            "§ 123\r\n§ 456", # Windows line break
            "§ 123\r§ 456",   # Old Mac line break
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        assert result.success
        assert len(result.issues) == 0

    def test_section_symbol_with_whitespace(self):
        """Test section symbol usage with various whitespace characters."""
        content = [
            "§ 123",     # Regular space
            "§\t123",    # Tab
            "§\n123",    # Newline
            "§\r123",    # Carriage return
            "§\f123",    # Form feed
            "§\v123",    # Vertical tab
        ]
        result = self.formatting_checker.check_section_symbol_usage(content)
        assert not result.success
        assert len(result.issues) == 5  # Should flag all except regular space