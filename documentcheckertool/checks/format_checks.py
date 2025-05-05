import re
from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
import logging

logger = logging.getLogger(__name__)

class FormatChecks(BaseChecker):
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all format-related checks."""
        logger.info(f"Running format checks for document type: {doc_type}")
        
        # Get all paragraph text
        paragraphs = [p.text for p in document.paragraphs]
        
        # Run specific format checks
        self._check_date_formats(paragraphs, results)
        self._check_phone_numbers(paragraphs, results)
        self._check_placeholders(paragraphs, results)
    
    def _check_date_formats(self, paragraphs: list, results: DocumentCheckResult):
        """Check for incorrect date formats."""
        incorrect_date_pattern = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        for i, text in enumerate(paragraphs):
            if re.search(incorrect_date_pattern, text):
                results.add_issue(
                    message="Incorrect date format found. Use YYYY-MM-DD format",
                    severity=Severity.MEDIUM,
                    line_number=i+1
                )
    
    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """Check for inconsistent phone number formats."""
        phone_patterns = [
            r'\b\d{3}[-\.]\d{3}[-\.]\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}[-\.]\d{4}\b'
        ]
        for i, text in enumerate(paragraphs):
            for pattern in phone_patterns:
                if re.search(pattern, text):
                    results.add_issue(
                        message="Inconsistent phone number format. Use (XXX) XXX-XXXX format",
                        severity=Severity.LOW,
                        line_number=i+1
                    )
    
    def _check_placeholders(self, paragraphs: list, results: DocumentCheckResult):
        """Check for placeholder text."""
        placeholder_patterns = [
            r'\bTBD\b',
            r'\bto be determined\b',
            r'\bXXX\b',
            r'\[.*?\]',
            r'\{.*?\}'
        ]
        for i, text in enumerate(paragraphs):
            for pattern in placeholder_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    results.add_issue(
                        message="Placeholder text found. Replace with actual content",
                        severity=Severity.HIGH,
                        line_number=i+1
                    )