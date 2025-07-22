import sys
from pathlib import Path

import pytest

# Ensure the project root and tests directories are on the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
tests_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(tests_dir))


@pytest.fixture
def managers():
    from govdocverify.checks.format_checks import (
        FormatChecks,
        FormattingChecker,
    )
    from govdocverify.utils.terminology_utils import TerminologyManager

    tm = TerminologyManager()
    return FormatChecks(tm), FormattingChecker(tm)
