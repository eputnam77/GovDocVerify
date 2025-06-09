import logging
import re
from functools import wraps
from typing import List, Optional

from docx import Document

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.models import DocumentCheckResult, Severity

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


# Message constants for structure checks
class StructureMessages:
    """Static message constants for structure checks."""

    # Paragraph length messages
    PARAGRAPH_LENGTH_WARNING = (
        "Paragraph '{preview}' has {word_count} words, exceeding the {max_words}-word limit. "
        "Consider breaking it up for clarity."
    )

    # Sentence length messages
    SENTENCE_LENGTH_INFO = (
        "Sentence '{preview}' has {word_count} words, exceeding the {max_words}-word limit. "
        "Consider breaking it up for clarity."
    )

    # Section balance messages
    SECTION_BALANCE_INFO = (
        "Section '{name}' has {length} paragraphs, which is much longer than the average of "
        "{avg:.1f}. Consider splitting this section for balance."
    )

    # List formatting messages
    LIST_FORMAT_INCONSISTENT = (
        "Found inconsistent list formatting. "
        "Use a consistent bullet or numbering style in each list."
    )

    # Parentheses messages
    PARENTHESES_UNMATCHED = (
        "Found unmatched parentheses. Add any missing opening or closing parentheses."
    )

    # Cross-reference messages
    CROSS_REFERENCE_INFO = (
        "Found cross-reference. Verify the referenced target exists and is correct."
    )

    # Watermark messages
    WATERMARK_MISSING = (
        "Watermark missing. Add the required watermark unless it is not needed for this document."
    )
    WATERMARK_UNKNOWN_STAGE = "Unknown document stage: {doc_type}"
    WATERMARK_INCORRECT = "Found incorrect watermark for {doc_type} stage. Use {expected}"


class ValidationFormatting:
    """Handles formatting of validation messages for consistency and clarity."""

    WATERMARK_VALIDATION = {
        "missing": "Document is missing required watermark",
        "incorrect": 'Incorrect watermark for {stage} stage. Found: "{found}", Expected: "{expected}"',
        "success": "Watermark validation passed: {watermark}",
    }

    def format_watermark_message(self, result_type: str, **kwargs) -> str:
        """Format watermark validation messages."""
        return self.WATERMARK_VALIDATION[result_type].format(**kwargs)

    @staticmethod
    def format_parentheses_issues(result: DocumentCheckResult) -> List[str]:
        """Format parentheses issues with clear instructions for fixing."""
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                formatted_issues.append(f"    • {issue['message']}")

        return formatted_issues

    @staticmethod
    def format_paragraph_length_issues(result: DocumentCheckResult) -> List[str]:
        """Format paragraph length issues with clear instructions for fixing.

        Args:
            result: DocumentCheckResult containing paragraph length issues

        Returns:
            List[str]: Formatted list of paragraph length issues
        """
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                if isinstance(issue, str):
                    formatted_issues.append(f"    • {issue}")
                elif isinstance(issue, dict) and "message" in issue:
                    formatted_issues.append(f"    • {issue['message']}")
                else:
                    # Fallback for unexpected issue format
                    formatted_issues.append(
                        f"    • Review paragraph for length issues: {str(issue)}"
                    )

        return formatted_issues


def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)

    return wrapper


class WatermarkRequirement:
    def __init__(self, text: str, doc_stage: str):
        self.text = text
        self.doc_stage = doc_stage


class StructureChecks(BaseChecker):
    """Checks for document structure issues."""

    VALID_WATERMARKS = [
        WatermarkRequirement("draft for FAA review", "internal_review"),
        WatermarkRequirement("draft for public comments", "public_comment"),
        WatermarkRequirement("draft for AGC review for public comment", "agc_public_comment"),
        WatermarkRequirement("draft for final issuance", "final_draft"),
        WatermarkRequirement("draft for AGC review for final issuance", "agc_final_review"),
    ]

    def __init__(self):
        super().__init__()
        self.category = "structure"

    @CheckRegistry.register("structure")
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all structure-related checks."""
        logger.info(f"Running structure checks for document type: {doc_type}")

        paragraphs = document.paragraphs
        self._check_section_balance(paragraphs, results)
        self._check_list_formatting(paragraphs, results)
        self._check_cross_references(document, results)
        self._check_parentheses(paragraphs, results)
        self._check_watermark(document, results, doc_type)

    def _get_text_preview(self, text: str, max_words: int = 6) -> str:
        """
        Get a preview of the text showing the first few words.

        Args:
            text: The text to preview
            max_words: Maximum number of words to include in preview

        Returns:
            A string containing the first few words followed by '...' if truncated
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        else:
            preview_words = words[:max_words]
            return " ".join(preview_words) + "..."

    def _check_section_balance(self, paragraphs, results):
        """Check for balanced section lengths."""
        current_section = []
        section_lengths = []
        section_names = []
        current_section_name = None
        list_section_patterns = [
            r"should include.*following",
            r"related materials",
            r"test category",
            r"requirements",
            r"items",
            r"steps",
            r"procedures",
        ]
        list_pattern = re.compile("|".join(list_section_patterns), re.IGNORECASE)
        bullet_pattern = re.compile(r"^[\s]*[•\-\*]\s+")

        logger.debug("Starting section balance check")
        logger.debug(f"List section patterns: {list_section_patterns}")

        for para in paragraphs:
            if para.style.name.startswith("Heading"):
                if current_section:
                    # Check if this was a list section
                    is_list_section = False
                    if current_section_name and list_pattern.search(current_section_name):
                        logger.debug(
                            f"Section '{current_section_name}' identified as list section by title pattern"
                        )
                        is_list_section = True
                    else:
                        # Check if majority of paragraphs are bullet points
                        bullet_count = sum(
                            1 for p in current_section if bullet_pattern.match(p.text)
                        )
                        bullet_percentage = (
                            (bullet_count / len(current_section)) * 100 if current_section else 0
                        )
                        logger.debug(
                            f"Section '{current_section_name}' bullet analysis: {bullet_count}/{len(current_section)} paragraphs are bullets ({bullet_percentage:.1f}%)"
                        )
                        is_list_section = bullet_count > len(current_section) * 0.5
                        if is_list_section:
                            logger.debug(
                                f"Section '{current_section_name}' identified as list section by bullet content"
                            )

                    section_lengths.append((len(current_section), is_list_section))
                    section_names.append(current_section_name)
                    logger.debug(
                        f"Added section '{current_section_name}' with length {len(current_section)} (is_list={is_list_section})"
                    )
                current_section = []
                current_section_name = para.text
            else:
                current_section.append(para)

        # Add last section
        if current_section:
            is_list_section = False
            if current_section_name and list_pattern.search(current_section_name):
                logger.debug(
                    f"Final section '{current_section_name}' identified as list section by title pattern"
                )
                is_list_section = True
            else:
                bullet_count = sum(1 for p in current_section if bullet_pattern.match(p.text))
                bullet_percentage = (
                    (bullet_count / len(current_section)) * 100 if current_section else 0
                )
                logger.debug(
                    f"Final section '{current_section_name}' bullet analysis: "
                    f"{bullet_count}/{len(current_section)} paragraphs are bullets "
                    f"({bullet_percentage:.1f}%)"
                )
                is_list_section = bullet_count > len(current_section) * 0.5
                if is_list_section:
                    logger.debug(
                        f"Final section '{current_section_name}' identified as list section by bullet content"
                    )
            section_lengths.append((len(current_section), is_list_section))
            section_names.append(current_section_name)
            logger.debug(
                f"Added final section '{current_section_name}' with length {len(current_section)} (is_list={is_list_section})"
            )

        # Check for significant imbalance
        if len(section_lengths) > 1:  # Only check if we have at least 2 sections
            # Calculate separate averages for list and non-list sections
            list_sections = [
                (length, name)
                for (length, is_list), name in zip(section_lengths, section_names)
                if is_list
            ]
            non_list_sections = [
                (length, name)
                for (length, is_list), name in zip(section_lengths, section_names)
                if not is_list
            ]

            list_avg = (
                sum(length for length, _ in list_sections) / len(list_sections)
                if list_sections
                else 0
            )
            non_list_avg = (
                sum(length for length, _ in non_list_sections) / len(non_list_sections)
                if non_list_sections
                else 0
            )

            logger.debug(f"List section lengths: {list_sections}")
            logger.debug(f"Non-list section lengths: {non_list_sections}")
            logger.debug(f"List section average: {list_avg}")
            logger.debug(f"Non-list section average: {non_list_avg}")
            logger.debug(f"List section threshold: {list_avg * 3}")
            logger.debug(f"Non-list section threshold: {non_list_avg * 2}")

            # Check each section against appropriate average
            for (length, is_list), name in zip(section_lengths, section_names):
                avg_length = list_avg if is_list else non_list_avg
                threshold = (
                    avg_length * 3 if is_list else avg_length * 2
                )  # Higher threshold for list sections

                logger.debug(
                    f"Checking section '{name}': length={length}, is_list={is_list}, avg={avg_length:.1f}, threshold={threshold:.1f}"
                )

                if length > threshold:
                    message = StructureMessages.SECTION_BALANCE_INFO.format(
                        name=name, length=length, avg=avg_length
                    )
                    logger.debug(f"Adding issue: {message}")
                    results.add_issue(
                        message=message,
                        severity=Severity.INFO,
                        line_number=section_names.index(name) + 1,
                    )
                    logger.debug(f"Current issues: {results.issues}")
                else:
                    logger.debug(f"Section '{name}' is within acceptable length range")

    def _check_list_formatting(self, paragraphs, results):
        """Check for consistent list formatting."""
        list_markers = ["•", "-", "*", "1.", "a.", "i."]
        current_list_style = None

        for i, para in enumerate(paragraphs):
            text = para.text.strip()
            for marker in list_markers:
                if text.startswith(marker):
                    if current_list_style and marker != current_list_style:
                        results.add_issue(
                            message=StructureMessages.LIST_FORMAT_INCONSISTENT,
                            severity=Severity.INFO,
                            line_number=i + 1,
                        )
                    current_list_style = marker
                    break
            else:
                current_list_style = None

    def _check_parentheses(self, paragraphs, results):
        """Check for unmatched parentheses."""
        for i, para in enumerate(paragraphs):
            text = para.text
            open_count = text.count("(")
            close_count = text.count(")")
            if open_count != close_count:
                results.add_issue(
                    message=StructureMessages.PARENTHESES_UNMATCHED,
                    severity=Severity.WARNING,
                    line_number=i + 1,
                )

    def _check_watermark(
        self, document: Document, results: DocumentCheckResult, doc_type: str
    ) -> None:
        """Check if document has appropriate watermark for its stage."""
        watermark_text = self._extract_watermark(document)

        if not watermark_text:
            results.add_issue(
                message=StructureMessages.WATERMARK_MISSING, severity=Severity.ERROR, line_number=1
            )
            return

        # Find matching requirement for stage
        expected_watermark = next(
            (w for w in self.VALID_WATERMARKS if w.doc_stage == doc_type), None
        )

        if not expected_watermark:
            results.add_issue(
                message=StructureMessages.WATERMARK_UNKNOWN_STAGE.format(doc_type=doc_type),
                severity=Severity.ERROR,
                line_number=1,
            )
            return

        if watermark_text != expected_watermark.text:
            results.add_issue(
                message=StructureMessages.WATERMARK_INCORRECT.format(
                    doc_type=doc_type, expected=expected_watermark.text
                ),
                severity=Severity.ERROR,
                line_number=1,
            )

    def _extract_watermark(self, doc: Document) -> Optional[str]:
        """Extract watermark text from Word document headers/footers."""
        # First check document body for watermark
        for para in doc.paragraphs:
            if para.text.strip().upper() == "DRAFT":
                return para.text.strip()

        # TODO: Implement header/footer watermark extraction
        # This will need to use python-docx to extract watermark
        # from document sections and headers/footers
        return None

    def _check_cross_references(self, document, results):
        """Check for cross-references."""
        for i, para in enumerate(document.paragraphs):
            text = para.text
            if re.search(
                r"(?:see|refer to|as discussed in).*(?:paragraph|section)\s+\d+(?:\.\d+)*",
                text,
                re.IGNORECASE,
            ):
                results.add_issue(
                    message=StructureMessages.CROSS_REFERENCE_INFO,
                    severity=Severity.INFO,
                    line_number=i + 1,
                )

    def _extract_paragraph_numbering(self, doc: Document) -> List[tuple]:
        """Extract paragraph numbering from headings."""
        heading_structure = []
        for para in doc.paragraphs:
            if para.style.name.startswith("Heading"):
                if match := re.match(r"^([A-Z]?\.?\d+(?:\.\d+)*)\s+(.+)$", para.text):
                    heading_structure.append((match.group(1), match.group(2)))
        return heading_structure

    @profile_performance
    def check_cross_references(self, doc_path: str) -> DocumentCheckResult:
        """Check for missing cross-referenced elements in the document."""
        try:
            doc = Document(doc_path)
        except Exception as e:
            logger.error(f"Error reading the document: {e}")
            return DocumentCheckResult(success=False, issues=[{"error": str(e)}], details={})

        heading_structure = self._extract_paragraph_numbering(doc)
        valid_sections = {number for number, _ in heading_structure}
        tables = set()
        figures = set()
        issues = []

        skip_patterns = [
            r"(?:U\.S\.C\.|USC)\s+(?:§+\s*)?(?:Section|section)?\s*\d+",
            r"Section\s+\d+(?:\([a-z]\))*\s+of\s+(?:the\s+)?(?:United States Code|U\.S\.C\.)",
            r"Section\s+\d+(?:\([a-z]\))*\s+of\s+Title\s+\d+",
            r"(?:Section|§)\s*\d+(?:\([a-z]\))*\s+of\s+the\s+Act",
            r"Section\s+\d+\([a-z]\)",
            r"§\s*\d+\([a-z]\)",
            r"\d+\s*(?:CFR|C\.F\.R\.)",
            r"Part\s+\d+(?:\.[0-9]+)*\s+of\s+Title\s+\d+",
            r"Public\s+Law\s+\d+[-–]\d+",
            r"Title\s+\d+,\s+Section\s+\d+(?:\([a-z]\))*",
            r"\d+\s+U\.S\.C\.\s+\d+(?:\([a-z]\))*",
        ]
        skip_regex = re.compile("|".join(skip_patterns), re.IGNORECASE)

        try:
            # Extract tables and figures
            for para in doc.paragraphs:
                text = para.text.strip() if hasattr(para, "text") else ""

                if text.lower().startswith("table"):
                    matches = [
                        re.match(r"^table\s+(\d{1,2}(?:-\d+)?)\b", text, re.IGNORECASE),
                        re.match(r"^table\s+(\d{1,2}(?:\.\d+)?)\b", text, re.IGNORECASE),
                    ]
                    for match in matches:
                        if match:
                            tables.add(match.group(1))

                if text.lower().startswith("figure"):
                    matches = [
                        re.match(r"^figure\s+(\d{1,2}(?:-\d+)?)\b", text, re.IGNORECASE),
                        re.match(r"^figure\s+(\d{1,2}(?:\.\d+)?)\b", text, re.IGNORECASE),
                    ]
                    for match in matches:
                        if match:
                            figures.add(match.group(1))

            # Check references
            for para in doc.paragraphs:
                para_text = para.text.strip() if hasattr(para, "text") else ""
                if not para_text or skip_regex.search(para_text):
                    continue

                # Table, Figure, and Section reference checks
                self._check_table_references(para_text, tables, issues)
                self._check_figure_references(para_text, figures, issues)
                self._check_section_references(para_text, valid_sections, skip_regex, issues)

        except Exception as e:
            logger.error(f"Error processing cross references: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[
                    {"type": "error", "message": f"Error processing cross references: {str(e)}"}
                ],
                details={},
            )

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details={
                "total_tables": len(tables),
                "total_figures": len(figures),
                "found_tables": sorted(list(tables)),
                "found_figures": sorted(list(figures)),
                "heading_structure": heading_structure,
                "valid_sections": sorted(list(valid_sections)),
            },
        )

    def _check_figure_references(self, para_text: str, figures: set, issues: list) -> None:
        """Check figure references."""
        figure_refs = re.finditer(
            r"(?:see|in|refer to)?\s*(?:figure|Figure)\s+(\d{1,2}(?:[-\.]\d+)?)\b", para_text
        )
        for match in figure_refs:
            ref = match.group(1)
            if ref not in figures:
                issues.append(
                    {
                        "type": "Figure",
                        "reference": ref,
                        "context": para_text,
                        "message": f"Referenced Figure {ref} not found in document",
                        "severity": Severity.ERROR,
                    }
                )

    def _check_section_references(
        self, para_text: str, valid_sections: set, skip_regex: re.Pattern, issues: list
    ) -> None:
        """Check section references."""
        if skip_regex.search(para_text):
            return

        section_refs = re.finditer(
            r"(?:paragraph|section|appendix)\s+([A-Z]?\.?\d+(?:\.\d+)*)", para_text, re.IGNORECASE
        )

        for match in section_refs:
            ref = match.group(1).strip(".")
            if ref not in valid_sections:
                found = False
                for valid_section in valid_sections:
                    if valid_section.strip(".") == ref.strip("."):
                        found = True
                        break

                if not found:
                    issues.append(
                        {
                            "type": "Paragraph",
                            "reference": ref,
                            "context": para_text,
                            "message": f"Confirm paragraph {ref} referenced in '{para_text}' exists in the document",
                            "severity": Severity.ERROR,
                        }
                    )

    def _check_table_references(self, para_text: str, tables: set, issues: list) -> None:
        """Check table references."""
        table_refs = re.finditer(
            r"(?:see|in|refer to)?\s*(?:table|Table)\s+(\d{1,2}(?:[-\.]\d+)?)\b", para_text
        )
        for match in table_refs:
            ref = match.group(1)
            if ref not in tables:
                issues.append(
                    {
                        "type": "Table",
                        "reference": ref,
                        "context": para_text,
                        "message": f"Referenced Table {ref} not found in document",
                        "severity": Severity.ERROR,
                    }
                )

    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for structure issues. Accepts a python-docx Document object."""
        logger.info("[StructureChecks] check_document called")
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        logger.info("[StructureChecks] check_document completed")
        return results

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for structure issues. Accepts a plain string."""
        logger.info("[StructureChecks] check_text called")
        results = DocumentCheckResult()
        lines = text.split("\n")
        # For text, treat each non-empty line as a paragraph
        paragraphs = [
            type("Para", (), {"text": line, "style": type("Style", (), {"name": ""})()})()
            for line in lines
            if line.strip()
        ]
        self._check_section_balance(paragraphs, results)
        self._check_list_formatting(paragraphs, results)
        self._check_parentheses(paragraphs, results)
        logger.info("[StructureChecks] check_text completed")
        return results

    # CONTRACT: All internal checkers expect a list of paragraph-like objects (with .text).
    # check_text always converts input to this format before calling internal checkers.
