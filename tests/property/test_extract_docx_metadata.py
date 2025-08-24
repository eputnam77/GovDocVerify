from datetime import datetime
from pathlib import Path

import pytest
from docx import Document
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from govdocverify.utils import extract_docx_metadata

ascii_chars = st.characters(min_codepoint=32, max_codepoint=126)


@pytest.mark.property
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    title=st.text(min_size=1, max_size=20, alphabet=ascii_chars),
    author=st.text(min_size=1, max_size=20, alphabet=ascii_chars),
    last_modified_by=st.text(min_size=1, max_size=20, alphabet=ascii_chars),
    created=st.one_of(
        st.none(),
        st.datetimes(
            timezones=st.just(None),
            min_value=datetime(1900, 1, 1),
            max_value=datetime(2100, 12, 31),
        ),
    ),
    modified=st.one_of(
        st.none(),
        st.datetimes(
            timezones=st.just(None),
            min_value=datetime(1900, 1, 1),
            max_value=datetime(2100, 12, 31),
        ),
    ),
)
def test_extract_docx_metadata_property(
    tmp_path: Path,
    title: str,
    author: str,
    last_modified_by: str,
    created: datetime | None,
    modified: datetime | None,
) -> None:
    doc = Document()
    cp = doc.core_properties
    cp.title = title
    cp.author = author
    cp.last_modified_by = last_modified_by
    if created is not None:
        cp.created = created
    if modified is not None:
        cp.modified = modified
    file_path = tmp_path / "meta.docx"
    doc.save(file_path)

    meta = extract_docx_metadata(str(file_path))
    assert meta["title"] == title
    assert meta["author"] == author
    assert meta["last_modified_by"] == last_modified_by
    if created is not None:
        assert meta["created"].startswith(created.date().isoformat())
    if modified is not None:
        assert meta["modified"].startswith(modified.date().isoformat())
