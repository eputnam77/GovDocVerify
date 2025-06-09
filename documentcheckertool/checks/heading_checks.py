import logging
import re
from functools import wraps
from typing import Any, Dict, List, Optional

from docx import Document

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.utils.text_utils import normalize_heading

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)

    return wrapper


class HeadingChecks(BaseChecker):
    """Class for handling heading-related checks."""

    # Maximum allowed length for a heading (excluding numbering)
    MAX_HEADING_LENGTH = 25

    # Maximum character/word limits for period checks to avoid false positives
    # from paragraphs incorrectly marked as headings
    MAX_HEADING_CHARS_FOR_PERIOD_CHECK = 100  # Characters
    MAX_HEADING_WORDS_FOR_PERIOD_CHECK = 15  # Words

    def __init__(self, pattern_cache=None):
        super().__init__()
        self.pattern_cache = pattern_cache
        self.terminology_manager = TerminologyManager()
        logger.info("Initialized HeadingChecks with pattern cache")
        self.heading_pattern = re.compile(r"^(\d+\.)+\s")
        logger.debug(f"Using heading pattern: {self.heading_pattern.pattern}")
        self.category = "heading"

    @staticmethod
    def _normalize_doc_type(doc_type: str) -> str:
        """Convert any 'Advisory Circular', '   advisory circular ', etc.
        into 'ADVISORY_CIRCULAR'. Preserves original string for invalid types."""
        if not isinstance(doc_type, str):
            return str(doc_type)
        # Check if this is a known document type
        known_types = {
            "ADVISORY_CIRCULAR",
            "ORDER",
            "NOTICE",
            "AC",
            "TECHNICAL_STANDARD_ORDER",
            "TSO",
        }
        normalized = re.sub(r"\s+", "_", doc_type.strip()).upper()
        if normalized not in known_types:
            return doc_type  # Preserve original for unknown types
        return normalized

    @CheckRegistry.register("heading")
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for heading issues."""
        doc_type_norm = self._normalize_doc_type(doc_type)
        results = DocumentCheckResult()
        self.run_checks(document, doc_type_norm, results)
        return results

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for heading issues."""
        results = DocumentCheckResult()
        lines = text.split("\n")
        self.check_heading_title(lines, "GENERAL")
        self.check_heading_period(lines, "GENERAL")
        return results

    def _get_doc_type_config(self, doc_type: str) -> Dict[str, Any]:
        """Get configuration for document type."""
        return self.terminology_manager.terminology_data.get("document_types", {}).get(doc_type, {})

    def validate_input(self, doc: List[str]) -> bool:
        """Validate input document content."""
        return isinstance(doc, list) and all(isinstance(line, str) for line in doc)

    @profile_performance
    def check_heading_title(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading titles for validity."""
        doc_type_norm = self._normalize_doc_type(doc_type)
        doc_type_config = self._get_doc_type_config(doc_type_norm)
        logger.debug(f"Document type config: {doc_type_config}")

        if doc_type_config.get("skip_title_check", False):
            logger.info(f"Skipping title check for document type: {doc_type_norm}")
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={
                    "message": f"Title check skipped for document type: {doc_type_norm}",
                    "document_type": doc_type_norm,
                },
            )

        required_headings = doc_type_config.get("required_headings", [])
        issues = []
        headings_found = set()

        logger.info(f"Starting heading title check for document type: {doc_type_norm}")
        logger.debug(f"Required headings: {required_headings}")

        # Get heading words from terminology data
        heading_words = self.terminology_manager.terminology_data.get("heading_words", [])
        logger.debug(f"Available heading words: {heading_words}")

        # Normalize required_headings to support both string and dict entries
        normalized_required_headings = []
        for h in required_headings:
            if isinstance(h, dict):
                normalized_required_headings.append(h)
            else:
                normalized_required_headings.append({"name": h})

        # Build a set of found headings (uppercase, no period)
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for heading format: {line}")
            if not self.heading_pattern.match(line):
                logger.debug(f"Line {i} is not a numbered heading")
                continue
            heading_text = line.split(".", 1)[1].strip()
            heading_text_no_period = heading_text.rstrip(".")

            # Check heading length first
            if len(heading_text_no_period) > self.MAX_HEADING_LENGTH:
                logger.warning(f"Heading exceeds maximum length in line {i}: {heading_text}")
                issues.append(
                    {
                        "type": "length_violation",
                        "line": line,
                        "message": (
                            f"Heading exceeds maximum length of "
                            f"{self.MAX_HEADING_LENGTH} characters."
                        ),
                        "suggestion": (
                            f"Shorten heading to {self.MAX_HEADING_LENGTH} characters or less."
                        ),
                        "category": self.category,
                    }
                )
                # Don't add to headings_found and skip other validations
                continue

            # Check if the heading text contains any of the valid heading words
            # Check if the heading text contains any of the valid heading words
            if not any(word in heading_text_no_period.upper() for word in heading_words):
                logger.warning(
                    "Line %d: Heading '%s' does not use a valid heading word.", i, heading_text
                )
                issues.append(
                    {
                        "type": "invalid_word",
                        "line": line,
                        "message": (
                            "This heading does not use an approved heading word."
                        ),
                        "suggestion": (
                            "Start the heading with one of these words: "
                            f"{', '.join(sorted(heading_words))}"
                        ),
                        "category": self.category,
                    }
                )
                # Don't add to headings_found if it's not a valid heading word
                continue

            # Check if heading is in uppercase
            if heading_text != heading_text.upper():
                logger.warning(f"Heading should be uppercase in line {i}")
                issues.append(
                    {
                        "type": "case_violation",
                        "line": line,
                        "message": "Heading should be uppercase",
                        "suggestion": line.split(".", 1)[0] + ". " + heading_text.upper(),
                        "category": self.category,
                    }
                )
            else:
                normalized = normalize_heading(line)
                if normalized != line:
                    logger.warning(f"Heading format mismatch in line {i}")
                    logger.debug(f"Original: {line}")
                    logger.debug(f"Normalized: {normalized}")
                    issues.append(
                        {
                            "type": "format_violation",
                            "line": line,
                            "message": "Heading formatting issue",
                            "suggestion": normalized,
                            "category": self.category,
                        }
                    )

            # Only add to headings_found if it passed all validations
            headings_found.add(heading_text_no_period.upper())

        # Additional required headings check with conditional logic
        missing_headings = []
        for h in normalized_required_headings:
            heading_name = h["name"]
            is_optional = h.get("optional", False)
            condition = h.get("condition")
            if heading_name.upper() not in headings_found:
                if is_optional or condition:
                    # INFO-level, non-blocking
                    info_message = (
                        f"Missing '{heading_name}' heading. "
                        "This section is needed only if the document cancels an earlier version. "
                        "If not applicable, you can ignore this message."
                    )
                    logger.info(
                        "Heading '%s' is missing. This section is needed only if the document "
                        "cancels an earlier version. If not, you can ignore this info.",
                        heading_name
                    )
                    issues.append(
                        {
                            "type": "missing_optional_heading",
                            "missing": heading_name,
                            "message": info_message,
                            "severity": Severity.INFO,
                            "category": self.category,
                        }
                    )
                else:
                    missing_headings.append(heading_name)
        if missing_headings:
            issues.append(
                {
                    "type": "missing_headings",
                    "missing": list(missing_headings),
                    "message": f'Missing required headings: {", ".join(missing_headings)}',
                    "severity": Severity.ERROR,
                    "category": self.category,
                }
            )

        details = {
            "found_headings": list(headings_found),
            "required_headings": [h["name"] for h in normalized_required_headings],
            "document_type": doc_type_norm,
            "missing_count": len(missing_headings) if required_headings else 0,
        }

        logger.info(f"Heading title check completed. Found {len(issues)} issues")
        logger.debug(f"Result details: {details}")
        # Determine overall severity
        overall_severity = (
            Severity.ERROR
            if any(issue.get("severity") == Severity.ERROR for issue in issues)
            else (
                Severity.WARNING
                if any(issue.get("severity") == Severity.WARNING for issue in issues)
                else (
                    Severity.INFO
                    if any(issue.get("severity") == Severity.INFO for issue in issues)
                    else None
                )
            )
        )
        return DocumentCheckResult(
            success=not any(
                issue.get("severity") == Severity.ERROR or issue.get("severity") == Severity.WARNING
                for issue in issues
            ),
            severity=overall_severity,
            issues=issues,
            details=details,
        )

    def check_heading_period(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """
        Check heading period usage.

        Skips period checks for text longer than MAX_HEADING_CHARS_FOR_PERIOD_CHECK characters
        or MAX_HEADING_WORDS_FOR_PERIOD_CHECK words to avoid false positives from paragraphs
        incorrectly marked as headings.
        """
        issues = []
        doc_type_norm = self._normalize_doc_type(doc_type)
        logger.info(f"Starting heading period check for document type: {doc_type_norm}")

        # Get period requirements from terminology data
        period_requirements = self.terminology_manager.terminology_data.get("heading_periods", {})
        requires_period = period_requirements.get(doc_type_norm, False)
        logger.debug(
            f"Document type {doc_type_norm} "
            "{'requires' if requires_period else 'does not require'} periods"
        )

        # Get heading words from terminology data
        heading_words = self.terminology_manager.terminology_data.get("heading_words", [])

        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for heading period: {line}")
            if any(word in line.upper() for word in heading_words):
                # Skip period check for long text that's a paragraph incorrectly marked as heading
                line_stripped = line.strip()
                word_count = len(line_stripped.split())
                char_count = len(line_stripped)

                if (
                    char_count > self.MAX_HEADING_CHARS_FOR_PERIOD_CHECK
                    or word_count > self.MAX_HEADING_WORDS_FOR_PERIOD_CHECK
                ):
                    logger.debug(
                        f"Skipping period check for line {i} - too long ({char_count} chars, {word_count} words)"
                    )
                    continue

                has_period = line_stripped.endswith(".")
                logger.debug(f"Line {i} has period: {has_period}")
                if requires_period and not has_period:
                    logger.warning(f"Missing required period in line {i}")
                    issues.append(
                        {
                            "line": line,
                            "message": "Heading missing required period",
                            "suggestion": f"{line.strip()}.",
                            "category": self.category,
                        }
                    )
                elif not requires_period and has_period:
                    logger.warning(f"Unexpected period in line {i}")
                    issues.append(
                        {
                            "line": line,
                            "message": "Heading should not end with period",
                            "suggestion": line.strip()[:-1],
                            "category": self.category,
                        }
                    )

        logger.info(f"Heading period check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0, issues=issues, details={"document_type": doc_type_norm}
        )

    def check_heading_structure(self, doc) -> List[Dict[str, Any]]:
        """Check heading sequence structure."""
        issues = []
        logger.info("Starting heading structure check")
        prev_numbers = None

        for i, paragraph in enumerate(doc.paragraphs, 1):
            text = paragraph.text.strip()
            if not text:
                continue

            logger.debug(f"Checking paragraph {i}: {text}")
            # Extract heading numbers (e.g., ["1", "2", "1"] from "1.2.1")
            match = re.match(r"^(\d+\.)+\s*", text)
            if not match:
                logger.debug(f"Paragraph {i} is not a numbered heading")
                continue

            numbers = [n.strip(".") for n in match.group(0).strip().split(".") if n.strip(".")]
            current_level = len(numbers)
            logger.debug(f"Found heading level {current_level} with numbers: {numbers}")

            if prev_numbers is not None:
                prev_level = len(prev_numbers)

                # Check level skipping
                if current_level > prev_level + 1:
                    logger.warning(
                        f"Invalid heading sequence in paragraph {i}: skipped level {prev_level + 1}"
                    )
                    issues.append(
                        {
                            "text": text,
                            "message": f"Invalid heading sequence: skipped level {prev_level + 1}",
                            "suggestion": "Ensure heading levels are sequential",
                            "category": self.category,
                        }
                    )

                # Check sequence within same level
                elif current_level == prev_level:
                    # Compare all but the last number
                    if numbers[:-1] == prev_numbers[:-1]:
                        # Check if the last number is sequential
                        try:
                            prev_last = int(prev_numbers[-1])
                            curr_last = int(numbers[-1])
                            if curr_last != prev_last + 1:
                                logger.warning(
                                    f"Invalid heading sequence in paragraph {i}: expected {prev_last + 1}"
                                )
                                issues.append(
                                    {
                                        "text": text,
                                        "message": f"Invalid heading sequence: expected {prev_last + 1}",
                                        "suggestion": f'Use {".".join(numbers[:-1] + [str(prev_last + 1)])}',
                                        "category": self.category,
                                    }
                                )
                        except ValueError:
                            logger.error(f"Invalid number format in paragraph {i}: {numbers[-1]}")

            prev_numbers = numbers

        logger.info(f"Heading structure check completed. Found {len(issues)} issues")
        return issues

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all heading-related checks."""
        logger.info(f"Running heading checks for document type: {doc_type}")

        # Get all paragraphs with heading style and track their line numbers
        headings_with_lines = []
        line_number = 1

        for paragraph in document.paragraphs:
            if paragraph.style.name.startswith("Heading"):
                headings_with_lines.append((paragraph, line_number))
            line_number += 1

        # Check heading structure
        self._check_heading_hierarchy(headings_with_lines, results)
        self._check_heading_format(headings_with_lines, results, doc_type)

    def _check_heading_sequence(self, current_level: int, previous_level: int) -> Optional[str]:
        """
        Check if heading sequence is valid.
        Returns error message if invalid, None if valid.

        Rules:
        - Can go from any level to H1 or H2 (restart numbering)
        - When going deeper, can only go one level at a time (e.g., H1 to H2, H2 to H3)
        - Can freely go to any higher level (e.g., H3 to H1, H4 to H2)
        """
        # When going to a deeper level, only allow one level at a time
        if current_level > previous_level:
            if current_level > previous_level:
                if current_level != previous_level + 1:
                    return (
                        f"Heading H{current_level} follows H{previous_level}. "
                        f"Missing heading H{previous_level + 1}. "
                        "Add the missing heading to keep correct order."
                    )
            return None

    def _check_heading_hierarchy(self, headings_with_lines, results):
        """Check if headings follow proper hierarchy."""
        previous_level = 0
        for heading, line_number in headings_with_lines:
            level = int(heading.style.name.replace("Heading ", ""))
            error_message = self._check_heading_sequence(level, previous_level)

            if error_message:
                results.add_issue(
                    message=f"{error_message} (Current heading: {heading.text})",
                    severity=Severity.ERROR,
                    line_number=line_number,
                    category=getattr(self, "category", "heading"),
                )
            previous_level = level

    def _check_heading_format(self, headings_with_lines, results, doc_type: str = "GENERAL"):
        """
        Check heading format (capitalization, punctuation, etc).

        Skips period checks for text longer than MAX_HEADING_CHARS_FOR_PERIOD_CHECK characters
        or MAX_HEADING_WORDS_FOR_PERIOD_CHECK words to avoid false positives from paragraphs
        incorrectly marked as headings.
        """
        doc_type_norm = self._normalize_doc_type(doc_type)

        # Get period requirements from terminology data
        period_requirements = self.terminology_manager.terminology_data.get("heading_periods", {})
        requires_period = period_requirements.get(doc_type_norm, False)

        for heading, line_number in headings_with_lines:
            text = heading.text.strip()

            # Skip period check for long text that's likely a paragraph
            # incorrectly marked as heading
            word_count = len(text.split())
            char_count = len(text)

            if (
                char_count > self.MAX_HEADING_CHARS_FOR_PERIOD_CHECK
                or word_count > self.MAX_HEADING_WORDS_FOR_PERIOD_CHECK
            ):
                logger.debug(
                    "Skipping period check for heading: too long (%d chars, %d words): %.50s...",
                    char_count,
                    word_count,
                    text,
                )
                continue

            has_period = text.endswith(".")

            # Check period usage based on document type requirements
            if requires_period and not has_period:
                results.add_issue(
                    message=f"Heading missing required period: {text}",
                    severity=Severity.WARNING,
                    line_number=line_number,
                    category=getattr(self, "category", "heading"),
                )
            elif not requires_period and has_period:
                results.add_issue(
                    message=f"Heading should not end with period: {text}",
                    severity=Severity.WARNING,
                    line_number=line_number,
                    category=getattr(self, "category", "heading"),
                )
