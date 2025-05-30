from typing import Dict, Any, List
from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.validation_patterns import PASSIVE_VOICE_PATTERNS
from documentcheckertool.config.document_config import READABILITY_CONFIG
from documentcheckertool.utils.text_utils import (
    count_words,
    count_syllables,
    split_sentences,
    calculate_readability_metrics
)
from documentcheckertool.utils.terminology_utils import TerminologyManager
import re
import logging
from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.utils.boilerplate_utils import is_boilerplate

logger = logging.getLogger(__name__)

class ReadabilityChecks(BaseChecker):
    """Class for handling readability-related checks."""

    def __init__(self, terminology_manager: TerminologyManager):
        super().__init__(terminology_manager)
        self.readability_config = terminology_manager.terminology_data.get('readability', {})
        self.category = "readability"
        logger.info("Initialized ReadabilityChecks with terminology manager")

    @CheckRegistry.register('readability')
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for readability issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    @CheckRegistry.register('readability')
    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for readability issues."""
        results = DocumentCheckResult()
        lines = text.split('\n')

        # Process paragraphs
        current_paragraph = []
        for line in lines:
            if line.strip():
                current_paragraph.append(line)
            elif current_paragraph:
                self._check_readability_thresholds(''.join(current_paragraph), results)
                current_paragraph = []
        if current_paragraph:
            self._check_readability_thresholds(''.join(current_paragraph), results)

        return results

    @CheckRegistry.register('readability')
    def _check_readability_thresholds(self, text: str, results: DocumentCheckResult) -> None:
        """Check readability metrics against thresholds."""
        try:
            if is_boilerplate(text):
                return  # skip mandated boiler-plate completely
            # Calculate basic metrics
            words = text.split()
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return

            avg_words_per_sentence = len(words) / len(sentences)
            avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)

            # Calculate readability scores
            flesch_ease = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word
            flesch_grade = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59

            # Check thresholds
            if flesch_ease < 60:
                results.add_issue(
                    message=f"Text may be difficult to read (Flesch Reading Ease: {flesch_ease:.1f}). Consider simplifying language.",
                    severity=Severity.WARNING,
                    category=getattr(self, "category", "readability")
                )

            if flesch_grade > 12:
                results.add_issue(
                    message=f"Text may be too complex for general audience (Flesch-Kincaid Grade Level: {flesch_grade:.1f}).",
                    severity=Severity.WARNING,
                    category=getattr(self, "category", "readability")
                )

            # Check sentence length
            for i, sentence in enumerate(sentences, 1):
                word_count = len(sentence.split())
                if word_count > 25:
                    sentence_preview = self._get_text_preview(sentence.strip())
                    results.add_issue(
                        message=f"Sentence '{sentence_preview}' is too long ({word_count} words). Consider breaking it into smaller sentences.",
                        severity=Severity.WARNING,
                        category=getattr(self, "category", "readability")
                    )

            # Check paragraph length
            if len(words) > 150:
                paragraph_preview = self._get_text_preview(text.strip())
                results.add_issue(
                    message=f"Paragraph '{paragraph_preview}' is too long ({len(words)} words). Consider breaking it into smaller paragraphs.",
                    severity=Severity.WARNING,
                    category=getattr(self, "category", "readability")
                )

        except Exception as e:
            logger.error(f"Error in readability check: {str(e)}")
            results.add_issue(
                message=f"Error calculating readability metrics: {str(e)}",
                severity=Severity.ERROR,
                category=getattr(self, "category", "readability")
            )

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using basic rules."""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        on_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel

        if word.endswith('e'):
            count -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        if count == 0:
            count = 1

        return count

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
            return ' '.join(preview_words) + '...'

    def check(self, content: str) -> Dict[str, Any]:
        """
        Check document content for readability issues.

        Args:
            content: The document content to check

        Returns:
            Dict containing check results
        """
        errors = []
        warnings = []

        # Check sentence length
        sentences = split_sentences(content)
        for i, sentence in enumerate(sentences, 1):
            word_count = count_words(sentence)
            if word_count > self.readability_config.get('max_sentence_length', 20):
                sentence_preview = self._get_text_preview(sentence.strip())
                warnings.append({
                    'line': i,
                    'message': f"Sentence '{sentence_preview}' is {word_count} words long. Consider breaking it into shorter sentences.",
                    'severity': Severity.WARNING
                })

        # Check paragraph length
        paragraphs = content.split('\n\n')
        for i, paragraph in enumerate(paragraphs, 1):
            sentence_count = len(split_sentences(paragraph))
            if sentence_count > self.readability_config.get('max_paragraph_sentences', 5):
                paragraph_preview = self._get_text_preview(paragraph.strip())
                warnings.append({
                    'line': i,
                    'message': f"Paragraph '{paragraph_preview}' contains {sentence_count} sentences. Consider breaking it into shorter paragraphs.",
                    'severity': Severity.WARNING
                })

        # Check for passive voice
        passive_patterns = [
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b',
            r'\b(?:has|have|had)\s+been\s+\w+ed\b',
            r'\b(?:has|have|had)\s+been\s+\w+en\b'
        ]
        passive_regex = re.compile('|'.join(passive_patterns), re.IGNORECASE)

        for i, sentence in enumerate(sentences, 1):
            if passive_regex.search(sentence):
                warnings.append({
                    'line': i,
                    'message': 'Consider using active voice instead of passive voice. Note: Passive voice is flagged as a readability recommendation. It is not a style requirement, and may be acceptable depending on context.',
                    'severity': Severity.WARNING,
                    'type': 'advisory'
                })

        return {
            'has_errors': len(errors) > 0,
            'errors': errors,
            'warnings': warnings
        }

    @CheckRegistry.register('readability')
    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability metrics."""
        stats = {
            'total_words': 0,
            'total_syllables': 0,
            'total_sentences': 0,
            'complex_words': 0
        }

        for paragraph in doc:
            sentences = split_sentences(paragraph)
            stats['total_sentences'] += len(sentences)

            for sentence in sentences:
                words = sentence.split()
                stats['total_words'] += len(words)

                for word in words:
                    syllables = count_syllables(word)
                    stats['total_syllables'] += syllables
                    if syllables >= 3:
                        stats['complex_words'] += 1

        metrics = calculate_readability_metrics(
            stats['total_words'],
            stats['total_sentences'],
            stats['total_syllables']
        )

        issues = self._check_readability_thresholds(metrics)

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details={'metrics': metrics}
        )

    @CheckRegistry.register('readability')
    def _check_readability_thresholds_metrics(self, metrics: Dict[str, float]) -> List[Dict]:
        """Check readability metrics against thresholds."""
        logger.debug("Checking readability metrics against thresholds")
        issues = []

        if metrics['flesch_reading_ease'] < READABILITY_CONFIG['min_flesch_ease']:
            logger.warning(f"Flesch Reading Ease score {metrics['flesch_reading_ease']} below threshold {READABILITY_CONFIG['min_flesch_ease']}")
            issues.append({
                'type': 'readability_score',
                'metric': 'Flesch Reading Ease',
                'score': metrics['flesch_reading_ease'],
                'message': 'Document may be too difficult for general audience'
            })

        return issues

    @CheckRegistry.register('readability')
    def check_sentence_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check for overly long sentences."""
        results = DocumentCheckResult()
        # ... existing code ...

    @CheckRegistry.register('readability')
    def check_paragraph_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check for overly long paragraphs."""
        results = DocumentCheckResult()
        # ... existing code ...

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all readability-related checks."""
        logger.info(f"Running readability checks for document type: {doc_type}")
        text = '\n'.join([p.text for p in document.paragraphs])
        check_result = self.check_text(text)
        results.issues.extend(check_result.issues)
        results.success = check_result.success
