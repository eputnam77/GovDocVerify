from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import normalize_heading
from documentcheckertool.models import DocumentCheckResult, DocumentType
import re
import logging

logger = logging.getLogger(__name__)

class HeadingChecks:
    """Class for handling heading-related checks."""
    
    HEADING_WORDS = frozenset({
        'APPLICABILITY', 'APPENDIX', 'AUTHORITY', 'BACKGROUND', 'CANCELLATION', 'CAUTION',
        'CHAPTER', 'CONCLUSION', 'DEPARTMENT', 'DEFINITION', 'DEFINITIONS', 'DISCUSSION',
        'DISTRIBUTION', 'EXCEPTION', 'EXPLANATION', 'FIGURE', 'GENERAL', 'GROUPS', 
        'INFORMATION', 'INSERT', 'INTRODUCTION', 'MATERIAL', 'NOTE', 'PARTS', 'PAST', 
        'POLICY', 'PRACTICE', 'PROCEDURES', 'PURPOSE', 'RELEVANT', 'RELATED', 
        'REQUIREMENTS', 'REPORT', 'SCOPE', 'SECTION', 'SUMMARY', 'TABLE', 'WARNING'
    })

    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized HeadingChecks with pattern cache")
        self.heading_pattern = re.compile(r'^(\d+\.)+\s')
        logger.debug(f"Using heading pattern: {self.heading_pattern.pattern}")

    def check_heading_title(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading title formatting."""
        issues = []
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
            if not any(word in heading_text.upper() for word in self.HEADING_WORDS):
                logger.warning(f"Invalid heading word in line {i}: {heading_text}")
                issues.append({
                    'line': line,
                    'message': 'Heading formatting issue',
                    'suggestion': f'Use a valid heading word from: {", ".join(sorted(self.HEADING_WORDS))}'
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
        
        logger.info(f"Heading title check completed. Found {len(issues)} issues")
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_heading_period(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading period usage."""
        issues = []
        logger.info(f"Starting heading period check for document type: {doc_type}")
        doc_type_enum = DocumentType.from_string(doc_type)
        requires_period = doc_type_enum in {
            DocumentType.ADVISORY_CIRCULAR,
            DocumentType.ORDER,
            DocumentType.TECHNICAL_STANDARD_ORDER
        }
        logger.debug(f"Document type {doc_type} {'requires' if requires_period else 'does not require'} periods")
        
        for i, line in enumerate(doc, 1):
            logger.debug(f"Checking line {i} for heading period: {line}")
            if any(word in line.upper() for word in self.HEADING_WORDS):
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