import unittest
from test_base import TestBase

class TestStructureChecks(TestBase):
    """Test suite for document structure and readability checks."""
    
    def test_paragraph_length_check_valid(self):
        """Test paragraph length check with valid paragraphs."""
        content = [
            "This is a short paragraph that is within the acceptable length limit.",
            "This is another short paragraph that is within the acceptable length limit.",
            "This is a third short paragraph that is within the acceptable length limit."
        ]
        doc_path = self.create_test_docx(content, "valid_paragraph_length.docx")
        result = self.checker.check_paragraph_length(content)
        self.assert_no_issues(result)
    
    def test_paragraph_length_check_invalid(self):
        """Test paragraph length check with invalid paragraphs."""
        content = [
            "This is a very long paragraph that exceeds the acceptable length limit. " * 20,
            "This is another very long paragraph that exceeds the acceptable length limit. " * 20,
            "This is a third very long paragraph that exceeds the acceptable length limit. " * 20
        ]
        doc_path = self.create_test_docx(content, "invalid_paragraph_length.docx")
        result = self.checker.check_paragraph_length(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "paragraph length")
    
    def test_sentence_length_check_valid(self):
        """Test sentence length check with valid sentences."""
        content = [
            "This is a short sentence.",
            "This is another short sentence.",
            "This is a third short sentence."
        ]
        doc_path = self.create_test_docx(content, "valid_sentence_length.docx")
        result = self.checker.check_sentence_length(content)
        self.assert_no_issues(result)
    
    def test_sentence_length_check_invalid(self):
        """Test sentence length check with invalid sentences."""
        content = [
            "This is a very long sentence that exceeds the acceptable length limit and contains many words and phrases that make it difficult to read and understand, especially for readers who may not be familiar with the subject matter or who may be reading quickly through the document.",
            "This is another very long sentence that exceeds the acceptable length limit and contains many words and phrases that make it difficult to read and understand, especially for readers who may not be familiar with the subject matter or who may be reading quickly through the document."
        ]
        doc_path = self.create_test_docx(content, "invalid_sentence_length.docx")
        result = self.checker.check_sentence_length(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "sentence length")
    
    def test_readability_check_valid(self):
        """Test readability check with valid text."""
        content = [
            "The aircraft must meet the requirements.",
            "The pilot must maintain visual contact.",
            "The runway must be clear for landing."
        ]
        doc_path = self.create_test_docx(content, "valid_readability.docx")
        result = self.checker.check_readability(content)
        self.assert_no_issues(result)
    
    def test_readability_check_invalid(self):
        """Test readability check with invalid text."""
        content = [
            "The aeronautical conveyance apparatus must satisfy the stipulated prerequisites.",
            "The aviator must sustain ocular observation.",
            "The landing strip must be devoid of obstructions for touchdown."
        ]
        doc_path = self.create_test_docx(content, "invalid_readability.docx")
        result = self.checker.check_readability(content)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "readability")
    
    def test_508_compliance_check_valid(self):
        """Test 508 compliance check with valid document."""
        content = [
            "This is a document with proper formatting.",
            "All images have alt text.",
            "Tables have proper headers.",
            "Links have descriptive text."
        ]
        doc_path = self.create_test_docx(content, "valid_508_compliance.docx")
        result = self.checker.check_508_compliance(doc_path)
        self.assert_no_issues(result)
    
    def test_508_compliance_check_invalid(self):
        """Test 508 compliance check with invalid document."""
        content = [
            "This is a document with improper formatting.",
            "Images without alt text.",
            "Tables without headers.",
            "Links without descriptive text."
        ]
        doc_path = self.create_test_docx(content, "invalid_508_compliance.docx")
        result = self.checker.check_508_compliance(doc_path)
        self.assert_has_issues(result)
        self.assert_issue_contains(result, "508 compliance")

if __name__ == '__main__':
    unittest.main() 