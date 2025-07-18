from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter


def _make_result(issues=None, details=None):
    return DocumentCheckResult(success=not issues, issues=issues or [], details=details)


def test_format_readability_issues():
    metrics = {
        "flesch_reading_ease": 65,
        "flesch_kincaid_grade": 9,
        "gunning_fog_index": 11,
        "passive_voice_percentage": 12,
    }
    issues = [
        {
            "type": "jargon",
            "word": "utilize",
            "suggestion": "use",
            "sentence": "We should utilize this API",
        },
        {"type": "readability_score", "message": "Low score"},
    ]
    result = _make_result(issues=issues, details={"metrics": metrics})
    fmt = ResultFormatter()
    lines = fmt._format_readability_issues(result)
    assert any("Flesch Reading Ease" in line for line in lines)
    assert any("utilize" in line for line in lines)
    assert any("Low score" in line for line in lines)


def test_format_readability_issues_dict():
    """Ensure formatting works when given a plain dictionary."""
    metrics = {
        "flesch_reading_ease": 60,
        "flesch_kincaid_grade": 10,
        "gunning_fog_index": 12,
        "passive_voice_percentage": 20,
    }
    issues = [
        {"type": "passive_voice", "message": "Too much passive"},
    ]
    result_dict = {"success": False, "issues": issues, "details": {"metrics": metrics}}
    fmt = ResultFormatter()
    lines = fmt._format_readability_issues(result_dict)
    assert any("Passive Voice" in line for line in lines)


def test_format_readability_missing_type():
    """Handle readability issues lacking a 'type' key."""
    metrics = {
        "flesch_reading_ease": 55,
        "flesch_kincaid_grade": 11,
        "gunning_fog_index": 13,
        "passive_voice_percentage": 15,
    }
    issues = [{"message": "Generic message"}]
    result = _make_result(issues=issues, details={"metrics": metrics})
    fmt = ResultFormatter()
    lines = fmt._format_readability_issues(result)
    assert any("Generic message" in line for line in lines)


def test_format_accessibility_and_standard_issue():
    access_result = _make_result(
        issues=[
            {
                "category": "508_compliance_heading_structure",
                "message": "Heading structure",
                "context": "H1 missing",
                "recommendation": "Add H1",
            },
            {"category": "image_alt_text", "context": "img.png"},
            {"category": "hyperlink_accessibility", "user_message": "Bad link"},
            {"category": "color_contrast", "message": "Low contrast"},
        ]
    )
    fmt = ResultFormatter()
    lines = fmt._format_accessibility_issues(access_result)
    assert any("Context" in line for line in lines)
    assert any("Missing alt text" in line for line in lines)
    assert any("Bad link" in line for line in lines)
    assert any("Low contrast" in line for line in lines)

    # standard issue helper
    assert fmt._format_standard_issue("simple") == "    \u2022 simple"
    d = fmt._format_standard_issue({"incorrect": "a", "correct": "b"})
    assert "Replace 'a'" in d
    d = fmt._format_standard_issue({"sentence": "s", "word_count": 5})
    assert "Review this sentence" in d
    d = fmt._format_standard_issue({"type": "long_paragraph", "message": "long"})
    assert "long" in d


def test_format_results_unknown_group():
    result = _make_result(issues=[{"message": "err", "severity": Severity.ERROR}])
    data = {"x": {"y": result}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    text = fmt.format_results(data, "AC", group_by="other")
    assert "Internal error" in text


def test_format_results_with_metadata():
    result = _make_result()
    data = {"x": {"y": result}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    text = fmt.format_results(
        data,
        "AC",
        metadata={"title": "Doc", "author": "A", "last_modified_by": "B"},
    )
    assert "Title: Doc" in text
    assert "Author: A" in text


def test_readability_section_position():
    metrics = {
        "flesch_reading_ease": 70,
        "flesch_kincaid_grade": 8,
        "gunning_fog_index": 10,
        "passive_voice_percentage": 5,
    }
    readability = _make_result(details={"metrics": metrics})
    heading = _make_result(issues=[{"message": "Heading issue", "severity": Severity.ERROR}])
    data = {"analysis": {"check": readability}, "headings": {"check": heading}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    report = fmt.format_results(data, "AC")
    assert "Flesch Reading Ease" not in report


def test_format_results_with_all_metadata_fields() -> None:
    """Placeholder test ensuring formatter outputs all metadata fields."""
    result = _make_result()
    data = {"x": {"y": result}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    text = fmt.format_results(
        data,
        "AC",
        metadata={
            "title": "Doc",
            "author": "A",
            "last_modified_by": "B",
            "created": "2024-01-01T00:00:00",
            "modified": "2024-01-02T00:00:00",
        },
    )
    expected_fields = [
        "Title: Doc",
        "Author: A",
        "Last Modified By: B",
        "Created: 2024-01-01",
        "Modified: 2024-01-02",
    ]
    for field in expected_fields:
        assert field in text
