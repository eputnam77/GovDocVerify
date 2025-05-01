from typing import List, Dict, Any
from utils.text_utils import split_sentences, count_words
from models import DocumentCheckResult

class StructureChecks:
    """Class for handling document structure checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache

    def check_paragraph_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check paragraph length."""
        issues = []
        for paragraph in doc:
            word_count = count_words(paragraph)
            if word_count > 150:
                issues.append({
                    'line': paragraph,
                    'message': 'Paragraph too long',
                    'suggestion': 'Consider breaking into shorter paragraphs'
                })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_sentence_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check sentence length."""
        issues = []
        for paragraph in doc:
            sentences = split_sentences(paragraph)
            for sentence in sentences:
                word_count = count_words(sentence)
                if word_count > 25:
                    issues.append({
                        'line': sentence,
                        'message': 'Sentence too long',
                        'suggestion': 'Consider breaking into shorter sentences'
                    })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_parentheses(self, doc: List[str]) -> DocumentCheckResult:
        """Check parentheses usage."""
        issues = []
        for line in doc:
            if line.count('(') != line.count(')'):
                issues.append({
                    'line': line,
                    'message': 'Mismatched parentheses',
                    'suggestion': 'Check and fix parentheses pairs'
                })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        ) 