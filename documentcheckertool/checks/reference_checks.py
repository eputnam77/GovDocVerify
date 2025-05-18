from typing import List, Dict, Any
import re
from documentcheckertool.models import DocumentCheckResult, Severity
from .base_checker import BaseChecker
import logging

logger = logging.getLogger(__name__)

class TableFigureReferenceCheck(BaseChecker):
    """Check for correctly formatted table and figure references."""

    def validate_input(self, doc: List[str]) -> bool:
        """Validate the input document."""
        logger.debug("Validating input document")
        if not isinstance(doc, list):
            logger.debug("Input is not a list")
            return False
        if not all(isinstance(line, str) for line in doc):
            logger.debug("Not all elements are strings")
            return False
        logger.debug("Input validation successful")
        return True

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content for table/figure reference issues."""
        logger.debug(f"Starting check_text with content length: {len(content) if content else 0}")

        if not content:
            logger.debug("Empty content received, returning error result")
            return DocumentCheckResult(success=False, issues=[{'error': 'Empty content'}])

        # Split content into lines
        lines = content.split('\n')
        logger.debug(f"Split content into {len(lines)} lines")
        return self.check(lines, "GENERAL")  # Default doc type

    def check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check for correctly formatted table and figure references."""
        logger.debug(f"Starting check with document type: {doc_type}")

        if not self.validate_input(doc):
            logger.debug("Invalid document input detected")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        incorrect_references = []

        # Pattern to identify table/figure captions - must be capitalized and end with a period
        caption_pattern = re.compile(r'^(Table|Figure)\s+\d+[-\d]*\.\s+[A-Z]', re.IGNORECASE)
        logger.debug("Initialized caption pattern for table/figure detection")

        # Patterns for references within sentences and at start
        table_ref_pattern = re.compile(r'\b([Tt]able)\s+\d+(?:-\d+)?')
        figure_ref_pattern = re.compile(r'\b([Ff]igure)\s+\d+(?:-\d+)?')
        logger.debug("Initialized reference patterns for table and figure detection")

        for paragraph_idx, paragraph in enumerate(doc):
            logger.debug(f"Processing paragraph {paragraph_idx + 1}: {paragraph[:50]}...")

            # Skip if this is a caption line - must be capitalized and end with a period
            if caption_pattern.match(paragraph.strip()):
                logger.debug(f"Skipping caption line: {paragraph.strip()}")
                continue

            # Split into sentences while preserving punctuation
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            logger.debug(f"Split paragraph into {len(sentences)} sentences")

            for sentence_idx, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    logger.debug(f"Skipping empty sentence at index {sentence_idx}")
                    continue

                logger.debug(f"Processing sentence {sentence_idx + 1}: {sentence[:50]}...")

                # Check table references
                for pattern, ref_type in [(table_ref_pattern, "Table"), (figure_ref_pattern, "Figure")]:
                    matches = list(pattern.finditer(sentence))
                    logger.debug(f"Found {len(matches)} {ref_type} references in sentence")

                    for match in matches:
                        ref = match.group()
                        word = match.group(1)  # The actual "Table" or "Figure" word
                        logger.debug(f"Found reference: {ref} (word: {word})")

                        # Get text before the reference
                        text_before = sentence[:match.start()].strip()
                        logger.debug(f"Text before reference: '{text_before}'")

                        # Determine if reference is at start of sentence
                        is_sentence_start = not text_before or text_before.endswith((':',';'))
                        logger.debug(f"Reference is at sentence start: {is_sentence_start}")

                        if is_sentence_start and word[0].islower():
                            logger.debug(f"Found lowercase {ref_type} reference at sentence start")
                            incorrect_references.append({
                                'reference': ref,
                                'issue': f"{ref_type} reference at sentence start should be capitalized",
                                'sentence': sentence,
                                'correct_form': ref.capitalize()
                            })
                        elif not is_sentence_start and word[0].isupper():
                            logger.debug(f"Found uppercase {ref_type} reference within sentence")
                            incorrect_references.append({
                                'reference': ref,
                                'issue': f"{ref_type} reference within sentence should be lowercase",
                                'sentence': sentence,
                                'correct_form': ref.lower()
                            })

        logger.debug(f"Check complete. Found {len(incorrect_references)} issues")
        return DocumentCheckResult(
            success=len(incorrect_references) == 0,
            issues=incorrect_references,
            details={
                'total_issues': len(incorrect_references),
                'issues_by_type': {
                    'table': len([i for i in incorrect_references if 'Table' in i['issue']]),
                    'figure': len([i for i in incorrect_references if 'Figure' in i['issue']])
                }
            }
        )