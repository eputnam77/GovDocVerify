import pytest

import backend.cli as cli  # noqa: F401


def test_backend_cli_main_not_implemented() -> None:
    """Placeholder test for CLI launch."""
    pytest.fail("backend.cli.main should start uvicorn server")
