import logging
from typing import List, Dict, Any, Optional
from docx import Document
from documentcheckertool.models import DocumentCheckResult, DocumentType
from documentcheckertool.checks.heading_checks import HeadingChecks
from documentcheckertool.checks.accessibility_checks import AccessibilityChecks
from documentcheckertool.checks.format_checks import FormatChecks
from documentcheckertool.checks.structure_checks import StructureChecks
from documentcheckertool.checks.terminology_checks import TerminologyChecks
from documentcheckertool.utils.text_utils import split_sentences, count_words, normalize_reference
from documentcheckertool.utils.pattern_cache import PatternCache

logger = logging.getLogger(__name__)

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

    def run_all_document_checks(self, document_path: str, doc_type: str = None) -> DocumentCheckResult:
        """Run all document checks."""
        try:
            doc = Document(document_path)
            results = DocumentCheckResult()
            
            # Run all check types
            self.heading_checks.run_checks(doc, doc_type, results)
            self.accessibility_checks.run_checks(doc, doc_type, results)
            self.format_checks.run_checks(doc, doc_type, results)
            self.structure_checks.run_checks(doc, doc_type, results)
            self.terminology_checks.run_checks(doc, doc_type, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running checks: {str(e)}")
            raise