from documentcheckertool.formatting.document_formatter import DocumentFormatter


def test_format_text_basic():
    formatter = DocumentFormatter()
    text = "He said 'hello'. See \u00a71.\n1. item"
    formatted = formatter.format_text(text)
    assert '"hello"' in formatted
    assert "\u00a7 1" in formatted
    assert formatted.splitlines()[1] == "item"


def test_check_formatting_issues():
    formatter = DocumentFormatter()
    text = "He said 'hello' and \"bye\".\n1.item\n\u00a71"
    result = formatter.check_formatting(text)
    assert not result.success
    msgs = [issue["message"] for issue in result.issues]
    assert any("Mixed quotation marks" in m for m in msgs)
    assert any("section symbol" in m for m in msgs)
    assert len(msgs) == 2
