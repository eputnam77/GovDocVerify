from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from govdocverify.models import DocumentCheckResult
from govdocverify.utils.formatting import FormatStyle, ResultFormatter


@st.composite
def metadata_dict(draw: st.DrawFn) -> dict[str, str]:
    title = draw(st.text(min_size=1, max_size=20))
    author = draw(st.text(min_size=1, max_size=20))
    last_modified_by = draw(st.text(min_size=1, max_size=20))
    created = draw(
        st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)).map(
            lambda d: d.isoformat()
        )
    )
    modified = draw(
        st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)).map(
            lambda d: d.isoformat()
        )
    )
    return {
        "title": title,
        "author": author,
        "last_modified_by": last_modified_by,
        "created": created,
        "modified": modified,
    }


@pytest.mark.property
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(metadata=metadata_dict())
def test_format_results_with_metadata_property(metadata: dict[str, str]) -> None:
    result = DocumentCheckResult(success=True, issues=[], details=None)
    data = {"section": {"check": result}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    text = fmt.format_results(data, "AC", metadata=metadata)

    assert f"Title: {metadata['title']}" in text
    assert f"Author: {metadata['author']}" in text
    assert f"Last Modified By: {metadata['last_modified_by']}" in text
    assert f"Created: {metadata['created'].split('T')[0]}" in text
    assert f"Modified: {metadata['modified'].split('T')[0]}" in text
