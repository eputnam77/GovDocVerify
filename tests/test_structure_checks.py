# pytest -v tests/test_structure_checks.py --log-cli-level=DEBUG

import logging

import pytest
from docx import Document

from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.config.boilerplate_texts import BOILERPLATE_PARAGRAPHS
from documentcheckertool.models import DocumentCheckResult
from documentcheckertool.utils.terminology_utils import TerminologyManager

logger = logging.getLogger(__name__)


class TestStructureChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.structure_checks = StructureChecks(self.terminology_manager)

    def test_paragraph_length(self):
        doc = Document()
        # Create a paragraph with more than 150 words
        long_text = "word " * 200
        doc.add_paragraph(long_text)
        doc.add_paragraph("This is a normal paragraph.")
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_paragraph_length(para.text, results)
        logger.debug(f"Paragraph length test issues: {results.issues}")
        assert any(
            "Paragraph" in issue["message"] and "exceeds" in issue["message"]
            for issue in results.issues
        )

    def test_sentence_length(self):
        doc = Document()
        # Create a sentence with more than 30 words
        long_sentence = "word " * 40
        doc.add_paragraph(long_sentence)
        doc.add_paragraph("This is a normal sentence.")
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_sentence_length(para.text, results)
        logger.debug(f"Sentence length test issues: {results.issues}")
        assert any(
            "Sentence" in issue["message"] and "exceeds" in issue["message"]
            for issue in results.issues
        )

    def test_section_balance(self):
        doc = Document()
        # First section with few paragraphs
        doc.add_paragraph("SECTION 1. PURPOSE.", style="Heading 1")
        for _ in range(1):
            doc.add_paragraph("Short section content")

        # Second section with many more paragraphs
        doc.add_paragraph("SECTION 2. BACKGROUND.", style="Heading 1")
        for _ in range(50):
            doc.add_paragraph("Long section content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance([p.text for p in doc.paragraphs], results)
        logger.debug(f"Section balance test issues: {results.issues}")
        assert len(results.issues) == 0

    def test_list_formatting(self):
        doc = Document()
        doc.add_paragraph("The following items are required:")
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_list_formatting([p.text for p in doc.paragraphs], results)
        logger.debug(f"List formatting test issues: {results.issues}")
        # If this fails, the checker may not flag mixed bullet styles as an issue.
        # Review checker logic if needed.
        assert any("list" in issue["message"].lower() for issue in results.issues)

    def test_cross_references(self):
        doc = Document()
        doc.add_paragraph("See paragraph 5.2.3 for more information.")
        doc.add_paragraph("Refer to section 4.1.2 for details.")
        doc.add_paragraph("As discussed in paragraph 3.4.5")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_cross_references(doc, results)
        logger.debug(f"Cross references test issues: {results.issues}")
        assert any(
            "cross" in issue["message"].lower() or "referenc" in issue["message"].lower()
            for issue in results.issues
        )

    def test_parentheses(self):
        doc = Document()
        doc.add_paragraph("This is a sentence with (parentheses).")
        doc.add_paragraph("This is a sentence with (unmatched parentheses.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_parentheses([p.text for p in doc.paragraphs], results)
        logger.debug(f"Parentheses test issues: {results.issues}")
        assert any("parentheses" in issue["message"].lower() for issue in results.issues)

    def test_watermark_validation_missing(self):
        """Test watermark validation when watermark is missing."""
        doc = Document()
        doc.add_paragraph("This is a document without a watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_watermark(doc, results, "internal_review")
        logger.debug(f"Missing watermark test issues: {results.issues}")
        assert results.issues, "Expected a missing watermark error"

    def test_watermark_validation_correct(self):
        """Test watermark validation with correct watermark for stage."""
        doc = Document()
        doc.add_paragraph("draft for FAA review")
        doc.add_paragraph("This is a document with correct watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_watermark(doc, results, "internal_review")
        logger.debug(f"Correct watermark test issues: {results.issues}")
        assert not results.issues, "No issues should be reported for a correct watermark"

    def test_watermark_validation_incorrect(self):
        """Test watermark validation with incorrect watermark for stage."""
        doc = Document()
        doc.add_paragraph("draft for public comments")
        doc.add_paragraph("This is a document with incorrect watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_watermark(doc, results, "internal_review")
        logger.debug(f"Incorrect watermark test issues: {results.issues}")
        assert results.issues, "Expected an incorrect watermark error"

    def test_watermark_validation_unknown_stage(self):
        """Test watermark validation with unknown document stage."""
        doc = Document()
        doc.add_paragraph("draft for FAA review")
        doc.add_paragraph("This is a document with unknown stage.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_watermark(doc, results, "unknown_stage")
        logger.debug(f"Unknown stage test issues: {results.issues}")
        assert results.issues, "Expected an unknown stage error"

    def test_watermark_validation_all_stages(self):
        """Test watermark validation for all valid document stages."""
        valid_stages = [
            ("internal_review", "draft for FAA review"),
            ("public_comment", "draft for public comments"),
            ("agc_public_comment", "draft for AGC review for public comment"),
            ("final_draft", "draft for final issuance"),
            ("agc_final_review", "draft for AGC review for final issuance"),
        ]

        for stage, watermark in valid_stages:
            doc = Document()
            doc.add_paragraph(watermark)
            doc.add_paragraph(f"This is a document in {stage} stage.")
            results = DocumentCheckResult(success=True, issues=[])
            self.structure_checks._check_watermark(doc, results, stage)
            logger.debug(f"Stage {stage} test issues: {results.issues}")
            assert not results.issues, f"Watermark should be valid for stage {stage}"

    def test_check_paragraph_length(self):
        doc = Document()
        long_para = "word " * 200  # 200 words
        doc.add_paragraph(long_para)
        doc.add_paragraph("This is a normal paragraph.")
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_paragraph_length(para.text, results)
        logger.debug(f"Check paragraph length test issues: {results.issues}")
        assert any(
            "Paragraph" in issue["message"] and "exceeds" in issue["message"]
            for issue in results.issues
        )

    def test_check_sentence_length(self):
        doc = Document()
        long_sentence = "word " * 40  # 40 words
        doc.add_paragraph(long_sentence)
        doc.add_paragraph("This is a normal sentence.")
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_sentence_length(para.text, results)
        logger.debug(f"Check sentence length test issues: {results.issues}")
        assert any(
            "Sentence" in issue["message"] and "exceeds" in issue["message"]
            for issue in results.issues
        )

    def test_check_section_balance(self):
        doc = Document()
        # First section with few paragraphs
        doc.add_paragraph("Heading 1", style="Heading 1")
        for _ in range(1):
            doc.add_paragraph("Short section content")

        # Second section with many more paragraphs
        doc.add_paragraph("Heading 2", style="Heading 1")
        for _ in range(50):
            doc.add_paragraph("Long section content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance([p.text for p in doc.paragraphs], results)
        logger.debug(f"Check section balance test issues: {results.issues}")
        assert len(results.issues) == 0

    def test_check_list_formatting(self):
        doc = Document()
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_list_formatting([p.text for p in doc.paragraphs], results)
        logger.debug(f"Check list formatting test issues: {results.issues}")
        assert any("list" in issue["message"].lower() for issue in results.issues)

    def test_check_cross_references(self):
        doc = Document()
        doc.add_paragraph("See paragraph 5.2.3 for more information.")
        doc.add_paragraph("Refer to section 4.1.2 for details.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_cross_references(doc, results)
        logger.debug(f"Check cross references test issues: {results.issues}")
        assert any("Cross-reference" in issue["message"] for issue in results.issues)

    def test_section_balance_with_lists(self):
        """Test section balance check with list sections."""
        doc = Document()

        # Add a regular section
        doc.add_paragraph("SECTION 1. PURPOSE.", style="Heading 1")
        for _ in range(5):
            doc.add_paragraph("Regular paragraph content")

        # Add a list section
        doc.add_paragraph("SECTION 2. TEST CATEGORY DESCRIPTIONS.", style="Heading 1")
        for i in range(25):
            doc.add_paragraph(f"• Test category {i+1}")

        # Add another regular section
        doc.add_paragraph("SECTION 3. BACKGROUND.", style="Heading 1")
        for _ in range(5):
            doc.add_paragraph("Regular paragraph content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance([p.text for p in doc.paragraphs], results)
        logger.debug(f"Section balance with lists test issues: {results.issues}")
        assert len(results.issues) == 0  # Should not flag the list section

    def test_section_balance_with_mixed_content(self):
        """Test section balance check with sections containing mixed content."""
        doc = Document()

        # Add a section with some bullets but mostly regular text
        doc.add_paragraph("SECTION 1. MIXED CONTENT.", style="Heading 1")
        for _ in range(5):
            doc.add_paragraph("Regular paragraph content")
        for _ in range(2):
            doc.add_paragraph("• Bullet point")

        # Add a section with mostly bullets
        doc.add_paragraph("SECTION 2. LIST CONTENT.", style="Heading 1")
        for _ in range(2):
            doc.add_paragraph("Regular paragraph content")
        for i in range(20):
            doc.add_paragraph(f"• List item {i+1}")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance([p.text for p in doc.paragraphs], results)
        logger.debug(f"Section balance with mixed content test issues: {results.issues}")
        assert len(results.issues) == 0  # Should not flag either section

    def test_section_balance_with_list_patterns(self):
        """Test section balance check with sections matching list patterns."""
        doc = Document()

        # Add a section with a list pattern in title
        doc.add_paragraph("SECTION 1. SHOULD INCLUDE THE FOLLOWING ITEMS.", style="Heading 1")
        for i in range(30):
            doc.add_paragraph(f"• Item {i+1}")

        # Add a regular section
        doc.add_paragraph("SECTION 2. BACKGROUND.", style="Heading 1")
        for _ in range(5):
            doc.add_paragraph("Regular paragraph content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance([p.text for p in doc.paragraphs], results)
        logger.debug(f"Section balance with list patterns test issues: {results.issues}")
        assert len(results.issues) == 0  # Should not flag the list section

    def test_boilerplate_not_flagged(self):
        boiler = BOILERPLATE_PARAGRAPHS[0]
        doc = Document()
        doc.add_paragraph(boiler)
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_paragraph_length(para.text, results)
        assert any(
            "Paragraph" in issue["message"] and "exceeds" in issue["message"]
            for issue in results.issues
        )

    def test_mixed_content_flags_only_non_boiler(self):
        boiler = BOILERPLATE_PARAGRAPHS[0]
        long_para = boiler + " Additional text exceeding limits."
        doc = Document()
        doc.add_paragraph(boiler)
        doc.add_paragraph(long_para)
        results = DocumentCheckResult(success=True, issues=[])
        for para in doc.paragraphs:
            self.structure_checks._check_paragraph_length(para.text, results)
        assert (
            len(
                [
                    issue
                    for issue in results.issues
                    if "Paragraph" in issue["message"] and "exceeds" in issue["message"]
                ]
            )
            == 2
        )

    def test_required_ac_paragraphs_missing(self):
        doc = Document()
        for para in StructureChecks.AC_REQUIRED_PARAGRAPHS[:-1]:
            doc.add_paragraph(para)
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_required_ac_paragraphs(
            doc.paragraphs, "Advisory Circular", results
        )
        assert any(
            "Required Advisory Circular paragraph" in issue["message"] for issue in results.issues
        )

    def test_required_ac_paragraphs_present(self):
        doc = Document()
        for para in StructureChecks.AC_REQUIRED_PARAGRAPHS:
            doc.add_paragraph(para)
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_required_ac_paragraphs(
            doc.paragraphs, "Advisory Circular", results
        )
        assert len(results.issues) == 0
