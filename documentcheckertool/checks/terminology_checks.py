from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
import re
import logging

logger = logging.getLogger(__name__)

class TerminologyChecks(BaseChecker):
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all terminology-related checks."""
        logger.info(f"Running terminology checks for document type: {doc_type}")
        
        text_content = [p.text for p in document.paragraphs]
        self._check_abbreviations(text_content, results)
        self._check_consistency(text_content, results)
        self._check_forbidden_terms(text_content, results)
    
    def _check_abbreviations(self, paragraphs, results):
        """Check for undefined abbreviations."""
        abbr_pattern = r'\b[A-Z]{2,}\b'
        defined_abbrs = set()
        
        for i, text in enumerate(paragraphs):
            # Look for definitions
            definitions = re.finditer(r'\b([A-Z]{2,})\s*\(([^)]+)\)', text)
            for match in definitions:
                defined_abbrs.add(match.group(1))
            
            # Skip if being defined in this line
            if any(re.search(fr'{abbr}\s*\([^)]+\)', text) for abbr in re.findall(abbr_pattern, text)):
                continue
                
            # Check for undefined abbreviations
            for abbr in re.findall(abbr_pattern, text):
                if abbr not in defined_abbrs:
                    results.add_issue(
                        message=f"Undefined abbreviation: {abbr}",
                        severity=Severity.MEDIUM,
                        line_number=i+1
                    )
    
    def _check_consistency(self, paragraphs, results):
        """Check for consistent terminology usage."""
        # Use raw strings for regex patterns
        variants = {
            r'website': ['web site', 'web-site'],
            r'online': ['on-line', 'on line'],
            r'email': ['e-mail', 'Email'],
        }
        
        for i, text in enumerate(paragraphs):
            for standard, variants_list in variants.items():
                pattern = fr'\b{standard}\b'
                for variant in variants_list:
                    if re.search(variant, text, re.IGNORECASE):
                        results.add_issue(
                            message=f"Inconsistent terminology: use '{standard}' instead of '{variant}'",
                            severity=Severity.LOW,
                            line_number=i+1
                        )
    
    def _check_forbidden_terms(self, paragraphs, results):
        """Check for forbidden or discouraged terms."""
        # Use raw strings for regex patterns
        forbidden_terms = {
            r'must': "Consider using 'shall' for requirements",
            r'should': "Use 'shall' for requirements or 'may' for recommendations",
            r'clearly': "Avoid using 'clearly' as it's subjective",
            r'obviously': "Avoid using 'obviously' as it's subjective",
        }
        
        for i, text in enumerate(paragraphs):
            for term, message in forbidden_terms.items():
                pattern = fr'\b{term}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    results.add_issue(
                        message=message,
                        severity=Severity.MEDIUM,
                        line_number=i+1
                    )