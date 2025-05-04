from typing import List, Dict, Any
from utils.text_utils import normalize_reference
from models import DocumentCheckResult
import logging

logger = logging.getLogger(__name__)

class TerminologyChecks:
    """Class for handling terminology and cross-reference checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized TerminologyChecks with pattern cache")

    def check_abbreviation_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check abbreviation usage and consistency."""
        issues = []
        defined_abbreviations = set()
        inconsistent_uses = set()
        
        def process_sentence(sentence: str) -> None:
            # Implementation of abbreviation checking logic
            pass
        
        for line in doc:
            process_sentence(line)
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_cross_reference_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check cross-reference formatting and usage."""
        issues = []
        invalid_references = [
            'above', 'below', 'preceding', 'following',
            'former', 'latter', 'earlier', 'aforementioned'
        ]
        
        for line in doc:
            for ref in invalid_references:
                if ref in line.lower():
                    issues.append({
                        'line': line,
                        'message': f'Avoid using "{ref}" for references',
                        'suggestion': 'Use specific section references instead'
                    })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_required_language(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check for required language based on document type."""
        issues = []
        logger.info(f"Checking required language for document type: {doc_type}")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_required_language_patterns(doc_type)
            if not patterns:
                logger.warning(f"No required language patterns found for document type: {doc_type}")
                return DocumentCheckResult(success=True, issues=[])
            
            # Check each line against the patterns
            for line in doc:
                for pattern in patterns:
                    if not pattern.search(line):
                        issues.append({
                            'line': line,
                            'message': 'Missing required language',
                            'suggestion': f'Document should contain: {pattern.pattern}'
                        })
            
            logger.info(f"Required language check completed with {len(issues)} issues found")
            return DocumentCheckResult(
                success=len(issues) == 0,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Error in check_required_language: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'line': 'Error in required language check',
                    'message': str(e),
                    'suggestion': 'Please check the logs for details'
                }]
            )

    def check_pronouns(self, doc: List[str]) -> DocumentCheckResult:
        """Check for inappropriate pronoun usage in the document."""
        issues = []
        logger.info("Checking for inappropriate pronoun usage")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_patterns('pronouns')
            if not patterns:
                logger.warning("No pronoun patterns found")
                return DocumentCheckResult(success=True, issues=[])
            
            # Check each line against the patterns
            for line in doc:
                for pattern in patterns:
                    matches = pattern.search(line)
                    if matches:
                        pronoun = matches.group(0)
                        replacement = pattern.get('replacement', 'specific entity')
                        if isinstance(replacement, dict):
                            replacement = replacement.get(pronoun.lower(), 'specific entity')
                        
                        issues.append({
                            'line': line,
                            'message': f'Avoid using pronoun "{pronoun}"',
                            'suggestion': f'Replace with {replacement}'
                        })
            
            logger.info(f"Pronoun check completed with {len(issues)} issues found")
            return DocumentCheckResult(
                success=len(issues) == 0,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Error in check_pronouns: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'line': 'Error in pronoun check',
                    'message': str(e),
                    'suggestion': 'Please check the logs for details'
                }]
            )

    def check_split_infinitives(self, doc: List[str]) -> DocumentCheckResult:
        """Check for split infinitives in the document."""
        issues = []
        logger.info("Checking for split infinitives")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_patterns('split_infinitives')
            if not patterns:
                logger.warning("No split infinitive patterns found")
                return DocumentCheckResult(success=True, issues=[])
            
            # Check each line against the patterns
            for line in doc:
                for pattern in patterns:
                    matches = pattern.search(line)
                    if matches:
                        split_infinitive = matches.group(0)
                        issues.append({
                            'line': line,
                            'message': 'Split infinitive detected',
                            'suggestion': pattern.get('suggestion', 'Consider rewriting to avoid the split infinitive'),
                            'is_error': False  # Mark as non-error since it's a style choice
                        })
            
            logger.info(f"Split infinitive check completed with {len(issues)} instances found")
            return DocumentCheckResult(
                success=True,  # Always return success since these are style suggestions
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Error in check_split_infinitives: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'line': 'Error in split infinitive check',
                    'message': str(e),
                    'suggestion': 'Please check the logs for details'
                }]
            ) 