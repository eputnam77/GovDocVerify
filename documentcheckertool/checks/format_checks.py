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
from documentcheckertool.checks.check_registry import CheckRegistry

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
        self._check_caption_formats(paragraphs, doc_type, results)

    @CheckRegistry.register('format')
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for format issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    @BaseChecker.register_check('format')
    def _check_date_formats(self, paragraphs: list, results: DocumentCheckResult):
        """Check for consistent date formats."""
        logger.debug(f"Checking date formats with {len(paragraphs)} paragraphs")
        for i, text in enumerate(paragraphs):
            for pattern in DATE_PATTERNS:
                if re.search(pattern, text):
                    results.add_issue(
                        "Inconsistent date format detected",
                        Severity.WARNING,
                        i+1
                    )

    @BaseChecker.register_check('format')
    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """Check for proper phone number formatting."""
        logger.debug(f"Checking phone numbers with {len(paragraphs)} paragraphs")
        for i, text in enumerate(paragraphs):
            for pattern in PHONE_PATTERNS:
                if re.search(pattern, text):
                    results.add_issue(
                        "Inconsistent phone number format detected",
                        Severity.WARNING,
                        i+1
                    )

    @BaseChecker.register_check('format')
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

    @BaseChecker.register_check('format')
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

    @BaseChecker.register_check('format')
    def _check_caption_formats(self, paragraphs: list, doc_type: str, results: DocumentCheckResult):
        """Check for correctly formatted table or figure captions."""
        logger.debug(f"Checking caption formats with {len(paragraphs)} paragraphs")

        for i, text in enumerate(paragraphs):
            text = text.strip()

            # Check for table captions
            if text.lower().startswith('table'):
                number_match = re.search(r'^table\s+(\d+(?:-\d+)?)\b', text, re.IGNORECASE)
                if number_match:
                    number_format = number_match.group(1)
                    if doc_type in ["Advisory Circular", "Order"]:
                        if '-' not in number_format:
                            results.add_issue(
                                {
                                    'incorrect_caption': f"Table {number_format}",
                                    'doc_type': doc_type,
                                    'caption_type': 'Table'
                                },
                                Severity.ERROR,
                                i+1
                            )
                    else:
                        if '-' in number_format:
                            results.add_issue(
                                {
                                    'incorrect_caption': f"Table {number_format}",
                                    'doc_type': doc_type,
                                    'caption_type': 'Table'
                                },
                                Severity.ERROR,
                                i+1
                            )

            # Check for figure captions
            if text.lower().startswith('figure'):
                number_match = re.search(r'^figure\s+(\d+(?:-\d+)?)\b', text, re.IGNORECASE)
                if number_match:
                    number_format = number_match.group(1)
                    if doc_type in ["Advisory Circular", "Order"]:
                        if '-' not in number_format:
                            results.add_issue(
                                {
                                    'incorrect_caption': f"Figure {number_format}",
                                    'doc_type': doc_type,
                                    'caption_type': 'Figure'
                                },
                                Severity.ERROR,
                                i+1
                            )
                    else:
                        if '-' in number_format:
                            results.add_issue(
                                {
                                    'incorrect_caption': f"Figure {number_format}",
                                    'doc_type': doc_type,
                                    'caption_type': 'Figure'
                                },
                                Severity.ERROR,
                                i+1
                            )

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check the text for format-related issues."""
        logger.debug(f"Running check_text in FormatChecks on text of length: {len(text)}")
        result = DocumentCheckResult()
        issues = []

        # Split text into lines for line-by-line checking
        lines = text.split('\n')
        logger.debug(f"Split text into {len(lines)} lines")

        # Check for double periods
        for i, line in enumerate(lines, 1):
            if '..' in line:
                issues.append({
                    'message': f'Double periods found in line {i}',
                    'severity': Severity.WARNING
                })

        # Check for extra spaces
        for i, line in enumerate(lines, 1):
            if '  ' in line:
                issues.append({
                    'message': f'Extra spaces found in line {i}',
                    'severity': Severity.WARNING
                })

        # Check for unmatched parentheses
        for i, line in enumerate(lines, 1):
            open_count = line.count('(')
            close_count = line.count(')')
            if open_count != close_count:
                issues.append({
                    'message': f'Unmatched parentheses in line {i}',
                    'severity': Severity.WARNING
                })

        # Add issues to the result
        result.issues.extend(issues)
        logger.debug(f"Format checks completed. Found {len(issues)} issues.")
        return result

class FormattingChecker(BaseChecker):
    """Checks for formatting issues in documents."""

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        logger.debug("Checking section symbols")
        issues = []

        # Pattern for valid section symbol usage
        # Must have exactly one space after § and be followed by numbers or valid subsection markers
        valid_pattern = re.compile(r'§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*')

        # Pattern for multiple section symbols (e.g., §§ 123-456)
        multiple_symbols_pattern = re.compile(r'§§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*-\d+(?:\.\d+)*(?:\([a-z0-9]+\))*')

        for i, line in enumerate(lines, 1):
            # Check for multiple section symbols (e.g., §§ 123-456)
            if '§§' in line:
                if not multiple_symbols_pattern.search(line):
                    logger.debug(f"Found incorrect section symbol usage in line {i}")
                    issues.append({
                        "message": f"Incorrect section symbol usage in line {i}",
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker"
                    })
            # Check for single section symbol
            elif '§' in line:
                # Find all section symbols in the line
                for match in re.finditer(r'§', line):
                    # Get the text after the section symbol
                    after_symbol = line[match.end():]
                    # Check for invalid spacing (no space or multiple spaces)
                    if re.match(r'\s{2,}|\S|\t|\n|\r|\f|\v', after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append({
                            "message": f"Incorrect section symbol usage in line {i}",
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker"
                        })
                        break
                    # Check for valid section number format
                    elif not re.match(r'\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*', after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append({
                            "message": f"Incorrect section symbol usage in line {i}",
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker"
                        })
                        break
                    # Check for alphanumeric section numbers
                    elif re.search(r'\s+\d+[a-zA-Z]', after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append({
                            "message": f"Incorrect section symbol usage in line {i}",
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker"
                        })
                        break

        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
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

    @CheckRegistry.register('format')
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