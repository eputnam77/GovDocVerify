import logging
import time

import pytest

from govdocverify.utils.decorators import profile_performance, retry_transient


def test_profile_performance(caplog):
    @profile_performance
    def sample(x):
        time.sleep(0.01)
        return x * 2

    with caplog.at_level(logging.DEBUG):
        result = sample(3)

    assert result == 6
    assert any("sample took" in record.message for record in caplog.records)


def test_retry_transient_defaults_on_invalid_env(monkeypatch):
    """Invalid environment variables should fall back to safe defaults."""

    # Provide non-numeric values that would previously raise ``ValueError``
    monkeypatch.setenv("GOVDOCVERIFY_MAX_RETRIES", "not-int")
    monkeypatch.setenv("GOVDOCVERIFY_BACKOFF", "bad")

    calls = {"count": 0}

    @retry_transient()
    def boom() -> None:
        calls["count"] += 1
        raise ValueError("boom")

    with pytest.raises(ValueError):
        boom()

    # Should retry the default number of times (3 attempts total)
    assert calls["count"] == 3
