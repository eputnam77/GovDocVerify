"""Tests for the :mod:`govdocverify.server_cli` module."""

from unittest import mock

from govdocverify import server_cli


def test_run_server_invokes_uvicorn() -> None:
    """``run_server`` should invoke ``uvicorn.run``."""
    with mock.patch("uvicorn.run") as mock_run:
        server_cli.run_server()
        mock_run.assert_called_once()
