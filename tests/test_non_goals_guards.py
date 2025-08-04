"""Placeholder tests for non-goals guardrails."""

import pytest


@pytest.mark.skip("NG-01: rejection of non-government docs not implemented")
def test_rejects_non_government_docs() -> None:
    """NG-01: system should reject documents outside scope."""
    ...


@pytest.mark.skip("NG-02: exclusion of legacy formats not implemented")
def test_excludes_legacy_formats() -> None:
    """NG-02: legacy document formats are ignored."""
    ...
