import json
import re
from unittest import mock

import pytest

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
