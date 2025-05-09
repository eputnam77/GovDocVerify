from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import split_sentences, count_words
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.validation_patterns import HEADING_PATTERNS
from docx import Document
from .base_checker import BaseChecker
import re
import logging

logger = logging.getLogger(__name__)

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)
    return wrapper

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

    def _extract_paragraph_numbering(self, doc: Document) -> List[tuple]:
        """Extract paragraph numbering from headings."""
        heading_structure = []
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                if match := re.match(r'^([A-Z]?\.?\d+(?:\.\d+)*)\s+(.+)$', para.text):
                    heading_structure.append((match.group(1), match.group(2)))
        return heading_structure

    @profile_performance
    def check_cross_references(self, doc_path: str) -> DocumentCheckResult:
        """Check for missing cross-referenced elements in the document."""
        try:
            doc = Document(doc_path)
        except Exception as e:
            logger.error(f"Error reading the document: {e}")
            return DocumentCheckResult(success=False, issues=[{'error': str(e)}], details={})

        heading_structure = self._extract_paragraph_numbering(doc)
        valid_sections = {number for number, _ in heading_structure}
        tables = set()
        figures = set()
        issues = []

        skip_patterns = [
            r'(?:U\.S\.C\.|USC)\s+(?:§+\s*)?(?:Section|section)?\s*\d+',
            r'Section\s+\d+(?:\([a-z]\))*\s+of\s+(?:the\s+)?(?:United States Code|U\.S\.C\.)',
            r'Section\s+\d+(?:\([a-z]\))*\s+of\s+Title\s+\d+',
            r'(?:Section|§)\s*\d+(?:\([a-z]\))*\s+of\s+the\s+Act',
            r'Section\s+\d+\([a-z]\)',
            r'§\s*\d+\([a-z]\)',
            r'\d+\s*(?:CFR|C\.F\.R\.)',
            r'Part\s+\d+(?:\.[0-9]+)*\s+of\s+Title\s+\d+',
            r'Public\s+Law\s+\d+[-–]\d+',
            r'Title\s+\d+,\s+Section\s+\d+(?:\([a-z]\))*',
            r'\d+\s+U\.S\.C\.\s+\d+(?:\([a-z]\))*',
        ]
        skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)

        try:
            # Extract tables and figures
            for para in doc.paragraphs:
                text = para.text.strip() if hasattr(para, 'text') else ''
                
                if text.lower().startswith('table'):
                    matches = [
                        re.match(r'^table\s+(\d{1,2}(?:-\d+)?)\b', text, re.IGNORECASE),
                        re.match(r'^table\s+(\d{1,2}(?:\.\d+)?)\b', text, re.IGNORECASE)
                    ]
                    for match in matches:
                        if match:
                            tables.add(match.group(1))

                if text.lower().startswith('figure'):
                    matches = [
                        re.match(r'^figure\s+(\d{1,2}(?:-\d+)?)\b', text, re.IGNORECASE),
                        re.match(r'^figure\s+(\d{1,2}(?:\.\d+)?)\b', text, re.IGNORECASE)
                    ]
                    for match in matches:
                        if match:
                            figures.add(match.group(1))

            # Check references
            for para in doc.paragraphs:
                para_text = para.text.strip() if hasattr(para, 'text') else ''
                if not para_text or skip_regex.search(para_text):
                    continue

                # Table, Figure, and Section reference checks
                self._check_table_references(para_text, tables, issues)
                self._check_figure_references(para_text, figures, issues)
                self._check_section_references(para_text, valid_sections, skip_regex, issues)

        except Exception as e:
            logger.error(f"Error processing cross references: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{'type': 'error', 'message': f"Error processing cross references: {str(e)}"}],
                details={}
            )

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details={
                'total_tables': len(tables),
                'total_figures': len(figures),
                'found_tables': sorted(list(tables)),
                'found_figures': sorted(list(figures)),
                'heading_structure': heading_structure,
                'valid_sections': sorted(list(valid_sections))
            }
        )

    def _check_table_references(self, para_text: str, tables: set, issues: list):
        """Check table references."""
        table_refs = re.finditer(
            r'(?:see|in|refer to)?\s*(?:table|Table)\s+(\d{1,2}(?:[-\.]\d+)?)\b', 
            para_text
        )
        for match in table_refs:
            ref = match.group(1)
            if ref not in tables:
                issues.append({
                    'type': 'Table',
                    'reference': ref,
                    'context': para_text,
                    'message': f"Referenced Table {ref} not found in document"
                })

    def _check_figure_references(self, para_text: str, figures: set, issues: list):
        """Check figure references."""
        figure_refs = re.finditer(
            r'(?:see|in|refer to)?\s*(?:figure|Figure)\s+(\d{1,2}(?:[-\.]\d+)?)\b', 
            para_text
        )
        for match in figure_refs:
            ref = match.group(1)
            if ref not in figures:
                issues.append({
                    'type': 'Figure',
                    'reference': ref,
                    'context': para_text,
                    'message': f"Referenced Figure {ref} not found in document"
                })

    def _check_section_references(self, para_text: str, valid_sections: set, skip_regex: re.Pattern, issues: list):
        """Check section references."""
        if skip_regex.search(para_text):
            return
            
        section_refs = re.finditer(
            r'(?:paragraph|section|appendix)\s+([A-Z]?\.?\d+(?:\.\d+)*)',
            para_text,
            re.IGNORECASE
        )

        for match in section_refs:
            ref = match.group(1).strip('.')
            if ref not in valid_sections:
                found = False
                for valid_section in valid_sections:
                    if valid_section.strip('.') == ref.strip('.'):
                        found = True
                        break
                
                if not found:
                    issues.append({
                        'type': 'Paragraph',
                        'reference': ref,
                        'context': para_text,
                        'message': f"Confirm paragraph {ref} referenced in '{para_text}' exists in the document"
                    })