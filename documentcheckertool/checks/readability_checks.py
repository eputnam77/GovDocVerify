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

logger = logging.getLogger(__name__)

class ReadabilityChecks(BaseChecker):
    """Class for handling readability-related checks."""

    def __init__(self, terminology_manager: TerminologyManager):
        super().__init__(terminology_manager)
        self.readability_config = terminology_manager.terminology_data.get('readability', {})
        logger.info("Initialized ReadabilityChecks with terminology manager")

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
                warnings.append({
                    'line': i,
                    'message': f'Sentence is {word_count} words long. Consider breaking it into shorter sentences.',
                    'severity': Severity.WARNING
                })

        # Check paragraph length
        paragraphs = content.split('\n\n')
        for i, paragraph in enumerate(paragraphs, 1):
            sentence_count = len(split_sentences(paragraph))
            if sentence_count > self.readability_config.get('max_paragraph_sentences', 5):
                warnings.append({
                    'line': i,
                    'message': f'Paragraph contains {sentence_count} sentences. Consider breaking it into shorter paragraphs.',
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
                    'message': 'Consider using active voice instead of passive voice.',
                    'severity': Severity.WARNING
                })

        return {
            'has_errors': len(errors) > 0,
            'errors': errors,
            'warnings': warnings
        }

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

    def _check_readability_thresholds(self, metrics: Dict[str, float]) -> List[Dict]:
        """Check readability metrics against thresholds."""
        issues = []

        if metrics['flesch_reading_ease'] < READABILITY_CONFIG['min_flesch_ease']:
            issues.append({
                'type': 'readability_score',
                'metric': 'Flesch Reading Ease',
                'score': metrics['flesch_reading_ease'],
                'message': 'Document may be too difficult for general audience'
            })

        # Add other threshold checks...

        return issues
