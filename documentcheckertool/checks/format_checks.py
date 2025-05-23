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
            # Skip if text matches any skip patterns
            if any(re.search(pattern, text) for pattern in DATE_PATTERNS['skip_patterns']):
                continue

            # Check for incorrect date format (MM/DD/YYYY)
            if re.search(DATE_PATTERNS['incorrect'], text):
                results.add_issue(
                    "Incorrect date format. Use Month Day, Year format (e.g., May 11, 2025)",
                    Severity.ERROR,
                    i+1
                )

    @BaseChecker.register_check('format')
    def _check_phone_numbers(self, paragraphs: list, results: DocumentCheckResult):
        """
        Flag every line whenever more than one phone-number style is used
        anywhere in the document. Supported styles:
            (123) 456-7890   → "paren"
            123-456-7890     → "dash"
            123.456.7890     → "dot"
            1234567890       → "plain"
        """
        logger.debug(f"Checking phone numbers with {len(paragraphs)} paragraphs")

        def _categorise(num: str) -> str:
            """Categorize a phone number into its style."""
            # Normalize whitespace and separators for consistent categorization
            normalized = re.sub(r'\s+', ' ', num)  # Replace multiple spaces with single space
            normalized = re.sub(r'[-.]+', '-', normalized)  # Normalize separators to single dash

            if re.fullmatch(r"\(\d{3}\)\s*\d{3}-\d{4}", normalized):
                return "paren"
            if re.fullmatch(r"\d{3}-\d{3}-\d{4}", normalized):
                return "dash"
            if re.fullmatch(r"\d{3}\.\d{3}\.\d{4}", normalized):
                return "dot"
            if re.fullmatch(r"\d{10}", normalized):
                return "plain"
            return "other"

        # Collect all phone numbers and their styles
        found: list[tuple[int, str]] = []  # (line_number, style)
        for idx, line in enumerate(paragraphs, start=1):
            for pattern in PHONE_PATTERNS:
                if match := re.search(pattern, line):
                    style = _categorise(match.group(0))
                    logger.debug(f"Found phone number in line {idx}: {match.group(0)} (style={style})")
                    found.append((idx, style))
                    break  # Only add each number once

        if not found:
            return

        # Check for style consistency
        styles_present = {style for _, style in found}
        logger.debug(f"Detected phone-number styles: {styles_present}")

        # If only one style is present, no issues to report
        if len(styles_present) == 1:
            return

        # Flag all lines with phone numbers when styles are inconsistent
        seen: set[int] = set()
        for line_no, _ in found:
            if line_no in seen:
                continue
            results.add_issue(
                "Inconsistent phone number format",
                Severity.WARNING,
                line_no
            )
            seen.add(line_no)
            logger.debug(f"Flagged line {line_no} for inconsistent phone number format")

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

    def check(self, content: List[str]) -> Dict[str, Any]:
        """
        Check document content for formatting issues.

        Args:
            content: List of strings representing document lines

        Returns:
            Dict containing check results with warnings, errors, and has_errors flag
        """
        logger.debug(f"Running format checks on {len(content)} lines")
        warnings = []
        errors = []
        has_errors = False

        # Check font consistency
        standard = None
        for i, line in enumerate(content, 1):
            if "BOLD" in line or "italic" in line.lower():
                if standard is None:
                    standard = "special"
                elif standard != "special":
                    warnings.append({
                        "line_number": i,
                        "message": "Inconsistent font usage",
                        "severity": "warning"
                    })
            else:
                if standard is None:
                    standard = "normal"
                elif standard != "normal":
                    warnings.append({
                        "line_number": i,
                        "message": "Inconsistent font usage",
                        "severity": "warning"
                    })

        # Check spacing consistency (excluding table rows)
        for i, line in enumerate(content, 1):
            # Skip spacing check for table rows
            if '|' in line or line.startswith('---'):
                continue
            if '  ' in line:  # Double space
                warnings.append({
                    "line_number": i,
                    "message": "Inconsistent spacing",
                    "severity": "warning"
                })

        # Check margin consistency
        margin_patterns = set()
        for i, line in enumerate(content, 1):
            # Skip empty lines
            if not line.strip():
                continue
            # Get the leading whitespace pattern
            leading_ws = len(line) - len(line.lstrip())
            if leading_ws > 0:
                margin_patterns.add(leading_ws)
                # If we have more than one margin pattern, flag it
                if len(margin_patterns) > 1:
                    warnings.append({
                        "line_number": i,
                        "message": "Inconsistent margins",
                        "severity": "warning"
                    })

        # Check reference formatting
        for i, line in enumerate(content, 1):
            if re.search(r'(?i)(see|refer to|under)\s+(section|paragraph|subsection)\s+\d+(\.\d+)*', line):
                warnings.append({
                    "line_number": i,
                    "message": "Inconsistent reference format",
                    "severity": "warning"
                })

        return {
            "warnings": warnings,
            "errors": errors,
            "has_errors": has_errors
        }

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
        logger.debug("Checking section symbols (including CFR-specific rule)")
        issues = []

        # --- 1️⃣  Explicit CFR rule --------------------------------------------------
        cfr_pattern = re.compile(r'\b14\s+CFR\s+§\s*(\d+\.\d+)\b')
        for i, line in enumerate(lines, 1):
            if match := cfr_pattern.search(line):
                sect = match.group(1)
                incorrect = match.group(0)
                correct = f"14 CFR {sect}"
                logger.debug(f"CFR-§ usage found on line {i}: {incorrect!r}")
                issues.append({
                    "incorrect": incorrect,
                    "correct": correct,
                    "description": 'Remove the section symbol after "14 CFR"',
                    "severity": Severity.ERROR,
                    "line_number": i,
                    "checker": "FormattingChecker"
                })
        # ---------------------------------------------------------------------------

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