# python -m pytest tests/test_gradio_ui.py -v
# pytest -v tests/test_gradio_ui.py --log-cli-level=DEBUG

import pytest
from unittest.mock import patch, MagicMock
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.document_checker import FAADocumentChecker

class MockGradioUI:
    def __init__(self):
        self.checker = None

    def process_document(self, file_path: str, doc_type: str) -> dict:
        if not self.checker:
            raise RuntimeError("Checker not initialized")
        try:
            result = self.checker.run_all_document_checks(file_path, doc_type)
            return {
                'has_errors': not result.success,
                'errors': [issue["message"] for issue in result.issues if issue["severity"] == Severity.ERROR],
                'warnings': [issue["message"] for issue in result.issues if issue["severity"] == Severity.WARNING]
            }
        except FileNotFoundError:
            raise
        except ValueError as e:
            raise

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