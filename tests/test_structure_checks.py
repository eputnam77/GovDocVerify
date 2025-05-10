# python -m pytest tests/test_structure_checks.py -v

import pytest
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.models import DocumentCheckResult
from docx import Document

class TestStructureChecks:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.terminology_manager = TerminologyManager()
        self.structure_checks = StructureChecks(self.terminology_manager)

    def test_paragraph_length(self):
        content = [
            "This is a very long paragraph that exceeds the recommended length. " * 10,
            "This is a normal paragraph.",
            "This is another very long paragraph that should trigger a warning. " * 10
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Paragraph is too long" in issue['message'] for issue in result['warnings'])

    def test_sentence_length(self):
        content = [
            "This is a very long sentence that should trigger a warning because it contains too many words and should be split into multiple shorter sentences for better readability.",
            "This is a normal sentence.",
            "This is another very long sentence that should also trigger a warning because it's too long and should be split into multiple shorter sentences."
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Sentence is too long" in issue['message'] for issue in result['warnings'])

    def test_section_balance(self):
        content = [
            "SECTION 1. PURPOSE.",
            "This is a very short section.",
            "SECTION 2. BACKGROUND.",
            "This is a much longer section with many more details and information. " * 20
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Section is too short" in issue['message'] for issue in result['warnings'])
        assert any("Section is too long" in issue['message'] for issue in result['warnings'])

    def test_list_formatting(self):
        content = [
            "The following items are required:",
            "1. First item",
            "2. Second item",
            "3. Third item",
            "4. Fourth item",
            "5. Fifth item",
            "6. Sixth item",
            "7. Seventh item",
            "8. Eighth item",
            "9. Ninth item",
            "10. Tenth item",
            "11. Eleventh item"
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("List is too long" in issue['message'] for issue in result['warnings'])

    def test_cross_references(self):
        content = [
            "See paragraph 5.2.3 for more information.",
            "Refer to section 4.1.2 for details.",
            "As discussed in paragraph 3.4.5"
        ]
        result = self.structure_checks.check(content)
        assert not result['has_errors']
        assert any("Cross-reference format" in issue['message'] for issue in result['warnings'])

    def test_parentheses(self):
        """Test parentheses checking."""
        content = [
            "Valid (balanced) parentheses.",
            "Invalid (unbalanced parentheses.",
            "Another invalid) parentheses."
        ]
        result = self.structure_checks.check_parentheses(content)
        assert not result['has_errors']
        assert any("Mismatched parentheses" in issue['message'] for issue in result['warnings'])

    def test_watermark_validation(self):
        """Test watermark validation for different document stages."""
        doc_with_watermark = """
        DRAFT - FOR INTERNAL FAA REVIEW
        Some document content.
        """
        result = self.structure_checks.check_watermark(doc_with_watermark.split('\n'), 'internal_review')
        assert not result['has_errors']
        assert any("Missing required watermark" in issue['message'] for issue in result['warnings'])

        doc_without_watermark = """
        Some document content without watermark.
        """
        result = self.structure_checks.check_watermark(doc_without_watermark.split('\n'), 'internal_review')
        assert not result['has_errors']
        assert any("Missing required watermark" in issue['message'] for issue in result['warnings'])

    def test_check_paragraph_length(self):
        doc = Document()
        # Add a long paragraph
        long_para = "word " * 200  # 200 words
        doc.add_paragraph(long_para)
        # Add a normal paragraph
        doc.add_paragraph("This is a normal paragraph.")

        results = DocumentCheckResult()
        self.structure_checks._check_paragraph_length(doc.paragraphs, results)
        assert len(results.issues) > 0
        assert any("Paragraph exceeds" in issue['message'] for issue in results.issues)

    def test_check_sentence_length(self):
        doc = Document()
        # Add a long sentence
        long_sentence = "word " * 40  # 40 words
        doc.add_paragraph(long_sentence)
        # Add a normal sentence
        doc.add_paragraph("This is a normal sentence.")

        results = DocumentCheckResult()
        self.structure_checks._check_sentence_length(doc.paragraphs, results)
        assert len(results.issues) > 0
        assert any("Sentence exceeds" in issue['message'] for issue in results.issues)

    def test_check_section_balance(self):
        doc = Document()
        # Add sections with unbalanced lengths
        doc.add_paragraph("Heading 1", style='Heading 1')
        for _ in range(10):
            doc.add_paragraph("Short section content")

        doc.add_paragraph("Heading 2", style='Heading 1')
        for _ in range(30):
            doc.add_paragraph("Long section content")

        results = DocumentCheckResult()
        self.structure_checks._check_section_balance(doc.paragraphs, results)
        assert len(results.issues) > 0
        assert any("significantly longer than average" in issue['message'] for issue in results.issues)

    def test_check_list_formatting(self):
        doc = Document()
        # Add inconsistently formatted list
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")

        results = DocumentCheckResult()
        self.structure_checks._check_list_formatting(doc.paragraphs, results)
        assert len(results.issues) > 0
        assert any("Inconsistent list formatting" in issue['message'] for issue in results.issues)

    def test_check_cross_references(self):
        doc = Document()
        # Add a table reference
        doc.add_paragraph("See Table 1 for details.")
        # Add a figure reference
        doc.add_paragraph("As shown in Figure 2.")
        # Add a section reference
        doc.add_paragraph("Refer to Section 1.2 for more information.")

        results = self.structure_checks.check_cross_references(doc)
        assert len(results.issues) > 0
        assert any("Missing reference" in issue['message'] for issue in results.issues)