from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import count_words, count_syllables, split_sentences
from documentcheckertool.models import DocumentCheckResult
import logging
from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity

logger = logging.getLogger(__name__)

class AccessibilityChecks(BaseChecker):
    """Class for handling accessibility-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized AccessibilityChecks with pattern cache")

    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability metrics."""
        issues = []
        total_sentences = 0
        total_words = 0
        total_syllables = 0
        logger.info("Starting readability check")
        
        for i, paragraph in enumerate(doc, 1):
            logger.debug(f"Processing paragraph {i}: {paragraph}")
            sentences = split_sentences(paragraph)
            total_sentences += len(sentences)
            logger.debug(f"Found {len(sentences)} sentences in paragraph {i}")
            
            for j, sentence in enumerate(sentences, 1):
                logger.debug(f"Processing sentence {j} in paragraph {i}: {sentence}")
                words = sentence.split()
                total_words += len(words)
                total_syllables += sum(count_syllables(word) for word in words)
                logger.debug(f"Sentence {j} has {len(words)} words and {sum(count_syllables(word) for word in words)} syllables")
                
                # Check sentence length
                if len(words) > 25:
                    logger.warning(f"Long sentence found in paragraph {i}, sentence {j}: {len(words)} words")
                    issues.append({
                        'line': sentence,
                        'message': 'Sentence too long',
                        'suggestion': 'Consider breaking into shorter sentences'
                    })
        
        if total_sentences > 0:
            avg_sentence_length = total_words / total_sentences
            logger.debug(f"Average sentence length: {avg_sentence_length:.2f} words")
            if avg_sentence_length > 20:
                logger.warning(f"High average sentence length: {avg_sentence_length:.2f} words")
                issues.append({
                    'message': 'Average sentence length too high',
                    'suggestion': 'Consider using shorter sentences'
                })
        
        logger.info(f"Readability check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_section_508_compliance(self, doc_path: str) -> DocumentCheckResult:
        """Check Section 508 compliance."""
        issues = []
        logger.info("Starting Section 508 compliance check")
        try:
            # Add specific 508 compliance checks here
            logger.debug(f"Checking file: {doc_path}")
            # ... implementation ...
            
            logger.info(f"Section 508 compliance check completed. Found {len(issues)} issues")
            return DocumentCheckResult(
                success=len(issues) == 0,
                issues=issues
            )
        except Exception as e:
            logger.error(f"Error in Section 508 compliance check: {str(e)}", exc_info=True)
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'message': f'Error in Section 508 compliance check: {str(e)}',
                    'suggestion': 'Please check the logs for details'
                }]
            )

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all accessibility-related checks."""
        logger.info(f"Running accessibility checks for document type: {doc_type}")
        
        self._check_alt_text(document, results)
        self._check_color_contrast(document, results)
        
    def _check_alt_text(self, document: Document, results: DocumentCheckResult):
        """Check for missing alt text in images."""
        for shape in document.inline_shapes:
            if not hasattr(shape, '_inline') or not hasattr(shape._inline, 'docPr'):
                continue
            if not shape._inline.docPr.get('descr'):
                results.add_issue(
                    message="Image missing alt text",
                    severity=Severity.HIGH
                )
    
    def _check_color_contrast(self, document: Document, results: DocumentCheckResult):
        """Check for potential color contrast issues."""
        # Basic check for now - to be expanded
        for paragraph in document.paragraphs:
            if hasattr(paragraph, '_element'):
                if hasattr(paragraph._element, 'rPr'):
                    if hasattr(paragraph._element.rPr, 'color'):
                        results.add_issue(
                            message="Potential color contrast issue detected",
                            severity=Severity.MEDIUM
                        )