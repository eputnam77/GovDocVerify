from documentcheckertool import server_cli


def test_run_server_invokes_uvicorn(mocker) -> None:
    mock_run = mocker.patch("uvicorn.run")
    server_cli.run_server()
    mock_run.assert_called_once()
