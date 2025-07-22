from datetime import datetime
from pathlib import Path

from docx import Document

from govdocverify.utils import extract_docx_metadata


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


def test_extract_docx_metadata_created_modified(tmp_path: Path) -> None:
    """Verify `created` and `modified` metadata are extracted."""
    doc = Document()
    doc.core_properties.created = datetime(2024, 1, 1, 12, 0, 0)
    doc.core_properties.modified = datetime(2024, 1, 2, 12, 0, 0)
    file_path = tmp_path / "meta2.docx"
    doc.save(file_path)

    meta = extract_docx_metadata(str(file_path))
    assert meta["created"].startswith("2024-01-01")
    assert meta["modified"].startswith("2024-01-02")
