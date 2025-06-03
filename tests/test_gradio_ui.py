# python -m pytest tests/test_gradio_ui.py -v
# pytest -v tests/test_gradio_ui.py --log-cli-level=DEBUG

import logging
from unittest.mock import patch

import pytest

from documentcheckertool.models import (
    DocumentCheckResult,
    DocumentType,
    Severity,
    VisibilitySettings,
)
from documentcheckertool.utils.terminology_utils import TerminologyManager


class MockGradioUI:
    def __init__(self):
        import logging

        logging.basicConfig(level=logging.DEBUG)
        self.checker = None
        self.last_result = None
        self.visibility_settings = VisibilitySettings()
        self.terminology_manager = TerminologyManager()
        # If you instantiate TerminologyChecks or ReadabilityChecks here,
        # pass self.terminology_manager
        # self.terminology_checks = TerminologyChecks(self.terminology_manager)
        # self.readability_checks = ReadabilityChecks(self.terminology_manager)
        logging.debug(
            f"MockGradioUI initialized with TerminologyManager: {self.terminology_manager}"
        )

    def process_document(
        self, file_path: str, doc_type: str, visibility_settings: VisibilitySettings = None
    ) -> dict:
        if not self.checker:
            raise RuntimeError("Checker not initialized")
        try:
            result = self.checker.run_all_document_checks(file_path, doc_type)
            self.last_result = result
            self.visibility_settings = visibility_settings or self.visibility_settings

            # Filter issues based on visibility settings (for legacy, but now return by_category)
            results_dict = getattr(result, "per_check_results", None) or {
                "all": {
                    "all": {
                        "success": result.success,
                        "issues": result.issues,
                        "details": getattr(result, "details", {}),
                    }
                }
            }
            # Filter issues by visibility settings for errors and warnings
            visible_errors = []
            visible_warnings = []
            for cat, checks in results_dict.items():
                for check in checks.values():
                    for issue in check.get("issues", []):
                        category = self._get_issue_category(issue)
                        is_visible = getattr(self.visibility_settings, f"show_{category}", True)
                        sev = issue.get("severity")
                        if hasattr(sev, "name"):
                            sev = sev.name
                        if not is_visible:
                            continue
                        if sev == "ERROR":
                            visible_errors.append(issue["message"])
                        elif sev == "WARNING":
                            visible_warnings.append(issue["message"])
            return {
                "has_errors": not result.success,
                "rendered": "",  # Could use formatter if needed
                "by_category": results_dict,
                "visibility_settings": self.visibility_settings.to_dict(),
                "errors": visible_errors,
                "warnings": visible_warnings,
            }
        except FileNotFoundError:
            raise
        except ValueError:
            raise

    def _get_issue_category(self, issue: dict) -> str:
        """Determine the category of an issue based on its attributes."""
        # This is a simplified version - in reality, you'd want to map issues to categories
        # based on the checker that generated them
        if "readability" in issue.get("message", "").lower():
            return "readability"
        elif (
            "paragraph" in issue.get("message", "").lower()
            or "sentence" in issue.get("message", "").lower()
        ):
            return "paragraph_length"
        elif "terminology" in issue.get("message", "").lower():
            return "terminology"
        elif "heading" in issue.get("message", "").lower():
            return "headings"
        elif "structure" in issue.get("message", "").lower():
            return "structure"
        elif "format" in issue.get("message", "").lower():
            return "format"
        elif "accessibility" in issue.get("message", "").lower():
            return "accessibility"
        elif "watermark" in issue.get("message", "").lower():
            return "document_status"
        return "general"

    def reset(self):
        """Reset the UI state."""
        self.last_result = None
        self.visibility_settings = VisibilitySettings()


class TestGradioUI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.ui = MockGradioUI()
        import logging

        logging.debug(
            f"TestGradioUI setup: TerminologyManager: {self.terminology_manager}, "
            f"MockGradioUI: {self.ui}"
        )

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_ui_creation(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True, issues=[]
        )

        self.ui.checker = mock_checker.return_value
        assert self.ui is not None

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_success(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True, issues=[]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        assert not result["has_errors"]
        assert "rendered" in result
        assert isinstance(result["rendered"], str)
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_error(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[{"message": "Test error", "severity": Severity.ERROR, "line_number": 1}],
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        assert result["has_errors"]
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_warnings(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[{"message": "Test warning", "severity": Severity.WARNING, "line_number": 1}],
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        assert not result["has_errors"]
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_invalid_file(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.side_effect = FileNotFoundError()

        self.ui.checker = mock_checker.return_value
        with pytest.raises(FileNotFoundError):
            self.ui.process_document("nonexistent.docx", "ADVISORY_CIRCULAR")

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_invalid_type(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.side_effect = ValueError(
            "Invalid document type"
        )

        self.ui.checker = mock_checker.return_value
        with pytest.raises(ValueError):
            self.ui.process_document("test.docx", "INVALID_TYPE")

    # New tests for multiple issues
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_process_document_multiple_issues(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {"message": "Error 1", "severity": Severity.ERROR, "line_number": 1},
                {"message": "Error 2", "severity": Severity.ERROR, "line_number": 2},
                {"message": "Warning 1", "severity": Severity.WARNING, "line_number": 3},
            ],
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        assert result["has_errors"]
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)

    # New tests for checker initialization
    def test_checker_not_initialized(self):
        with pytest.raises(RuntimeError, match="Checker not initialized"):
            self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_checker_initialization_failure(self, mock_checker):
        mock_checker.side_effect = Exception("Checker initialization failed")
        with pytest.raises(Exception, match="Checker initialization failed"):
            self.ui.checker = mock_checker()

    # New tests for document type validation
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_all_valid_document_types(self, mock_checker):
        """Test that all document types are valid."""
        logging.basicConfig(level=logging.DEBUG)
        mock_checker.check_document.return_value = DocumentCheckResult(success=True, issues=[])
        for doc_type in DocumentType.values():
            result = mock_checker.check_document("test.txt", doc_type)
            logging.debug(f"Testing doc_type: {doc_type}, result: {result}, type: {type(result)}")
            assert result is not None
            assert isinstance(result, DocumentCheckResult)

    # New tests for UI state management
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_ui_state_management(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True, issues=[]
        )
        self.ui.checker = mock_checker.return_value

        # First check
        result1 = self.ui.process_document("test1.docx", "ADVISORY_CIRCULAR")
        assert self.ui.last_result is not None

        # Reset UI
        self.ui.reset()
        assert self.ui.last_result is None

        # Second check
        result2 = self.ui.process_document("test2.docx", "ADVISORY_CIRCULAR")
        assert self.ui.last_result is not None
        assert result1 == result2  # Results should be identical

    # New tests for error message formatting
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_error_message_formatting(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {
                    "message": "Error on line 5",
                    "severity": Severity.ERROR,
                    "line_number": 5,
                    "suggestion": "Fix the error",
                }
            ],
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        assert result["has_errors"]
        assert len(result["errors"]) == 1
        assert "Error on line 5" in result["errors"][0]

    # New tests for checker integration
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_checker_method_calls(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True, issues=[]
        )
        self.ui.checker = mock_checker.return_value

        # Test checker method calls
        self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")
        mock_checker.return_value.run_all_document_checks.assert_called_once_with(
            "test.docx", "ADVISORY_CIRCULAR"
        )

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_checker_configuration_changes(self, mock_checker):
        # First check with default config
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True, issues=[]
        )
        self.ui.checker = mock_checker.return_value
        result1 = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")

        # Change checker configuration
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {
                    "message": "New error after config change",
                    "severity": Severity.ERROR,
                    "line_number": 1,
                }
            ],
        )
        result2 = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")

        assert result1 != result2  # Results should be different after config change
        assert result2["has_errors"]
        assert "New error after config change" in result2["errors"][0]

    # New tests for visibility controls
    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_visibility_controls_default(self, mock_checker):
        """Test that all sections are visible by default."""
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {"message": "Readability issue", "severity": Severity.ERROR, "line_number": 1},
                {"message": "Terminology issue", "severity": Severity.WARNING, "line_number": 2},
            ],
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR")

        # Verify all sections are visible by default
        assert result["visibility_settings"]["readability"]
        assert result["visibility_settings"]["terminology"]
        assert len(result["errors"]) == 1
        assert len(result["warnings"]) == 1

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_visibility_controls_hide_section(self, mock_checker):
        """Test hiding a specific section."""
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {"message": "Readability issue", "severity": Severity.ERROR, "line_number": 1},
                {"message": "Terminology issue", "severity": Severity.WARNING, "line_number": 2},
            ],
        )

        self.ui.checker = mock_checker.return_value

        # Create visibility settings with readability hidden
        visibility_settings = VisibilitySettings(show_readability=False)
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR", visibility_settings)

        # Verify readability section is hidden
        assert not result["visibility_settings"]["readability"]
        assert result["visibility_settings"]["terminology"]
        assert len(result["errors"]) == 0  # Readability error should be hidden
        assert len(result["warnings"]) == 1  # Terminology warning should still be visible

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_visibility_controls_multiple_sections(self, mock_checker):
        """Test hiding multiple sections."""
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {"message": "Readability issue", "severity": Severity.ERROR, "line_number": 1},
                {"message": "Terminology issue", "severity": Severity.WARNING, "line_number": 2},
                {"message": "Heading issue", "severity": Severity.ERROR, "line_number": 3},
            ],
        )

        self.ui.checker = mock_checker.return_value

        # Create visibility settings with multiple sections hidden
        visibility_settings = VisibilitySettings(show_readability=False, show_terminology=False)
        result = self.ui.process_document("test.docx", "ADVISORY_CIRCULAR", visibility_settings)

        # Verify multiple sections are hidden
        assert not result["visibility_settings"]["readability"]
        assert not result["visibility_settings"]["terminology"]
        assert result["visibility_settings"]["headings"]
        assert len(result["errors"]) == 1  # Only heading error should be visible
        assert len(result["warnings"]) == 0  # Terminology warning should be hidden

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_visibility_controls_persistence(self, mock_checker):
        """Test that visibility settings persist between checks."""
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[{"message": "Readability issue", "severity": Severity.ERROR, "line_number": 1}],
        )

        self.ui.checker = mock_checker.return_value

        # First check with custom visibility settings
        visibility_settings = VisibilitySettings(show_readability=False)
        result1 = self.ui.process_document("test1.docx", "ADVISORY_CIRCULAR", visibility_settings)

        # Second check without specifying visibility settings
        result2 = self.ui.process_document("test2.docx", "ADVISORY_CIRCULAR")

        # Verify settings persisted
        assert not result1["visibility_settings"]["readability"]
        assert not result2["visibility_settings"]["readability"]
        assert len(result1["errors"]) == 0
        assert len(result2["errors"]) == 0

    @patch("documentcheckertool.document_checker.FAADocumentChecker")
    def test_visibility_controls_reset(self, mock_checker):
        """Test that visibility settings are reset properly."""
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[{"message": "Readability issue", "severity": Severity.ERROR, "line_number": 1}],
        )

        self.ui.checker = mock_checker.return_value

        # First check with custom visibility settings
        visibility_settings = VisibilitySettings(show_readability=False)
        result1 = self.ui.process_document("test1.docx", "ADVISORY_CIRCULAR", visibility_settings)

        # Reset UI
        self.ui.reset()

        # Second check after reset
        result2 = self.ui.process_document("test2.docx", "ADVISORY_CIRCULAR")

        # Verify settings were reset
        assert not result1["visibility_settings"]["readability"]
        assert result2["visibility_settings"]["readability"]  # Should be back to default
        assert len(result1["errors"]) == 0
        assert len(result2["errors"]) == 1  # Error should be visible again
