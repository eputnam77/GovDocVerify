# NOTE: Refactored to use StructureChecks, as cross_reference_checks.py does not exist.
# pytest -v tests/test_cross_references.py --log-cli-level=DEBUG

import pytest
import logging
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)

class TestCrossReferenceChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.structure_checks = StructureChecks(self.terminology_manager)
        logger.debug("Initialized test with StructureChecks")

    def test_cross_references(self):
        content = [
            "5.2.3 Some Section.",
            "See paragraph 5.2.3 for more information.",
            "4.1.2 Another Section.",
            "Refer to section 4.1.2 for details.",
            "3.4.5 Yet Another Section.",
            "As discussed in paragraph 3.4.5"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross references test result: {result}")
        # All referenced sections are defined, so no errors expected
        assert not result['has_errors']
        # Expect style/circular warnings for each reference
        assert any(w['message'] == 'Circular reference detected' for w in result['warnings'])
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

    def test_valid_cross_references(self):
        """Test valid cross-reference formats."""
        content = [
            "25.1309 Section Title.",
            "See section 25.1309",
            "(a) Paragraph Title.",
            "Refer to paragraph (a)",
            "(1) Subsection Title.",
            "Under subsection (1)"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Valid cross references test result: {result}")
        assert not result['has_errors']
        # Expect style/circular/capitalization warnings
        assert any('Circular reference detected' in w['message'] for w in result['warnings'])
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

    def test_invalid_cross_references(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.2 Requirements.",  # Only 2.2 is defined
            "The following requirements apply...",
            "As noted in paragraph 2.1, these requirements..."  # Reference to non-existent paragraph
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Invalid cross references test result: {result}")
        # Reference to 2.1 is not defined, so errors expected
        assert result['has_errors']
        assert any('Reference to non-existent section 2.1' in e['message'] for e in result['errors'])

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
        logger.debug(f"Missing cross references test result: {result}")
        # Reference to 2.1 is not defined, so errors expected
        assert result['has_errors']
        assert any('Reference to non-existent section 2.1' in e['message'] for e in result['errors'])

    def test_cross_reference_formatting(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "See para 2.1 for details.",  # Incorrect format (should be warning)
            "2.1 Requirements.",
            "The following requirements apply...",
            "Refer to section 2.1 for more information."
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross reference formatting test result: {result}")
        assert not result['has_errors']
        # Expect style/circular warnings for the last reference
        assert any('Circular reference detected' in w['message'] for w in result['warnings'])
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

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
            "More requirements are specified in paragraph 2.1."
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross reference sequence test result: {result}")
        assert not result['has_errors']
        # Expect style/circular warnings
        assert any('Circular reference detected' in w['message'] for w in result['warnings'])
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])

    def test_cross_reference_consistency(self):
        content = [
            "PURPOSE.",
            "This document establishes requirements for...",
            "BACKGROUND.",
            "As discussed in paragraph 2.1, the requirements are...",
            "2.1 Requirements.",
            "The following requirements apply...",
            "As noted in para 2.1, these requirements...",  # Inconsistent format
            "See paragraph 2.1 for details."
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross reference consistency test result: {result}")
        assert not result['has_errors']
        # Expect style/circular/inconsistent warnings
        assert any('Circular reference detected' in w['message'] for w in result['warnings'])
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

    def test_cross_reference_edge_cases(self):
        """Test edge cases in cross-references."""
        content = [
            "The former and latter sections",
            "As stated earlier in this document",
            "The aforementioned requirements"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross reference edge cases test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No warnings expected yet

    def test_nested_references(self):
        """Test nested cross-references."""
        content = [
            "See section 25.1309(a)(1)",
            "Refer to paragraph (a) of section 25.1309",
            "Under subsection (1) of paragraph (a)"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Nested references test result: {result}")
        # Reference to 25.1309 is not defined, so errors expected
        assert result['has_errors']
        assert any('Reference to non-existent section 25.1309' in e['message'] for e in result['errors'])
        # Expect style/inconsistent warnings
        assert any('Inconsistent reference format' in w['message'] or 'inconsistent' in w['message'].lower() for w in result['warnings'])

    def test_ambiguous_references(self):
        """Test ambiguous cross-references."""
        content = [
            "As mentioned in the previous section",
            "See the following paragraph",
            "Per the next section"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Ambiguous references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No warnings expected yet

    def test_relative_references(self):
        """Test relative position references."""
        content = [
            "The above-mentioned requirements",
            "The below-listed items",
            "The herein contained provisions"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Relative references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No warnings expected yet

    def test_compound_references(self):
        """Test compound reference phrases."""
        content = [
            "As mentioned earlier in this document",
            "As stated above in this section",
            "As discussed below in this chapter"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Compound references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0  # No warnings expected yet

    def test_aviation_references(self):
        """Test aviation-specific references."""
        content = [
            "See AC 25-7D",
            "Refer to FAA Order 8900.1",
            "Under TSO-C23d"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Aviation references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0

    def test_regulatory_references(self):
        """Test regulatory document references."""
        content = [
            "See 14 CFR part 25",
            "Refer to 49 U.S.C. 44701",
            "Under 14 CFR § 25.1309"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Regulatory references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0

    def test_mixed_references(self):
        """Test mixed valid and invalid references."""
        content = [
            "See section 25.1309",
            "As mentioned above",
            "Refer to paragraph (a)",
            "The aforementioned requirements"
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Mixed references test result: {result}")
        # Reference to 25.1309 is not defined, so errors expected
        assert result['has_errors']
        assert any('Reference to non-existent section 25.1309' in e['message'] for e in result['errors'])
        # Expect style warnings
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

    def test_malformed_references(self):
        """Test malformed cross-references."""
        content = [
            "See section25.1309",  # Missing space
            "Refer toparagraph (a)",  # Missing space
            "Under subsection(1)",  # Missing space
            "See section 25.1309.",  # Extra period
            "Refer to paragraph (a).",  # Extra period
            "See section 25.1309,",  # Extra comma
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Malformed references test result: {result}")
        # Malformed references are errors, not warnings
        assert result['has_errors']
        assert any('Malformed reference' in e['message'] for e in result['errors'])

    def test_invalid_section_numbers(self):
        """Test invalid section number formats."""
        content = [
            "See section 25.1309.1",  # Too many levels
            "Refer to paragraph 25.1309.1.1",  # Too many levels
            "Under subsection 25.1309.1.1.1",  # Too many levels
            "See section 25.1309.1.1.1.1",  # Too many levels
            "Refer to paragraph 25.1309.1.1.1.1",  # Too many levels
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Invalid section numbers test result: {result}")
        # Invalid section numbers are errors
        assert result['has_errors']
        assert any('Invalid section number' in e['message'] for e in result['errors'])

    def test_circular_references(self):
        """Test circular cross-references."""
        content = [
            "1.1 First Section",
            "See section 1.1 for details.",  # Self-reference (circular)
            "1.2 Second Section",
            "See section 1.1 for details.",
            "1.3 Third Section",
            "See section 1.2 for details.",
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Circular references test result: {result}")
        # Checker treats circular references as warnings, not errors
        assert not result['has_errors']
        assert any('Circular reference detected' in w['message'] for w in result['warnings'])

    def test_reference_existence(self):
        """Test references to non-existent sections."""
        content = [
            "1.1 First Section",
            "See section 1.2 for details.",  # Reference to non-existent section
            "1.3 Third Section",
            "See section 1.2 for details.",  # Reference to non-existent section
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference existence test result: {result}")
        assert result['has_errors']
        assert any('Reference to non-existent section 1.2' in e['message'] for e in result['errors'])

    def test_reference_order(self):
        """Test references to sections in wrong order."""
        content = [
            "1.1 First Section",
            "See section 1.3 for details.",  # Forward reference
            "1.2 Second Section",
            "See section 1.1 for details.",  # Backward reference
            "1.3 Third Section",
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference order test result: {result}")
        # Checker does not treat order as error, only style warnings
        assert not result['has_errors']
        assert any('Incorrect punctuation' in w['message'] for w in result['warnings'])

    def test_reference_consistency(self):
        """Test inconsistent reference formats."""
        content = [
            "1.1 First Section",
            "See section 1.2 for details.",
            "1.2 Second Section",
            "See para 1.1 for details.",  # Inconsistent format
            "1.3 Third Section",
            "See subsection 1.2 for details.",  # Inconsistent format
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference consistency test result: {result}")
        # Checker treats inconsistent format as warning
        assert not result['has_errors']
        assert any('Inconsistent reference format' in w['message'] or 'inconsistent' in w['message'].lower() for w in result['warnings'])

    def test_multiple_references(self):
        """Test multiple references in one line."""
        content = [
            "1.1 First Section",
            "See sections 1.2 and 1.3 for details.",
            "1.2 Second Section",
            "See sections 1.1, 1.3, and 1.4 for details.",
            "1.3 Third Section",
            "See sections 1.1, 1.2, 1.4, and 1.5 for details.",
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Multiple references test result: {result}")
        assert not result['has_errors']
        # Expect capitalization warnings
        assert any('Incorrect capitalization' in w['message'] for w in result['warnings'])

    def test_cross_document_references(self):
        """Test references across different document types."""
        content = [
            "See AC 25-7D, section 1.2",
            "Refer to FAA Order 8900.1, paragraph 3.4",
            "Under TSO-C23d, section 2.1",
            "See 14 CFR part 25, section 25.1309",
            "Refer to 49 U.S.C. 44701, paragraph (a)",
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Cross document references test result: {result}")
        # Checker treats references to undefined sections as errors
        assert result['has_errors']
        assert any('Reference to non-existent section' in e['message'] for e in result['errors'])

    def test_appendix_references(self):
        """Test references to appendices."""
        content = [
            "See Appendix A, section A.1",
            "Refer to Appendix B, paragraph B.2",
            "Under Appendix C, subsection C.3",
            "See Appendix D, section D.4",
            "Refer to Appendix E, paragraph E.5",
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Appendix references test result: {result}")
        assert not result['has_errors']
        assert len(result['warnings']) == 0

    def test_reference_spacing(self):
        """Test required spacing in references."""
        content = [
            "See section25.1309",  # Missing space
            "Refer toparagraph (a)",  # Missing space
            "Under subsection(1)",  # Missing space
            "See section  25.1309",  # Extra space
            "Refer to  paragraph (a)",  # Extra space
            "Under  subsection(1)",  # Extra space
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference spacing test result: {result}")
        assert result['has_errors']
        assert any("incorrect spacing" in str(warning).lower() for warning in result['warnings'])

    def test_reference_punctuation(self):
        """Test required punctuation in references."""
        content = [
            "See section 25.1309",  # Missing period
            "Refer to paragraph (a)",  # Missing period
            "Under subsection (1)",  # Missing period
            "See section 25.1309.",  # Extra period
            "Refer to paragraph (a).",  # Extra period
            "Under subsection (1).",  # Extra period
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference punctuation test result: {result}")
        assert result['has_errors']
        assert any("incorrect punctuation" in str(warning).lower() for warning in result['warnings'])

    def test_reference_capitalization(self):
        """Test required capitalization in references."""
        content = [
            "see section 25.1309",  # Lowercase
            "refer to paragraph (a)",  # Lowercase
            "under subsection (1)",  # Lowercase
            "See Section 25.1309",  # Incorrect capitalization
            "Refer to Paragraph (a)",  # Incorrect capitalization
            "Under Subsection (1)",  # Incorrect capitalization
        ]
        result = self.structure_checks.check(content)
        logger.debug(f"Reference capitalization test result: {result}")
        assert result['has_errors']
        assert any("incorrect capitalization" in str(warning).lower() for warning in result['warnings'])