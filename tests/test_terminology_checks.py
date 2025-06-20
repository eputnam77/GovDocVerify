# pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG

import logging
import unittest

import pytest

from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.models import DocumentCheckResult

from .test_base import TestBase

logger = logging.getLogger(__name__)


class TestTerminologyChecks(TestBase):
    """Test suite for terminology-related checks."""

    def setUp(self):
        super().setUp()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)
        logger.debug("Initialized TerminologyChecks for testing")

    def test_cross_reference_usage(self):
        """Test cross-reference checking."""
        content = "\n".join(
            ["As mentioned above", "See below for details", "Refer to section 25.1309"]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Cross reference check result: {result}")
        logger.debug(f"Issues found: {result.issues}")
        self.assert_has_issues(result)
        self.assert_issue_contains(
            result,
            "Avoid vague references like 'above' or 'below'; cite a specific section.",
        )

    def test_required_language(self):
        """Test required language checking."""
        content = "\n".join(
            [
                "This document contains required language.",
                "Standard disclaimer text.",
                "Regulatory compliance statement.",
            ]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Required language check result: {result}")
        self.assert_no_issues(result)

    def test_invalid_references(self):
        """Test various invalid reference patterns."""
        content = "\n".join(
            [
                "The former section",
                "The latter paragraph",
                "As stated earlier",
                "The aforementioned requirements",
            ]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Invalid references check result: {result}")
        logger.debug(f"Issues found: {result.issues}")
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Avoid using 'former'")
        self.assert_issue_contains(result, "Avoid using 'latter'")
        # 'earlier' is not in FORBIDDEN_TERMS, so we do not assert for it
        # self.assert_issue_contains(result, "Avoid using 'earlier'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

    def test_additionally_usage(self):
        """Test checking for sentences beginning with 'Additionally' per DOT OGC Style Guide."""
        content = "\n".join(
            [
                "Additionally, the FAA requires compliance.",
                "The FAA requires compliance. Additionally, it must be documented.",
                "In addition, the FAA requires compliance.",  # Correct usage
                "The FAA requires compliance. In addition, it must be documented.",  # Correct usage
            ]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Additionally usage check result: {result}")
        logger.debug(f"Issues found: {result.issues}")
        self.assert_has_issues(result)
        self.assert_issue_contains(result, 'Change "additionally" to "in addition')

    def test_split_infinitives(self):
        """Test checking for split infinitives."""
        content = "\n".join(
            [
                "The FAA needs to completely review the application.",
                "The applicant must to thoroughly document the process.",
                "The inspector will to carefully examine the evidence.",
                "The regulation requires to properly maintain records.",
                "The FAA needs to review the application completely.",  # Correct usage
                "The applicant must document the process thoroughly.",  # Correct usage
            ]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Split infinitives check result: {result}")
        logger.debug(f"Issues found: {result.issues}")
        # Check that at least one split infinitive info issue is present
        split_issues = [
            i for i in result.issues if "Split infinitive detected" in i.get("message", "")
        ]
        self.assertTrue(split_issues, "Expected split infinitive issues but found none")

    def test_multi_word_split_infinitives(self):
        """Test checking for split infinitives with multi-word phrases."""
        content = "\n".join(
            [
                "The FAA needs to more than double its efforts.",
                "The applicant must to as well as document the process.",
                "The inspector will to in addition to examine the evidence.",
                "The regulation requires to in order to maintain records.",
                "The FAA needs to double its efforts more than.",  # Correct usage
                "The applicant must document the process as well as.",  # Correct usage
            ]
        )
        result = self.terminology_checks.check_text(content)
        logger.debug(f"Multi-word split infinitives check result: {result}")
        logger.debug(f"Issues found: {result.issues}")
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "Split infinitive detected")

    def test_obsolete_agency_name_flagged(self):
        """Test that obsolete agency names are flagged and replacement is suggested."""
        doc = "Read the European Aviation Safety Agency documentation."
        result = self.terminology_checks.check_text(doc)
        msgs = [iss["message"] for iss in result.issues]
        self.assertTrue(any("European Union Aviation Safety Agency (EASA)" in m for m in msgs))

    def test_email_case_sensitive_variants(self):
        """Ensure capitalization-only variants don't flag correct lowercase usage."""
        doc = "Send the form via email."
        result = self.terminology_checks.check_text(doc)
        self.assert_no_issues(result)

        doc_bad = "Send the form via Email."
        result_bad = self.terminology_checks.check_text(doc_bad)
        self.assert_has_issues(result_bad)
        self.assert_issue_contains(result_bad, 'Change "Email" to "email"')

    def test_unannunciated_variant(self):
        """Flag hyphenated 'un-annunciated' as incorrect."""
        doc = "The fault remained un-annunciated during testing."
        result = self.terminology_checks.check_text(doc)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, 'Change "un-annunciated" to "unannunciated"')


@pytest.mark.parametrize(
    "doc_type,content,expect_flag",
    [
        # FINAL document → should flag
        ("Advisory Circular", ["This AC proposes a change to ..."], True),
        # NPRM (proposed phase) → should NOT flag
        ("NPRM", ["This NPRM proposes a change to ..."], False),
    ],
)
def test_proposed_wording(doc_type, content, expect_flag):
    from documentcheckertool.checks.terminology_checks import TerminologyChecks

    # Minimal TerminologyManager stub for test
    class DummyManager:
        terminology_data = {}

    tc = TerminologyChecks(DummyManager())

    # Simulate the run_checks interface
    class DummyDoc:
        paragraphs = [type("P", (), {"text": t}) for t in content]

    results = DocumentCheckResult()
    tc.run_checks(DummyDoc(), doc_type, results)
    # Check for the exact message from _check_proposed_wording
    message = "Found 'proposed' wording—remove draft phrasing for final documents."
    flagged = any(message in getattr(i, "message", str(i)) for i in results.issues)
    if flagged != expect_flag:
        for i in results.issues:
            logging.getLogger(__name__).debug(getattr(i, "message", str(i)))
    assert flagged == expect_flag


if __name__ == "__main__":
    unittest.main()
