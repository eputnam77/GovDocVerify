# mypy: ignore-errors
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from documentcheckertool import export


@pytest.mark.property
@given(
    results=st.dictionaries(keys=st.text(min_size=1, max_size=10), values=st.integers()),
    file_name=st.text(
        min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_save_results_as_docx_property(
    tmp_path: Path, results: dict[str, int], file_name: str
) -> None:
    path = tmp_path / f"{file_name}.docx"
    export.save_results_as_docx(results, str(path))
    assert path.exists()


@pytest.mark.property
@given(
    results=st.dictionaries(keys=st.text(min_size=1, max_size=10), values=st.integers()),
    file_name=st.text(
        min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)
    ),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_save_results_as_pdf_property(
    tmp_path: Path, results: dict[str, int], file_name: str
) -> None:
    path = tmp_path / f"{file_name}.pdf"
    export.save_results_as_pdf(results, str(path))
    assert path.exists()
