import importlib
import importlib.util
from pathlib import Path

import pytest


def _load_src(module: str):
    base = Path(__file__).resolve().parents[1] / "src" / module
    spec = importlib.util.spec_from_file_location(module.replace("/", "."), base)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


decorators = _load_src("govdocverify/utils/decorators.py")
profile_performance = decorators.profile_performance
retry_transient = decorators.retry_transient

link_utils = _load_src("govdocverify/utils/link_utils.py")
find_urls = link_utils.find_urls
normalise = link_utils.normalise

security = _load_src("govdocverify/utils/security.py")
SecurityError = security.SecurityError
validate_source = security.validate_source


def test_validate_source_domain() -> None:
    # Allowed .gov domain should pass
    validate_source("https://agency.gov/file.docx")

    # Lookalike domain with disallowed suffix should fail
    with pytest.raises(SecurityError):
        validate_source("https://agency.gov.com/file.docx")

    with pytest.raises(SecurityError):
        validate_source("https://agency.gov/noextension")


def test_decorators_work() -> None:
    calls = {"count": 0}

    @profile_performance
    def foo() -> str:
        return "ok"

    assert foo() == "ok"

    @retry_transient(max_attempts=2, backoff=0.01)
    def flaky() -> int:
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("boom")
        return 42

    assert flaky() == 42


def test_formatting_import() -> None:
    mod = importlib.import_module("govdocverify.utils.formatting")
    assert hasattr(mod, "ResultFormatter")


def test_normalise_handles_uppercase_scheme() -> None:
    assert normalise("HTTP://Example.GOV/Path/") == "example.gov/Path"


def test_normalise_strips_whitespace() -> None:
    assert normalise("  HTTPS://Example.GOV/Path/  ") == "example.gov/Path"


def test_normalise_strips_trailing_dot_from_hostname() -> None:
    assert normalise("HTTP://Example.GOV./Path/") == "example.gov/Path"


def test_find_urls_strips_trailing_punctuation() -> None:
    text = "See https://example.gov/test, and https://example.gov/again."
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["https://example.gov/test", "https://example.gov/again"]


def test_find_urls_handles_root_and_query_only_urls() -> None:
    text = "Links: https://example.gov/ and https://example.gov?foo=bar"
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["https://example.gov/", "https://example.gov?foo=bar"]


def test_find_urls_strips_closing_brackets() -> None:
    text = "Links: [https://example.gov/test] and (https://example.gov/again)"
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["https://example.gov/test", "https://example.gov/again"]


def test_find_urls_strips_opening_brackets() -> None:
    text = "See https://example.gov/test( for details"
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["https://example.gov/test"]


def test_find_urls_preserves_uppercase_scheme() -> None:
    text = "Visit HTTPS://Example.gov/ for info"
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["HTTPS://Example.gov/"]


def test_find_urls_handles_port_numbers() -> None:
    text = "See http://example.gov:8080/path for details"
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["http://example.gov:8080/path"]


def test_find_urls_handles_parentheses_in_url() -> None:
    text = "More info at https://example.gov/path_(test)."
    urls = [u for u, _ in find_urls(text)]
    assert urls == ["https://example.gov/path_(test)"]


def test_find_urls_handles_local_addresses() -> None:
    text = "Local http://localhost/test and http://127.0.0.1/test should both be found"
    urls = [u for u, _ in find_urls(text)]
    assert "http://localhost/test" in urls
    assert "http://127.0.0.1/test" in urls


def test_retry_transient_respects_zero_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOVDOCVERIFY_MAX_RETRIES", "5")
    calls = {"count": 0}

    @retry_transient(max_attempts=0, backoff=0)
    def boom() -> None:
        calls["count"] += 1
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom()
    assert calls["count"] == 1


@pytest.mark.parametrize(
    "url",
    [
        "https://agency.gov/file.docx?download=1",
        "https://agency.gov/file.docx#section",
    ],
)
def test_validate_source_allows_query_and_fragment(url: str) -> None:
    validate_source(url)


def test_validate_source_allows_trailing_dot_domain() -> None:
    validate_source("https://agency.gov./file.docx")


def test_normalise_preserves_port() -> None:
    assert normalise("https://Example.gov:8000/path/") == "example.gov:8000/path"


def test_normalise_strips_default_ports() -> None:
    """Default HTTP/HTTPS ports should not appear in normalised output."""
    assert normalise("http://Example.gov:80/path/") == "example.gov/path"
    assert normalise("https://Example.gov:443/path/") == "example.gov/path"
