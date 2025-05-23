# pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG

import unittest
import logging
from test_base import TestBase
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.models import DocumentCheckResult
import pytest

logger = logging.getLogger(__name__)

class TestTerminologyChecks(TestBase):
    """Test suite for terminology-related checks."""

    def setUp(self):
        super().setUp()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)
        logger.debug("Initialized TerminologyChecks for testing")

    def test_cross_reference_usage(self):
        """Test cross-reference checking."""
        content = "\n".join([
            "As mentioned above",
            "See below for details",
            "Refer to section 25.1309"
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Cross reference check result: {result}")
        logger.debug(f"Issues found: {result['warnings']}")
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Avoid using 'above'")
        self.assert_issue_contains(result, "Avoid using 'below'")

    def test_required_language(self):
        """Test required language checking."""
        content = "\n".join([
            "This document contains required language.",
            "Standard disclaimer text.",
            "Regulatory compliance statement."
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Required language check result: {result}")
        self.assertTrue(result['has_errors'] is False)

    def test_invalid_references(self):
        """Test various invalid reference patterns."""
        content = "\n".join([
            "The former section",
            "The latter paragraph",
            "As stated earlier",
            "The aforementioned requirements"
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Invalid references check result: {result}")
        logger.debug(f"Issues found: {result['warnings']}")
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Avoid using 'former'")
        self.assert_issue_contains(result, "Avoid using 'latter'")
        self.assert_issue_contains(result, "Avoid using 'earlier'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

    def test_additionally_usage(self):
        """Test checking for sentences beginning with 'Additionally' per DOT OGC Style Guide."""
        content = "\n".join([
            "Additionally, the FAA requires compliance.",
            "The FAA requires compliance. Additionally, it must be documented.",
            "In addition, the FAA requires compliance.",  # Correct usage
            "The FAA requires compliance. In addition, it must be documented."  # Correct usage
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Additionally usage check result: {result}")
        logger.debug(f"Issues found: {result['warnings']}")
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Avoid using 'Additionally'")
        self.assert_issue_contains(result, "Replace with 'In addition'")

    def test_split_infinitives(self):
        """Test checking for split infinitives."""
        content = "\n".join([
            "The FAA needs to completely review the application.",
            "The applicant must to thoroughly document the process.",
            "The inspector will to carefully examine the evidence.",
            "The regulation requires to properly maintain records.",
            "The FAA needs to review the application completely.",  # Correct usage
            "The applicant must document the process thoroughly."  # Correct usage
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Split infinitives check result: {result}")
        logger.debug(f"Issues found: {result['warnings']}")
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Split infinitive detected")

    def test_multi_word_split_infinitives(self):
        """Test checking for split infinitives with multi-word phrases."""
        content = "\n".join([
            "The FAA needs to more than double its efforts.",
            "The applicant must to as well as document the process.",
            "The inspector will to in addition to examine the evidence.",
            "The regulation requires to in order to maintain records.",
            "The FAA needs to double its efforts more than.",  # Correct usage
            "The applicant must document the process as well as."  # Correct usage
        ])
        result = self.terminology_checks.check(content)
        logger.debug(f"Multi-word split infinitives check result: {result}")
        logger.debug(f"Issues found: {result['warnings']}")
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Split infinitive detected")

    def test_obsolete_agency_name_flagged(self):
        """Test that obsolete agency names are flagged and replacement is suggested."""
        doc = "Read the European Aviation Safety Agency documentation."
        result = self.terminology_checks.check_text(doc)
        msgs = [iss["message"] for iss in result.issues]
        self.assertTrue(any("European Union Aviation Safety Agency (EASA)" in m for m in msgs))

@pytest.mark.parametrize("doc_type,content,expect_flag", [
    # FINAL document → should flag
    ("Advisory Circular",
     ["This AC proposes a change to ..."],
     True),
    # NPRM (proposed phase) → should NOT flag
    ("NPRM",
     ["This NPRM proposes a change to ..."],
     False),
])
def test_proposed_wording(doc_type, content, expect_flag):
    from documentcheckertool.checks.terminology_checks import TerminologyChecks
    from documentcheckertool.utils.terminology_utils import TerminologyManager
    from documentcheckertool.models import DocumentCheckResult
    # Minimal TerminologyManager stub for test
    class DummyManager:
        terminology_data = {}
    tc = TerminologyChecks(DummyManager())
    # Simulate the run_checks interface
    class DummyDoc:
        paragraphs = [type('P', (), {'text': t}) for t in content]
    results = DocumentCheckResult()
    tc.run_checks(DummyDoc(), doc_type, results)
    flagged = any("proposed" in i.message for i in results.issues)
    assert flagged == expect_flag

if __name__ == '__main__':
    unittest.main()