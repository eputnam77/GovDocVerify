import re
from pathlib import Path
from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import normalize_reference
from documentcheckertool.models import DocumentCheckResult, Issue
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
        logger.info("Starting abbreviation usage check")
        
        def process_sentence(sentence: str) -> None:
            logger.debug(f"Processing sentence: {sentence}")
            # Implementation of abbreviation checking logic
            pass
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Processing line {i}: {line}")
            process_sentence(line)
        
        logger.info(f"Abbreviation check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_cross_reference_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check cross-reference formatting and usage."""
        issues = []
        logger.info("Starting cross-reference check")
        invalid_references = [
            'above', 'below', 'preceding', 'following',
            'former', 'latter', 'earlier', 'aforementioned'
        ]
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for invalid references: {line}")
            for ref in invalid_references:
                if ref in line.lower():
                    logger.warning(f"Found invalid reference '{ref}' in line {i}")
                    issues.append({
                        'line': line,
                        'message': f'Avoid using "{ref}" for references',
                        'suggestion': 'Use specific section references instead'
                    })
        
        logger.info(f"Cross-reference check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_required_language(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check for required language based on document type."""
        issues = []
        logger.info(f"Starting required language check for document type: {doc_type}")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_required_language_patterns(doc_type)
            if not patterns:
                logger.warning(f"No required language patterns found for document type: {doc_type}")
                return DocumentCheckResult(success=True, issues=[])
            
            logger.debug(f"Found {len(patterns)} required language patterns")
            
            # Check each line against the patterns
            for i, line in enumerate(doc, 1):
                logger.debug(f"Checking line {i} for required language: {line}")
                for pattern in patterns:
                    if not pattern.search(line):
                        logger.warning(f"Missing required language pattern '{pattern.pattern}' in line {i}")
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
            logger.error(f"Error in check_required_language: {str(e)}", exc_info=True)
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
        logger.info("Starting pronoun usage check")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_patterns('pronouns')
            if not patterns:
                logger.warning("No pronoun patterns found")
                return DocumentCheckResult(success=True, issues=[])
            
            logger.debug(f"Found {len(patterns)} pronoun patterns")
            
            # Check each line against the patterns
            for i, line in enumerate(doc, 1):
                logger.debug(f"Checking line {i} for pronouns: {line}")
                for pattern in patterns:
                    matches = pattern.search(line)
                    if matches:
                        pronoun = matches.group(0)
                        logger.warning(f"Found inappropriate pronoun '{pronoun}' in line {i}")
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
            logger.error(f"Error in check_pronouns: {str(e)}", exc_info=True)
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
        logger.info("Starting split infinitive check")
        
        try:
            # Get pre-compiled patterns from cache
            patterns = self.pattern_cache.get_patterns('split_infinitives')
            if not patterns:
                logger.warning("No split infinitive patterns found")
                return DocumentCheckResult(success=True, issues=[])
            
            logger.debug(f"Found {len(patterns)} split infinitive patterns")
            
            # Check each line against the patterns
            for i, line in enumerate(doc, 1):
                logger.debug(f"Checking line {i} for split infinitives: {line}")
                for pattern in patterns:
                    matches = pattern.search(line)
                    if matches:
                        split_infinitive = matches.group(0)
                        logger.warning(f"Found split infinitive '{split_infinitive}' in line {i}")
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
            logger.error(f"Error in check_split_infinitives: {str(e)}", exc_info=True)
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'line': 'Error in split infinitive check',
                    'message': str(e),
                    'suggestion': 'Please check the logs for details'
                }]
            )

def check_acronyms(file_path: Path) -> DocumentCheckResult:
    """Check for proper acronym usage and definitions."""
    issues = []
    acronyms = {}  # Store acronym definitions
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()
        
    # First pass: collect all acronym definitions and check for duplicates
    for i, line in enumerate(lines, 1):
        print(f"\nProcessing line {i}: {line}")
        print(f"Looking for pattern: \\b([A-Z]{{2,}})\\s*\\(([^)]+)\\)")
        matches = re.finditer(r'\b([A-Z]{2,})\s*\(([^)]+)\)', line)
        match_count = 0
        for match in matches:
            match_count += 1
            acronym = match.group(1)
            definition = match.group(2)
            print(f"Match {match_count}: Found acronym definition: {acronym} = {definition}")
            print(f"Full match: {match.group(0)}")
            
            if acronym in acronyms:
                print(f"Duplicate acronym found: {acronym}")
                issues.append({
                    "message": f"Acronym '{acronym}' defined multiple times",
                    "line_number": i,
                    "severity": "warning"
                })
            else:
                print(f"New acronym added: {acronym}")
                acronyms[acronym] = definition
        if match_count == 0:
            print("No matches found in this line")
    
    print(f"\nCollected acronyms: {acronyms}")
    
    # Second pass: check for undefined acronyms (only if no definition issues)
    if not issues:
        for i, line in enumerate(lines, 1):
            print(f"\nChecking line {i} for undefined acronyms: {line}")
            # Extract all acronyms from the line
            matches = re.finditer(r'\b([A-Z]{2,})\b', line)
            for match in matches:
                acronym = match.group(1)
                print(f"Found potential acronym: {acronym}")
                # Skip if it's being defined in this line
                if re.search(fr'{re.escape(acronym)}\s*\([^)]+\)', line):
                    print(f"Skipping {acronym} - it's being defined in this line")
                    continue
                # Skip if it's already defined
                if acronym in acronyms:
                    print(f"Skipping {acronym} - it's already defined")
                    continue
                # Check if it's undefined
                if len(acronym) > 1:
                    # Skip if it's part of a definition
                    if re.search(r'\([^)]*' + re.escape(acronym) + r'[^)]*\)', line):
                        print(f"Skipping {acronym} - it's part of a definition")
                        continue
                    print(f"Adding issue for undefined acronym: {acronym}")
                    issues.append({
                        "message": f"Acronym '{acronym}' used without definition",
                        "line_number": i,
                        "severity": "warning"
                    })
                
    return DocumentCheckResult(
        success=len(issues) == 0,
        issues=issues,
        score=1.0 if len(issues) == 0 else 0.0
    ) 