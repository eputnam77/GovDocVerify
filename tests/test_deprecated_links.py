# pytest -v tests/test_deprecated_links.py --log-cli-level=DEBUG

from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.models import Severity

checker = AccessibilityChecks()

PARAMS = [
    ("# Title\nRefer to https://rgl.faa.gov for data.", "https://drs.faa.gov"),
    ("# Title\nSystem is listed at rgl.faa.gov/index.html.", "https://drs.faa.gov"),
    ("# Title\nOld link: https://www.faa.gov/info.", "https://www.faa.gov"),
]


def test_deprecated_links():
    for text, expected in PARAMS:
        result = checker.check_text(text)
        msgs = [
            i["message"]
            for i in result.issues
            if i.get("severity") in (Severity.ERROR, Severity.WARNING)
        ]
        assert any(expected in m for m in msgs), f"Expected suggestion '{expected}' in {msgs}"
