# mypy: ignore-errors
import pytest
from hypothesis import given
from hypothesis import strategies as st

from documentcheckertool import export


@pytest.mark.property
@given(
    results=st.dictionaries(keys=st.text(min_size=1, max_size=10), values=st.integers()),
    path=st.text(min_size=1, max_size=20),
)
def test_save_results_as_docx_raises(results: dict[str, int], path: str) -> None:
    with pytest.raises(NotImplementedError):
        export.save_results_as_docx(results, path)


@pytest.mark.property
@given(
    results=st.dictionaries(keys=st.text(min_size=1, max_size=10), values=st.integers()),
    path=st.text(min_size=1, max_size=20),
)
def test_save_results_as_pdf_raises(results: dict[str, int], path: str) -> None:
    with pytest.raises(NotImplementedError):
        export.save_results_as_pdf(results, path)
