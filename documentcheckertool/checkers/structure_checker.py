from docx import Document
from typing import List, Optional

class WatermarkRequirement:
    def __init__(self, text: str, doc_stage: str):
        self.text = text
        self.doc_stage = doc_stage

class StructureChecker:
    VALID_WATERMARKS = [
        WatermarkRequirement("DRAFT - FOR INTERNAL FAA REVIEW", "internal_review"),
        WatermarkRequirement("DRAFT - FOR PUBLIC COMMENTS", "public_comment"),
        WatermarkRequirement("DRAFT - FOR AGC REVIEW OF PUBLIC COMMENTS", "agc_public_comment"),
        WatermarkRequirement("DRAFT - FOR FINAL ISSUANCE", "final_draft"),
        WatermarkRequirement("DRAFT - FOR AGC REVIEW OF FINAL ISSUANCE", "agc_final_review")
    ]

    def check_watermark(self, doc: Document, expected_stage: str) -> tuple[bool, str]:
        """Check if document has appropriate watermark for its stage."""
        # Get watermark from document header/footer sections
        watermark_text = self._extract_watermark(doc)
        
        # Find matching requirement for stage
        expected_watermark = next(
            (w for w in self.VALID_WATERMARKS if w.doc_stage == expected_stage),
            None
        )

        if not watermark_text:
            return False, "Document is missing required watermark"
        
        if not expected_watermark:
            return False, f"Unknown document stage: {expected_stage}"
            
        if watermark_text != expected_watermark.text:
            return False, f"Incorrect watermark for {expected_stage} stage. Expected: {expected_watermark.text}"
            
        return True, "Watermark is correct for document stage"

    def _extract_watermark(self, doc: Document) -> Optional[str]:
        """Extract watermark text from Word document headers/footers."""
        # Implementation will need to use python-docx to extract watermark
        # from document sections and headers/footers
        pass
