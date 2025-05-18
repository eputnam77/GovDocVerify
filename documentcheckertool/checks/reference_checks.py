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

    @CheckRegistry.register('reference')
    def check(self, doc: List[str], doc_type: str = "GENERAL") -> DocumentCheckResult:
        """Check for correctly formatted table and figure references.

        Args:
            doc: List of strings representing document lines
            doc_type: Type of document being checked (default: "GENERAL")

        Returns:
            DocumentCheckResult containing check results and any issues found
        """
        logger.debug(f"Starting reference check with document type: {doc_type}")
        logger.debug(f"Document length: {len(doc)} lines")

        if not self.validate_input(doc):
            logger.error("Invalid document input detected")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        issues = self.check_text(doc)
        logger.debug(f"Reference check complete. Found {len(issues)} issues")

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details={
                'total_issues': len(issues),
                'issues_by_type': {
                    'table': len([i for i in issues if 'Table' in i['issue']]),
                    'figure': len([i for i in issues if 'Figure' in i['issue']])
                }
            }
        )

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

    def check_text(self, content: List[str]) -> List[Dict[str, Any]]:
        """Check text content for table and figure reference issues."""
        logger.debug(f"Starting text check with {len(content)} lines")
        if not content:
            logger.debug("Empty content provided")
            return []

        issues = []
        logger.debug("Initializing text check patterns")

        # Pattern to identify table/figure captions
        caption_pattern = re.compile(r'^(Table|Figure)\s+\d+[-\d]*\.\s+[A-Z]', re.IGNORECASE)
        logger.debug(f"Caption pattern: {caption_pattern.pattern}")

        # Patterns for references within sentences and at start
        table_ref_pattern = re.compile(r'\b([Tt]able)\s+\d+(?:-\d+)?')
        figure_ref_pattern = re.compile(r'\b([Ff]igure)\s+\d+(?:-\d+)?')
        logger.debug(f"Table reference pattern: {table_ref_pattern.pattern}")
        logger.debug(f"Figure reference pattern: {figure_ref_pattern.pattern}")

        for line_idx, line in enumerate(content):
            logger.debug(f"Processing line {line_idx + 1}: {line[:50]}...")

            # Skip if this is a caption line
            if caption_pattern.match(line.strip()):
                logger.debug(f"Skipping caption line: {line.strip()}")
                continue

            # Check for references
            for pattern, ref_type in [(table_ref_pattern, "Table"), (figure_ref_pattern, "Figure")]:
                matches = list(pattern.finditer(line))
                logger.debug(f"Found {len(matches)} {ref_type} references in line")

                for match in matches:
                    ref = match.group()
                    word = match.group(1)
                    logger.debug(f"Found reference: {ref} (word: {word})")

                    # Get text before the reference
                    text_before = line[:match.start()].strip()
                    logger.debug(f"Text before reference: '{text_before}'")

                    # Determine if reference is at start of sentence
                    is_sentence_start = not text_before or text_before.endswith((':',';'))
                    logger.debug(f"Reference is at sentence start: {is_sentence_start}")

                    if is_sentence_start and word[0].islower():
                        logger.debug(f"Found lowercase {ref_type} reference at sentence start")
                        issues.append({
                            'reference': ref,
                            'issue': f"{ref_type} reference at sentence start should be capitalized",
                            'line': line,
                            'correct_form': ref.capitalize()
                        })
                    elif not is_sentence_start and word[0].isupper():
                        logger.debug(f"Found uppercase {ref_type} reference within sentence")
                        issues.append({
                            'reference': ref,
                            'issue': f"{ref_type} reference within sentence should be lowercase",
                            'line': line,
                            'correct_form': ref.lower()
                        })

        logger.debug(f"Text check complete. Found {len(issues)} issues")
        logger.debug(f"Issues by type: {len([i for i in issues if 'Table' in i['issue']])} table issues, {len([i for i in issues if 'Figure' in i['issue']])} figure issues")
        return issues