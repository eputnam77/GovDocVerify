"""Placeholder tests for end-to-end scenarios."""

import pytest


@pytest.mark.skip("E2E-A: CLI single-file run not implemented")
def test_cli_single_file_run() -> None:
    """E2E-A: CLI single-file run with exports and fail-on flag."""
    ...


@pytest.mark.skip("E2E-B: API + frontend integration not implemented")
def test_api_frontend_integration() -> None:
    """E2E-B: API upload and frontend rendering with downloadable exports."""
    ...


@pytest.mark.skip("E2E-C: batch gate under STRICT_MODE not implemented")
def test_batch_gate_strict_mode() -> None:
    """E2E-C: batch processing fails build on High severity under STRICT_MODE=1."""
    ...
