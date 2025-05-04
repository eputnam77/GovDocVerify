from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import split_sentences, count_words
from documentcheckertool.models import DocumentCheckResult
import logging

logger = logging.getLogger(__name__)

class StructureChecks:
    """Class for handling document structure checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized StructureChecks with pattern cache")

    def check_paragraph_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check paragraph length."""
        issues = []
        logger.info("Starting paragraph length check")
        
        for i, paragraph in enumerate(doc, 1):
            logger.debug(f"Checking paragraph {i}: {paragraph}")
            word_count = count_words(paragraph)
            logger.debug(f"Paragraph {i} has {word_count} words")
            
            if word_count > 150:
                logger.warning(f"Long paragraph found in paragraph {i}: {word_count} words")
                issues.append({
                    'line': paragraph,
                    'message': 'Paragraph too long',
                    'suggestion': 'Consider breaking into shorter paragraphs'
                })
        
        logger.info(f"Paragraph length check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_sentence_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check sentence length."""
        issues = []
        logger.info("Starting sentence length check")
        
        for i, paragraph in enumerate(doc, 1):
            logger.debug(f"Processing paragraph {i}: {paragraph}")
            sentences = split_sentences(paragraph)
            logger.debug(f"Found {len(sentences)} sentences in paragraph {i}")
            
            for j, sentence in enumerate(sentences, 1):
                logger.debug(f"Checking sentence {j} in paragraph {i}: {sentence}")
                word_count = count_words(sentence)
                logger.debug(f"Sentence {j} has {word_count} words")
                
                if word_count > 25:
                    logger.warning(f"Long sentence found in paragraph {i}, sentence {j}: {word_count} words")
                    issues.append({
                        'line': sentence,
                        'message': 'Sentence too long',
                        'suggestion': 'Consider breaking into shorter sentences'
                    })
        
        logger.info(f"Sentence length check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_parentheses(self, doc: List[str]) -> DocumentCheckResult:
        """Check parentheses usage."""
        issues = []
        logger.info("Starting parentheses check")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for parentheses: {line}")
            open_count = line.count('(')
            close_count = line.count(')')
            logger.debug(f"Line {i} has {open_count} opening and {close_count} closing parentheses")
            
            if open_count != close_count:
                logger.warning(f"Mismatched parentheses in line {i}: {open_count} opening, {close_count} closing")
                issues.append({
                    'line': line,
                    'message': 'Mismatched parentheses',
                    'suggestion': 'Check and fix parentheses pairs'
                })
        
        logger.info(f"Parentheses check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        ) 