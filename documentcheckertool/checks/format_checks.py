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

        # Pattern for incorrect date formats (MM/DD/YYYY, YYYY-MM-DD, etc.)
        incorrect_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
            r'\d{1,2}\.\d{1,2}\.\d{4}'  # MM.DD.YYYY
        ]

        for i, text in enumerate(paragraphs):
            for pattern in incorrect_patterns:
                if re.search(pattern, text):
                    logger.debug(f"Found incorrect date format in line {i+1}: {text}")
                    try:
                        results.add_issue(
                            "Incorrect date format. Use Month Day, Year format (e.g., May 11, 2025)",
                            Severity.ERROR,
                            i+1
                        )
                        logger.debug(f"Successfully added issue for line {i+1}")
                        break  # Only add one issue per line
                    except Exception as e:
                        logger.error(f"Error adding issue: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        raise

    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """Check for inconsistent phone number formats (consistency among formats, not a single standard)."""
        logger.debug(f"Checking phone numbers with {len(paragraphs)} paragraphs")

        # Define regexes for common phone number formats
        format_patterns = [
            (r'^\d{3}-\d{3}-\d{4}$', 'dash'),
            (r'^\(\d{3}\) \d{3}-\d{4}$', 'paren-dash'),
            (r'^\d{3}\.\d{3}\.\d{4}$', 'dot'),
            (r'^\d{10}$', 'plain'),
            (r'^\d{3} \d{3} \d{4}$', 'space'),
        ]

        # General phone number regex: matches (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890, 123 456 7890
        phone_regex = re.compile(r'(\(\d{3}\) \d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}|\d{10}|\d{3} \d{3} \d{4})')

        phone_numbers = []
        formats = set()
        for i, text in enumerate(paragraphs):
            for match in phone_regex.finditer(text):
                phone = match.group(0)
                phone_numbers.append((phone, i+1))
                # Classify format
                fmt = 'other'
                for pattern, label in format_patterns:
                    if re.match(pattern, phone):
                        fmt = label
                        break
                formats.add(fmt)

        # If more than one unique format, flag all as inconsistent
        if len(formats) > 1 and phone_numbers:
            for _, line_num in phone_numbers:
                logger.debug(f"Flagging inconsistent phone number format in line {line_num}")
                try:
                    results.add_issue(
                        "Inconsistent phone number format",
                        Severity.WARNING,
                        line_num
                    )
                    logger.debug(f"Successfully added issue for line {line_num}")
                except Exception as e:
                    logger.error(f"Error adding issue: {str(e)}")
                    logger.error(f"Error type: {type(e)}")
                    raise
        # Set success based on whether any issues were found
        results.success = len(results.issues) == 0

    def _check_placeholders(self, paragraphs: list, results: DocumentCheckResult):
        """Check for placeholder text."""
        logger.debug(f"Checking placeholders with {len(paragraphs)} paragraphs")
        placeholder_patterns = [
            r'\b(TODO|FIXME|XXX|HACK|NOTE|REVIEW|DRAFT):',
            r'\b(Add|Update|Review|Fix|Complete)\s+.*\b(here|this|needed)\b',
            r'\b(Placeholder|Temporary|Draft)\b'
        ]

        for i, text in enumerate(paragraphs):
            for pattern in placeholder_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"Found placeholder in line {i+1}: {text}")
                    try:
                        results.add_issue(
                            "Placeholder text found",
                            Severity.ERROR,
                            i+1
                        )
                        logger.debug(f"Successfully added issue for line {i+1}")
                        break  # Only add one issue per line
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

        # Set success based on whether any issues were found
        results.success = len(results.issues) == 0

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
        issues.extend(self.check_placeholders(lines).issues)  # Add placeholder check

        logger.debug(f"Found {len(issues)} total issues")
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.ERROR if issues else None, issues=issues)

    def check_punctuation(self, lines: List[str]) -> DocumentCheckResult:
        """Check for double periods and other punctuation issues."""
        logger.debug("Checking punctuation")
        issues = []
        for i, line in enumerate(lines, 1):
            if '..' in line:
                logger.debug(f"Found double period in line {i}")
                issues.append({
                    "message": f"Double periods found in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_spacing(self, lines: List[str]) -> DocumentCheckResult:
        """Check for spacing issues."""
        logger.debug("Checking spacing")
        issues = []
        for i, line in enumerate(lines, 1):
            if '  ' in line:  # Double space
                logger.debug(f"Found extra spaces in line {i}")
                issues.append({
                    "message": f"Extra spaces found in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_parentheses(self, lines: List[str]) -> DocumentCheckResult:
        """Check for unmatched parentheses."""
        logger.debug("Checking parentheses")
        issues = []
        for i, line in enumerate(lines, 1):
            open_count = line.count('(')
            close_count = line.count(')')
            if open_count != close_count:
                logger.debug(f"Found unmatched parentheses in line {i}")
                issues.append({
                    "message": f"Unmatched parentheses in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        logger.debug("Checking section symbols")
        issues = []
        for i, line in enumerate(lines, 1):
            if '§' in line and not re.search(r'§\s+\d', line):
                logger.debug(f"Found incorrect section symbol usage in line {i}")
                issues.append({
                    "message": f"Incorrect section symbol usage in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_list_formatting(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent list formatting."""
        logger.debug("Checking list formatting")
        issues = []
        for i, line in enumerate(lines, 1):
            # Check numbered lists
            if re.match(r'^\d+[^.\s]', line):
                logger.debug(f"Found inconsistent list formatting in line {i}")
                issues.append({
                    "message": f"Inconsistent list formatting in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
            # Check bullet lists
            if line.startswith('•') and not line.startswith('• '):
                logger.debug(f"Found inconsistent bullet spacing in line {i}")
                issues.append({
                    "message": f"Inconsistent bullet spacing in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_quotation_marks(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent quotation mark usage."""
        logger.debug("Checking quotation marks")
        issues = []
        for i, line in enumerate(lines, 1):
            if '"' in line and '"' in line:
                logger.debug(f"Found inconsistent quotation marks in line {i}")
                issues.append({
                    "message": f"Inconsistent quotation marks in line {i}",
                    "severity": Severity.WARNING,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    def check_placeholders(self, lines: List[str]) -> DocumentCheckResult:
        """Check for placeholder text."""
        logger.debug("Checking placeholders")
        issues = []
        placeholder_patterns = [
            r'\b(TODO|FIXME|XXX|HACK|NOTE|REVIEW|DRAFT):',
            r'\b(Add|Update|Review|Fix|Complete)\s+.*\b(here|this|needed)\b',
            r'\b(Placeholder|Temporary|Draft)\b'
        ]

        for i, line in enumerate(lines, 1):
            for pattern in placeholder_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    logger.debug(f"Found placeholder in line {i}")
                    issues.append({
                        "message": "Placeholder text found",
                        "severity": Severity.ERROR,
                        "line_number": i,
                        "checker": "FormattingChecker"
                    })
                    break  # Only add one issue per line
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.ERROR if issues else None, issues=issues)