import logging
import re
from typing import Any, Dict, List

try:
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    from typing import Any as Document  # type: ignore


from govdocverify.checks.check_registry import CheckRegistry
from govdocverify.config.validation_patterns import (
    DATE_PATTERNS,
    PHONE_PATTERNS,
)
from govdocverify.models import DocumentCheckResult, Severity

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
    DASH_SPACE_REMOVE_AROUND = (
        "Use X–Y (no spaces around the dash), unless spacing is needed for clarity or context."
    )
    DASH_SPACE_REMOVE_BEFORE = (
        "Use X–Y (no spaces before the dash), unless spacing is needed for clarity or context."
    )
    DASH_SPACE_REMOVE_AFTER = (
        "Use X–Y (no spaces after the dash), unless spacing is needed for clarity or context."
    )

    # Punctuation messages
    DOUBLE_PERIOD_WARNING = "Found double periods in line {line}. Remove the unnecessary periods."

    # Parentheses messages
    UNMATCHED_PARENTHESES_WARNING = "Add missing opening or closing parentheses in: '{context}'"

    # Section symbol messages
    SECTION_SYMBOL_CFR_ERROR = 'Remove the section symbol after "14 CFR"'
    SECTION_SYMBOL_WARNING = "Found incorrect section symbol usage in line {line}."

    # List formatting messages
    LIST_FORMAT_WARNING = "Found inconsistent list formatting in line {line}"
    BULLET_SPACING_WARNING = "Found inconsistent bullet spacing in line {line}"
    LIST_NUMBERING_GAP_WARNING = (
        "List numbering expected {expected} but found {found} in line {line}"
    )
    ORPHAN_BULLET_WARNING = "Bullet in line {line} is not part of a list"

    # Quotation marks messages
    QUOTATION_MARKS_WARNING = "Found inconsistent quotation marks in line {line}"

    # Caption format messages
    CAPTION_FORMAT_ERROR = (
        "Use '{caption_type} X-Y' for ACs and Orders, "
        "or '{caption_type} X' for other document types."
    )


class FormatChecks(BaseChecker):
    def __init__(self, terminology_manager=None) -> None:
        """Initialize the format checks.

        Parameters
        ----------
        terminology_manager : TerminologyManager | None
            Optional terminology manager passed through ``BaseChecker``.  It is
            currently unused but kept for API compatibility.
        """

        super().__init__(terminology_manager)
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

        found_numbers = self._collect_phone_numbers_from_paragraphs(paragraphs)
        if not found_numbers:
            return

        styles_present = {style for _, style in found_numbers}
        logger.debug(f"Detected phone-number styles: {styles_present}")

        if len(styles_present) > 1:
            self._flag_inconsistent_phone_formats_in_paragraphs(found_numbers, results)

    def _collect_phone_numbers_from_paragraphs(self, paragraphs: list) -> list:
        """Collect all phone numbers and their styles from paragraphs."""
        found = []  # (line_number, style)

        for idx, line in enumerate(paragraphs, start=1):
            for pattern in PHONE_PATTERNS:
                if match := re.search(pattern, line):
                    style = self._categorise_phone_number_in_paragraph(match.group(0))
                    logger.debug(
                        f"Found phone number in line {idx}: {match.group(0)} (style={style})"
                    )
                    found.append((idx, style))
                    break  # Only add each number once

        return found

    def _categorise_phone_number_in_paragraph(self, num: str) -> str:
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

    def _flag_inconsistent_phone_formats_in_paragraphs(
        self, found_numbers: list, results: DocumentCheckResult
    ):
        """Flag all lines with phone numbers when styles are inconsistent."""
        seen = set()

        for line_no, _ in found_numbers:
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
                    logger.debug(f"Found placeholder in line {i + 1}: {text}")
                    try:
                        results.add_issue(
                            FormatMessages.PLACEHOLDER_ERROR,
                            Severity.ERROR,
                            i + 1,
                            category=getattr(self, "category", "format"),
                        )
                        logger.debug(f"Successfully added issue for line {i + 1}")
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
                        logger.debug(f"Found dash spacing issue in line {i + 1}: {text}")
                        try:
                            results.add_issue(
                                message,
                                Severity.WARNING,
                                i + 1,
                                category=getattr(self, "category", "format"),
                            )
                            logger.debug(f"Successfully added issue for line {i + 1}")
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
            line_num = i + 1

            self._check_table_caption_format(text, doc_type, line_num, results)
            self._check_figure_caption_format(text, doc_type, line_num, results)

    def _check_table_caption_format(
        self, text: str, doc_type: str, line_num: int, results: DocumentCheckResult
    ):
        """Check table caption formatting."""
        if not text.lower().startswith("table"):
            return

        number_match = re.search(r"^table\s+(\d+(?:-\d+)?)\b", text, re.IGNORECASE)
        if number_match:
            number_format = number_match.group(1)
            if self._should_add_caption_issue(number_format, doc_type):
                self._add_caption_issue("Table", number_format, doc_type, line_num, results)

    def _check_figure_caption_format(
        self, text: str, doc_type: str, line_num: int, results: DocumentCheckResult
    ):
        """Check figure caption formatting."""
        if not text.lower().startswith("figure"):
            return

        number_match = re.search(r"^figure\s+(\d+(?:-\d+)?)\b", text, re.IGNORECASE)
        if number_match:
            number_format = number_match.group(1)
            if self._should_add_caption_issue(number_format, doc_type):
                self._add_caption_issue("Figure", number_format, doc_type, line_num, results)

    def _should_add_caption_issue(self, number_format: str, doc_type: str) -> bool:
        """Determine if a caption format issue should be added."""
        if doc_type in ["Advisory Circular", "Order"]:
            return "-" not in number_format
        else:
            return "-" in number_format

    def _add_caption_issue(
        self,
        caption_type: str,
        number_format: str,
        doc_type: str,
        line_num: int,
        results: DocumentCheckResult,
    ):
        """Add a caption format issue."""
        results.add_issue(
            FormatMessages.CAPTION_FORMAT_ERROR.format(
                caption_type=caption_type,
                incorrect_caption=f"{caption_type} {number_format}",
                doc_type=doc_type,
            ),
            Severity.ERROR,
            line_num,
            category=getattr(self, "category", "format"),
            context={
                "incorrect_caption": f"{caption_type} {number_format}",
                "doc_type": doc_type,
                "caption_type": caption_type,
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

        # Run individual check methods
        warnings.extend(self._check_font_consistency(content))
        warnings.extend(self._check_spacing_consistency(content))
        warnings.extend(self._check_margin_consistency(content))
        warnings.extend(self._check_reference_formatting(content))

        return {"warnings": warnings, "errors": errors, "has_errors": has_errors}

    def _check_font_consistency(self, content: List[str]) -> List[Dict]:
        """Check for consistent font usage."""
        warnings = []
        standard = None

        for i, line in enumerate(content, 1):
            current_type = self._get_font_type(line)

            if standard is None:
                standard = current_type
            elif standard != current_type:
                warnings.append(
                    {
                        "line_number": i,
                        "message": "Inconsistent font usage",
                        "severity": "warning",
                    }
                )

        return warnings

    def _get_font_type(self, line: str) -> str:
        """Determine font type of a line."""
        if "BOLD" in line or "italic" in line.lower():
            return "special"
        return "normal"

    def _check_spacing_consistency(self, content: List[str]) -> List[Dict]:
        """Check spacing consistency (excluding table rows)."""
        warnings = []

        for i, line in enumerate(content, 1):
            if self._is_table_row(line):
                continue
            if "  " in line:  # Double space
                warnings.append(
                    {"line_number": i, "message": "Inconsistent spacing", "severity": "warning"}
                )

        return warnings

    def _is_table_row(self, line: str) -> bool:
        """Check if line is a table row."""
        return "|" in line or line.startswith("---")

    def _check_margin_consistency(self, content: List[str]) -> List[Dict]:
        """Check margin consistency."""
        warnings = []
        margin_patterns = set()

        for i, line in enumerate(content, 1):
            if not line.strip():
                continue

            leading_ws = len(line) - len(line.lstrip())
            if leading_ws > 0:
                margin_patterns.add(leading_ws)
                if len(margin_patterns) > 1:
                    warnings.append(
                        {"line_number": i, "message": "Inconsistent margins", "severity": "warning"}
                    )

        return warnings

    def _check_reference_formatting(self, content: List[str]) -> List[Dict]:
        """Check reference formatting."""
        warnings = []
        reference_pattern = (
            r"(?i)(see|refer to|under)\s+(section|paragraph|subsection)\s+\d+(\.\d+)*"
        )

        for i, line in enumerate(content, 1):
            if re.search(reference_pattern, line):
                warnings.append(
                    {
                        "line_number": i,
                        "message": "Inconsistent reference format",
                        "severity": "warning",
                    }
                )

        return warnings


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
                    "Missing space in regulatory reference at position "
                    f"{m.start()} in line {i}: {line!r}"
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
                snippet = line.strip()
                if len(snippet) > 60:
                    snippet = snippet[:60] + "..."
                issues.append(
                    {
                        "message": FormatMessages.UNMATCHED_PARENTHESES_WARNING.format(
                            line=i, context=snippet
                        ),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "context": snippet,
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

        # Check CFR-specific rule and general section symbol usage
        issues.extend(self._check_cfr_section_symbols(lines))
        issues.extend(self._check_general_section_symbols(lines))

        return DocumentCheckResult(
            success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues
        )

    def _check_cfr_section_symbols(self, lines: List[str]) -> List[Dict]:
        """Skip 14 CFR citations.

        Historically the checker enforced removal of the section symbol when
        citing the Code of Federal Regulations.  FAA guidance now permits
        citations such as ``14 CFR § 25.1309``.  The checker therefore avoids
        flagging these references and simply returns an empty list.
        """

        return []

    def _check_general_section_symbols(self, lines: List[str]) -> List[Dict]:
        """Check for general section symbol usage issues."""
        issues = []
        multiple_symbols_pattern = re.compile(
            r"§§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*-\d+(?:\.\d+)*(?:\([a-z0-9]+\))*"
        )

        for i, line in enumerate(lines, 1):
            if "§§" in line:
                issues.extend(
                    self._check_multiple_section_symbols(line, i, multiple_symbols_pattern)
                )
            elif "§" in line:
                issues.extend(self._check_single_section_symbols(line, i))

        return issues

    def _check_multiple_section_symbols(self, line: str, line_num: int, pattern) -> List[Dict]:
        """Check multiple section symbols (e.g., §§ 123-456)."""
        if not pattern.search(line):
            logger.debug(f"Found incorrect section symbol usage in line {line_num}")
            return [
                {
                    "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=line_num),
                    "severity": Severity.WARNING,
                    "line_number": line_num,
                    "checker": "FormattingChecker",
                }
            ]
        return []

    def _check_single_section_symbols(self, line: str, line_num: int) -> List[Dict]:
        """Check single section symbols for proper formatting."""
        for match in re.finditer(r"§", line):
            after_symbol = line[match.end() :]

            if self._has_invalid_section_format(after_symbol):
                logger.debug(f"Found incorrect section symbol usage in line {line_num}")
                return [
                    {
                        "message": FormatMessages.SECTION_SYMBOL_WARNING.format(line=line_num),
                        "severity": Severity.WARNING,
                        "line_number": line_num,
                        "checker": "FormattingChecker",
                    }
                ]
        return []

    def _has_invalid_section_format(self, after_symbol: str) -> bool:
        """Check if the text after section symbol has invalid format."""
        # Check for invalid spacing (no space or multiple spaces)
        if re.match(r"\s{2,}|\S|\t|\n|\r|\f|\v", after_symbol):
            return True

        # Check for valid section number format
        if not re.match(r"\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*", after_symbol):
            return True

        # Check for alphanumeric section numbers
        if re.search(r"\s+\d+[a-zA-Z]", after_symbol):
            return True

        return False

    def check_list_formatting(self, lines: List[str]) -> DocumentCheckResult:
        """Check for consistent list formatting."""
        logger.debug("Checking list formatting")
        issues = []
        last_number: int | None = None
        for i, line in enumerate(lines, 1):
            # Numbered lists require a period and sequential numbering
            gap_match = re.match(r"^(\d+)\.\s", line)
            if gap_match:
                current = int(gap_match.group(1))
                if last_number is not None and current != last_number + 1:
                    logger.debug(
                        "List numbering gap: expected %s but found %s at line %s",
                        last_number + 1,
                        current,
                        i,
                    )
                    issues.append(
                        {
                            "message": FormatMessages.LIST_NUMBERING_GAP_WARNING.format(
                                expected=last_number + 1, found=current, line=i
                            ),
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker",
                        }
                    )
                last_number = current
            elif re.match(r"^\d+[^.\s]", line):
                logger.debug(f"Found inconsistent list formatting in line {i}")
                issues.append(
                    {
                        "message": FormatMessages.LIST_FORMAT_WARNING.format(line=i),
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker",
                    }
                )
                last_number = None
            else:
                last_number = None

            # Bullet list checks
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

            if line.startswith("• "):
                prev = lines[i - 2] if i > 1 else ""
                nxt = lines[i] if i < len(lines) else ""
                if not prev.strip().startswith("•") and not nxt.strip().startswith("•"):
                    logger.debug(f"Found orphan bullet in line {i}")
                    issues.append(
                        {
                            "message": FormatMessages.ORPHAN_BULLET_WARNING.format(line=i),
                            "severity": Severity.WARNING,
                            "line_number": i,
                            "checker": "FormattingChecker",
                        }
                    )

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.WARNING if issues else None,
            issues=issues,
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
                logger.debug(f"[Text] Skipping line {i + 1} due to skip pattern: {text!r}")
                continue
            # Check for incorrect date format (MM/DD/YYYY)
            if re.search(DATE_PATTERNS["incorrect"], text):
                logger.debug(f"[Text] Found incorrect date format in line {i + 1}: {text!r}")
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

        found_numbers = self._collect_phone_numbers_from_lines(lines)
        if not found_numbers:
            return []

        styles_present = {style for _, style in found_numbers}
        logger.debug(f"[Text] Detected phone-number styles: {styles_present}")

        if len(styles_present) == 1:
            return []

        return self._create_phone_format_issues_for_lines(found_numbers)

    def _collect_phone_numbers_from_lines(self, lines: list) -> list:
        """Collect phone numbers from individual lines."""
        found = []  # (line_number, style)

        for idx, line in enumerate(lines, start=1):
            for pattern in PHONE_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    style = self._categorise_phone_number_text(match.group(0))
                    logger.debug(
                        f"[Text] Found phone number in line {idx}: {match.group(0)} (style={style})"
                    )
                    found.append((idx, style))
                    break  # Only add each number once

        return found

    def _categorise_phone_number_text(self, num: str) -> str:
        """Categorize a phone number into its style for text checking."""
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

    def _create_phone_format_issues_for_lines(self, found_numbers: list) -> list:
        """Create issues for inconsistent phone formats in lines."""
        seen = set()
        issues = []

        for line_no, _ in found_numbers:
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
                            "    • Do not begin a sentence with the section symbol. "
                            f"Replace '{issue['incorrect']}' with '{issue['correct']}' "
                            "at the start of the sentence."
                        )
                    else:
                        formatted_issues.append(
                            f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"
                        )

        return formatted_issues
