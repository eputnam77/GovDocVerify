import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "govdocverify_models_file",
    Path(__file__).resolve().parents[1] / "govdocverify" / "models.py",
)
assert spec is not None
models = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(models)


def test_severity_helpers() -> None:
    assert models.Severity.ERROR.to_color() == "red"
    assert models.Severity.WARNING.value_str == "warning"


def test_document_check_result_html() -> None:
    res = models.DocumentCheckResult()
    assert "No issues" in res.to_html()
    res.add_issue("msg1", models.Severity.WARNING, line_number=1)
    res.add_issue("msg2", models.Severity.ERROR, line_number=2)
    html = res.to_html()
    assert "msg1" in html and "msg2" in html
    assert "warning" in html and "error" in html


def test_document_check_result_html_handles_string_severity() -> None:
    res = models.DocumentCheckResult(
        issues=[{"message": "msg", "severity": "warning"}]
    )
    html = res.to_html()
    assert "msg" in html
    assert "warning" in html.lower()


def test_visibility_settings_roundtrip() -> None:
    vis = models.VisibilitySettings(
        show_readability=False,
        show_format=False,
        show_document_status=False,
        show_acronym=False,
    )
    data = vis.to_dict()
    assert not data["readability"]
    json_str = json.dumps(data)
    vis2 = models.VisibilitySettings.from_dict_json(json_str)
    assert vis2.show_readability is False
    assert vis2.show_format is False
    assert vis2.show_document_status is False
    assert vis2.show_acronym is False


def test_issue_dataclass_and_pattern_config() -> None:
    pc = models.PatternConfig(pattern="foo", description="desc", is_error=True)
    assert pc.pattern == "foo"
    issue = models.Issue(message="msg")
    assert issue.message == "msg"


def test_document_check_result_preserves_initial_severity() -> None:
    from govdocverify.models import DocumentCheckResult, Severity

    res = DocumentCheckResult(success=True, severity=Severity.WARNING)
    assert res.severity == Severity.WARNING

    legacy = models.DocumentCheckResult(success=True, severity=models.Severity.WARNING)
    assert legacy.severity == models.Severity.WARNING
