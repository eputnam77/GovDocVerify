from typing import List, Dict, Any
from utils.text_utils import count_words, count_syllables, split_sentences
from models import DocumentCheckResult

class AccessibilityChecks:
    """Class for handling accessibility-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache

    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability metrics."""
        issues = []
        total_sentences = 0
        total_words = 0
        total_syllables = 0
        
        for paragraph in doc:
            sentences = split_sentences(paragraph)
            total_sentences += len(sentences)
            
            for sentence in sentences:
                words = sentence.split()
                total_words += len(words)
                total_syllables += sum(count_syllables(word) for word in words)
                
                # Check sentence length
                if len(words) > 25:
                    issues.append({
                        'line': sentence,
                        'message': 'Sentence too long',
                        'suggestion': 'Consider breaking into shorter sentences'
                    })
        
        if total_sentences > 0:
            avg_sentence_length = total_words / total_sentences
            if avg_sentence_length > 20:
                issues.append({
                    'message': 'Average sentence length too high',
                    'suggestion': 'Consider using shorter sentences'
                })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_section_508_compliance(self, doc_path: str) -> DocumentCheckResult:
        """Check Section 508 compliance."""
        issues = []
        # Add specific 508 compliance checks here
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        ) 