# pytest -v tests/test_cli.py --log-cli-level=DEBUG

from pathlib import Path
from unittest.mock import patch

import pytest

from govdocverify.cli import main, process_document
from govdocverify.utils.security import SecurityError
from govdocverify.utils.terminology_utils import TerminologyManager


class TestCLI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()

    @patch("govdocverify.processing.FAADocumentChecker")
    def test_process_document(self, mock_checker):
        # Mock the checker's run_all_document_checks method
        mock_result = type(
            "MockResult",
            (),
            {
                "success": True,
                "issues": [],
                "partial_failures": [],
                "per_check_results": {
                    "test_category": {"test_check": {"success": True, "issues": [], "details": {}}}
                },
            },
        )()
        mock_checker.return_value.run_all_document_checks.return_value = mock_result

        result = process_document("test.docx", "ADVISORY_CIRCULAR")
        assert not result["has_errors"]
        assert "rendered" in result
        assert isinstance(result["rendered"], str)
        assert "by_category" in result
        assert isinstance(result["by_category"], dict)
        assert "metadata" in result

    @patch("govdocverify.cli.process_document")
    def test_main_success(self, mock_process):
        mock_process.return_value = {"has_errors": False, "rendered": "", "by_category": {}}

        with patch("sys.argv", ["script.py", "test.docx", "Advisory Circular"]):
            result = main()
            assert result == 0

    @patch("govdocverify.cli.process_document")
    def test_main_error(self, mock_process):
        mock_process.return_value = {"has_errors": True, "rendered": "", "by_category": {}}

        with patch("sys.argv", ["script.py", "test.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 1

    @patch("govdocverify.cli.process_document")
    def test_main_invalid_args(self, mock_process):
        with patch("sys.argv", ["script.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    @patch("govdocverify.cli.process_document")
    def test_main_invalid_doc_type(self, mock_process):
        with patch("sys.argv", ["script.py", "test.docx", "INVALID_TYPE"]):
            result = main()
            assert result == 1

    @patch("govdocverify.cli.process_document")
    def test_main_file_not_found(self, mock_process):
        mock_process.side_effect = FileNotFoundError()

        with patch("sys.argv", ["script.py", "nonexistent.docx", "ADVISORY_CIRCULAR"]):
            result = main()
            assert result == 1

    @patch("govdocverify.cli.process_document")
    def test_main_permission_error(self, mock_process):
        mock_process.side_effect = PermissionError()

        with patch("sys.argv", ["script.py", "test.docx", "ADVISORY_CIRCULAR"]):
            result = main()
        assert result == 1

    @patch("govdocverify.cli.process_document")
    def test_main_unsupported_extension(self, mock_process):
        """CL-01: unsupported file types exit with an error."""
        mock_process.side_effect = SecurityError("Invalid file type")

        with patch("sys.argv", ["script.py", "file.pdf", "ORDER"]):
            result = main()
        assert result == 1

    @patch("govdocverify.cli.process_document")
    def test_main_exit_codes_reflect_error_severity(self, mock_process):
        """CL-02: exit code is non-zero when high-severity issues exist."""
        mock_process.return_value = {
            "has_errors": True,
            "rendered": "",
            "by_category": {},
        }
        with patch(
            "sys.argv",
            ["script.py", "--file", "test.docx", "--type", "ORDER"],
        ):
            assert main() == 1

        mock_process.return_value = {
            "has_errors": False,
            "rendered": "",
            "by_category": {},
        }
        with patch(
            "sys.argv",
            ["script.py", "--file", "test.docx", "--type", "ORDER"],
        ):
            assert main() == 0

    @patch("govdocverify.cli.process_document")
    def test_batch_mode_processes_multiple_files(self, mock_process, tmp_path):
        """CL-03: batch glob processing preserves order and continues on errors."""
        file1 = tmp_path / "a.docx"
        file2 = tmp_path / "b.docx"
        file1.write_text("doc1")
        file2.write_text("doc2")

        mock_process.side_effect = [
            {"has_errors": False, "rendered": "", "by_category": {}},
            RuntimeError("boom"),
        ]
        with patch(
            "sys.argv",
            ["script.py", "--file", str(tmp_path / "*.docx"), "--type", "ORDER"],
        ):
            assert main() == 1
        processed = [c.args[0] for c in mock_process.call_args_list]
        assert processed == [str(file1), str(file2)]

    @patch("govdocverify.cli.process_document")
    @pytest.mark.parametrize("fmt", ["html", "docx", "pdf"])
    def test_report_formats_are_generated(self, mock_process, tmp_path, fmt):
        """CL-04: --out html/docx/pdf each produces a readable artifact."""
        mock_process.return_value = {
            "has_errors": False,
            "rendered": "content",
            "by_category": {},
        }
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with (
            patch("govdocverify.export.save_results_as_docx") as save_docx,
            patch("govdocverify.export.save_results_as_pdf") as save_pdf,
        ):
            save_docx.side_effect = lambda _r, p: Path(p).write_text("docx")
            save_pdf.side_effect = lambda _r, p: Path(p).write_text("pdf")
            with patch(
                "sys.argv",
                [
                    "script.py",
                    "--file",
                    "test.docx",
                    "--type",
                    "ORDER",
                    "--out",
                    fmt,
                    "--output-dir",
                    str(out_dir),
                ],
            ):
                assert main() == 0
        output_file = out_dir / f"test.{fmt}"
        assert output_file.exists()
        assert output_file.stat().st_size > 0
