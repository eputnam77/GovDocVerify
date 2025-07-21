from documentcheckertool import export


def test_save_results_as_docx(tmp_path) -> None:
    output = tmp_path / "out.docx"
    export.save_results_as_docx({}, str(output))
    assert output.exists()


def test_save_results_as_pdf(tmp_path) -> None:
    output = tmp_path / "out.pdf"
    export.save_results_as_pdf({}, str(output))
    assert output.exists()
