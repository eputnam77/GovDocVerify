from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import split_sentences, count_words
from documentcheckertool.models import DocumentCheckResult
from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
import logging

logger = logging.getLogger(__name__)

class StructureChecks(BaseChecker):
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all structure-related checks."""
        logger.info(f"Running structure checks for document type: {doc_type}")
        
        paragraphs = document.paragraphs
        self._check_paragraph_length(paragraphs, results)
        self._check_sentence_length(paragraphs, results)
        self._check_section_balance(paragraphs, results)
        self._check_list_formatting(paragraphs, results)
    
    def _check_paragraph_length(self, paragraphs, results):
        """Check for overly long paragraphs."""
        MAX_WORDS = 150
        for i, para in enumerate(paragraphs):
            words = len(para.text.split())
            if words > MAX_WORDS:
                results.add_issue(
                    message=f"Paragraph exceeds {MAX_WORDS} words ({words} words)",
                    severity=Severity.MEDIUM,
                    line_number=i+1
                )
    
    def _check_sentence_length(self, paragraphs, results):
        """Check for overly long sentences."""
        MAX_WORDS = 30
        for i, para in enumerate(paragraphs):
            sentences = para.text.split('. ')
            for sentence in sentences:
                words = len(sentence.split())
                if words > MAX_WORDS:
                    results.add_issue(
                        message=f"Sentence exceeds {MAX_WORDS} words ({words} words)",
                        severity=Severity.LOW,
                        line_number=i+1
                    )
    
    def _check_section_balance(self, paragraphs, results):
        """Check for balanced section lengths."""
        current_section = []
        section_lengths = []
        
        for para in paragraphs:
            if para.style.name.startswith('Heading'):
                if current_section:
                    section_lengths.append(len(current_section))
                current_section = []
            else:
                current_section.append(para)
        
        # Add last section
        if current_section:
            section_lengths.append(len(current_section))
        
        # Check for significant imbalance
        if section_lengths:
            avg_length = sum(section_lengths) / len(section_lengths)
            for i, length in enumerate(section_lengths):
                if length > avg_length * 2:
                    results.add_issue(
                        message=f"Section {i+1} is significantly longer than average",
                        severity=Severity.LOW
                    )
    
    def _check_list_formatting(self, paragraphs, results):
        """Check for consistent list formatting."""
        list_markers = ['•', '-', '*', '1.', 'a.', 'i.']
        current_list_style = None
        
        for i, para in enumerate(paragraphs):
            text = para.text.strip()
            for marker in list_markers:
                if text.startswith(marker):
                    if current_list_style and marker != current_list_style:
                        results.add_issue(
                            message="Inconsistent list formatting detected",
                            severity=Severity.LOW,
                            line_number=i+1
                        )
                    current_list_style = marker
                    break
            else:
                current_list_style = None