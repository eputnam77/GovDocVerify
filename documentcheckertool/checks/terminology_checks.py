# pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG

from docx import Document
from .base_checker import BaseChecker
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.terminology_rules import (
    TERM_REPLACEMENTS,
    FORBIDDEN_TERMS,
    TERMINOLOGY_VARIANTS
)
from typing import List, Dict, Any, Optional
from ..utils.decorators import profile_performance
import re
import logging
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.utils.text_utils import count_words, count_syllables, split_sentences
import string
from documentcheckertool.checks.check_registry import CheckRegistry

logger = logging.getLogger(__name__)

class TerminologyChecks(BaseChecker):
    """Class for handling terminology-related checks."""

    def __init__(self, terminology_manager: TerminologyManager):
        super().__init__(terminology_manager)
        self.heading_words = terminology_manager.terminology_data.get('heading_words', [])
        logger.info("Initialized TerminologyChecks with terminology manager")

    @CheckRegistry.register('terminology')
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for terminology issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    @CheckRegistry.register('terminology')
    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all terminology-related checks."""
        logger.info(f"Running terminology checks for document type: {doc_type}")

        text_content = [p.text for p in document.paragraphs]
        self._check_consistency(text_content, results)
        self._check_forbidden_terms(text_content, results)

    @CheckRegistry.register('terminology')
    def _check_consistency(self, paragraphs, results):
        """Check for consistent terminology usage."""
        for i, text in enumerate(paragraphs):
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                pattern = fr'\b{standard}\b'
                for variant in variants:
                    if re.search(variant, text, re.IGNORECASE):
                        results.add_issue(
                            message=f"Inconsistent terminology: use '{standard}' instead of '{variant}'",
                            severity=Severity.INFO,
                            line_number=i+1
                        )

    @CheckRegistry.register('terminology')
    def _check_forbidden_terms(self, paragraphs, results):
        """Check for forbidden or discouraged terms."""
        for i, text in enumerate(paragraphs):
            for term, message in FORBIDDEN_TERMS.items():
                pattern = fr'\b{term}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    results.add_issue(
                        message=message,
                        severity=Severity.WARNING,
                        line_number=i+1
                    )

    @CheckRegistry.register('terminology')
    def check_text(self, text: str) -> DocumentCheckResult:
        """Check the text for terminology-related issues."""
        logger.debug(f"Running check_text in TerminologyChecks on text of length: {len(text)}")
        result = DocumentCheckResult()
        issues = []

        # Split text into lines for line-by-line checking
        lines = text.split('\n')
        logger.debug(f"Split text into {len(lines)} lines")

        # Check for forbidden terms
        for i, line in enumerate(lines, 1):
            for term, message in FORBIDDEN_TERMS.items():
                if term in line.lower():
                    issues.append({
                        'message': message,
                        'severity': Severity.WARNING
                    })

        # Check for inconsistent terminology
        for i, line in enumerate(lines, 1):
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                for variant in variants:
                    if variant in line.lower():
                        issues.append({
                            'message': f'Inconsistent terminology: use "{standard}" instead of "{variant}"',
                            'severity': Severity.WARNING
                        })

        # Add issues to the result
        result.issues.extend(issues)
        logger.debug(f"Terminology checks completed. Found {len(issues)} issues.")
        return result

    def check(self, content: str) -> Dict[str, Any]:
        """
        Check document content for terminology issues.

        Args:
            content: The document content to check

        Returns:
            Dict containing check results
        """
        errors = []
        warnings = []

        # Split content into paragraphs
        paragraphs = content.split('\n')
        logger.debug(f"Processing {len(paragraphs)} paragraphs")

        # Check USC/CFR formatting
        for i, paragraph in enumerate(paragraphs, 1):
            # Check USC formatting
            if 'USC' in paragraph:
                warnings.append({
                    'line': i,
                    'message': 'USC should be U.S.C.',
                    'severity': Severity.WARNING
                })
            if 'U.S.C ' in paragraph:
                warnings.append({
                    'line': i,
                    'message': 'U.S.C should have a final period',
                    'severity': Severity.WARNING
                })

            # Check CFR formatting
            if 'C.F.R.' in paragraph:
                warnings.append({
                    'line': i,
                    'message': 'C.F.R. should be CFR',
                    'severity': Severity.WARNING
                })
            if 'CFR Part' in paragraph:
                warnings.append({
                    'line': i,
                    'message': 'CFR Part should be CFR part',
                    'severity': Severity.WARNING
                })

        # Check gendered terms
        gendered_terms = {
            'chairman': 'chair',
            'flagman': 'flagperson',
            'manpower': 'labor force'
        }
        for i, paragraph in enumerate(paragraphs, 1):
            for term, replacement in gendered_terms.items():
                if term in paragraph.lower():
                    warnings.append({
                        'line': i,
                        'message': f'{term} should be {replacement}',
                        'severity': Severity.WARNING
                    })

        # Check plain language
        legalese_terms = [
            'pursuant to',
            'in accordance with',
            'in compliance with',
            'aforementioned',
            'herein',
            'thereto'
        ]
        for i, paragraph in enumerate(paragraphs, 1):
            for term in legalese_terms:
                if term in paragraph.lower():
                    if term in ['pursuant to', 'in accordance with', 'in compliance with']:
                        warnings.append({
                            'line': i,
                            'message': "Use simpler alternatives like 'under' or 'following'",
                            'severity': Severity.WARNING
                        })
                    else:
                        warnings.append({
                            'line': i,
                            'message': 'Avoid archaic or legalese terms',
                            'severity': Severity.WARNING
                        })

        # Check aviation terminology
        aviation_terms = {
            'flight crew': 'flightcrew',
            'cockpit': 'flight deck',
            'notice to air missions': 'notice to airmen'
        }
        for i, paragraph in enumerate(paragraphs, 1):
            for term, replacement in aviation_terms.items():
                if term in paragraph.lower():
                    warnings.append({
                        'line': i,
                        'message': f'{term} should be {replacement}',
                        'severity': Severity.WARNING
                    })

        # Check qualifiers
        qualifiers = ['very', 'extremely', 'quite']
        for i, paragraph in enumerate(paragraphs, 1):
            for qualifier in qualifiers:
                if qualifier in paragraph.lower():
                    warnings.append({
                        'line': i,
                        'message': 'Avoid unnecessary qualifiers',
                        'severity': Severity.WARNING
                    })

        # Check plural usage
        plural_terms = ['data', 'criteria', 'phenomena']
        for i, paragraph in enumerate(paragraphs, 1):
            for term in plural_terms:
                if term in paragraph.lower():
                    warnings.append({
                        'line': i,
                        'message': 'Ensure consistent singular/plural usage',
                        'severity': Severity.WARNING
                    })

        # Check authority citations
        for i, paragraph in enumerate(paragraphs, 1):
            if 'Authority:' in paragraph and '49 U.S.C. 106(g)' in paragraph:
                warnings.append({
                    'line': i,
                    'message': '49 U.S.C. 106(g) should not be included',
                    'severity': Severity.WARNING
                })

        return {
            'has_errors': len(errors) > 0,
            'errors': errors,
            'warnings': warnings
        }