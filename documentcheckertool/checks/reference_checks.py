import logging
import re
from typing import List

from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.utils.terminology_utils import TerminologyManager

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
            lines = str(text).split('\n')

        return self._check_document_title_formatting(lines, doc_type)

    def _check_document_title_formatting(self, lines: List[str], doc_type: str) -> DocumentCheckResult:
        """Check for proper document title formatting based on document type."""
        logger.debug(f"Checking document title formatting for doc_type: {doc_type}")
        issues = []

        # Pattern to match document references with titles
        # Matches various document types: AC, Order, etc.
        # Captures the title part between the document reference and "dated"
        # Updated pattern to handle quoted titles with commas inside
        doc_title_pattern = re.compile(
            r'\b(?:AC|Order|AD|SFAR|Notice|Policy|Memo)\s+[\d.-]+[A-Z]?,\s*([^,]*(?:"[^"]*"[^,]*)*[^,]*?)(?:,\s*dated|\s+dated)',
            re.IGNORECASE
        )

        for line_idx, line in enumerate(lines):
            logger.debug(f"Processing line {line_idx + 1}: {line[:100]}...")

            # Find document references with titles
            matches = doc_title_pattern.finditer(line)

            for match in matches:
                title_text = match.group(1).strip()
                # Clean up any trailing punctuation that might be captured
                title_text = title_text.rstrip(',')
                logger.debug(f"Found document title: '{title_text}'")

                # Check if this is an Advisory Circular document
                if doc_type == "Advisory Circular":
                    # For ACs, titles should be in italics (markdown style *text*)
                    # Check for incorrect formats

                    # Check if title is in quotes (incorrect for ACs)
                    if (title_text.startswith('"') and title_text.endswith('"')) or \
                       (title_text.startswith("'") and title_text.endswith("'")):
                        # Remove quotes and any trailing comma/punctuation
                        clean_title = title_text.strip('\"\'').rstrip(',').strip()
                        issues.append({
                            "line": line,
                            "line_number": line_idx + 1,
                            "title": title_text,
                            "issue": "AC document titles should use italics, not quotation marks",
                            "incorrect_format": title_text,
                            "correct_format": f"*{clean_title}*",
                            "severity": Severity.ERROR
                        })
                        logger.debug(f"Found quoted title in AC: {title_text}")

                    # Check if title has no formatting (incorrect for ACs)
                    elif not (title_text.startswith('*') and title_text.endswith('*')) and \
                         not (title_text.startswith('"') and title_text.endswith('"')) and \
                         not (title_text.startswith("'") and title_text.endswith("'")):
                        issues.append({
                            "line": line,
                            "line_number": line_idx + 1,
                            "title": title_text,
                            "issue": "AC document titles should be formatted in italics",
                            "incorrect_format": title_text,
                            "correct_format": f"*{title_text.strip()}*",
                            "severity": Severity.ERROR
                        })
                        logger.debug(f"Found unformatted title in AC: {title_text}")

                    # Title is correctly formatted in italics - no issue
                    elif title_text.startswith('*') and title_text.endswith('*'):
                        logger.debug(f"Correctly formatted AC title: {title_text}")

                else:
                    # For non-AC documents, titles should be in quotes
                    # Check if title is in italics (incorrect for non-ACs)
                    if title_text.startswith('*') and title_text.endswith('*'):
                        # Remove asterisks
                        clean_title = title_text.strip('*').strip()
                        issues.append({
                            "line": line,
                            "line_number": line_idx + 1,
                            "title": title_text,
                            "issue": f"{doc_type} document titles should use quotation marks, not italics",
                            "incorrect_format": title_text,
                            "correct_format": f'"{clean_title}"',
                            "severity": Severity.ERROR
                        })
                        logger.debug(f"Found italicized title in non-AC: {title_text}")

                    # Check if title has no formatting (incorrect for non-ACs)
                    elif not (title_text.startswith('"') and title_text.endswith('"')) and \
                         not (title_text.startswith("'") and title_text.endswith("'")) and \
                         not (title_text.startswith('*') and title_text.endswith('*')):
                        issues.append({
                            "line": line,
                            "line_number": line_idx + 1,
                            "title": title_text,
                            "issue": f"{doc_type} document titles should be formatted in quotation marks",
                            "incorrect_format": title_text,
                            "correct_format": f'"{title_text.strip()}"',
                            "severity": Severity.ERROR
                        })
                        logger.debug(f"Found unformatted title in non-AC: {title_text}")

        logger.debug(f"Document title formatting check complete. Found {len(issues)} issues")

        # Ensure all issues have the correct category
        for issue in issues:
            if 'category' not in issue:
                issue['category'] = getattr(self, 'category', 'formatting')

        return DocumentCheckResult(
            success=len(issues) == 0,
            severity=Severity.ERROR if issues else Severity.INFO,
            issues=issues,
            details={
                'total_issues': len(issues),
                'doc_type': doc_type
            }
        )

    def run_checks(self, document, doc_type, results: DocumentCheckResult) -> None:
        """Run document title formatting checks."""
        if hasattr(document, 'paragraphs'):
            lines = [p.text for p in document.paragraphs]
        elif hasattr(document, 'text'):
            lines = str(document.text).split('\n')
        elif isinstance(document, list):
            lines = document
        else:
            lines = str(document).split('\n')

        check_result = self._check_document_title_formatting(lines, doc_type)

        # Only mark as failed if there are actual errors
        if not check_result.success:
            results.success = False

        # Add formatted issues to results using static messages
        for issue in check_result.issues:
            # Create user-friendly message
            title = issue.get("title", "")
            incorrect_format = issue.get("incorrect_format", "")
            correct_format = issue.get("correct_format", "")
            issue_text = issue.get("issue", "")

            # Map issue text to static messages
            if "AC document titles should use italics, not quotation marks" in issue_text:
                message = f"{ReferenceMessages.AC_TITLE_USE_ITALICS}. Change '{incorrect_format}' to '{correct_format}'"
            elif "AC document titles should be formatted in italics" in issue_text:
                message = f"{ReferenceMessages.AC_TITLE_FORMAT_ITALICS}. Change '{incorrect_format}' to '{correct_format}'"
            elif "document titles should use quotation marks, not italics" in issue_text:
                message = f"{ReferenceMessages.NON_AC_TITLE_USE_QUOTES}. Change '{incorrect_format}' to '{correct_format}'"
            elif "document titles should be formatted in quotation marks" in issue_text:
                message = f"{ReferenceMessages.NON_AC_TITLE_FORMAT_QUOTES}. Change '{incorrect_format}' to '{correct_format}'"
            else:
                # Fallback for any unmapped messages
                if incorrect_format and correct_format:
                    message = f"{issue_text}. Change '{incorrect_format}' to '{correct_format}'"
                else:
                    message = issue_text

            results.add_issue(
                message=message,
                severity=issue.get("severity", Severity.WARNING),
                line_number=issue.get("line_number", 0),
                category=getattr(self, "category", "reference")
            )

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
        if not lines or (len(lines) == 1 and not lines[0].strip()):
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

        # Ensure all issues have the correct category
        for issue in issues:
            if 'category' not in issue:
                issue['category'] = getattr(self, 'category', 'formatting')

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

    def run_checks(self, document, doc_type, results: DocumentCheckResult) -> None:
        if hasattr(document, 'paragraphs'):
            lines = [p.text for p in document.paragraphs]
        elif hasattr(document, 'text'):
            lines = str(document.text).split('\n')
        elif isinstance(document, list):
            lines = document
        else:
            lines = str(document).split('\n')

        check_result = self._check_core(lines)

        # Only mark as failed if there are actual errors
        if not check_result.success:
            results.success = False

        # Add formatted issues to results using static messages like format_checks
        for issue in check_result.issues:
            # Create user-friendly message from the issue data
            reference = issue.get('reference', '')
            issue_text = issue.get('issue', '')
            correct_form = issue.get('correct_form', '')

            # Map issue text to static messages
            if "Table reference at sentence start should be capitalized" in issue_text:
                message = f"{ReferenceMessages.TABLE_REF_SENTENCE_START}. Change '{reference}' to '{correct_form}'"
            elif "Table reference within sentence should be lowercase" in issue_text:
                message = f"{ReferenceMessages.TABLE_REF_WITHIN_SENTENCE}. Change '{reference}' to '{correct_form}'"
            elif "Table reference in quotes/parentheses should be lowercase" in issue_text:
                message = f"{ReferenceMessages.TABLE_REF_IN_QUOTES_PARENS}. Change '{reference}' to '{correct_form}'"
            elif "Figure reference at sentence start should be capitalized" in issue_text:
                message = f"{ReferenceMessages.FIGURE_REF_SENTENCE_START}. Change '{reference}' to '{correct_form}'"
            elif "Figure reference within sentence should be lowercase" in issue_text:
                message = f"{ReferenceMessages.FIGURE_REF_WITHIN_SENTENCE}. Change '{reference}' to '{correct_form}'"
            elif "Figure reference in quotes/parentheses should be lowercase" in issue_text:
                message = f"{ReferenceMessages.FIGURE_REF_IN_QUOTES_PARENS}. Change '{reference}' to '{correct_form}'"
            else:
                # Fallback for any unmapped messages
                if reference and correct_form:
                    message = f"{issue_text}. Change '{reference}' to '{correct_form}'"
                else:
                    message = issue_text

            results.add_issue(
                message=message,
                severity=Severity.WARNING,
                line_number=0,  # Line numbers aren't tracked in the current issue format
                category=getattr(self, "category", "reference")
            )

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
            ref_type = issue.get('type', '')
            ref_num = issue.get('reference', '')
            context = issue.get('context', '').strip()

            if context:  # Only include context if it exists
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} referenced in '{context}' exists in the document"
                )
            else:
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} exists in the document"
                )

        return formatted_issues
