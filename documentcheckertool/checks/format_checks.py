import re
from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.validation_patterns import (
    PHONE_PATTERNS,
    PLACEHOLDER_PATTERNS,
    DATE_PATTERNS
)
import logging
from typing import List, Dict, Any

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
        self._check_dash_spacing(paragraphs, results)

    def _check_date_formats(self, paragraphs: list, results: DocumentCheckResult):
        """Check for incorrect date formats."""
        for i, text in enumerate(paragraphs):
            if re.search(DATE_PATTERNS['incorrect'], text):
                results.add_issue(
                    message="Incorrect date format. Use YYYY-MM-DD format",
                    severity=Severity.MEDIUM,
                    line_number=i+1
                )

    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """Check for inconsistent phone number formats."""
        for i, text in enumerate(paragraphs):
            for pattern in PHONE_PATTERNS:
                if re.search(pattern, text):
                    results.add_issue(
                        message="Inconsistent phone number format",
                        severity=Severity.LOW,
                        line_number=i+1
                    )

    def _check_placeholders(self, paragraphs: list, results: DocumentCheckResult):
        """Check for placeholder text."""
        for i, text in enumerate(paragraphs):
            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    results.add_issue(
                        message="Placeholder text found",
                        severity=Severity.HIGH,
                        line_number=i+1
                    )

    def _check_dash_spacing(self, paragraphs: list, results: DocumentCheckResult):
        """Check for incorrect spacing around hyphens, en-dashes, and em-dashes."""
        dash_patterns = [
            (r'\s+[-–—]\s+', "Remove spaces around dash"),  # Spaces before and after
            (r'\s+[-–—](?!\s)', "Remove space before dash"),  # Space only before
            (r'(?<!\s)[-–—]\s+', "Remove space after dash")  # Space only after
        ]

        for i, text in enumerate(paragraphs):
            for pattern, message in dash_patterns:
                if matches := re.finditer(pattern, text):
                    for match in matches:
                        results.add_issue(
                            message=f"{message}: '{match.group(0)}'",
                            severity=Severity.LOW,
                            line_number=i+1,
                            suggestion=f"Replace with '{match.group(0).strip()}'"
                        )

class FormattingChecker(BaseChecker):
    """Checks for formatting issues in documents."""

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content for formatting issues."""
        issues = []

        # Split content into lines for line-by-line checking
        lines = content.split('\n')

        # Run all format checks
        issues.extend(self.check_punctuation(lines).issues)
        issues.extend(self.check_spacing(lines).issues)
        issues.extend(self.check_parentheses(lines).issues)
        issues.extend(self.check_section_symbol_usage(lines).issues)
        issues.extend(self.check_list_formatting(lines).issues)
        issues.extend(self.check_quotation_marks(lines).issues)

        return self.create_result(issues, success=len(issues) == 0)

    def check_punctuation(self, lines: List[str]) -> DocumentCheckResult:
        """Check for double periods and other punctuation issues."""
        issues = []
        for i, line in enumerate(lines, 1):
            if '..' in line:
                issues.append(self.create_issue(
                    f"Double periods found in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)

    def check_spacing(self, lines: List[str]) -> DocumentCheckResult:
        """Check for spacing issues."""
        issues = []
        for i, line in enumerate(lines, 1):
            if '  ' in line:  # Double space
                issues.append(self.create_issue(
                    f"Extra spaces found in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)

    def check_parentheses(self, lines: List[str]) -> DocumentCheckResult:
        """Check for unmatched parentheses."""
        issues = []
        for i, line in enumerate(lines, 1):
            open_count = line.count('(')
            close_count = line.count(')')
            if open_count != close_count:
                issues.append(self.create_issue(
                    f"Unmatched parentheses in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)

    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        issues = []
        for i, line in enumerate(lines, 1):
            if '§' in line and not re.search(r'§\s+\d', line):
                issues.append(self.create_issue(
                    f"Incorrect section symbol usage in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)

    def check_list_formatting(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent list formatting."""
        issues = []
        for i, line in enumerate(lines, 1):
            # Check numbered lists
            if re.match(r'^\d+[^.\s]', line):
                issues.append(self.create_issue(
                    f"Inconsistent list formatting in line {i}",
                    line_number=i
                ))
            # Check bullet lists
            if line.startswith('•') and not line.startswith('• '):
                issues.append(self.create_issue(
                    f"Inconsistent bullet spacing in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)

    def check_quotation_marks(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent quotation mark usage."""
        issues = []
        for i, line in enumerate(lines, 1):
            if '"' in line and '"' in line:
                issues.append(self.create_issue(
                    f"Inconsistent quotation marks in line {i}",
                    line_number=i
                ))
        return self.create_result(issues)