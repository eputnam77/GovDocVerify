import os
import unittest

from test_base import TestBase


class TestStructureChecks(TestBase):
    """Test suite for document structure and readability checks."""

    def test_paragraph_length_check_valid(self):
        """Test paragraph length check with valid paragraphs."""
        content = [
            "This is a short paragraph that is within the acceptable length limit.",
            "This is another short paragraph that is within the acceptable length limit.",
            "This is a third short paragraph that is within the acceptable length limit.",
        ]
        self.create_test_docx(content, "valid_paragraph_length.docx")
        result = self.checker.check_paragraph_length(content)
        self.assert_no_issues(result)

    def test_paragraph_length_check_invalid(self):
        """Test paragraph length check with invalid paragraphs."""
        long_para = " ".join([f"Sentence {i}." for i in range(7)])
        content = [long_para, long_para, long_para]
        self.create_test_docx(content, "invalid_paragraph_length.docx")
        result = self.checker.check_paragraph_length(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "exceeds length limits")

    def test_sentence_length_check_valid(self):
        """Test sentence length check with valid sentences."""
        content = [
            "This is a short sentence.",
            "This is another short sentence.",
            "This is a third short sentence.",
        ]
        self.create_test_docx(content, "valid_sentence_length.docx")
        result = self.checker.check_sentence_length(content)
        self.assert_no_issues(result)

    def test_sentence_length_check_invalid(self):
        """Test sentence length check with invalid sentences."""
        content = [
            (
                "This is a very long sentence that exceeds the acceptable length limit and "
                "contains many words and phrases that make it difficult to read and understand, "
                "especially for readers who may not be familiar with the subject matter or "
                "who may be reading quickly through the document."
            ),
            (
                "This is another very long sentence that exceeds the acceptable length limit and "
                "contains many words and phrases that make it difficult to read and understand, "
                "especially for readers who may not be familiar with the subject matter or "
                "who may be reading quickly through the document."
            ),
        ]
        self.create_test_docx(content, "invalid_sentence_length.docx")
        result = self.checker.check_sentence_length(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "exceeds the 30-word limit")

    def test_readability_check_valid(self):
        """Test readability check with valid text."""
        content = [
            "The cat sat on the mat.",
            "The dog barked.",
            "It rained today.",
        ]
        self.create_test_docx(content, "valid_readability.docx")
        result = self.checker.check_readability(content)
        self.assert_no_issues(result)

    def test_readability_check_invalid(self):
        """Test readability check with invalid text."""
        content = [
            "The aeronautical conveyance apparatus must satisfy the stipulated prerequisites.",
            "The aviator must sustain ocular observation.",
            "The landing strip must be devoid of obstructions for touchdown.",
        ]
        self.create_test_docx(content, "invalid_readability.docx")
        result = self.checker.check_readability(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "readability")

    def test_508_compliance_valid(self):
        """Test Section 508 compliance check with valid document."""
        doc_path = os.path.join(self.test_data_dir, "valid_508_compliance.docx")
        result = self.checker.check_section_508_compliance(doc_path)
        self.assert_no_issues(result)

    def test_508_compliance_invalid(self):
        """Test Section 508 compliance check with invalid document."""
        doc_path = os.path.join(self.test_data_dir, "invalid_508_compliance.docx")
        result = self.checker.check_section_508_compliance(doc_path)
        self.assert_has_issues(result)


if __name__ == "__main__":
    unittest.main()
