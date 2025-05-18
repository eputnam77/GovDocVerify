# pytest -v tests/test_reference_checks.py --log-cli-level=DEBUG

import pytest
import logging
from documentcheckertool.checks.reference_checks import TableFigureReferenceCheck
from documentcheckertool.models import DocumentCheckResult

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestTableFigureReferenceCheck:
    @pytest.fixture(autouse=True)
    def setup(self):
        logger.debug("Setting up test fixture")
        self.checker = TableFigureReferenceCheck()

    def test_empty_content(self):
        """Test handling of empty content."""
        logger.debug("Testing empty content handling")
        result = self.checker.check_text("")
        logger.debug(f"Empty content result: {result}")
        assert not result.success
        assert len(result.issues) == 1
        assert result.issues[0]['error'] == 'Empty content'

    def test_caption_skipping(self):
        """Test that caption lines are skipped."""
        logger.debug("Testing caption line skipping")
        content = [
            "Table 1. Sample Table",
            "This is a reference to table 1.",
            "Figure 2. Sample Figure",
            "This is a reference to figure 2."
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Caption skipping result: {result}")
        assert result.success
        assert len(result.issues) == 0

    def test_sentence_start_capitalization(self):
        """Test capitalization at sentence start."""
        logger.debug("Testing sentence start capitalization")
        content = [
            "table 1 shows the data.",
            "figure 2 illustrates the process.",
            "As shown in table 1, the data is clear.",
            "The process is shown in figure 2."
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Sentence start capitalization result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert any("Table reference at sentence start should be capitalized" in i['issue'] for i in result.issues)
        assert any("Figure reference at sentence start should be capitalized" in i['issue'] for i in result.issues)

    def test_inline_lowercase(self):
        """Test lowercase within sentences."""
        logger.debug("Testing inline lowercase references")
        content = [
            "The data is shown in Table 1.",
            "The process is illustrated in Figure 2.",
            "Table 1 shows the data.",
            "Figure 2 illustrates the process."
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Inline lowercase result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert any("Table reference within sentence should be lowercase" in i['issue'] for i in result.issues)
        assert any("Figure reference within sentence should be lowercase" in i['issue'] for i in result.issues)

    def test_mixed_references(self):
        """Test mixed correct and incorrect references."""
        logger.debug("Testing mixed references")
        content = [
            "Table 1 shows the data.",
            "The data is shown in table 1.",
            "Figure 2 illustrates the process.",
            "The process is shown in figure 2."
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Mixed references result: {result}")
        assert result.success
        assert len(result.issues) == 0

    def test_reference_with_colon(self):
        """Test references after a colon (should be capitalized)."""
        logger.debug("Testing references after colon")
        content = [
            "The following data is shown: table 1",
            "The process is illustrated: figure 2"
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Colon reference result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert any("Table reference at sentence start should be capitalized" in i['issue'] for i in result.issues)
        assert any("Figure reference at sentence start should be capitalized" in i['issue'] for i in result.issues)

    def test_reference_with_semicolon(self):
        """Test references after a semicolon (should be capitalized)."""
        logger.debug("Testing references after semicolon")
        content = [
            "First point; table 1 shows the data",
            "Second point; figure 2 illustrates the process"
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Semicolon reference result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert any("Table reference at sentence start should be capitalized" in i['issue'] for i in result.issues)
        assert any("Figure reference at sentence start should be capitalized" in i['issue'] for i in result.issues)

    def test_multiple_references(self):
        """Test multiple references in one sentence."""
        logger.debug("Testing multiple references in one sentence")
        content = [
            "The data in table 1 and Table 2 shows the process.",
            "The process in Figure 1 and figure 2 is illustrated."
        ]
        logger.debug(f"Test content: {content}")
        result = self.checker.check(content, "GENERAL")
        logger.debug(f"Multiple references result: {result}")
        assert not result.success
        assert len(result.issues) == 2
        assert any("Table reference within sentence should be lowercase" in i['issue'] for i in result.issues)
        assert any("Figure reference within sentence should be lowercase" in i['issue'] for i in result.issues)