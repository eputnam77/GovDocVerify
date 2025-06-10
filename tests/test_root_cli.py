from unittest.mock import patch

import cli


def test_root_cli_delegates_to_package():
    with patch("documentcheckertool.cli.main", return_value=0) as mock_main:
        assert cli.main() == 0
        mock_main.assert_called_once()
