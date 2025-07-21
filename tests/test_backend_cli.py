import backend.cli as cli  # noqa: F401


def test_backend_cli_invokes_uvicorn(mocker) -> None:
    mock_run = mocker.patch("uvicorn.run")
    cli.main(["--host", "127.0.0.1", "--port", "9001"])
    mock_run.assert_called_once()
