# pytest -v tests/test_structure_checks.py --log-cli-level=DEBUG

import pytest
import logging
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.models import DocumentCheckResult, Severity
from docx import Document

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
        self.structure_checks._check_paragraph_length(doc.paragraphs, results)
        logger.debug(f"Paragraph length test issues: {results.issues}")
        assert any("Paragraph exceeds" in issue['message'] for issue in results.issues)

    def test_sentence_length(self):
        doc = Document()
        # Create a sentence with more than 30 words
        long_sentence = "word " * 40
        doc.add_paragraph(long_sentence)
        doc.add_paragraph("This is a normal sentence.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_sentence_length(doc.paragraphs, results)
        logger.debug(f"Sentence length test issues: {results.issues}")
        assert any("Sentence exceeds" in issue['message'] for issue in results.issues)

    def test_section_balance(self):
        doc = Document()
        # First section with few paragraphs
        doc.add_paragraph("SECTION 1. PURPOSE.", style='Heading 1')
        for _ in range(1):
            doc.add_paragraph("Short section content")

        # Second section with many more paragraphs
        doc.add_paragraph("SECTION 2. BACKGROUND.", style='Heading 1')
        for _ in range(50):
            doc.add_paragraph("Long section content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance(doc.paragraphs, results)
        logger.debug(f"Section balance test issues: {results.issues}")
        assert len(results.issues) == 0

    def test_list_formatting(self):
        doc = Document()
        doc.add_paragraph("The following items are required:")
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        logger.debug(f"List formatting test issues: {results.issues}")
        assert any("Inconsistent list formatting" in issue['message'] for issue in results.issues)

    def test_cross_references(self):
        doc = Document()
        doc.add_paragraph("See paragraph 5.2.3 for more information.")
        doc.add_paragraph("Refer to section 4.1.2 for details.")
        doc.add_paragraph("As discussed in paragraph 3.4.5")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        logger.debug(f"Cross references test issues: {results.issues}")
        assert any("Cross-reference" in issue['message'] or "referenced" in issue['message'] for issue in results.issues)

    def test_parentheses(self):
        doc = Document()
        doc.add_paragraph("This is a sentence with (parentheses).")
        doc.add_paragraph("This is a sentence with (unmatched parentheses.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        logger.debug(f"Parentheses test issues: {results.issues}")
        assert any("Unmatched parentheses" in issue['message'] for issue in results.issues)

    def test_watermark_validation_missing(self):
        """Test watermark validation when watermark is missing."""
        doc = Document()
        doc.add_paragraph("This is a document without a watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, "internal_review", results)
        logger.debug(f"Missing watermark test issues: {results.issues}")
        assert any("Document is missing required watermark" in issue['message'] for issue in results.issues)

    def test_watermark_validation_correct(self):
        """Test watermark validation with correct watermark for stage."""
        doc = Document()
        doc.add_paragraph("DRAFT - FOR INTERNAL FAA REVIEW")
        doc.add_paragraph("This is a document with correct watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, "internal_review", results)
        logger.debug(f"Correct watermark test issues: {results.issues}")
        assert any("Document is missing required watermark" in issue['message'] for issue in results.issues)

    def test_watermark_validation_incorrect(self):
        """Test watermark validation with incorrect watermark for stage."""
        doc = Document()
        doc.add_paragraph("DRAFT - FOR PUBLIC COMMENTS")
        doc.add_paragraph("This is a document with incorrect watermark.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, "internal_review", results)
        logger.debug(f"Incorrect watermark test issues: {results.issues}")
        assert any("Document is missing required watermark" in issue['message'] for issue in results.issues)

    def test_watermark_validation_unknown_stage(self):
        """Test watermark validation with unknown document stage."""
        doc = Document()
        doc.add_paragraph("DRAFT - FOR INTERNAL FAA REVIEW")
        doc.add_paragraph("This is a document with unknown stage.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, "unknown_stage", results)
        logger.debug(f"Unknown stage test issues: {results.issues}")
        assert any("Document is missing required watermark" in issue['message'] for issue in results.issues)

    def test_watermark_validation_all_stages(self):
        """Test watermark validation for all valid document stages."""
        valid_stages = [
            ("internal_review", "DRAFT - FOR INTERNAL FAA REVIEW"),
            ("public_comment", "DRAFT - FOR PUBLIC COMMENTS"),
            ("agc_public_comment", "DRAFT - FOR AGC REVIEW OF PUBLIC COMMENTS"),
            ("final_draft", "DRAFT - FOR FINAL ISSUANCE"),
            ("agc_final_review", "DRAFT - FOR AGC REVIEW OF FINAL ISSUANCE")
        ]

        for stage, watermark in valid_stages:
            doc = Document()
            doc.add_paragraph(watermark)
            doc.add_paragraph(f"This is a document in {stage} stage.")
            results = DocumentCheckResult(success=True, issues=[])
            self.structure_checks.run_checks(doc, stage, results)
            logger.debug(f"Stage {stage} test issues: {results.issues}")
            assert any("Document is missing required watermark" in issue['message'] for issue in results.issues)

    def test_check_paragraph_length(self):
        doc = Document()
        long_para = "word " * 200  # 200 words
        doc.add_paragraph(long_para)
        doc.add_paragraph("This is a normal paragraph.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_paragraph_length(doc.paragraphs, results)
        logger.debug(f"Check paragraph length test issues: {results.issues}")
        assert any("Paragraph exceeds" in issue['message'] for issue in results.issues)

    def test_check_sentence_length(self):
        doc = Document()
        long_sentence = "word " * 40  # 40 words
        doc.add_paragraph(long_sentence)
        doc.add_paragraph("This is a normal sentence.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_sentence_length(doc.paragraphs, results)
        logger.debug(f"Check sentence length test issues: {results.issues}")
        assert any("Sentence exceeds" in issue['message'] for issue in results.issues)

    def test_check_section_balance(self):
        doc = Document()
        # First section with few paragraphs
        doc.add_paragraph("Heading 1", style='Heading 1')
        for _ in range(1):
            doc.add_paragraph("Short section content")

        # Second section with many more paragraphs
        doc.add_paragraph("Heading 2", style='Heading 1')
        for _ in range(50):
            doc.add_paragraph("Long section content")

        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance(doc.paragraphs, results)
        logger.debug(f"Check section balance test issues: {results.issues}")
        assert len(results.issues) == 0

    def test_check_list_formatting(self):
        doc = Document()
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_list_formatting(doc.paragraphs, results)
        logger.debug(f"Check list formatting test issues: {results.issues}")
        assert any("Inconsistent list formatting" in issue['message'] for issue in results.issues)

    def test_check_cross_references(self):
        doc = Document()
        doc.add_paragraph("See paragraph 5.2.3 for more information.")
        doc.add_paragraph("Refer to section 4.1.2 for details.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_cross_references(doc, results)
        logger.debug(f"Check cross references test issues: {results.issues}")
        assert any("Cross-reference" in issue['message'] for issue in results.issues)