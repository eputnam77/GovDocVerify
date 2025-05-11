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
        self.terminology_manager = TerminologyManager()
        self.format_checks = FormatChecks(self.terminology_manager)
        self.formatting_checker = FormattingChecker(self.terminology_manager)
        logger.debug("Initialized test with FormatChecks")

    def test_check_date_formats(self):
        content = [
            "Date: 01/01/2023",  # Incorrect format
            "Date: 2023-01-01"   # Correct format
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing date formats with content: {content}")
        self.format_checks._check_date_formats(content, result)
        logger.debug(f"Date formats test result: {result}")
        assert result.success
        assert len(result.issues) == 0  # No warnings expected yet

    def test_check_phone_numbers(self):
        content = [
            "Phone: (123) 456-7890",
            "Phone: 123-456-7890"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing phone numbers with content: {content}")
        self.format_checks._check_phone_numbers(content, result)
        logger.debug(f"Phone numbers test result: {result}")
        assert result.success
        assert len(result.issues) == 0  # No warnings expected yet

    def test_check_placeholders(self):
        content = [
            "Lorem ipsum dolor sit amet",
            "TODO: Add content here"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing placeholders with content: {content}")
        self.format_checks._check_placeholders(content, result)
        logger.debug(f"Placeholders test result: {result}")
        assert result.success
        assert len(result.issues) == 0  # No warnings expected yet

    def test_check_dash_spacing(self):
        content = [
            "This is a test - with incorrect spacing",
            "This is a test-without-spaces"
        ]
        result = DocumentCheckResult()
        logger.debug(f"Testing dash spacing with content: {content}")
        self.format_checks._check_dash_spacing(content, result)
        logger.debug(f"Dash spacing test result: {result}")
        assert result.success
        assert len(result.issues) == 0  # No warnings expected yet

    def test_formatting_checker(self):
        content = """
        This is a test document.
        It has some formatting issues:
        •Inconsistent bullet spacing
        •  Extra spaces
        "Mixed" quotation marks"
        """
        logger.debug(f"Testing formatting checker with content: {content}")
        result = self.formatting_checker.check_text(content)
        logger.debug(f"Formatting checker test result: {result}")
        assert not result.success  # Expecting issues
        assert any("Extra spaces found" in issue["message"] for issue in result.issues)
        assert any("Inconsistent quotation marks" in issue["message"] for issue in result.issues)