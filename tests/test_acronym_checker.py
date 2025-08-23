import pytest

from govdocverify.checks.acronym_checks import AcronymChecker


@pytest.fixture
def checker() -> AcronymChecker:
    return AcronymChecker()


def test_defined_acronym_not_flagged(checker: AcronymChecker) -> None:
    text = "The Federal Aviation Administration (FAA) regulates aviation. " "FAA oversees safety."
    result = checker.check_text(text)
    assert result.success
    assert result.issues == []


def test_valid_word_not_flagged(checker: AcronymChecker) -> None:
    text = "The CAT sat on the mat."
    result = checker.check_text(text)
    assert result.success
    assert result.issues == []


def test_special_cases_no_false_positive(checker: AcronymChecker) -> None:
    texts = [
        "Meet in Washington DC next week.",
        "Refer to 42 USC 1981 for details.",
        "Section IV covers procedures.",
    ]
    for text in texts:
        result = checker.check_text(text)
        assert result.success
        assert result.issues == []


def test_undefined_acronym_flagged(checker: AcronymChecker) -> None:
    text = "The QZX launched a rocket."
    result = checker.check_text(text)
    assert not result.success
    assert any(
        issue.get("message") == "Confirm 'QZX' was defined at its first use"
        for issue in result.issues
    )
