# python -m pytest tests/test_gradio_ui.py -v

import pytest
from unittest.mock import patch, MagicMock
from documentcheckertool.utils.terminology_utils import TerminologyManager

class TestGradioUI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_ui_creation(self, mock_checker):
        mock_checker.return_value.check.return_value = {
            'has_errors': False,
            'errors': [],
            'warnings': []
        }

        ui = create_ui()
        assert ui is not None

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_process_document_success(self, mock_checker):
        mock_checker.return_value.check.return_value = {
            'has_errors': False,
            'errors': [],
            'warnings': []
        }

        ui = create_ui()
        result = ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert not result['has_errors']
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_process_document_error(self, mock_checker):
        mock_checker.return_value.check.return_value = {
            'has_errors': True,
            'errors': ['Test error'],
            'warnings': []
        }

        ui = create_ui()
        result = ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert result['has_errors']
        assert len(result['errors']) == 1
        assert result['errors'][0] == 'Test error'

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_process_document_warnings(self, mock_checker):
        mock_checker.return_value.check.return_value = {
            'has_errors': False,
            'errors': [],
            'warnings': ['Test warning']
        }

        ui = create_ui()
        result = ui.process_document('test.docx', 'ADVISORY_CIRCULAR')
        assert not result['has_errors']
        assert len(result['warnings']) == 1
        assert result['warnings'][0] == 'Test warning'

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_process_document_invalid_file(self, mock_checker):
        mock_checker.return_value.check.side_effect = FileNotFoundError()

        ui = create_ui()
        with pytest.raises(FileNotFoundError):
            ui.process_document('nonexistent.docx', 'ADVISORY_CIRCULAR')

    @patch('documentcheckertool.ui.gradio_ui.DocumentChecker')
    def test_process_document_invalid_type(self, mock_checker):
        mock_checker.return_value.check.side_effect = ValueError("Invalid document type")

        ui = create_ui()
        with pytest.raises(ValueError):
            ui.process_document('test.docx', 'INVALID_TYPE')

# Mock or stub for testing purposes
def create_ui():
    return "Mocked create_ui result"