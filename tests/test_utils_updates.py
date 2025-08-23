import importlib

import pytest

from govdocverify.utils.decorators import profile_performance, retry_transient
from govdocverify.utils.link_utils import normalise
from govdocverify.utils.security import SecurityError, validate_source


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
