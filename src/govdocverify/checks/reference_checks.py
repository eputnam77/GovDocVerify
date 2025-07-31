import logging
import re
from typing import List

from govdocverify.models import DocumentCheckResult, Severity
from govdocverify.utils.terminology_utils import TerminologyManager

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


# Message constants for reference checks
class ReferenceMessages:
    """Static message constants for reference checks."""

    # Table/Figure reference messages
    TABLE_REF_SENTENCE_START = "Table reference at sentence start should be capitalized"
    TABLE_REF_WITHIN_SENTENCE = "Table reference within sentence should be lowercase"
    TABLE_REF_IN_QUOTES_PARENS = "Table reference in quotes/parentheses should be lowercase"

    FIGURE_REF_SENTENCE_START = "Figure reference at sentence start should be capitalized"
    FIGURE_REF_WITHIN_SENTENCE = "Figure reference within sentence should be lowercase"
    FIGURE_REF_IN_QUOTES_PARENS = "Figure reference in quotes/parentheses should be lowercase"

    # Numbering format messages
    TABLE_FIGURE_NUMBERING = (
        "Use '{ref_type} X-Y' for ACs and Orders, or '{ref_type} X' for other document types."
    )

    # Document title format messages
    AC_TITLE_USE_ITALICS = "AC document titles should use italics, not quotation marks"
    AC_TITLE_FORMAT_ITALICS = "AC document titles should be formatted in italics"
    NON_AC_TITLE_USE_QUOTES = "Document titles should use quotation marks, not italics"
    NON_AC_TITLE_FORMAT_QUOTES = "Document titles should be formatted in quotation marks"


class DocumentTitleFormatCheck(BaseChecker):
    """Class for checking document title formatting based on document type."""

    def __init__(self):
        super().__init__()
        self.category = "formatting"
        logger.info("Initialized DocumentTitleFormatCheck")

    def check_text(self, text, doc_type: str = "GENERAL") -> DocumentCheckResult:
        """
        Check document title formatting based on document type.

        Args:
            text: String or list of strings representing document content
            doc_type: Type of document being checked

        Returns:
            DocumentCheckResult containing check results and any issues found
        """
        if isinstance(text, list):
            lines = text
        else:
            lines = str(text).split("\n")

        return self._check_document_title_formatting(lines, doc_type)

    def _check_document_title_formatting(self, lines: List, doc_type: str) -> DocumentCheckResult:
        """Check for proper document title formatting based on document type."""
        logger.debug(f"Checking document title formatting for doc_type: {doc_type}")
        issues = []

        # Pattern to match document references with titles
        doc_title_pattern = self._get_document_title_pattern()

        for line_idx, line in enumerate(lines):
            if hasattr(line, "text"):
                text = line.text
                italic_regions = self._get_italic_regions(line)
            else:
                text = str(line)
                italic_regions = None

            logger.debug(f"Processing line {line_idx + 1}: {text[:100]}...")
            matches = doc_title_pattern.finditer(text)

            for match in matches:
                title_text = match.group(1).strip().rstrip(",")
                start, end = match.span(1)
                logger.debug(f"Found document title: '{title_text}'")

                issue = self._check_title_format(
                    title_text,
                    doc_type,
                    text,
                    line_idx,
                    italic_regions=italic_regions,
                    start=start,
                    end=end,
                )
                if issue:
                    issues.append(issue)

        logger.debug(f"Document title formatting check complete. Found {len(issues)} issues")

        return self._create_check_result(issues, doc_type)

    def _get_document_title_pattern(self) -> re.Pattern:
        """Get the regex pattern for matching document titles."""
        return re.compile(
            r'\b(?:AC|Order|AD|SFAR|Notice|Policy|Memo)\s+[\d.-]+[A-Z]?,\s*([^,]*(?:"[^"]*"[^,]*)*[^,]*?)(?:,\s*dated|\s+dated)',
            re.IGNORECASE,
        )

    def _check_title_format(
        self,
        title_text: str,
        doc_type: str,
        line: str,
        line_idx: int,
        *,
        italic_regions: list | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> dict:
        """Check the format of a single title and return issue if found."""
        if doc_type == "Advisory Circular":
            return self._check_ac_title_format(
                title_text,
                line,
                line_idx,
                italic_regions=italic_regions,
                start=start,
                end=end,
            )
        return self._check_non_ac_title_format(
            title_text,
            doc_type,
            line,
            line_idx,
            italic_regions=italic_regions,
            start=start,
            end=end,
        )

    def _check_ac_title_format(
        self,
        title_text: str,
        line: str,
        line_idx: int,
        *,
        italic_regions: list | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> dict:
        """Check AC document title formatting (should be in italics)."""
        if self._is_quoted(title_text):
            clean_title = title_text.strip("\"'").rstrip(",").strip()
            logger.debug(f"Found quoted title in AC: {title_text}")
            return self._create_issue(
                line,
                line_idx,
                title_text,
                "AC document titles should use italics, not quotation marks",
                f"*{clean_title}*",
            )
        elif not self._is_formatted(title_text, italic_regions, start, end):
            logger.debug(f"Found unformatted title in AC: {title_text}")
            return self._create_issue(
                line,
                line_idx,
                title_text,
                "AC document titles should be formatted in italics",
                f"*{title_text.strip()}*",
            )
        elif self._is_italicized(title_text, italic_regions, start, end):
            logger.debug(f"Correctly formatted AC title: {title_text}")

        return None

    def _check_non_ac_title_format(
        self,
        title_text: str,
        doc_type: str,
        line: str,
        line_idx: int,
        *,
        italic_regions: list | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> dict:
        """Check non-AC document title formatting (should be in quotes)."""
        if self._is_italicized(title_text, italic_regions, start, end):
            clean_title = title_text.strip("*").strip()
            logger.debug(f"Found italicized title in non-AC: {title_text}")
            return self._create_issue(
                line,
                line_idx,
                title_text,
                f"{doc_type} document titles should use quotation marks, not italics",
                f'"{clean_title}"',
            )
        elif not self._is_formatted(title_text, italic_regions, start, end):
            logger.debug(f"Found unformatted title in non-AC: {title_text}")
            return self._create_issue(
                line,
                line_idx,
                title_text,
                f"{doc_type} document titles should be formatted in quotation marks",
                f'"{title_text.strip()}"',
            )

        return None

    def _is_quoted(self, title_text: str) -> bool:
        """Check if title is wrapped in quotes."""
        return (title_text.startswith('"') and title_text.endswith('"')) or (
            title_text.startswith("'") and title_text.endswith("'")
        )

    def _is_italicized(
        self,
        title_text: str,
        italic_regions: list | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> bool:
        """Check if title is italicized in text or by docx formatting."""
        if italic_regions is not None and start is not None and end is not None:
            for i_start, i_end in italic_regions:
                if start >= i_start and end <= i_end:
                    return True
            return False
        return title_text.startswith("*") and title_text.endswith("*")

    def _is_formatted(
        self,
        title_text: str,
        italic_regions: list | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> bool:
        """Check if title has any formatting (quotes or italics)."""
        return self._is_quoted(title_text) or self._is_italicized(
            title_text,
            italic_regions,
            start,
            end,
        )

    def _get_italic_regions(self, paragraph) -> list:
        """Return ranges of italic text within a paragraph."""
        regions = []
        index = 0
        in_region = False
        region_start = 0
        for run in getattr(paragraph, "runs", []):
            run_len = len(run.text)
            if bool(run.italic):
                if not in_region:
                    region_start = index
                    in_region = True
            elif in_region:
                regions.append((region_start, index))
                in_region = False
            index += run_len
        if in_region:
            regions.append((region_start, index))
        return regions

    def _create_issue(
        self, line: str, line_idx: int, title_text: str, issue_text: str, correct_format: str
    ) -> dict:
        """Create a formatting issue dictionary."""
        return {
            "line": line,
            "line_number": line_idx + 1,
            "title": title_text,
            "issue": issue_text,
            "incorrect_format": title_text,
            "correct_format": correct_format,
            "severity": Severity.ERROR,
            "category": getattr(self, "category", "formatting"),
        }

    def _create_check_result(self, issues: List[dict], doc_type: str) -> DocumentCheckResult:
        """Create the final DocumentCheckResult."""
        # Ensure all issues have the correct category
        for issue in issues:
            if "category" not in issue:
                issue["category"] = getattr(self, "category", "formatting")

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.ERROR if issues else Severity.INFO,
            issues=issues,
            details={"total_issues": len(issues), "doc_type": doc_type},
        )

    def run_checks(self, document, doc_type, results: DocumentCheckResult) -> None:
        """Run document title formatting checks."""
        lines = self._extract_lines_from_document(document)
        check_result = self._check_document_title_formatting(lines, doc_type)

        # Only mark as failed if there are actual errors
        if not check_result.success:
            results.success = False

        # Add formatted issues to results using static messages
        for issue in check_result.issues:
            message = self._create_issue_message(issue)
            results.add_issue(
                message=message,
                severity=issue.get("severity", Severity.WARNING),
                line_number=issue.get("line_number", 0),
                category=getattr(self, "category", "reference"),
            )

    def _extract_lines_from_document(self, document) -> List:
        """Extract lines or paragraphs from various document formats."""
        if hasattr(document, "paragraphs"):
            return list(document.paragraphs)
        elif hasattr(document, "text"):
            return str(document.text).split("\n")
        elif isinstance(document, list):
            return document
        else:
            return str(document).split("\n")

    def _create_issue_message(self, issue: dict) -> str:
        """Create a user-friendly message from issue data."""
        incorrect_format = issue.get("incorrect_format", "")
        correct_format = issue.get("correct_format", "")
        issue_text = issue.get("issue", "")

        # Map issue text to static messages
        message_mapping = {
            "AC document titles should use italics, not quotation marks": (
                ReferenceMessages.AC_TITLE_USE_ITALICS
            ),
            "AC document titles should be formatted in italics": (
                ReferenceMessages.AC_TITLE_FORMAT_ITALICS
            ),
            "document titles should use quotation marks, not italics": (
                ReferenceMessages.NON_AC_TITLE_USE_QUOTES
            ),
            "document titles should be formatted in quotation marks": (
                ReferenceMessages.NON_AC_TITLE_FORMAT_QUOTES
            ),
        }

        for key, static_message in message_mapping.items():
            if key in issue_text:
                return f"{static_message}. Change '{incorrect_format}' to '{correct_format}'"

        # Fallback for any unmapped messages
        if incorrect_format and correct_format:
            return f"{issue_text}. Change '{incorrect_format}' to '{correct_format}'"
        else:
            return issue_text

    def check_document(self, document, doc_type) -> DocumentCheckResult:
        """
        Accepts a Document, list, or str. Uses run_checks to ensure proper formatting.
        """
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results


class TableFigureReferenceCheck(BaseChecker):
    """Class for checking table and figure references."""

    def __init__(self):
        super().__init__()
        self.terminology_manager = TerminologyManager()
        self.category = "formatting"
        self.doc_type = "GENERAL"
        logger.info("Initialized TableFigureReferenceCheck")

    def check(self, doc: List[str], doc_type: str = "GENERAL") -> DocumentCheckResult:
        """Check for correctly formatted table and figure references.

        Args:
            doc: List of strings representing document lines
            doc_type: Type of document being checked (default: "GENERAL")

        Returns:
            DocumentCheckResult containing check results and any issues found
        """
        # Early validation before any len() calls
        if not self.validate_input(doc):
            logger.error("Invalid document input detected")
            return DocumentCheckResult(success=False, issues=[{"error": "Invalid document input"}])

        logger.debug(f"Starting reference check with document type: {doc_type}")
        logger.debug(f"Document length: {len(doc)} lines")

        self.doc_type = doc_type
        return self._check_core(doc)

    def validate_input(self, doc: List[str]) -> bool:
        """Validate input document content."""
        logger.debug("Validating document input")
        if not isinstance(doc, list):
            logger.error(f"Invalid document type: {type(doc)}")
            return False
        if not all(isinstance(line, str) for line in doc):
            logger.error("Document contains non-string lines")
            return False
        logger.debug(f"Document validation successful: {len(doc)} lines")
        return True

    def check_text(self, text, doc_type: str = "GENERAL") -> DocumentCheckResult:
        """
        Accepts a string or list of strings, and calls the main check logic.
        """
        self.doc_type = doc_type
        if isinstance(text, list):
            lines = text
        else:
            lines = str(text).split("\n")
        return self._check_core(lines)

    def _check_core(self, lines: List[str]) -> DocumentCheckResult:
        """Main logic for checking references, expects a list of strings."""
        logger.debug(f"Starting text check with {len(lines)} lines")

        # Handle empty cases
        empty_result = self._handle_empty_input(lines)
        if empty_result:
            return empty_result

        issues = []
        patterns = self._initialize_patterns()
        in_code_block = False

        for line_idx, line in enumerate(lines):
            logger.debug(f"Processing line {line_idx + 1}: {line[:50]}...")

            # Handle code blocks and skip special lines
            if self._should_skip_line(line, patterns["caption"], in_code_block):
                if line.strip() == "```":
                    in_code_block = not in_code_block
                continue

            line_issues = self._process_line_references(line, line_idx, patterns, in_code_block)
            issues.extend(line_issues)

        return self._create_final_result(issues)

    def _handle_empty_input(self, lines: List[str]) -> DocumentCheckResult:
        """Handle empty input cases."""
        if lines == []:  # explicit empty list → success
            logger.debug("Empty list provided - nothing to check")
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={"total_issues": 0, "issues_by_type": {"table": 0, "figure": 0}},
            )
        if not lines or (len(lines) == 1 and not lines[0].strip()):
            logger.debug("Empty content provided")
            return DocumentCheckResult(
                success=False,
                issues=[{"error": "Empty content"}],
                details={"total_issues": 1, "issues_by_type": {"table": 0, "figure": 0}},
            )
        return None

    def _initialize_patterns(self) -> dict:
        """Initialize regex patterns for reference checking."""
        logger.debug("Initializing text check patterns")

        patterns = {
            "caption": re.compile(r"^(Table|Figure)\s+\d+(?:[\.-]\d+)*\.\s+[A-Z]", re.IGNORECASE),
            "table_ref": re.compile(r"\b([Tt]able)s?\s+(\d+(?:[\.-]\d+)*)"),
            "figure_ref": re.compile(r"\b([Ff]igure)s?\s+(\d+(?:[\.-]\d+)*)"),
            "special_context": re.compile(
                "|".join(
                    [
                        r"^[•\-\*]\s+",  # List items
                        r"^\|\s*",  # Table cells
                        r"^```",  # Code blocks
                        r"^<[^>]+>",  # HTML tags
                        r"^[\*\`\_]+",  # Markdown formatting
                    ]
                )
            ),
        }

        logger.debug(f"Caption pattern: {patterns['caption'].pattern}")
        logger.debug(f"Table reference pattern: {patterns['table_ref'].pattern}")
        logger.debug(f"Figure reference pattern: {patterns['figure_ref'].pattern}")

        return patterns

    def _should_skip_line(
        self, line: str, caption_pattern: re.Pattern, in_code_block: bool
    ) -> bool:
        """Determine if a line should be skipped during processing."""
        if line.strip() == "```":
            return True
        if caption_pattern.match(line.strip()):
            logger.debug(f"Skipping caption line: {line.strip()}")
            return True
        if in_code_block:
            logger.debug("Skipping line in code block")
            return True
        return False

    def _process_line_references(
        self, line: str, line_idx: int, patterns: dict, in_code_block: bool
    ) -> List[dict]:
        """Process references in a single line."""
        if in_code_block:
            return []

        issues = []
        is_special_context = bool(patterns["special_context"].match(line.strip()))
        logger.debug(f"Line is in special context: {is_special_context}")

        # Clean the line for reference checking
        cleaned_line = self._clean_line_for_checking(line)

        # Check for references
        ref_patterns = [(patterns["table_ref"], "Table"), (patterns["figure_ref"], "Figure")]
        for pattern, ref_type in ref_patterns:
            matches = list(pattern.finditer(cleaned_line))
            logger.debug(f"Found {len(matches)} {ref_type} references in line")

            for match in matches:
                ref_issues = self._check_reference_match(
                    match,
                    ref_type,
                    line,
                    cleaned_line,
                    is_special_context,
                )
                issues.extend(ref_issues)

        return issues

    def _clean_line_for_checking(self, line: str) -> str:
        """Clean line for reference checking."""
        cleaned_line = re.sub(r'["\']|\(|\)', "", line.strip())
        logger.debug(f"Cleaned line: {cleaned_line}")
        return cleaned_line

    def _check_reference_match(
        self,
        match,
        ref_type: str,
        original_line: str,
        cleaned_line: str,
        is_special_context: bool,
    ) -> List[dict]:
        """Check a single reference match and return list of issues if found."""
        issues = []
        ref_text = match.group()
        word = match.group(1)
        number_part = match.group(2)

        start, end = match.span()
        orig_match = re.search(re.escape(ref_text), original_line)
        if orig_match:
            start, end = orig_match.span()
        before = original_line[:start]
        after = original_line[end:]
        before_stripped = before.rstrip()
        after_stripped = after.lstrip()
        has_parentheses = (
            before_stripped.endswith("(") or (start == 0 and original_line.lstrip().startswith("("))
        ) and after_stripped.startswith(")")
        has_quotes = (
            (
                before_stripped.endswith('"')
                or (start == 0 and original_line.lstrip().startswith('"'))
            )
            and after_stripped.startswith('"')
        ) or (
            (
                before_stripped.endswith("'")
                or (start == 0 and original_line.lstrip().startswith("'"))
            )
            and after_stripped.startswith("'")
        )

        # Handle references wrapped in quotes or parentheses first
        if (has_quotes or has_parentheses) and word[0].isupper():
            logger.debug(f"Found uppercase {ref_type} reference in quotes/parentheses")
            issues.append(
                {
                    "reference": ref_text,
                    "issue": f"{ref_type} reference in quotes/parentheses should be lowercase",
                    "line": original_line,
                    "correct_form": ref_text.lower(),
                }
            )
            return issues

        # Skip complex references
        if self._is_complex_reference(ref_text, word):
            logger.debug(f"Skipping style check for complex reference: {ref_text}")
            return issues

        # Skip validation for special contexts
        if is_special_context:
            logger.debug(f"Skipping validation for special context: {ref_text}")
            return issues

        # Check numbering format based on doc_type
        numbering_issue = self._check_number_format(number_part, ref_type, original_line)
        if numbering_issue:
            issues.append(numbering_issue)

        # Check sentence position and capitalization
        is_sentence_start = self._is_sentence_start(cleaned_line, match)

        cap_issue = self._validate_reference_capitalization(
            ref_text,
            word,
            ref_type,
            original_line,
            is_sentence_start,
            has_quotes,
            has_parentheses,
        )
        if cap_issue:
            issues.append(cap_issue)

        return issues

    def _is_complex_reference(self, ref_text: str, word: str) -> bool:
        """Check if reference is complex and should skip style checking."""
        rest = ref_text.split(word, 1)[1]  # part after "Table"/"Figure"
        if (
            self.doc_type in ["Advisory Circular", "Order"]
            and re.fullmatch(r"\d+-\d+", rest)
            and word.lower() in ("table", "figure")
        ):
            return False

        return (
            "." in rest
            or "-" in rest
            or "\t" in rest
            or "\n" in rest
            or re.search(r"\s{2,}", rest) is not None
        )

    def _is_sentence_start(self, cleaned_line: str, match) -> bool:
        """Determine if reference is at the start of a sentence."""
        text_before = cleaned_line[: match.start()].strip()
        text_before_clean = re.sub(r"^[\s\W]+", "", text_before)
        logger.debug(f"Text before reference: '{text_before}' (cleaned: '{text_before_clean}')")

        is_start = not text_before_clean or text_before_clean.endswith((".", ":", ";"))
        logger.debug(f"Reference is at sentence start: {is_start}")
        return is_start

    def _validate_reference_capitalization(
        self,
        ref_text: str,
        word: str,
        ref_type: str,
        line: str,
        is_sentence_start: bool,
        has_quotes: bool,
        has_parentheses: bool,
    ) -> dict:
        """Validate reference capitalization and return issue if found."""
        if is_sentence_start and word[0].islower():
            logger.debug(f"Found lowercase {ref_type} reference at sentence start")
            return {
                "reference": ref_text,
                "issue": f"{ref_type} reference at sentence start should be capitalized",
                "line": line,
                "correct_form": ref_text.capitalize(),
            }
        elif (has_quotes or has_parentheses) and word[0].isupper():
            logger.debug(f"Found uppercase {ref_type} reference in quotes/parentheses")
            return {
                "reference": ref_text,
                "issue": f"{ref_type} reference in quotes/parentheses should be lowercase",
                "line": line,
                "correct_form": ref_text.lower(),
            }
        elif not is_sentence_start and word[0].isupper():
            logger.debug(f"Found uppercase {ref_type} reference within sentence")
            return {
                "reference": ref_text,
                "issue": f"{ref_type} reference within sentence should be lowercase",
                "line": line,
                "correct_form": ref_text.lower(),
            }

        return None

    def _check_number_format(self, number: str, ref_type: str, line: str) -> dict | None:
        """Check numbering format based on document type."""
        doc_type = getattr(self, "doc_type", "GENERAL")
        has_hyphen = "-" in number
        if doc_type in ["Advisory Circular", "Order"] and not has_hyphen:
            return {
                "reference": f"{ref_type} {number}",
                "issue": ReferenceMessages.TABLE_FIGURE_NUMBERING.format(ref_type=ref_type),
                "line": line,
            }
        return None

    def _create_final_result(self, issues: List[dict]) -> DocumentCheckResult:
        """Create the final DocumentCheckResult."""
        logger.debug(f"Text check complete. Found {len(issues)} issues")
        logger.debug(
            f"Issues by type: "
            f"{len([i for i in issues if 'Table' in i['issue']])} table issues, "
            f"{len([i for i in issues if 'Figure' in i['issue']])} figure issues"
        )

        # Ensure all issues have the correct category
        for issue in issues:
            if "category" not in issue:
                issue["category"] = getattr(self, "category", "formatting")

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.ERROR if issues else Severity.INFO,
            issues=issues,
            details={
                "total_issues": len(issues),
                "issues_by_type": {
                    "table": len([i for i in issues if "Table" in i["issue"]]),
                    "figure": len([i for i in issues if "Figure" in i["issue"]]),
                },
            },
        )

    def run_checks(self, document, doc_type, results: DocumentCheckResult) -> None:
        lines = self._extract_lines_from_document(document)
        check_result = self._check_core(lines)

        # Only mark as failed if there are actual errors
        if not check_result.success:
            results.success = False

        # Add formatted issues to results using static messages
        for issue in check_result.issues:
            message = self._create_reference_issue_message(issue)
            results.add_issue(
                message=message,
                severity=Severity.WARNING,
                line_number=0,  # Line numbers aren't tracked in the current issue format
                category=getattr(self, "category", "reference"),
            )

    def _extract_lines_from_document(self, document) -> List[str]:
        """Extract lines from various document formats."""
        if hasattr(document, "paragraphs"):
            return [p.text for p in document.paragraphs]
        elif hasattr(document, "text"):
            return str(document.text).split("\n")
        elif isinstance(document, list):
            return document
        else:
            return str(document).split("\n")

    def _create_reference_issue_message(self, issue: dict) -> str:
        """Create a user-friendly message from reference issue data."""
        reference = issue.get("reference", "")
        issue_text = issue.get("issue", "")
        correct_form = issue.get("correct_form", "")

        # Map issue text to static messages
        message_mapping = {
            "Table reference at sentence start should be capitalized": (
                ReferenceMessages.TABLE_REF_SENTENCE_START
            ),
            "Table reference within sentence should be lowercase": (
                ReferenceMessages.TABLE_REF_WITHIN_SENTENCE
            ),
            "Table reference in quotes/parentheses should be lowercase": (
                ReferenceMessages.TABLE_REF_IN_QUOTES_PARENS
            ),
            "Figure reference at sentence start should be capitalized": (
                ReferenceMessages.FIGURE_REF_SENTENCE_START
            ),
            "Figure reference within sentence should be lowercase": (
                ReferenceMessages.FIGURE_REF_WITHIN_SENTENCE
            ),
            "Figure reference in quotes/parentheses should be lowercase": (
                ReferenceMessages.FIGURE_REF_IN_QUOTES_PARENS
            ),
        }

        for key, static_message in message_mapping.items():
            if key in issue_text:
                return f"{static_message}. Change '{reference}' to '{correct_form}'"

        # Fallback for any unmapped messages
        if reference and correct_form:
            return f"{issue_text}. Change '{reference}' to '{correct_form}'"
        else:
            return issue_text

    def check_document(self, document, doc_type) -> DocumentCheckResult:
        """
        Accepts a Document, list, or str. Uses run_checks to ensure proper formatting.
        """
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    @staticmethod
    def format_reference_issues(result: DocumentCheckResult) -> List[str]:
        """Format reference issues with clear, concise descriptions."""
        formatted_issues = []

        for issue in result.issues:
            ref_type = issue.get("type", "")
            ref_num = issue.get("reference", "")
            context = issue.get("context", "").strip()

            if context:  # Only include context if it exists
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} referenced in '{context}' exists in the "
                    "document"
                )
            else:
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} exists in the document"
                )

        return formatted_issues
