from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.models import Severity

checker = AccessibilityChecks()

PARAMS = [
    ("Refer to https://rgl.faa.gov for data.", "https://drs.faa.gov"),
    ("System is listed at rgl.faa.gov/index.html.", "https://drs.faa.gov"),
    ("Old link: https://www.faa.gov/info.", "https://www.faa.gov"),
]

def test_deprecated_links():
    for text, expected in PARAMS:
        result = checker.check_text(text)
        msgs = [i['message'] for i in result.issues if i.get('severity') == Severity.ERROR]
        assert any(expected in m for m in msgs), f"Expected suggestion '{expected}' in {msgs}"