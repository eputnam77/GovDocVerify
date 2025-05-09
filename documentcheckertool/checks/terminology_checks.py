from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.terminology_rules import (
    TERM_REPLACEMENTS,
    FORBIDDEN_TERMS,
    TERMINOLOGY_VARIANTS
)
from documentcheckertool.config.validation_patterns import ACRONYM_PATTERNS
import re
import logging

logger = logging.getLogger(__name__)

class TerminologyChecks(BaseChecker):
    """Class for handling terminology-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized TerminologyChecks with pattern cache")
        # Remove hardcoded patterns since they're now in config files
    
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all terminology-related checks."""
        logger.info(f"Running terminology checks for document type: {doc_type}")
        
        text_content = [p.text for p in document.paragraphs]
        self._check_abbreviations(text_content, results)
        self._check_consistency(text_content, results)
        self._check_forbidden_terms(text_content, results)
    
    def _load_valid_words(self):
        """Load valid words from valid_words.txt file."""
        valid_words = set()
        try:
            with open('/workspaces/DocumentCheckerToolSandbox/valid_words.txt', 'r') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:  # Skip empty lines
                        valid_words.add(word)
        except FileNotFoundError:
            logger.warning("valid_words.txt not found - using default minimal set")
            # Fallback to minimal set if file not found
            valid_words = {'pdf', 'xml', 'html', 'css', 'url', 'api'}
        except Exception as e:
            logger.error(f"Error loading valid_words.txt: {e}")
            # Fallback to minimal set on any error
            valid_words = {'pdf', 'xml', 'html', 'css', 'url', 'api'}
            
        return valid_words

    def _check_abbreviations(self, paragraphs, results):
        """Check for acronyms and their definitions."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Load valid words
        valid_words = self._load_valid_words()

        # Common words that might appear in uppercase but aren't acronyms
        heading_words = self.config_manager.config.get('heading_words', self.HEADING_WORDS)

        # Standard acronyms that don't need to be defined
        predefined_acronyms = self.config_manager.config.get('predefined_acronyms', self.PREDEFINED_ACRONYMS)

        # Use patterns from config
        ignore_pattern = re.compile('|'.join(f'(?:{pattern})' for pattern in ACRONYM_PATTERNS['ignore_patterns']))
        defined_pattern = re.compile(ACRONYM_PATTERNS['defined'])
        acronym_pattern = re.compile(ACRONYM_PATTERNS['usage'])
        
        # Tracking structures
        defined_acronyms = {}  # Stores definition info
        used_acronyms = set()  # Stores acronyms used after definition
        reported_acronyms = set()  # Stores acronyms that have already been noted as issues

        issues = []

        for paragraph in doc:
            # Skip lines that appear to be headings
            words = paragraph.strip().split()
            if all(word.isupper() for word in words) and any(word in heading_words for word in words):
                continue

            # First, find all text that should be ignored
            ignored_spans = []
            for match in ignore_pattern.finditer(paragraph):
                ignored_spans.append(match.span())

            # Check for acronym definitions first
            defined_matches = defined_pattern.finditer(paragraph)
            for match in defined_matches:
                full_term, acronym = match.groups()
                # Skip if the acronym is in an ignored span
                if not any(start <= match.start(2) <= end for start, end in ignored_spans):
                    if acronym not in predefined_acronyms:
                        if acronym not in defined_acronyms:
                            defined_acronyms[acronym] = {
                                'full_term': full_term.strip(),
                                'defined_at': paragraph.strip(),
                                'used': False
                            }

            # Check for acronym usage
            usage_matches = acronym_pattern.finditer(paragraph)
            for match in usage_matches:
                acronym = match.group()
                start_pos = match.start()

                # Skip if the acronym is in an ignored span
                if any(start <= start_pos <= end for start, end in ignored_spans):
                    continue

                # Skip predefined acronyms, valid words, and other checks
                if (acronym in predefined_acronyms or
                    acronym in heading_words or
                    acronym.lower() in valid_words or  # Check against valid words list
                    any(not c.isalpha() for c in acronym) or
                    len(acronym) > 10):
                    continue

                if acronym not in defined_acronyms and acronym not in reported_acronyms:
                    # Undefined acronym used; report only once
                    issues.append(f"Confirm '{acronym}' was defined at its first use.")
                    reported_acronyms.add(acronym)
                elif acronym in defined_acronyms:
                    defined_acronyms[acronym]['used'] = True
                    used_acronyms.add(acronym)

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    @profile_performance
    def acronym_usage_check(self, doc: List[str]) -> DocumentCheckResult:
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Pattern to find acronym definitions (e.g., "Environmental Protection Agency (EPA)")
        defined_pattern = re.compile(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)')

        # Pattern to find acronym usage (e.g., "FAA", "EPA")
        acronym_pattern = re.compile(r'\b[A-Z]{2,}\b')

        # Tracking structures
        defined_acronyms = {}
        used_acronyms = set()

        # Step 1: Extract all defined acronyms
        for paragraph in doc:
            defined_matches = defined_pattern.findall(paragraph)
            for full_term, acronym in defined_matches:
                if acronym not in defined_acronyms:
                    defined_acronyms[acronym] = {
                        'full_term': full_term.strip(),
                        'defined_at': paragraph.strip()
                    }

        # Step 2: Check for acronym usage, excluding definitions
        for paragraph in doc:
            # Remove definitions from paragraph for usage checks
            paragraph_excluding_definitions = re.sub(defined_pattern, '', paragraph)

            usage_matches = acronym_pattern.findall(paragraph_excluding_definitions)
            for acronym in usage_matches:
                if acronym in defined_acronyms:
                    used_acronyms.add(acronym)

        # Step 3: Identify unused acronyms
        unused_acronyms = [
            {
                'acronym': acronym,
                'full_term': data['full_term'],
                'defined_at': data['defined_at']
            }
            for acronym, data in defined_acronyms.items()
            if acronym not in used_acronyms
        ]

        # Success is true if no unused acronyms are found
        success = len(unused_acronyms) == 0

        return DocumentCheckResult(success=success, issues=unused_acronyms)

    def _check_consistency(self, paragraphs, results):
        """Check for consistent terminology usage."""
        for i, text in enumerate(paragraphs):
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                pattern = fr'\b{standard}\b'
                for variant in variants:
                    if re.search(variant, text, re.IGNORECASE):
                        results.add_issue(
                            message=f"Inconsistent terminology: use '{standard}' instead of '{variant}'",
                            severity=Severity.LOW,
                            line_number=i+1
                        )
    
    def _check_forbidden_terms(self, paragraphs, results):
        """Check for forbidden or discouraged terms."""
        for i, text in enumerate(paragraphs):
            for term, message in FORBIDDEN_TERMS.items():
                pattern = fr'\b{term}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    results.add_issue(
                        message=message,
                        severity=Severity.MEDIUM,
                        line_number=i+1
                    )