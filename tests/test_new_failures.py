from govdocverify.models import DocumentCheckResult, Severity
from govdocverify.utils.formatting import format_results_to_text
from govdocverify.utils.link_utils import find_urls
from govdocverify.utils.security import rate_limit


def test_rate_limit_allows_sync_functions():
    @rate_limit
    def sync_func():
        return "ok"

    assert sync_func() == "ok"


def test_find_urls_strips_quotes():
    text = "See 'https://example.gov/' for details."
    urls = list(find_urls(text))
    assert urls[0][0] == "https://example.gov/"


def test_format_results_to_text_plain():
    res = DocumentCheckResult(success=False)
    res.add_issue("err", Severity.ERROR)
    data = {"x": {"check": res}}
    out = format_results_to_text(data, "AC")
    assert "<" not in out and ">" not in out
