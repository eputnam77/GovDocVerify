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
        logger.debug(f"Checking date formats with {len(paragraphs)} paragraphs")
        logger.debug(f"DocumentCheckResult type: {type(results)}")
        logger.debug(f"DocumentCheckResult dir: {dir(results)}")
        logger.debug(f"Severity enum values: {[s.value for s in Severity]}")

        for i, text in enumerate(paragraphs):
            if re.search(DATE_PATTERNS['incorrect'], text):
                logger.debug(f"Found incorrect date format in line {i+1}: {text}")
                try:
                    results.add_issue(
                        "Incorrect date format. Use YYYY-MM-DD format",
                        Severity.ERROR,
                        i+1
                    )
                    logger.debug(f"Successfully added issue for line {i+1}")
                except Exception as e:
                    logger.error(f"Error adding issue: {str(e)}")
                    logger.error(f"Error type: {type(e)}")
                    raise

    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """Check for inconsistent phone number formats."""
        logger.debug(f"Checking phone numbers with {len(paragraphs)} paragraphs")
        for i, text in enumerate(paragraphs):
            for pattern in PHONE_PATTERNS:
                if re.search(pattern, text):
                    logger.debug(f"Found phone number in line {i+1}: {text}")
                    try:
                        results.add_issue(
                            "Inconsistent phone number format",
                            Severity.WARNING,
                            i+1
                        )
                        logger.debug(f"Successfully added issue for line {i+1}")
                    except Exception as e:
                        logger.error(f"Error adding issue: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        raise

    def _check_placeholders(self, paragraphs: list, results: DocumentCheckResult):
        """Check for placeholder text."""
        logger.debug(f"Checking placeholders with {len(paragraphs)} paragraphs")
        for i, text in enumerate(paragraphs):
            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"Found placeholder in line {i+1}: {text}")
                    try:
                        results.add_issue(
                            "Placeholder text found",
                            Severity.ERROR,
                            i+1
                        )
                        logger.debug(f"Successfully added issue for line {i+1}")
                    except Exception as e:
                        logger.error(f"Error adding issue: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        raise

    def _check_dash_spacing(self, paragraphs: list, results: DocumentCheckResult):
        """Check for incorrect spacing around hyphens, en-dashes, and em-dashes."""
        logger.debug(f"Checking dash spacing with {len(paragraphs)} paragraphs")
        dash_patterns = [
            (r'\s+[-–—]\s+', "Remove spaces around dash"),  # Spaces before and after
            (r'\s+[-–—](?!\s)', "Remove space before dash"),  # Space only before
            (r'(?<!\s)[-–—]\s+', "Remove space after dash")  # Space only after
        ]

        for i, text in enumerate(paragraphs):
            for pattern, message in dash_patterns:
                if matches := re.finditer(pattern, text):
                    for match in matches:
                        logger.debug(f"Found dash spacing issue in line {i+1}: {text}")
                        try:
                            results.add_issue(
                                f"{message}: '{match.group(0)}'",
                                Severity.WARNING,
                                i+1
                            )
                            logger.debug(f"Successfully added issue for line {i+1}")
                        except Exception as e:
                            logger.error(f"Error adding issue: {str(e)}")
                            logger.error(f"Error type: {type(e)}")
                            raise

class FormattingChecker(BaseChecker):
    """Checks for formatting issues in documents."""

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content for formatting issues."""
        logger.debug("Starting text formatting check")
        issues = []

        # Split content into lines for line-by-line checking
        lines = content.split('\n')
        logger.debug(f"Split content into {len(lines)} lines")

        # Run all format checks
        issues.extend(self.check_punctuation(lines).issues)
        issues.extend(self.check_spacing(lines).issues)
        issues.extend(self.check_parentheses(lines).issues)
        issues.extend(self.check_section_symbol_usage(lines).issues)
        issues.extend(self.check_list_formatting(lines).issues)
        issues.extend(self.check_quotation_marks(lines).issues)

        logger.debug(f"Found {len(issues)} total issues")
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_punctuation(self, lines: List[str]) -> DocumentCheckResult:
        """Check for double periods and other punctuation issues."""
        logger.debug("Checking punctuation")
        issues = []
        for i, line in enumerate(lines, 1):
            if '..' in line:
                logger.debug(f"Found double period in line {i}")
                issues.append(self.create_issue(
                    f"Double periods found in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_spacing(self, lines: List[str]) -> DocumentCheckResult:
        """Check for spacing issues."""
        logger.debug("Checking spacing")
        issues = []
        for i, line in enumerate(lines, 1):
            if '  ' in line:  # Double space
                logger.debug(f"Found extra spaces in line {i}")
                issues.append(self.create_issue(
                    f"Extra spaces found in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_parentheses(self, lines: List[str]) -> DocumentCheckResult:
        """Check for unmatched parentheses."""
        logger.debug("Checking parentheses")
        issues = []
        for i, line in enumerate(lines, 1):
            open_count = line.count('(')
            close_count = line.count(')')
            if open_count != close_count:
                logger.debug(f"Found unmatched parentheses in line {i}")
                issues.append(self.create_issue(
                    f"Unmatched parentheses in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        logger.debug("Checking section symbols")
        issues = []
        for i, line in enumerate(lines, 1):
            if '§' in line and not re.search(r'§\s+\d', line):
                logger.debug(f"Found incorrect section symbol usage in line {i}")
                issues.append(self.create_issue(
                    f"Incorrect section symbol usage in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_list_formatting(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent list formatting."""
        logger.debug("Checking list formatting")
        issues = []
        for i, line in enumerate(lines, 1):
            # Check numbered lists
            if re.match(r'^\d+[^.\s]', line):
                logger.debug(f"Found inconsistent list formatting in line {i}")
                issues.append(self.create_issue(
                    f"Inconsistent list formatting in line {i}",
                    i
                ))
            # Check bullet lists
            if line.startswith('•') and not line.startswith('• '):
                logger.debug(f"Found inconsistent bullet spacing in line {i}")
                issues.append(self.create_issue(
                    f"Inconsistent bullet spacing in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def check_quotation_marks(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent quotation mark usage."""
        logger.debug("Checking quotation marks")
        issues = []
        for i, line in enumerate(lines, 1):
            if '"' in line and '"' in line:
                logger.debug(f"Found inconsistent quotation marks in line {i}")
                issues.append(self.create_issue(
                    f"Inconsistent quotation marks in line {i}",
                    i
                ))
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)