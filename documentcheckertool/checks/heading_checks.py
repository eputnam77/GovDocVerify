from typing import List, Dict, Any, Optional, Tuple
from functools import wraps
from documentcheckertool.utils.text_utils import normalize_heading
from documentcheckertool.models import DocumentCheckResult, DocumentType, Severity
from documentcheckertool.config.document_config import (
    HEADING_WORDS,
    DOC_TYPE_CONFIG,
    PERIOD_REQUIRED
)
import re
import logging
from docx import Document
from .base_checker import BaseChecker

logger = logging.getLogger(__name__)

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)
    return wrapper

class HeadingChecks(BaseChecker):
    """Class for handling heading-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized HeadingChecks with pattern cache")
        self.heading_pattern = re.compile(r'^(\d+\.)+\s')
        logger.debug(f"Using heading pattern: {self.heading_pattern.pattern}")

    def _get_doc_type_config(self, doc_type: str) -> Tuple[Dict, str]:
        """Get configuration for document type."""
        normalized_type = doc_type.strip().lower()
        for known_type, config in DOC_TYPE_CONFIG.items():
            if known_type.lower() == normalized_type:
                return config, known_type
        return {}, doc_type

    def validate_input(self, doc: List[str]) -> bool:
        """Validate document input."""
        return bool(doc and all(isinstance(p, str) for p in doc))

    @profile_performance
    def check_heading_title(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading title formatting."""
        if not self.validate_input(doc):
            logger.error("Invalid document input for heading check")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        try:
            doc_type_config, normalized_type = self._get_doc_type_config(doc_type)
        except Exception as e:
            logger.error(f"Error getting document type configuration: {str(e)}")
            return DocumentCheckResult(success=False, issues=[{'error': str(e)}])

        # Add skip title check logic
        if doc_type_config.get('skip_title_check', False):
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={'message': f'Title check skipped for document type: {doc_type}'}
            )
            
        required_headings = doc_type_config.get('required_headings', [])
        issues = []
        headings_found = set()
        
        logger.info(f"Starting heading title check for document type: {doc_type}")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for heading format: {line}")
            # Check if line starts with a number followed by a dot
            if not self.heading_pattern.match(line):
                logger.debug(f"Line {i} is not a numbered heading")
                continue
                
            # Extract the heading text (everything after the number)
            heading_text = line.split('.', 1)[1].strip()
            logger.debug(f"Found heading text: {heading_text}")
            
            # Check if the heading text contains any of the valid heading words
            if not any(word in heading_text.upper() for word in HEADING_WORDS):
                logger.warning(f"Invalid heading word in line {i}: {heading_text}")
                issues.append({
                    'line': line,
                    'message': 'Heading formatting issue',
                    'suggestion': f'Use a valid heading word from: {", ".join(sorted(HEADING_WORDS))}'
                })
            else:
                normalized = normalize_heading(line)
                if normalized != line:
                    logger.warning(f"Heading format mismatch in line {i}")
                    logger.debug(f"Original: {line}")
                    logger.debug(f"Normalized: {normalized}")
                    issues.append({
                        'line': line,
                        'message': 'Heading formatting issue',
                        'suggestion': normalized
                    })
            
            headings_found.add(heading_text.upper())
        
        # Additional required headings check
        if required_headings:
            missing_headings = set(required_headings) - headings_found
            if missing_headings:
                issues.append({
                    'type': 'missing_headings',
                    'missing': list(missing_headings),
                    'message': f'Missing required headings: {", ".join(missing_headings)}'
                })

        details = {
            'found_headings': list(headings_found),
            'required_headings': required_headings,
            'document_type': normalized_type,
            'missing_count': len(missing_headings) if required_headings else 0
        }

        logger.info(f"Heading title check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details=details
        )

    def check_heading_period(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading period usage."""
        issues = []
        logger.info(f"Starting heading period check for document type: {doc_type}")
        doc_type_enum = DocumentType.from_string(doc_type)
        requires_period = PERIOD_REQUIRED.get(doc_type_enum, False)
        logger.debug(f"Document type {doc_type} {'requires' if requires_period else 'does not require'} periods")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for heading period: {line}")
            if any(word in line.upper() for word in HEADING_WORDS):
                has_period = line.strip().endswith('.')
                logger.debug(f"Line {i} has period: {has_period}")
                if requires_period and not has_period:
                    logger.warning(f"Missing required period in line {i}")
                    issues.append({
                        'line': line,
                        'message': 'Heading missing required period',
                        'suggestion': f"{line.strip()}."
                    })
                elif not requires_period and has_period:
                    logger.warning(f"Unexpected period in line {i}")
                    issues.append({
                        'line': line,
                        'message': 'Heading should not end with period',
                        'suggestion': line.strip()[:-1]
                    })
        
        logger.info(f"Heading period check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_heading_structure(self, doc) -> List[Dict[str, Any]]:
        """Check heading sequence structure."""
        issues = []
        logger.info("Starting heading structure check")
        prev_numbers = None
        
        for i, paragraph in enumerate(doc.paragraphs, 1):
            text = paragraph.text.strip()
            if not text:
                continue
                
            logger.debug(f"Checking paragraph {i}: {text}")
            # Extract heading numbers (e.g., ["1", "2", "1"] from "1.2.1")
            match = re.match(r'^(\d+\.)+\s*', text)
            if not match:
                logger.debug(f"Paragraph {i} is not a numbered heading")
                continue
                
            numbers = [n.strip('.') for n in match.group(0).strip().split('.') if n.strip('.')]
            current_level = len(numbers)
            logger.debug(f"Found heading level {current_level} with numbers: {numbers}")
            
            if prev_numbers is not None:
                prev_level = len(prev_numbers)
                
                # Check level skipping
                if current_level > prev_level + 1:
                    logger.warning(f"Invalid heading sequence in paragraph {i}: skipped level {prev_level + 1}")
                    issues.append({
                        'text': text,
                        'message': f'Invalid heading sequence: skipped level {prev_level + 1}',
                        'suggestion': 'Ensure heading levels are sequential'
                    })
                
                # Check sequence within same level
                elif current_level == prev_level:
                    # Compare all but the last number
                    if numbers[:-1] == prev_numbers[:-1]:
                        # Check if the last number is sequential
                        try:
                            prev_last = int(prev_numbers[-1])
                            curr_last = int(numbers[-1])
                            if curr_last != prev_last + 1:
                                logger.warning(f"Invalid heading sequence in paragraph {i}: expected {prev_last + 1}")
                                issues.append({
                                    'text': text,
                                    'message': f'Invalid heading sequence: expected {prev_last + 1}',
                                    'suggestion': f'Use {".".join(numbers[:-1] + [str(prev_last + 1)])}'
                                })
                        except ValueError:
                            logger.error(f"Invalid number format in paragraph {i}: {numbers[-1]}")
            
            prev_numbers = numbers
            
        logger.info(f"Heading structure check completed. Found {len(issues)} issues")
        return issues

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all heading-related checks."""
        logger.info(f"Running heading checks for document type: {doc_type}")
        
        # Get all paragraphs with heading style
        headings = [p for p in document.paragraphs if p.style.name.startswith('Heading')]
        
        # Check heading structure
        self._check_heading_hierarchy(headings, results)
        self._check_heading_format(headings, results)
        
    def _check_heading_sequence(self, current_level: int, previous_level: int) -> Optional[str]:
        """
        Check if heading sequence is valid.
        Returns error message if invalid, None if valid.
        
        Rules:
        - Can go from any level to H1 or H2 (restart numbering)
        - When going deeper, can only go one level at a time (e.g., H1 to H2, H2 to H3)
        - Can freely go to any higher level (e.g., H3 to H1, H4 to H2)
        """
        # When going to a deeper level, only allow one level at a time
        if current_level > previous_level:
            if current_level != previous_level + 1:
                return f"Skipped heading level(s) {previous_level + 1} - Found H{current_level} after H{previous_level}. Add H{previous_level + 1} before this section."
            
        # All other cases are valid:
        # - Going to H1 (restart numbering)
        # - Going to any higher level (e.g., H3 to H1)
        return None

    def _check_heading_hierarchy(self, headings, results):
        """Check if headings follow proper hierarchy."""
        previous_level = 0
        for heading in headings:
            level = int(heading.style.name.replace('Heading ', ''))
            error_message = self._check_heading_sequence(level, previous_level)
            
            if error_message:
                results.add_issue(
                    message=error_message,
                    severity=Severity.HIGH,
                    line_number=heading._element.sourceline,
                    context=f"Current heading: {heading.text}"
                )
            previous_level = level
    
    def _check_heading_format(self, headings, results):
        """Check heading format (capitalization, punctuation, etc)."""
        for heading in headings:
            text = heading.text.strip()
            if text.endswith('.'):
                results.add_issue(
                    message=f"Heading should not end with period: {text}",
                    severity=Severity.MEDIUM,
                    line_number=heading._element.sourceline
                )