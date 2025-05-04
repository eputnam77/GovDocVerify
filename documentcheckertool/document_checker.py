from typing import List, Dict, Any, Optional
from models import DocumentCheckResult, DocumentType
from checks.heading_checks import HeadingChecks
from checks.accessibility_checks import AccessibilityChecks
from checks.format_checks import FormatChecks
from checks.structure_checks import StructureChecks
from checks.terminology_checks import TerminologyChecks
from utils.text_utils import split_sentences, count_words, normalize_reference
from utils.pattern_cache import PatternCache

class FAADocumentChecker:
    """Main document checker class that coordinates various checks."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.pattern_cache = PatternCache()
        self.heading_checks = HeadingChecks(self.pattern_cache)
        self.accessibility_checks = AccessibilityChecks(self.pattern_cache)
        self.format_checks = FormatChecks(self.pattern_cache)
        self.structure_checks = StructureChecks(self.pattern_cache)
        self.terminology_checks = TerminologyChecks(self.pattern_cache)
        # Initialize other check modules here

    def run_all_document_checks(self, doc: List[str], doc_type: str, template_type: str) -> Dict[str, DocumentCheckResult]:
        """Run all document checks and return results."""
        results = {}
        
        # Run heading checks
        results['heading_title'] = self.heading_checks.check_heading_title(doc, doc_type)
        results['heading_period'] = self.heading_checks.check_heading_period(doc, doc_type)
        
        # Run accessibility checks
        results['readability'] = self.accessibility_checks.check_readability(doc)
        results['section_508'] = self.accessibility_checks.check_section_508_compliance(doc)
        
        # Run format checks
        results['date_format'] = self.format_checks.check_date_format_usage(doc)
        results['phone_format'] = self.format_checks.check_phone_number_format_usage(doc)
        results['placeholder'] = self.format_checks.check_placeholder_usage(doc)
        
        # Run structure checks
        results['paragraph_length'] = self.structure_checks.check_paragraph_length(doc)
        results['sentence_length'] = self.structure_checks.check_sentence_length(doc)
        results['parentheses'] = self.structure_checks.check_parentheses(doc)
        
        # Run terminology checks
        results['abbreviation'] = self.terminology_checks.check_abbreviation_usage(doc)
        results['cross_reference'] = self.terminology_checks.check_cross_reference_usage(doc)
        results['required_language'] = self.terminology_checks.check_required_language(doc, doc_type)
        results['pronouns'] = self.terminology_checks.check_pronouns(doc)
        results['split_infinitives'] = self.terminology_checks.check_split_infinitives(doc)
        
        # Add other checks here
        
        return results 