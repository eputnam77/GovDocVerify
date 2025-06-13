import json
import os
import re
from unittest import mock

import pytest

from documentcheckertool.interfaces import gradio_ui
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.utils.formatting import FormatStyle, ResultFormatter
from documentcheckertool.utils.pattern_cache import PatternCache
from documentcheckertool.utils.security import (
    RateLimiter,
    SecurityError,
    validate_file,
)


def test_pattern_cache_basic(tmp_path):
    data = {
        "required_language": {"TEST": ["foo"]},
        "boilerplate": {"TEST": ["bar"]},
    }
    patterns_file = tmp_path / "p.json"
    patterns_file.write_text(json.dumps(data))
    pc = PatternCache(str(patterns_file))
    assert pc.get_required_language_patterns("TEST")[0].pattern == "foo"
    assert pc.get_boilerplate_patterns("TEST")[0].pattern == "bar"
    pat = pc.get_pattern("foo")
    assert isinstance(pat, re.Pattern)
    pc.clear()
    assert pc._cache == {}
    with pytest.raises(ValueError):
        pc.get_pattern("[")


def test_validate_file_and_rate_limiter(tmp_path):
    f = tmp_path / "x.docx"
    f.write_bytes(b"test")
    with mock.patch("documentcheckertool.utils.security.filetype.guess") as g:
        g.return_value = mock.Mock(mime="application/msword")
        validate_file(str(f))
        g.return_value = None
        with pytest.raises(SecurityError):
            validate_file(str(f))
    rl = RateLimiter(max_requests=2, time_window=1)
    assert not rl.is_rate_limited("a")
    assert not rl.is_rate_limited("a")
    assert rl.is_rate_limited("a")


def test_result_formatter_severity_grouping():
    res = DocumentCheckResult(success=False)
    res.add_issue("err", Severity.ERROR)
    results = {"format": {"check": res}}
    fmt = ResultFormatter(style=FormatStyle.PLAIN)
    out_cat = fmt.format_results(results, "AC", group_by="category")
    assert "err" in out_cat
    out_sev = fmt.format_results(results, "AC", group_by="severity")
    assert "ERROR" in out_sev


def test_gradio_ui_helpers(tmp_path):
    vis = gradio_ui._build_visibility_settings(
        True, False, True, True, False, True, False, True, False
    )
    selected = gradio_ui._get_selected_categories(vis)
    assert "readability" in selected
    assert "paragraph_length" not in selected
    res_dict = {"readability": {"c": {"issues": [{"message": "m"}]}}}
    filtered = gradio_ui._filter_results_by_visibility(res_dict, selected)
    assert "readability" in filtered
    total, counts = gradio_ui._count_issues_in_results(filtered)
    assert total == 1 and counts["readability"] == 1
    filtered_export = gradio_ui._filter_results_for_export(res_dict, vis)
    assert "readability" in filtered_export
    count_exp = gradio_ui._count_export_issues(filtered_export)
    assert count_exp == 1
    html = gradio_ui._build_pdf_html_content(
        {"total": 1, "by_category": {"readability": 1}},
        filtered_export,
    )
    assert '<li class="issue">' in html
    gradio_ui._last_results = {
        "results": res_dict,
        "filtered_results": filtered_export,
        "visibility": vis.to_dict(),
        "summary": {"total": 1, "by_category": {"readability": 1}},
        "formatted_results": "<div>ok</div>",
    }
    file_path = gradio_ui.generate_report_file(None, None, format="html")
    assert file_path and os.path.exists(file_path)
    os.remove(file_path)


def test_generate_report_file_docx_pdf(tmp_path):
    res_dict = {"readability": {"c": {"issues": [{"message": "m"}]}}}
    data = {
        "results_dict": res_dict,
        "visibility_settings": gradio_ui.VisibilitySettings(),
        "summary": {"total": 1, "by_category": {"readability": 1}},
        "formatted_results": "<div>ok</div>",
    }

    docx_path = gradio_ui.generate_report_file(data, "AC", format="docx")
    assert docx_path and os.path.exists(docx_path)
    os.remove(docx_path)

    with mock.patch("pdfkit.from_string") as mk:
        mk.side_effect = lambda html, path: open(path, "wb").write(b"%PDF-1.4")
        pdf_path = gradio_ui.generate_report_file(data, "AC", format="pdf")
        assert pdf_path and os.path.exists(pdf_path)
        mk.assert_called_once()
        os.remove(pdf_path)
