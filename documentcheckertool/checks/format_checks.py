from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import split_sentences, normalize_reference
from documentcheckertool.models import DocumentCheckResult, DocumentType
import logging

logger = logging.getLogger(__name__)

class FormatChecks:
    """Class for handling format-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized FormatChecks with pattern cache")

    def check_date_format_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check date format usage."""
        issues = []
        logger.info("Starting date format check")
        date_pattern = self.pattern_cache.get_pattern(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        logger.debug(f"Using date pattern: {date_pattern.pattern}")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for date formats: {line}")
            matches = date_pattern.finditer(line)
            match_count = 0
            for match in matches:
                match_count += 1
                date_str = match.group(0)
                logger.warning(f"Found incorrect date format '{date_str}' in line {i}")
                issues.append({
                    'line': line,
                    'message': 'Incorrect date format',
                    'suggestion': 'Use YYYY-MM-DD format'
                })
            if match_count > 0:
                logger.debug(f"Found {match_count} date format issues in line {i}")
        
        logger.info(f"Date format check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_phone_number_format_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check phone number format usage."""
        issues = []
        logger.info("Starting phone number format check")
        phone_pattern = self.pattern_cache.get_pattern(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        logger.debug(f"Using phone pattern: {phone_pattern.pattern}")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for phone numbers: {line}")
            matches = phone_pattern.finditer(line)
            match_count = 0
            for match in matches:
                match_count += 1
                phone_str = match.group(0)
                logger.warning(f"Found incorrect phone format '{phone_str}' in line {i}")
                issues.append({
                    'line': line,
                    'message': 'Incorrect phone number format',
                    'suggestion': 'Use (XXX) XXX-XXXX format'
                })
            if match_count > 0:
                logger.debug(f"Found {match_count} phone number format issues in line {i}")
        
        logger.info(f"Phone number format check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_placeholder_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check placeholder usage."""
        issues = []
        logger.info("Starting placeholder check")
        placeholder_patterns = [
            self.pattern_cache.get_pattern(r'\bTBD\b'),
            self.pattern_cache.get_pattern(r'\bTo be determined\b'),
            self.pattern_cache.get_pattern(r'\bTo be added\b')
        ]
        logger.debug(f"Using {len(placeholder_patterns)} placeholder patterns")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for placeholders: {line}")
            for pattern in placeholder_patterns:
                if pattern.search(line):
                    placeholder = pattern.search(line).group(0)
                    logger.warning(f"Found placeholder '{placeholder}' in line {i}")
                    issues.append({
                        'line': line,
                        'message': 'Placeholder found',
                        'suggestion': 'Replace with actual content'
                    })
        
        logger.info(f"Placeholder check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        ) 