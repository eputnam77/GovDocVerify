from pathlib import Path

from docx import Document

from documentcheckertool.utils import extract_docx_metadata


def test_extract_docx_metadata(tmp_path: Path) -> None:
    doc = Document()
    doc.core_properties.title = "My Title"
    doc.core_properties.author = "Alice"
    doc.core_properties.last_modified_by = "Bob"
    file_path = tmp_path / "meta.docx"
    doc.save(file_path)

    meta = extract_docx_metadata(str(file_path))
    assert meta["title"] == "My Title"
    assert meta["author"] == "Alice"
    assert meta["last_modified_by"] == "Bob"
