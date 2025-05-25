from typing import List, Dict, Any
import re
from documentcheckertool.models import DocumentCheckResult, Severity
from .base_checker import BaseChecker
import logging
from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.utils.terminology_utils import TerminologyManager
from docx import Document

logger = logging.getLogger(__name__)

class TableFigureReferenceCheck(BaseChecker):
    """Class for checking table and figure references."""

    def __init__(self):
        self.terminology_manager = TerminologyManager()
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
            return DocumentCheckResult(
                success=False,
                issues=[{'error': 'Invalid document input'}]
            )

        logger.debug(f"Starting reference check with document type: {doc_type}")
        logger.debug(f"Document length: {len(doc)} lines")

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

    @CheckRegistry.register('reference')
    def check_text(self, text) -> DocumentCheckResult:
        """
        Accepts a string or list of strings, and calls the main check logic.
        """
        if isinstance(text, list):
            lines = text
        else:
            lines = str(text).split('\n')
        return self._check_core(lines)

    def _check_core(self, lines: List[str]) -> DocumentCheckResult:
        """Main logic for checking references, expects a list of strings."""
        logger.debug(f"Starting text check with {len(lines)} lines")

        # Handle empty list case (success) vs empty string (error)
        if lines == []:                       # explicit empty list → success
            logger.debug("Empty list provided - nothing to check")
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={'total_issues': 0, 'issues_by_type': {'table': 0, 'figure': 0}}
            )
        if not lines:
            logger.debug("Empty content provided")
            return DocumentCheckResult(
                success=False,
                issues=[{'error': 'Empty content'}],
                details={'total_issues': 1, 'issues_by_type': {'table': 0, 'figure': 0}}
            )

        issues = []
        logger.debug("Initializing text check patterns")

        # Pattern to identify table/figure captions
        caption_pattern = re.compile(r'^(Table|Figure)\s+\d+(?:[\.-]\d+)*\.\s+[A-Z]', re.IGNORECASE)
        logger.debug(f"Caption pattern: {caption_pattern.pattern}")

        # Patterns for references within sentences and at start
        # Allow decimal points, ranges, and plurals in numbers
        table_ref_pattern = re.compile(r'\b([Tt]able)s?\s+(\d+(?:[\.-]\d+)*)')
        figure_ref_pattern = re.compile(r'\b([Ff]igure)s?\s+(\d+(?:[\.-]\d+)*)')
        logger.debug(f"Table reference pattern: {table_ref_pattern.pattern}")
        logger.debug(f"Figure reference pattern: {figure_ref_pattern.pattern}")

        # Special context patterns
        special_context_patterns = [
            r'^[•\-\*]\s+',  # List items
            r'^\|\s*',       # Table cells
            r'^```',         # Code blocks
            r'^<[^>]+>',     # HTML tags
            r'^[\*\`\_]+',   # Markdown formatting
        ]
        special_context_pattern = re.compile('|'.join(special_context_patterns))

        # Track if we're inside a code block
        in_code_block = False

        for line_idx, line in enumerate(lines):
            logger.debug(f"Processing line {line_idx + 1}: {line[:50]}...")

            # Handle code block markers
            if line.strip() == '```':
                in_code_block = not in_code_block
                logger.debug(f"Code block state changed to: {in_code_block}")
                continue

            # Skip if this is a caption line
            if caption_pattern.match(line.strip()):
                logger.debug(f"Skipping caption line: {line.strip()}")
                continue

            # Skip if we're in a code block
            if in_code_block:
                logger.debug("Skipping line in code block")
                continue

            # Check for special contexts
            is_special_context = bool(special_context_pattern.match(line.strip()))
            logger.debug(f"Line is in special context: {is_special_context}")

            # Clean the line for reference checking while preserving context
            cleaned_line = line.strip()
            # Remove quotes and parentheses for reference checking but preserve their presence
            has_quotes = '"' in cleaned_line or "'" in cleaned_line
            has_parentheses = '(' in cleaned_line or ')' in cleaned_line
            cleaned_line = re.sub(r'["\']|\(|\)', '', cleaned_line)
            logger.debug(f"Cleaned line: {cleaned_line}")

            # Check for references
            for pattern, ref_type in [(table_ref_pattern, "Table"), (figure_ref_pattern, "Figure")]:
                matches = list(pattern.finditer(cleaned_line))
                logger.debug(f"Found {len(matches)} {ref_type} references in line")

                for match in matches:
                    ref_text = match.group()
                    word = match.group(1)

                    # 1. Handle references wrapped in quotes or parentheses *first*
                    if (has_quotes or has_parentheses) and word[0].isupper():
                        logger.debug(f"Found uppercase {ref_type} reference in quotes/parentheses")
                        issues.append({
                            "reference": ref_text,
                            "issue": f"{ref_type} reference in quotes/parentheses should be lowercase",
                            "line": line,
                            "correct_form": ref_text.lower()
                        })
                        continue

                    # 2. Decide if the reference is "complex"
                    rest = ref_text.split(word, 1)[1]  # part after "Table"/"Figure"
                    is_complex = (
                        "." in rest or "-" in rest or
                        "\t" in rest or "\n" in rest or
                        re.search(r"\s{2,}", rest) is not None
                    )
                    if is_complex:
                        logger.debug(f"Skipping style check for complex reference: {ref_text}")
                        continue

                    # Get text before the reference and clean it
                    text_before = cleaned_line[:match.start()].strip()
                    text_before_clean = re.sub(r'^[\s\W]+', '', text_before)
                    logger.debug(f"Text before reference: '{text_before}' (cleaned: '{text_before_clean}')")

                    # Start of a (sub-)sentence if nothing before, or previous char is . : ;
                    is_sentence_start = not text_before_clean or text_before_clean.endswith(('.', ':', ';'))
                    logger.debug(f"Reference is at sentence start: {is_sentence_start}")

                    # Skip validation for special contexts
                    if is_special_context:
                        logger.debug(f"Skipping validation for special context: {ref_text}")
                        continue

                    if is_sentence_start and word[0].islower():
                        logger.debug(f"Found lowercase {ref_type} reference at sentence start")
                        issues.append({
                            'reference': ref_text,
                            'issue': f"{ref_type} reference at sentence start should be capitalized",
                            'line': line,
                            'correct_form': ref_text.capitalize()
                        })
                    elif (has_quotes or has_parentheses) and word[0].isupper():
                        logger.debug(f"Found uppercase {ref_type} reference in quotes/parentheses")
                        issues.append({
                            'reference': ref_text,
                            'issue': f"{ref_type} reference in quotes/parentheses should be lowercase",
                            'line': line,
                            'correct_form': ref_text.lower()
                        })
                    elif not is_sentence_start and word[0].isupper():
                        logger.debug(f"Found uppercase {ref_type} reference within sentence")
                        issues.append({
                            'reference': ref_text,
                            'issue': f"{ref_type} reference within sentence should be lowercase",
                            'line': line,
                            'correct_form': ref_text.lower()
                        })

        logger.debug(f"Text check complete. Found {len(issues)} issues")
        logger.debug(f"Issues by type: {len([i for i in issues if 'Table' in i['issue']])} table issues, {len([i for i in issues if 'Figure' in i['issue']])} figure issues")

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.ERROR if issues else Severity.INFO,
            issues=issues,
            details={
                'total_issues': len(issues),
                'issues_by_type': {
                    'table': len([i for i in issues if 'Table' in i['issue']]),
                    'figure': len([i for i in issues if 'Figure' in i['issue']])
                }
            }
        )

    @CheckRegistry.register('reference')
    def run_checks(self, document, doc_type, results: DocumentCheckResult) -> None:
        if hasattr(document, 'paragraphs'):
            lines = [p.text for p in document.paragraphs]
        elif isinstance(document, list):
            lines = document
        else:
            lines = str(document).split('\n')
        check_result = self._check_core(lines)
        results.issues.extend(check_result.issues)
        results.success = check_result.success

    @CheckRegistry.register('reference')
    def check_document(self, document, doc_type) -> DocumentCheckResult:
        """
        Accepts a Document, list, or str. Normalizes to a list of strings (paragraphs) and calls check_text.
        """
        if hasattr(document, 'paragraphs'):
            lines = [p.text for p in document.paragraphs]
        elif isinstance(document, list):
            lines = document
        else:
            lines = str(document).split('\n')
        return self._check_core('\n'.join(lines))