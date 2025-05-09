from typing import List, Dict
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
import re
import logging

logger = logging.getLogger(__name__)

class ReadabilityChecks(BaseChecker):
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
