import logging
import re
from typing import Any, Dict, List

from docx import Document

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.config.validation_patterns import (
    DATE_PATTERNS,
    PHONE_PATTERNS,
)
from documentcheckertool.models import DocumentCheckResult, Severity

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


# Message constants for format checks
class FormatMessages:
    """Static message constants for format checks."""

    # Date format messages
    DATE_FORMAT_ERROR = (
        "Found incorrect date format. Use Month Day, Year format (e.g., May 11, 2025)."
    )

    # Phone number messages
    PHONE_FORMAT_WARNING = "Found inconsistent phone number format. Use one format throughout."

    # Placeholder messages
    PLACEHOLDER_ERROR = "Found placeholder text ('TBD' or similar). Replace with final text."

    # Spacing messages
    DOUBLE_SPACE_WARNING = "Found spacing issues. Remove extra spaces."
    MISSING_SPACE_WARNING = "Found spacing issues. Add a space between '{prefix}' and '{number}'."

    # Dash spacing messages
    DASH_SPACE_REMOVE_AROUND = "Found spacing issues. Remove spaces around dashes unless context specifically requires them."
    DASH_SPACE_REMOVE_BEFORE = (
        "Found spacing issues. Remove space before dash unless context specifically requires it."
    )
    DASH_SPACE_REMOVE_AFTER = (
        "Found spacing issues. Remove space after dash unless context specifically requires it."
    )

    # Punctuation messages
    DOUBLE_PERIOD_WARNING = "Found double periods in line {line}. Remove the unnecessary periods."

    # Parentheses messages
    UNMATCHED_PARENTHESES_WARNING = (
        "Found unmatched parentheses in line {line}. Add missing opening or closing parentheses."
    )

    # Section symbol messages
    SECTION_SYMBOL_CFR_ERROR = 'Remove the section symbol after "14 CFR"'
    SECTION_SYMBOL_WARNING = "Found incorrect section symbol usage in line {line}."

    # List formatting messages
    LIST_FORMAT_WARNING = "Found inconsistent list formatting in line {line}"
    BULLET_SPACING_WARNING = "Found inconsistent bullet spacing in line {line}"

    # Quotation marks messages
    QUOTATION_MARKS_WARNING = "Found inconsistent quotation marks in line {line}"

    # Caption format messages
    CAPTION_FORMAT_ERROR = "Incorrect caption format. Use '{caption_type} X-Y' (AC, Order) or '{caption_type} X' (other document types)."


class FormatChecks(BaseChecker):
    def __init__(self):
        super().__init__()
        self.category = "format"

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

    @CheckRegistry.register("format")
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for format issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    @BaseChecker.register_check("format")
    def _check_date_formats(self, paragraphs: list, results: DocumentCheckResult):
        """Check for consistent date formats."""
        logger.debug(f"Checking date formats with {len(paragraphs)} paragraphs")
        for i, text in enumerate(paragraphs):
            # Skip if text matches any skip patterns
            if any(re.search(pattern, text) for pattern in DATE_PATTERNS["skip_patterns"]):
                continue

            # Check for incorrect date format (MM/DD/YYYY)
            if re.search(DATE_PATTERNS["incorrect"], text):
                results.add_issue(
                    FormatMessages.DATE_FORMAT_ERROR,
                    Severity.ERROR,
                    i + 1,
                    category=getattr(self, "category", "format"),
                )

    @BaseChecker.register_check("format")
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
            normalized = re.sub(r"\s+", " ", num)  # Replace multiple spaces with single space
            normalized = re.sub(r"[-.]+", "-", normalized)  # Normalize separators to single dash

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
                    logger.debug(
                        f"Found phone number in line {idx}: {match.group(0)} (style={style})"
                    )
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
                FormatMessages.PHONE_FORMAT_WARNING,
                Severity.WARNING,
                line_no,
                category=getattr(self, "category", "format"),
            )
            seen.add(line_no)
            logger.debug(f"Flagged line {line_no} for inconsistent phone number format")

    @BaseChecker.register_check("format")
    def _check_placeholders(self, paragraphs: list, results: DocumentCheckResult):
        """Check for placeholder text."""
        logger.debug(f"Checking placeholders with {len(paragraphs)} paragraphs")
        placeholder_patterns = [
            r"\b(TODO|FIXME|XXX|HACK|NOTE|REVIEW|DRAFT):",
            r"\b(Add|Update|Review|Fix|Complete)\s+.*\b(here|this|needed)\b",
            r"\b(Placeholder|Temporary|Draft)\b",
        ]

        for i, text in enumerate(paragraphs):
            for pattern in placeholder_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"Found placeholder in line {i+1}: {text}")
                    try:
                        results.add_issue(
                            FormatMessages.PLACEHOLDER_ERROR,
                            Severity.ERROR,
                            i + 1,
                            category=getattr(self, "category", "format"),
                        )
                        logger.debug(f"Successfully added issue for line {i+1}")
                        break  # Only add one issue per line
                    except Exception as e:
                        logger.error(f"Error adding issue: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        raise

    @BaseChecker.register_check("format")
    def _check_dash_spacing(self, paragraphs: list, results: DocumentCheckResult):
        """Check for incorrect spacing around hyphens, en-dashes, and em-dashes."""
        logger.debug(f"Checking dash spacing with {len(paragraphs)} paragraphs")
        dash_patterns = [
            (r"\s+[-–—]\s+", FormatMessages.DASH_SPACE_REMOVE_AROUND),  # Spaces before and after
            (r"\s+[-–—](?!\s)", FormatMessages.DASH_SPACE_REMOVE_BEFORE),  # Space only before
            (r"(?<!\s)[-–—]\s+", FormatMessages.DASH_SPACE_REMOVE_AFTER),  # Space only after
        ]

        for i, text in enumerate(paragraphs):
            for pattern, message in dash_patterns:
                if matches := re.finditer(pattern, text):
                    for match in matches:
                        logger.debug(f"Found dash spacing issue in line {i+1}: {text}")
                        try:
                            results.add_issue(
                                message,
                                Severity.WARNING,
                                i + 1,
                                category=getattr(self, "category", "format"),
                            )
                            logger.debug(f"Successfully added issue for line {i+1}")
                        except Exception as e:
                            logger.error(f"Error adding issue: {str(e)}")
                            logger.error(f"Error type: {type(e)}")
                            raise

    @BaseChecker.register_check("format")
    def _check_caption_formats(self, paragraphs: list, doc_type: str, results: DocumentCheckResult):
        """Check for correctly formatted table or figure captions."""
        logger.debug(f"Checking caption formats with {len(paragraphs)} paragraphs")

        for i, text in enumerate(paragraphs):
            text = text.strip()

            # Check for table captions
            if text.lower().startswith("table"):
                number_match = re.search(r"^table\s+(\d+(?:-\d+)?)\b", text, re.IGNORECASE)
                if number_match:
                    number_format = number_match.group(1)
                    if doc_type in ["Advisory Circular", "Order"]:
                        if "-" not in number_format:
                            results.add_issue(
                                FormatMessages.CAPTION_FORMAT_ERROR.format(
                                    caption_type="Table",
                                    incorrect_caption=f"Table {number_format}",
                                    doc_type=doc_type,
                                ),
                                Severity.ERROR,
                                i + 1,
                                category=getattr(self, "category", "format"),
                                context={
                                    "incorrect_caption": f"Table {number_format}",
                                    "doc_type": doc_type,
                                    "caption_type": "Table",
                                },
                            )
                    else:
                        if "-" in number_format:
                            results.add_issue(
                                FormatMessages.CAPTION_FORMAT_ERROR.format(
                                    caption_type="Table",
                                    incorrect_caption=f"Table {number_format}",
                                    doc_type=doc_type,
                                ),
                                Severity.ERROR,
                                i + 1,
                                category=getattr(self, "category", "format"),
                                context={
                                    "incorrect_caption": f"Table {number_format}",
                                    "doc_type": doc_type,
                                    "caption_type": "Table",
                                },
                            )

            # Check for figure captions
            if text.lower().startswith("figure"):
                number_match = re.search(r"^figure\s+(\d+(?:-\d+)?)\b", text, re.IGNORECASE)
                if number_match:
                    number_format = number_match.group(1)
                    if doc_type in ["Advisory Circular", "Order"]:
                        if "-" not in number_format:
                            results.add_issue(
                                FormatMessages.CAPTION_FORMAT_ERROR.format(
                                    caption_type="Figure",
                                    incorrect_caption=f"Figure {number_format}",
                                    doc_type=doc_type,
                                ),
                                Severity.ERROR,
                                i + 1,
                                category=getattr(self, "category", "format"),
                                context={
                                    "incorrect_caption": f"Figure {number_format}",
                                    "doc_type": doc_type,
                                    "caption_type": "Figure",
                                },
                            )
                    else:
                        if "-" in number_format:
                            results.add_issue(
                                FormatMessages.CAPTION_FORMAT_ERROR.format(
                                    caption_type="Figure",
                                    incorrect_caption=f"Figure {number_format}",
                                    doc_type=doc_type,
                                ),
                                Severity.ERROR,
                                i + 1,
                                category=getattr(self, "category", "format"),
                                context={
                                    "incorrect_caption": f"Figure {number_format}",
                                    "doc_type": doc_type,
                                    "caption_type": "Figure",
                                },
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
                    warnings.append(
                        {
                            "line_number": i,
                            "message": "Inconsistent font usage",
                            "severity": "warning",
                        }
                    )
            else:
                if standard is None:
                    standard = "normal"
                elif standard != "normal":
                    warnings.append(
                        {
                            "line_number": i,
                            "message": "Inconsistent font usage",
                            "severity": "warning",
                        }
                    )

        # Check spacing consistency (excluding table rows)
        for i, line in enumerate(content, 1):
            # Skip spacing check for table rows
            if "|" in line or line.startswith("---"):
                continue
            if "  " in line:  # Double space
                warnings.append(
                    {"line_number": i, "message": "Inconsistent spacing", "severity": "warning"}
                )

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
                    warnings.append(
                        {"line_number": i, "message": "Inconsistent margins", "severity": "warning"}
                    )

        # Check reference formatting
        for i, line in enumerate(content, 1):
            if re.search(
                r"(?i)(see|refer to|under)\s+(section|paragraph|subsection)\s+\d+(\.\d+)*", line
            ):
                warnings.append(
                    {
                        "line_number": i,
                        "message": "Inconsistent reference format",
                        "severity": "warning",
                    }
                )

        return {"warnings": warnings, "errors": errors, "has_errors": has_errors}


class FormattingChecker(BaseChecker):
    """Checks for formatting issues in documents."""

    # ── spacing helpers ──────────────────────────────────────────────────────
    _DOUBLE_SPACE_RE = re.compile(r" {2,}")
    _MISSING_SPACE_REF_RE = re.compile(
        r"(?<!\s)(?P<prefix>(AC|AD|CFR|FAA|N|SFAR|Part))" r"(?P<number>\d+(?:[-]\d+)?[A-Z]?)"
    )

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content for formatting issues, including date and phone number formats."""
        logger.debug("Starting text formatting check")
        issues = []

        # Split content into lines for line-by-line checking
        lines = content.split("\n")
        logger.debug(f"Split content into {len(lines)} lines")

        # Run all format checks
        issues.extend(self.check_punctuation(lines).issues)
        issues.extend(self.check_spacing(lines).issues)
        issues.extend(self.check_parentheses(lines).issues)
        issues.extend(self.check_section_symbol_usage(lines).issues)
        issues.extend(self.check_list_formatting(lines).issues)
        issues.extend(self.check_quotation_marks(lines).issues)
        issues.extend(self.check_placeholders(lines).issues)  # Add placeholder check

        # --- Additional checks for date and phone number formats ---
        issues.extend(self._check_date_formats_text(lines))
        issues.extend(self._check_phone_numbers_text(lines))

        logger.debug(f"Found {len(issues)} total issues")
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.ERROR if issues else None, issues=issues
        )

    def check_punctuation(self, lines: List[str]) -> DocumentCheckResult:
        """Check for double periods and other punctuation issues."""
        logger.debug("Checking punctuation")
        issues = []
        for i, line in enumerate(lines, 1):
            if ".." in line:
                logger.debug(f"Found double period in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.DOUBLE_PERIOD_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def check_spacing(self, lines: List[str]) -> DocumentCheckResult:
        """
        Detect **all** spacing errors in one pass:
        • double (or more) consecutive spaces
        • missing space before the numeric part of regulatory references
          (e.g. "AC25.1" → "AC 25.1", "§25.1309" handled elsewhere)
        All spacing rules are centralised here and processed before other format checks.
        """
        logger.debug("Checking spacing (double & missing).")
        issues: list[dict] = []

        for i, line in enumerate(lines, 1):
            # 1) Double or multiple spaces anywhere in the line
            for m in self._DOUBLE_SPACE_RE.finditer(line):
                logger.debug(f"Double space found at pos {m.start()} in line {i}: {line!r}")
                issues.append(
                    {
                        "message": FormatMessages.DOUBLE_SPACE_WARNING,
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "context": line.strip(),
                        "checker": "FormattingChecker",
                    }
                )

            # 2) Missing space between prefix and number (AC25.1, CFR14 etc.)
            for m in self._MISSING_SPACE_REF_RE.finditer(line):
                logger.debug(
                    f"Missing space in regulatory reference at pos {m.start()} in line {i}: {line!r}"
                )
                issues.append(
                    {
                        "message": FormatMessages.MISSING_SPACE_WARNING.format(
                            prefix=m.group("prefix"), number=m.group("number")
                        ),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "context": line.strip(),
                        "checker": "FormattingChecker",
                    }
                )

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.WARNING if issues else None,
            issues=issues,
        )

    def check_parentheses(self, lines: List[str]) -> DocumentCheckResult:
        """Check for unmatched parentheses."""
        logger.debug("Checking parentheses")
        issues = []
        for i, line in enumerate(lines, 1):
            open_count = line.count("(")
            close_count = line.count(")")
            if open_count != close_count:
                logger.debug(f"Found unmatched parentheses in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.UNMATCHED_PARENTHESES_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        logger.debug("Checking section symbols (including CFR-specific rule)")
        issues = []

        # --- 1️⃣  Explicit CFR rule --------------------------------------------------
        cfr_pattern = re.compile(r"\b14\s+CFR\s+§\s*(\d+\.\d+)\b")
        for i, line in enumerate(lines, 1):
            if match := cfr_pattern.search(line):
                sect = match.group(1)
                incorrect = match.group(0)
                correct = f"14 CFR {sect}"
                logger.debug(f"CFR-§ usage found on line {i}: {incorrect!r}")
                issues.append(
                    {
                        "incorrect": incorrect,
                        "correct": correct,
                        "description": FormatMessages.SECTION_SYMBOL_CFR_ERROR,
                        "severity": Severity.ERROR,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
        # ---------------------------------------------------------------------------

        # Pattern for valid section symbol usage
        # Must have exactly one space after § and be followed by numbers or valid subsection markers
        re.compile(r"§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*")

        # Pattern for multiple section symbols (e.g., §§ 123-456)
        multiple_symbols_pattern = re.compile(
            r"§§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*-\d+(?:\.\d+)*(?:\([a-z0-9]+\))*"
        )

        for i, line in enumerate(lines, 1):
            # Check for multiple section symbols (e.g., §§ 123-456)
            if "§§" in line:
                if not multiple_symbols_pattern.search(line):
                    logger.debug(f"Found incorrect section symbol usage in line {i}")
                    issues.append(
                        {
                            "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=i),
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker",
                        }
                    )
            # Check for single section symbol
            elif "§" in line:
                # Find all section symbols in the line
                for match in re.finditer(r"§", line):
                    # Get the text after the section symbol
                    after_symbol = line[match.end() :]
                    # Check for invalid spacing (no space or multiple spaces)
                    if re.match(r"\s{2,}|\S|\t|\n|\r|\f|\v", after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append(
                            {
                                "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=i),
                                "severity": Severity.WARNING,
                                "line_number": i,
                                "checker": "FormattingChecker",
                            }
                        )
                        break
                    # Check for valid section number format
                    elif not re.match(r"\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*", after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append(
                            {
                                "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=i),
                                "severity": Severity.WARNING,
                                "line_number": i,
                                "checker": "FormattingChecker",
                            }
                        )
                        break
                    # Check for alphanumeric section numbers
                    elif re.search(r"\s+\d+[a-zA-Z]", after_symbol):
                        logger.debug(f"Found incorrect section symbol usage in line {i}")
                        issues.append(
                            {
                                "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=i),
                                "severity": Severity.WARNING,
                                "line_number": i,
                                "checker": "FormattingChecker",
                            }
                        )
                        break

        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def check_list_formatting(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent list formatting."""
        logger.debug("Checking list formatting")
        issues = []
        for i, line in enumerate(lines, 1):
            # Check numbered lists
            if re.match(r"^\d+[^.\s]", line):
                logger.debug(f"Found inconsistent list formatting in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.LIST_FORMAT_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
            # Check bullet lists
            if line.startswith("•") and not line.startswith("• "):
                logger.debug(f"Found inconsistent bullet spacing in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.BULLET_SPACING_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def check_quotation_marks(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent quotation mark usage."""
        logger.debug("Checking quotation marks")
        issues = []
        for i, line in enumerate(lines, 1):
            if '"' in line and '"' in line:
                logger.debug(f"Found inconsistent quotation marks in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.QUOTATION_MARKS_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def check_placeholders(self, lines: List[str]) -> DocumentCheckResult:
        """Check for placeholder text."""
        logger.debug("Checking placeholders")
        issues = []
        placeholder_patterns = [
            r"\b(TODO|FIXME|XXX|HACK|NOTE|REVIEW|DRAFT):",
            r"\b(Add|Update|Review|Fix|Complete)\s+.*\b(here|this|needed)\b",
            r"\b(Placeholder|Temporary|Draft)\b",
        ]

        for i, line in enumerate(lines, 1):
            for pattern in placeholder_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    logger.debug(f"Found placeholder in line {i}")
                    issues.append(
                        {
                            "message": FormatMessages.PLACEHOLDER_ERROR,
                            "severity": Severity.ERROR,
                            "line_number": i,
                            "checker": "FormattingChecker",
                        }
                    )
                    break  # Only add one issue per line
        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.ERROR if issues else None, issues=issues
        )

    def _check_date_formats_text(self, lines: list) -> list:
        """
        Check for consistent date formats in plain text (line-by-line),
        skipping lines that match skip patterns (e.g., technical references).
        Returns a list of issues.
        """
        logger.debug(f"[Text] Checking date formats with {len(lines)} lines")
        issues = []
        for i, text in enumerate(lines):
            # Skip if text matches any skip patterns
            if any(re.search(pattern, text) for pattern in DATE_PATTERNS["skip_patterns"]):
                logger.debug(f"[Text] Skipping line {i+1} due to skip pattern: {text!r}")
                continue
            # Check for incorrect date format (MM/DD/YYYY)
            if re.search(DATE_PATTERNS["incorrect"], text):
                logger.debug(f"[Text] Found incorrect date format in line {i+1}: {text!r}")
                issues.append(
                    {
                        "message": FormatMessages.DATE_FORMAT_ERROR,
                        "severity": Severity.ERROR,
                        "line_number": i + 1,
                        "context": text.strip(),
                        "checker": "FormattingChecker",
                    }
                )
        return issues

    def _check_phone_numbers_text(self, lines: list) -> list:
        """
        Check for inconsistent phone number formats in plain text (line-by-line).
        Flags all lines with phone numbers if more than one style is present.
        Returns a list of issues.
        """
        logger.debug(f"[Text] Checking phone numbers with {len(lines)} lines")

        def _categorise(num: str) -> str:
            # Normalize whitespace and separators for consistent categorization
            normalized = re.sub(r"\s+", " ", num)
            normalized = re.sub(r"[-.]+", "-", normalized)
            if re.fullmatch(r"\(\d{3}\)\s*\d{3}-\d{4}", normalized):
                return "paren"
            if re.fullmatch(r"\d{3}-\d{3}-\d{4}", normalized):
                return "dash"
            if re.fullmatch(r"\d{3}\.\d{3}\.\d{4}", normalized):
                return "dot"
            if re.fullmatch(r"\d{10}", normalized):
                return "plain"
            return "other"

        found = []  # (line_number, style)
        for idx, line in enumerate(lines, start=1):
            for pattern in PHONE_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    style = _categorise(match.group(0))
                    logger.debug(
                        f"[Text] Found phone number in line {idx}: {match.group(0)} (style={style})"
                    )
                    found.append((idx, style))
                    break  # Only add each number once
        if not found:
            return []
        styles_present = {style for _, style in found}
        logger.debug(f"[Text] Detected phone-number styles: {styles_present}")
        if len(styles_present) == 1:
            return []
        # Flag all lines with phone numbers when styles are inconsistent
        seen = set()
        issues = []
        for line_no, _ in found:
            if line_no in seen:
                continue
            issues.append(
                {
                    "message": FormatMessages.PHONE_FORMAT_WARNING,
                    "severity": Severity.WARNING,
                    "line_number": line_no,
                    "checker": "FormattingChecker",
                }
            )
            seen.add(line_no)
            logger.debug(f"[Text] Flagged line {line_no} for inconsistent phone number format")
        return issues

    @staticmethod
    def format_caption_issues(issues: List[Dict], doc_type: str) -> List[str]:
        """Format caption check issues with clear replacement instructions."""
        formatted_issues = []
        for issue in issues:
            if "incorrect_caption" in issue:
                caption_parts = issue["incorrect_caption"].split()
                if len(caption_parts) >= 2:
                    caption_type = caption_parts[0]  # "Table" or "Figure"
                    number = caption_parts[1]

                    # Determine correct format based on document type
                    if doc_type in ["Advisory Circular", "Order"]:
                        if "-" not in number:
                            correct_format = f"{caption_type} {number}-1"
                    else:
                        if "-" in number:
                            correct_format = f"{caption_type} {number.split('-')[0]}"
                        else:
                            correct_format = issue["incorrect_caption"]

                    formatted_issues.append(
                        f"    • Replace '{issue['incorrect_caption']}' with '{correct_format}'"
                    )

        return formatted_issues

    @staticmethod
    def format_section_symbol_issues(result: DocumentCheckResult) -> List[str]:
        """Format section symbol issues with clear replacement instructions."""
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                if "incorrect" in issue and "correct" in issue:
                    if issue.get("is_sentence_start"):
                        formatted_issues.append(
                            f"    • Do not begin sentences with the section symbol. "
                            f"Replace '{issue['incorrect']}' with '{issue['correct']}' at the start of the sentence"
                        )
                    else:
                        formatted_issues.append(
                            f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"
                        )

        return formatted_issues
