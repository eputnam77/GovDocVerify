from typing import List, Dict, Any
from utils.text_utils import normalize_heading
from models import DocumentCheckResult, DocumentType
import re

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
        self.heading_pattern = re.compile(r'^(\d+\.)+\s')

    def check_heading_title(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading title formatting."""
        issues = []
        for line in doc:
            # Check if line starts with a number followed by a dot
            if not self.heading_pattern.match(line):
                continue
                
            # Extract the heading text (everything after the number)
            heading_text = line.split('.', 1)[1].strip()
            
            # Check if the heading text contains any of the valid heading words
            if not any(word in heading_text.upper() for word in self.HEADING_WORDS):
                issues.append({
                    'line': line,
                    'message': 'Heading formatting issue',
                    'suggestion': f'Use a valid heading word from: {", ".join(sorted(self.HEADING_WORDS))}'
                })
            else:
                normalized = normalize_heading(line)
                if normalized != line:
                    issues.append({
                        'line': line,
                        'message': 'Heading formatting issue',
                        'suggestion': normalized
                    })
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_heading_period(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check heading period usage."""
        issues = []
        doc_type_enum = DocumentType.from_string(doc_type)
        requires_period = doc_type_enum in {
            DocumentType.ADVISORY_CIRCULAR,
            DocumentType.ORDER,
            DocumentType.TECHNICAL_STANDARD_ORDER
        }
        
        for line in doc:
            if any(word in line.upper() for word in self.HEADING_WORDS):
                has_period = line.strip().endswith('.')
                if requires_period and not has_period:
                    issues.append({
                        'line': line,
                        'message': 'Heading missing required period',
                        'suggestion': f"{line.strip()}."
                    })
                elif not requires_period and has_period:
                    issues.append({
                        'line': line,
                        'message': 'Heading should not end with period',
                        'suggestion': line.strip()[:-1]
                    })
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def check_heading_structure(self, doc) -> List[Dict[str, Any]]:
        """Check heading sequence structure.
        
        Args:
            doc: A python-docx Document object
            
        Returns:
            List of issues found in heading sequence
        """
        issues = []
        prev_numbers = None
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
                
            # Extract heading numbers (e.g., ["1", "2", "1"] from "1.2.1")
            match = re.match(r'^(\d+\.)+\s*', text)
            if not match:
                continue
                
            numbers = [n.strip('.') for n in match.group(0).strip().split('.') if n.strip('.')]
            current_level = len(numbers)
            
            if prev_numbers is not None:
                prev_level = len(prev_numbers)
                
                # Check level skipping
                if current_level > prev_level + 1:
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
                                issues.append({
                                    'text': text,
                                    'message': f'Invalid heading sequence: expected {prev_last + 1}',
                                    'suggestion': f'Use {".".join(numbers[:-1] + [str(prev_last + 1)])}'
                                })
                        except ValueError:
                            pass
            
            prev_numbers = numbers
            
        return issues 