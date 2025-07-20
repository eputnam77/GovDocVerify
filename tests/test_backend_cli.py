import pytest

import backend.cli as cli  # noqa: F401


def test_backend_cli_main_not_implemented() -> None:
    """Ensure the CLI entry point is not yet implemented."""
    with pytest.raises(NotImplementedError):
        cli.main()
