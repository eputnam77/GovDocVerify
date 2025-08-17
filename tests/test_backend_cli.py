from unittest import mock

import backend.cli as cli  # noqa: F401


def test_backend_cli_invokes_uvicorn() -> None:
    """CLI should invoke the graceful runner with provided arguments."""
    with mock.patch("backend.cli.run") as mock_run:
        cli.main(["--host", "127.0.0.1", "--port", "9001"])
        mock_run.assert_called_once()
