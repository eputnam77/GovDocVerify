# python -m pytest tests/test_gradio_ui.py -v
# pytest -v tests/test_gradio_ui.py --log-cli-level=DEBUG

import pytest
from unittest.mock import patch, MagicMock, call
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.models import DocumentCheckResult, Severity, DocumentType
from documentcheckertool.document_checker import FAADocumentChecker

class MockGradioUI:
    def __init__(self):
        self.checker = None
        self.last_result = None

    def process_document(self, file_path: str, doc_type: str) -> dict:
        if not self.checker:
            raise RuntimeError("Checker not initialized")
        try:
            result = self.checker.run_all_document_checks(file_path, doc_type)
            self.last_result = result
            return {
                'has_errors': not result.success,
                'errors': [issue["message"] for issue in result.issues if issue["severity"] == Severity.ERROR],
                'warnings': [issue["message"] for issue in result.issues if issue["severity"] == Severity.WARNING]
            }
        except FileNotFoundError:
            raise
        except ValueError as e:
            raise

    def reset(self):
        """Reset the UI state."""
        self.last_result = None

class TestGradioUI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.ui = MockGradioUI()

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_ui_creation(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[]
        )

        self.ui.checker = mock_checker.return_value
        assert self.ui is not None

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_success(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert not result['has_errors']
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_error(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[{
                "message": "Test error",
                "severity": Severity.ERROR,
                "line_number": 1
            }]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert result['has_errors']
        assert len(result['errors']) == 1
        assert result['errors'][0] == 'Test error'

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_warnings(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[{
                "message": "Test warning",
                "severity": Severity.WARNING,
                "line_number": 1
            }]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert not result['has_errors']
        assert len(result['warnings']) == 1
        assert result['warnings'][0] == 'Test warning'

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_invalid_file(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.side_effect = FileNotFoundError()

        self.ui.checker = mock_checker.return_value
        with pytest.raises(FileNotFoundError):
            self.ui.process_document('nonexistent.docx', 'ADVISORY_CIRCULAR')

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_invalid_type(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.side_effect = ValueError("Invalid document type")

        self.ui.checker = mock_checker.return_value
        with pytest.raises(ValueError):
            self.ui.process_document('test.docx', 'INVALID_TYPE')

    # New tests for multiple issues
    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_process_document_multiple_issues(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {
                    "message": "Error 1",
                    "severity": Severity.ERROR,
                    "line_number": 1
                },
                {
                    "message": "Error 2",
                    "severity": Severity.ERROR,
                    "line_number": 2
                },
                {
                    "message": "Warning 1",
                    "severity": Severity.WARNING,
                    "line_number": 3
                }
            ]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert result['has_errors']
        assert len(result['errors']) == 2
        assert len(result['warnings']) == 1
        assert "Error 1" in result['errors']
        assert "Error 2" in result['errors']
        assert "Warning 1" in result['warnings']

    # New tests for checker initialization
    def test_checker_not_initialized(self):
        with pytest.raises(RuntimeError, match="Checker not initialized"):
            self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_checker_initialization_failure(self, mock_checker):
        mock_checker.side_effect = Exception("Checker initialization failed")
        with pytest.raises(Exception, match="Checker initialization failed"):
            self.ui.checker = mock_checker()

    # New tests for document type validation
    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_all_valid_document_types(self, mock_checker):
        """Test that all document types are valid."""
        for doc_type in DocumentType.values():
            result = mock_checker.check_document("test.txt", doc_type)
            self.assertIsNotNone(result)
            self.assertIsInstance(result, DocumentCheckResult)

    # New tests for UI state management
    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_ui_state_management(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[]
        )
        self.ui.checker = mock_checker.return_value

        # First check
        result1 = self.ui.process_document('test1.docx', 'ADVISORY_CIRCULAR')
        assert self.ui.last_result is not None

        # Reset UI
        self.ui.reset()
        assert self.ui.last_result is None

        # Second check
        result2 = self.ui.process_document('test2.docx', 'ADVISORY_CIRCULAR')
        assert self.ui.last_result is not None
        assert result1 == result2  # Results should be identical

    # New tests for error message formatting
    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_error_message_formatting(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[
                {
                    "message": "Error on line 5",
                    "severity": Severity.ERROR,
                    "line_number": 5,
                    "suggestion": "Fix the error"
                }
            ]
        )

        self.ui.checker = mock_checker.return_value
        result = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert result['has_errors']
        assert len(result['errors']) == 1
        assert "Error on line 5" in result['errors'][0]

    # New tests for checker integration
    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_checker_method_calls(self, mock_checker):
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[]
        )
        self.ui.checker = mock_checker.return_value

        # Test checker method calls
        self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        mock_checker.return_value.run_all_document_checks.assert_called_once_with(
            'test.docx', 'ADVISORY_CIRCULAR'
        )

    @patch('documentcheckertool.document_checker.FAADocumentChecker')
    def test_checker_configuration_changes(self, mock_checker):
        # First check with default config
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=True,
            issues=[]
        )
        self.ui.checker = mock_checker.return_value
        result1 = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')

        # Change checker configuration
        mock_checker.return_value.run_all_document_checks.return_value = DocumentCheckResult(
            success=False,
            issues=[{
                "message": "New error after config change",
                "severity": Severity.ERROR,
                "line_number": 1
            }]
        )
        result2 = self.ui.process_document('test.docx', 'ADVISORY_CIRCULAR')

        assert result1 != result2  # Results should be different after config change
        assert result2['has_errors']
        assert "New error after config change" in result2['errors'][0]