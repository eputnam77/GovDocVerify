# pytest -v tests/test_cli.py --log-cli-level=DEBUG

from unittest.mock import patch

import pytest

from documentcheckertool.cli import main, process_document
from documentcheckertool.utils.terminology_utils import TerminologyManager


class TestCLI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()

    @patch("documentcheckertool.cli.FAADocumentChecker")
    def test_process_document(self, mock_checker):
        # Mock the checker's run_all_document_checks method
        mock_result = type('MockResult', (), {
            'success': True,
            'issues': [],
            'per_check_results': {
                'test_category': {
                    'test_check': {
                        'success': True,
                        'issues': [],
                        'details': {}
                    }
                }
            }
        })()
        mock_checker.return_value.run_all_document_checks.return_value = mock_result

        result = process_document("test.docx", "ADVISORY_CIRCULAR")
        assert not result["has_errors"]
        assert "rendered" in result
        assert isinstance(result["rendered"], str)
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)

    @patch("documentcheckertool.cli.process_document")
    def test_main_success(self, mock_process):
        mock_process.return_value = {"has_errors": False, "rendered": "", "by_category": {}}

        with patch("sys.argv", ["script.py", "test.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 0

    @patch("documentcheckertool.cli.process_document")
    def test_main_error(self, mock_process):
        mock_process.return_value = {"has_errors": True, "rendered": "", "by_category": {}}

        with patch("sys.argv", ["script.py", "test.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 1

    @patch("documentcheckertool.cli.process_document")
    def test_main_invalid_args(self, mock_process):
        with patch("sys.argv", ["script.py"]):
            result = main()
            assert result == 1

    @patch("documentcheckertool.cli.process_document")
    def test_main_invalid_doc_type(self, mock_process):
        with patch("sys.argv", ["script.py", "test.docx", "INVALID_TYPE"]):
            result = main()
            assert result == 1

    @patch("documentcheckertool.cli.process_document")
    def test_main_file_not_found(self, mock_process):
        mock_process.side_effect = FileNotFoundError()

        with patch("sys.argv", ["script.py", "nonexistent.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 1

    @patch("documentcheckertool.cli.process_document")
    def test_main_permission_error(self, mock_process):
        mock_process.side_effect = PermissionError()

        with patch("sys.argv", ["script.py", "test.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 1
