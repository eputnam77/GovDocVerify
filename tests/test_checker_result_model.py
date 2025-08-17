from govdocverify.models.checker_result import DocumentValidationResults


def test_watermark_addition() -> None:
    dvr = DocumentValidationResults(is_valid=True, message="ok")
    assert dvr.watermark_validation is None
    dvr.add_watermark_result(True, "good", found_watermark="foo", expected_watermark="foo")
    assert dvr.watermark_validation == {
        "is_valid": True,
        "message": "good",
        "found": "foo",
        "expected": "foo",
    }


def test_serialization_roundtrip() -> None:
    dvr = DocumentValidationResults(is_valid=False, message="oops")
    data = dvr.to_dict()
    assert data["version"] == DocumentValidationResults.SERIALIZATION_VERSION
    restored = DocumentValidationResults.from_dict(data)
    assert restored == dvr


def test_serialization_legacy_input() -> None:
    legacy = {"is_valid": True, "message": "ok"}
    restored = DocumentValidationResults.from_dict(legacy)
    assert restored.is_valid is True
    assert restored.message == "ok"
