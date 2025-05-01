from typing import List, Dict, Any
from utils.text_utils import split_sentences, normalize_reference
from models import DocumentCheckResult, DocumentType

class FormatChecks:
    """Class for handling format-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache

    def check_date_format_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check date format usage."""
        issues = []
        date_pattern = self.pattern_cache.get_pattern(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        
        for line in doc:
            matches = date_pattern.finditer(line)
            for match in matches:
                issues.append({
                    'line': line,
                    'message': 'Incorrect date format',
                    'suggestion': 'Use YYYY-MM-DD format'
                })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_phone_number_format_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check phone number format usage."""
        issues = []
        phone_pattern = self.pattern_cache.get_pattern(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
        for line in doc:
            matches = phone_pattern.finditer(line)
            for match in matches:
                issues.append({
                    'line': line,
                    'message': 'Incorrect phone number format',
                    'suggestion': 'Use (XXX) XXX-XXXX format'
                })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_placeholder_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check placeholder usage."""
        issues = []
        placeholder_patterns = [
            self.pattern_cache.get_pattern(r'\bTBD\b'),
            self.pattern_cache.get_pattern(r'\bTo be determined\b'),
            self.pattern_cache.get_pattern(r'\bTo be added\b')
        ]
        
        for line in doc:
            for pattern in placeholder_patterns:
                if pattern.search(line):
                    issues.append({
                        'line': line,
                        'message': 'Placeholder found',
                        'suggestion': 'Replace with actual content'
                    })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        ) 