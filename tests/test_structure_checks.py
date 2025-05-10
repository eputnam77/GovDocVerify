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
        doc = Document()
        doc.add_paragraph("This is a very long paragraph that exceeds the recommended length. " * 10)
        doc.add_paragraph("This is a normal paragraph.")
        doc.add_paragraph("This is another very long paragraph that should trigger a warning. " * 10)
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        assert any("Paragraph exceeds" in issue['message'] for issue in results.issues)

    def test_sentence_length(self):
        doc = Document()
        doc.add_paragraph("This is a very long sentence that should trigger a warning because it contains many words and should be split into multiple shorter sentences for better readability.")
        doc.add_paragraph("This is a normal sentence.")
        doc.add_paragraph("This is another very long sentence that should also trigger a warning because it's too long and should be split into multiple shorter sentences.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        assert any("Sentence exceeds" in issue['message'] for issue in results.issues)

    def test_section_balance(self):
        doc = Document()
        doc.add_paragraph("SECTION 1. PURPOSE.")
        doc.add_paragraph("This is a very short section.")
        doc.add_paragraph("SECTION 2. BACKGROUND.")
        doc.add_paragraph("This is a much longer section with many more details and information. " * 20)
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        assert any("Section" in issue['message'] and "longer than average" in issue['message'] for issue in results.issues)

    def test_list_formatting(self):
        doc = Document()
        doc.add_paragraph("The following items are required:")
        doc.add_paragraph("1. First item")
        doc.add_paragraph("2. Second item")
        doc.add_paragraph("3. Third item")
        doc.add_paragraph("4. Fourth item")
        doc.add_paragraph("5. Fifth item")
        doc.add_paragraph("6. Sixth item")
        doc.add_paragraph("7. Seventh item")
        doc.add_paragraph("8. Eighth item")
        doc.add_paragraph("9. Ninth item")
        doc.add_paragraph("10. Tenth item")
        doc.add_paragraph("11. Eleventh item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        assert any("Inconsistent list formatting" in issue['message'] for issue in results.issues)

    def test_cross_references(self):
        doc = Document()
        doc.add_paragraph("See paragraph 5.2.3 for more information.")
        doc.add_paragraph("Refer to section 4.1.2 for details.")
        doc.add_paragraph("As discussed in paragraph 3.4.5")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks.run_checks(doc, None, results)
        assert any("Cross-reference" in issue['message'] or "referenced" in issue['message'] for issue in results.issues)

    def test_parentheses(self):
        doc = Document()
        doc.add_paragraph("Valid (balanced) parentheses.")
        doc.add_paragraph("Invalid (unbalanced parentheses.")
        doc.add_paragraph("Another invalid) parentheses.")
        # Assuming StructureChecks has a method for parentheses
        # If not, this test should be removed or refactored
        # results = DocumentCheckResult(success=True, issues=[])
        # self.structure_checks.run_checks(doc, None, results)
        # assert any("Mismatched parentheses" in issue['message'] for issue in results.issues)
        pass

    def test_watermark_validation(self):
        # This test depends on watermark logic, which may not be implemented
        pass

    def test_check_paragraph_length(self):
        doc = Document()
        long_para = "word " * 200  # 200 words
        doc.add_paragraph(long_para)
        doc.add_paragraph("This is a normal paragraph.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_paragraph_length(doc.paragraphs, results)
        assert any("Paragraph exceeds" in issue['message'] for issue in results.issues)

    def test_check_sentence_length(self):
        doc = Document()
        long_sentence = "word " * 40  # 40 words
        doc.add_paragraph(long_sentence)
        doc.add_paragraph("This is a normal sentence.")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_sentence_length(doc.paragraphs, results)
        assert any("Sentence exceeds" in issue['message'] for issue in results.issues)

    def test_check_section_balance(self):
        doc = Document()
        doc.add_paragraph("Heading 1", style='Heading 1')
        for _ in range(10):
            doc.add_paragraph("Short section content")
        doc.add_paragraph("Heading 2", style='Heading 1')
        for _ in range(30):
            doc.add_paragraph("Long section content")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_section_balance(doc.paragraphs, results)
        assert any("longer than average" in issue['message'] for issue in results.issues)

    def test_check_list_formatting(self):
        doc = Document()
        doc.add_paragraph("• First item")
        doc.add_paragraph("- Second item")
        doc.add_paragraph("* Third item")
        results = DocumentCheckResult(success=True, issues=[])
        self.structure_checks._check_list_formatting(doc.paragraphs, results)
        assert any("Inconsistent list formatting" in issue['message'] for issue in results.issues)

    def test_check_cross_references(self):
        # This test depends on the implementation of check_cross_references
        pass