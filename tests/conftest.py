import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add the tests directory to the Python path
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

import pytest

from documentcheckertool.checks.format_checks import FormatChecks, FormattingChecker
from documentcheckertool.utils.terminology_utils import TerminologyManager


@pytest.fixture
def managers():
    tm = TerminologyManager()
    return FormatChecks(tm), FormattingChecker(tm)
