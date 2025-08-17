import pytest

from govdocverify.models import DocumentCheckResult, Severity


def test_document_check_result_round_trip() -> None:
    res = DocumentCheckResult(
        success=False,
        issues=[{"message": "m", "severity": Severity.WARNING, "line_number": 1, "category": "c"}],
        checker_name="checker",
        score=0.5,
        severity=Severity.WARNING,
        details={"x": 1},
    )
    data = res.to_dict()
    assert data["version"] == DocumentCheckResult.SERIALIZATION_VERSION
    restored = DocumentCheckResult.from_dict(data)
    assert restored == res


def test_document_check_result_deserialize_legacy() -> None:
    legacy = {"success": True, "issues": [], "checker_name": "old"}
    res = DocumentCheckResult.from_dict(legacy)
    assert res.success is True
    assert res.checker_name == "old"


def test_document_check_result_rejects_future_version() -> None:
    data = {"version": 999, "success": True, "issues": []}
    with pytest.raises(ValueError):
        DocumentCheckResult.from_dict(data)
