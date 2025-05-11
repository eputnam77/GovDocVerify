# pytest -v tests/test_terminology.py --log-cli-level=DEBUG

import pytest
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

class TestTerminologyChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.terminology_checks = TerminologyChecks(self.terminology_manager)

    def test_usc_formatting(self):
        content = "\n".join([
            "According to 49 USC 106(g)",
            "As per 49 U.S.C 106(g)",
            "Under 49 U.S.C. 106(g)"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("USC should be U.S.C." in issue['message'] for issue in result['warnings'])
        assert any("U.S.C should have a final period" in issue['message'] for issue in result['warnings'])

    def test_cfr_formatting(self):
        content = "\n".join([
            "Under 14 C.F.R. Part 25",
            "According to 14 CFR Part 25",
            "Per 14 CFR part 25"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("C.F.R. should be CFR" in issue['message'] for issue in result['warnings'])
        assert any("CFR Part should be CFR part" in issue['message'] for issue in result['warnings'])

    def test_gendered_terms(self):
        content = "\n".join([
            "The chairman will preside",
            "The flagman will signal",
            "The manpower is needed"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("chairman should be chair" in issue['message'] for issue in result['warnings'])
        assert any("flagman should be flagperson" in issue['message'] for issue in result['warnings'])
        assert any("manpower should be labor force" in issue['message'] for issue in result['warnings'])

    def test_plain_language(self):
        content = "\n".join([
            "Pursuant to the regulations",
            "In accordance with the rules",
            "In compliance with the standards"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Use simpler alternatives like 'under' or 'following'" in issue['message'] for issue in result['warnings'])

    def test_aviation_terminology(self):
        content = "\n".join([
            "The flight crew will perform",
            "The cockpit is equipped with",
            "Notice to air missions is required"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("flight crew should be flightcrew" in issue['message'] for issue in result['warnings'])
        assert any("cockpit should be flight deck" in issue['message'] for issue in result['warnings'])
        assert any("notice to air missions should be notice to airmen" in issue['message'] for issue in result['warnings'])

    def test_legalese_terms(self):
        content = "\n".join([
            "The aforementioned requirements",
            "The herein contained provisions",
            "The thereto attached documents"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Avoid archaic or legalese terms" in issue['message'] for issue in result['warnings'])

    def test_qualifiers(self):
        content = "\n".join([
            "This is very important",
            "The system is extremely reliable",
            "The process is quite efficient"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Avoid unnecessary qualifiers" in issue['message'] for issue in result['warnings'])

    def test_plural_usage(self):
        content = "\n".join([
            "The data are available",
            "The criteria is met",
            "The phenomena is observed"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("Ensure consistent singular/plural usage" in issue['message'] for issue in result['warnings'])

    def test_document_type_specific_terms(self):
        content = "\n".join([
            "This is an Advisory Circular",
            "This is a Policy Statement",
            "This is a Special Condition"
        ])
        result = self.terminology_checks.check(content)
        assert result['has_errors'] is False
        assert len(result['errors']) == 0

    def test_authority_citations(self):
        content = "\n".join([
            "Authority: 49 U.S.C. 106(g)",
            "Authority: 49 U.S.C. 106(f), 40113, 44701, 44702, and 44704"
        ])
        result = self.terminology_checks.check(content)
        assert not result['has_errors']
        assert any("49 U.S.C. 106(g) should not be included" in issue['message'] for issue in result['warnings'])