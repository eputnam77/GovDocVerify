# NOTE: Refactored to use StructureChecks, as cross_reference_checks.py does not exist.
import pytest
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

class TestCrossReferenceChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.structure_checks = StructureChecks(self.terminology_manager)

    def test_cross_references(self):
        content = [
            "See paragraph 5.2.3 for more information.",
            "Refer to section 4.1.2 for details.",
            "As discussed in paragraph 3.4.5"
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Cross-reference format" in issue['message'] for issue in result['warnings'])

    def test_valid_cross_references(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.1 Requirements.",
            "The following requirements apply...",
            "As noted in paragraph 2.1, these requirements..."
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert len(result['warnings']) == 0

    def test_invalid_cross_references(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.2 Requirements.",  # Wrong paragraph number
            "The following requirements apply...",
            "As noted in paragraph 2.1, these requirements..."  # Reference to non-existent paragraph
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Invalid cross-reference" in issue['message'] for issue in result['warnings'])

    def test_missing_cross_references(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "The requirements are discussed in paragraph 2.1.",  # Reference to non-existent paragraph
            "2.2 Requirements.",
            "The following requirements apply..."
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Missing cross-reference" in issue['message'] for issue in result['warnings'])

    def test_cross_reference_formatting(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "See para 2.1 for details.",  # Incorrect format
            "2.1 Requirements.",
            "The following requirements apply...",
            "Refer to section 2.1 for more information."  # Incorrect format
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Incorrect cross-reference format" in issue['message'] for issue in result['warnings'])

    def test_cross_reference_sequence(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.1 Requirements.",
            "The following requirements apply...",
            "As noted in paragraph 2.1, these requirements...",
            "2.2 Additional Requirements.",
            "More requirements are specified in paragraph 2.1."  # Reference to earlier paragraph
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Cross-reference to earlier paragraph" in issue['message'] for issue in result['warnings'])

    def test_cross_reference_consistency(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.1 Requirements.",
            "The following requirements apply...",
            "As noted in para 2.1, these requirements...",  # Inconsistent format
            "See paragraph 2.1 for details."  # Inconsistent format
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Inconsistent cross-reference format" in issue['message'] for issue in result['warnings'])

    def test_cross_reference_edge_cases(self):
        """Test edge cases in cross-references."""
        content = [
            "The former and latter sections",
            "As stated earlier in this document",
            "The aforementioned requirements"
        ]
        result = self.structure_checks.check(content)
        self.assertFalse(result['has_errors'])
        self.assert_issue_contains(result, "Avoid using 'former'")
        self.assert_issue_contains(result, "Avoid using 'latter'")
        self.assert_issue_contains(result, "Avoid using 'earlier'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

    def test_valid_cross_references(self):
        """Test valid cross-reference formats."""
        content = [
            "See section 25.1309",
            "Refer to paragraph (a)",
            "Under subsection (1)"
        ]
        result = self.structure_checks.check(content)
        self.assertTrue(result['has_errors'] == False and len(result['warnings']) == 0)

    def test_nested_references(self):
        """Test nested cross-references."""
        content = [
            "See section 25.1309(a)(1)",
            "Refer to paragraph (a) of section 25.1309",
            "Under subsection (1) of paragraph (a)"
        ]
        result = self.structure_checks.check(content)
        self.assertTrue(result.success)

    def test_ambiguous_references(self):
        """Test ambiguous cross-references."""
        content = [
            "As mentioned in the previous section",
            "See the following paragraph",
            "Per the next section"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'previous'")
        self.assert_issue_contains(result, "Avoid using 'following'")
        self.assert_issue_contains(result, "Avoid using 'next'")

    def test_relative_references(self):
        """Test relative position references."""
        content = [
            "The above-mentioned requirements",
            "The below-listed items",
            "The herein contained provisions"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using relative position references")

    def test_compound_references(self):
        """Test compound reference phrases."""
        content = [
            "As mentioned earlier in this document",
            "As stated above in this section",
            "As discussed below in this chapter"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using compound reference phrases")

    def test_aviation_references(self):
        """Test aviation-specific references."""
        content = [
            "See AC 25-7D",
            "Refer to FAA Order 8900.1",
            "Under TSO-C23d"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)

    def test_regulatory_references(self):
        """Test regulatory document references."""
        content = [
            "See 14 CFR part 25",
            "Refer to 49 U.S.C. 44701",
            "Under 14 CFR § 25.1309"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertTrue(result.success)

    def test_mixed_references(self):
        """Test mixed valid and invalid references."""
        content = [
            "See section 25.1309",
            "As mentioned above",
            "Refer to paragraph (a)",
            "The aforementioned requirements"
        ]
        result = self.checker.check_cross_reference_usage(content)
        self.assertFalse(result.success)
        self.assert_issue_contains(result, "Avoid using 'above'")
        self.assert_issue_contains(result, "Avoid using 'aforementioned'")

if __name__ == '__main__':
    unittest.main()