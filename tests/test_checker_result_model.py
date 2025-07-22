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
