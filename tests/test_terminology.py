# pytest -v tests/test_terminology.py --log-cli-level=DEBUG

import pytest

from govdocverify.checks.terminology_checks import TerminologyChecks
from govdocverify.utils.terminology_utils import TerminologyManager


class TestTerminologyChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)

    def test_usc_formatting(self):
        content = "\n".join(
            ["According to 49 USC 106(g)", "As per 49 U.S.C 106(g)", "Under 49 U.S.C. 106(g)"]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any("USC should be U.S.C." in issue["message"] for issue in result["warnings"])
        assert any(
            "U.S.C should have a final period" in issue["message"] for issue in result["warnings"]
        )

    def test_cfr_formatting(self):
        content = "\n".join(
            ["Under 14 C.F.R. Part 25", "According to 14 CFR Part 25", "Per 14 CFR part 25"]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any("C.F.R. should be CFR" in issue["message"] for issue in result["warnings"])
        assert any(
            "CFR Part should be CFR part" in issue["message"] for issue in result["warnings"]
        )

    def test_gendered_terms(self):
        content = "\n".join(
            ["The chairman will preside", "The flagman will signal", "The manpower is needed"]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any("Change chairman to chair" in issue["message"] for issue in result["warnings"])
        assert any(
            "Change flagman to flagperson" in issue["message"] for issue in result["warnings"]
        )
        assert any(
            "Change manpower to labor force" in issue["message"] for issue in result["warnings"]
        )

    def test_plain_language(self):
        content = "\n".join(
            [
                "Pursuant to the regulations",
                "In accordance with the rules",
                "In compliance with the standards",
            ]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any(
            "Change" in issue["message"]
            and "to an alternative like 'under' or 'following'" in issue["message"]
            for issue in result["warnings"]
        )

    def test_aviation_terminology(self):
        content = "\n".join(
            [
                "The flight crew will perform",
                "The cockpit is equipped with",
                "Notice to air missions is required",
            ]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any(
            "Change flight crew to flightcrew" in issue["message"] for issue in result["warnings"]
        )
        assert any(
            "Change cockpit to flight deck" in issue["message"] for issue in result["warnings"]
        )
        assert any(
            "Change notice to air missions to notice to airmen" in issue["message"]
            for issue in result["warnings"]
        )

    def test_legalese_terms(self):
        content = "\n".join(
            [
                "The aforementioned requirements",
                "The herein contained provisions",
                "The thereto attached documents",
            ]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any(
            "Avoid archaic or legalese terms" in issue["message"] for issue in result["warnings"]
        )

    def test_qualifiers(self):
        content = "\n".join(
            [
                "This is very important",
                "The system is extremely reliable",
                "The process is quite efficient",
            ]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any(
            "Remove the unnecessary qualifier" in issue["message"] for issue in result["warnings"]
        )

    def test_plural_usage(self):
        content = "\n".join(
            ["The data are available", "The criteria is met", "The phenomena is observed"]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        assert any(
            "Use" in issue["message"] and "as a plural noun" in issue["message"]
            for issue in result["warnings"]
        )

    def test_document_type_specific_terms(self):
        content = "\n".join(
            [
                "This is an Advisory Circular",
                "This is a Policy Statement",
                "This is a Special Condition",
            ]
        )
        result = self.terminology_checks.check(content)
        assert result["has_errors"] is False
        assert len(result["errors"]) == 0

    def test_standard_definition_allows_leading_article(self):
        """Definitions starting with 'the' should still match standard wording."""
        text = (
            "the Federal Aviation Administration (FAA) oversees safety. "
            "FAA coordinates national airspace operations."
        )
        result = self.terminology_manager.check_text(text)
        assert result.success
        assert all(
            "non-standard definition" not in issue.get("message", "")
            for issue in result.issues
        )

    def test_authority_citations(self):
        content = "\n".join(
            [
                "Authority: 49 U.S.C. 106(g)",
                "Authority: 49 U.S.C. 106(f), 40113, 44701, 44702, and 44704",
                "Authority: 49 USC §106(g), 40113, 44701",
                "Authority: §106(g), 40113, 44701",
                "Authority: 106(g), 40113, 44701",
            ]
        )
        result = self.terminology_checks.check(content)
        assert not result["has_errors"]
        # Check that the new message is present for all forms
        flagged = [
            issue
            for issue in result["warnings"]
            if "Remove '49 U.S.C. 106(g)'" in issue["message"]
            and "This authority citation was deleted" in issue["message"]
        ]
        assert len(flagged) >= 1
        # Check that a suggestion is present and 106(g) is removed from the suggestion
        for issue in flagged:
            assert "suggestion" in issue
            assert "106(g)" not in issue["suggestion"]
