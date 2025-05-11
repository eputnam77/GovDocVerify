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
        self.terminology_manager = TerminologyManager()
        self.format_checks = FormatChecks(self.terminology_manager)
        self.formatting_checker = FormattingChecker(self.terminology_manager)
        logger.debug("Initialized test with FormatChecks")
        logger.debug(f"Available Severity values: {[s.value for s in Severity]}")

    def test_check_date_formats(self):
        """Test date format checking."""
        content = [
            "Date: 01/01/2023",  # Incorrect format
            "Date: 2023-01-01"   # Correct format
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing date formats with content: {content}")
        self.format_checks._check_date_formats(content, result)
        logger.debug(f"Date format test result: {result}")
        assert not result.success
        assert len(result.issues) == 1
        assert result.issues[0]["message"] == "Incorrect date format. Use YYYY-MM-DD format"
        assert result.issues[0]["severity"] == "error"
        assert result.issues[0]["line_number"] == 1

    def test_check_phone_numbers(self):
        """Test phone number format checking."""
        content = [
            "Phone: (123) 456-7890",
            "Phone: 123-456-7890"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing phone numbers with content: {content}")
        self.format_checks._check_phone_numbers(content, result)
        logger.debug(f"Phone number test result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert all(issue["severity"] == "warning" for issue in result.issues)
        assert all(issue["line_number"] in [1, 2] for issue in result.issues)

    def test_check_placeholders(self):
        """Test placeholder text checking."""
        content = [
            "Lorem ipsum dolor sit amet",
            "TODO: Add content here"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing placeholders with content: {content}")
        self.format_checks._check_placeholders(content, result)
        logger.debug(f"Placeholders test result: {result}")
        assert not result.success
        assert len(result.issues) == 1
        assert result.issues[0]["message"] == "Placeholder text found"
        assert result.issues[0]["severity"] == "error"
        assert result.issues[0]["line_number"] == 2

    def test_check_dash_spacing(self):
        """Test dash spacing checking."""
        content = [
            "This is a test - with incorrect spacing",
            "This is a test-without-spaces"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing dash spacing with content: {content}")
        self.format_checks._check_dash_spacing(content, result)
        logger.debug(f"Dash spacing test result: {result}")
        assert not result.success
        assert len(result.issues) == 1
        assert "Remove spaces around dash" in result.issues[0]["message"]
        assert result.issues[0]["severity"] == "warning"
        assert result.issues[0]["line_number"] == 1

    def test_formatting_checker(self):
        """Test the formatting checker."""
        content = """
        This is a test document.
        It has some formatting issues:
        •Inconsistent bullet spacing
        •  Extra spaces
        "Mixed" quotation marks"
        """
        logger.debug(f"Testing formatting checker with content:\n{content}")
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Formatting checker test result: {result}")
        assert not result.success
        assert len(result.issues) > 0
        assert any("Extra spaces" in issue["message"] for issue in result.issues)
        assert any("quotation marks" in issue["message"] for issue in result.issues)