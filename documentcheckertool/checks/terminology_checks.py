# pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG

import logging
import re
from typing import Any, Dict

from docx import Document

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.config.terminology_rules import (
    FORBIDDEN_TERMS,
    TERM_REPLACEMENTS,
    TERMINOLOGY_VARIANTS,
    TerminologyMessages,
)
from documentcheckertool.models import DocumentCheckResult, Severity

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


class TerminologyChecks(BaseChecker):
    """Class for handling terminology-related checks."""

    def __init__(self, terminology_manager=None):
        super().__init__(terminology_manager)
        self.category = "terminology"
        self.heading_words = terminology_manager.terminology_data.get("heading_words", [])
        logger.info("Initialized TerminologyChecks with terminology manager")

    @CheckRegistry.register("terminology")
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for terminology issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all terminology-related checks."""
        logger.info(f"Running terminology checks for document type: {doc_type}")

        text_content = [p.text for p in document.paragraphs]
        self._check_proposed_wording(text_content, doc_type, results)
        self._check_consistency(text_content, results)
        self._check_forbidden_terms(text_content, results)
        self._check_term_replacements(text_content, results)

    def _check_consistency(self, paragraphs, results):
        """Check for consistent terminology usage."""
        for i, text in enumerate(paragraphs):
            logger.debug(f"[Terminology] Checking line {i+1}: {text!r}")
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                for variant in variants:
                    pattern = rf"\b{re.escape(variant)}\b"
                    if re.search(pattern, text, re.IGNORECASE):
                        logger.debug(
                            f"[Terminology] Matched variant '{variant}' (should use '{standard}') in line {i+1}"
                        )
                        results.add_issue(
                            message=TerminologyMessages.INCONSISTENT_TERMINOLOGY.format(
                                standard=standard, variant=variant
                            ),
                            severity=Severity.INFO,
                            line_number=i + 1,
                            category=getattr(self, "category", "terminology"),
                        )

    def _check_forbidden_terms(self, paragraphs, results):
        """Check for forbidden or discouraged terms."""
        for i, text in enumerate(paragraphs):
            logger.debug(f"[Terminology] Checking forbidden terms in line {i+1}: {text!r}")
            for term, message in FORBIDDEN_TERMS.items():
                pattern = rf"\b{re.escape(term)}\b"
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"[Terminology] Matched forbidden term '{term}' in line {i+1}")
                    results.add_issue(
                        message=message,
                        severity=Severity.WARNING,
                        line_number=i + 1,
                        category=getattr(self, "category", "terminology"),
                    )

    def _check_term_replacements(self, paragraphs, results):
        """
        Flag any outdated terms that have a direct replacement in
        TERM_REPLACEMENTS.  Suggest the approved wording.
        """
        for i, text in enumerate(paragraphs):
            logger.debug(f"[Terminology] Checking term replacements in line {i+1}: {text!r}")
            for obsolete, approved in TERM_REPLACEMENTS.items():
                # Handle special cases that need different regex patterns
                if obsolete in [
                    "CFR Part",
                    "U.S.C",
                    "USC",
                    "in accordance with",
                    "in compliance with",
                ]:
                    # For phrases and specific formatting, use exact matching
                    if obsolete == "CFR Part":
                        pattern = r"\bCFR\s+Part\b"
                    elif obsolete == "U.S.C":
                        # Match U.S.C without a final period - more precise pattern
                        pattern = r"\bU\.S\.C(?!\.)(?=\s|$)"
                    elif obsolete == "USC":
                        # Match USC without periods
                        pattern = r"\bUSC\b"
                    elif obsolete in ["in accordance with", "in compliance with"]:
                        # Match the full phrase
                        pattern = rf"\b{re.escape(obsolete)}\b"
                    else:
                        pattern = rf"\b{re.escape(obsolete)}\b"
                else:
                    # Standard word boundary matching for other terms
                    pattern = rf"\b{re.escape(obsolete)}\b"

                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"[Terminology] Matched obsolete term '{obsolete}' in line {i+1}")
                    results.add_issue(
                        message=f'Replace "{obsolete}" with "{approved}"',
                        severity=Severity.WARNING,
                        line_number=i + 1,
                        category=getattr(self, "category", "terminology"),
                    )

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check the text for terminology-related issues."""
        logger.debug(f"Running check_text in TerminologyChecks on text of length: {len(text)}")
        result = DocumentCheckResult()
        issues = []

        # Split text into lines for line-by-line checking
        lines = text.split("\n")
        logger.debug(f"Split text into {len(lines)} lines")

        # Split infinitive detection (info-level, may be acceptable)
        # Enhanced: match 'to' followed by 1-3 words, then a word (likely a verb)
        split_infinitive_pattern = re.compile(r"\bto\s+(?:\w+\s+){1,3}\w+\b", re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            logger.debug(f"[Terminology] Checking line {i}: {line!r}")
            for match in split_infinitive_pattern.finditer(line):
                # Optionally, filter out common false positives (e.g., 'to in addition to')
                # For now, flag all matches
                issues.append(
                    {
                        "message": "Split infinitive detected (may be acceptable in some contexts)",
                        "severity": Severity.INFO,
                        "category": getattr(self, "category", "terminology"),
                    }
                )

        # Check for forbidden terms (whole-word, case-insensitive)
        for i, line in enumerate(lines, 1):
            for term, message in FORBIDDEN_TERMS.items():
                pattern = rf"\b{re.escape(term)}\b"
                if re.search(pattern, line, re.IGNORECASE):
                    logger.debug(f"[Terminology] Matched forbidden term '{term}' in line {i}")
                    issues.append(
                        {
                            "message": message,
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Check for inconsistent terminology
        for i, line in enumerate(lines, 1):
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                for variant in variants:
                    pattern = rf"\b{re.escape(variant)}\b"
                    if re.search(pattern, line, re.IGNORECASE):
                        logger.debug(
                            f"[Terminology] Matched variant '{variant}' (should use '{standard}') in line {i}"
                        )
                        issues.append(
                            {
                                "message": f'Inconsistent terminology: use "{standard}" instead of "{variant}"',
                                "severity": Severity.WARNING,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )

        # Check for obsolete term replacements
        for i, line in enumerate(lines, 1):
            for obsolete, approved in TERM_REPLACEMENTS.items():
                # Handle special cases that need different regex patterns
                if obsolete in [
                    "CFR Part",
                    "U.S.C",
                    "USC",
                    "in accordance with",
                    "in compliance with",
                ]:
                    # For phrases and specific formatting, use exact matching
                    if obsolete == "CFR Part":
                        pattern = r"\bCFR\s+Part\b"
                    elif obsolete == "U.S.C":
                        # Match U.S.C without a final period - more precise pattern
                        pattern = r"\bU\.S\.C(?!\.)(?=\s|$)"
                    elif obsolete == "USC":
                        # Match USC without periods
                        pattern = r"\bUSC\b"
                    elif obsolete in ["in accordance with", "in compliance with"]:
                        # Match the full phrase
                        pattern = rf"\b{re.escape(obsolete)}\b"
                    else:
                        pattern = rf"\b{re.escape(obsolete)}\b"
                else:
                    # Standard word boundary matching for other terms
                    pattern = rf"\b{re.escape(obsolete)}\b"

                if re.search(pattern, line, re.IGNORECASE):
                    logger.debug(f"[Terminology] Matched obsolete term '{obsolete}' in line {i}")
                    # Skip 'additionally' since it's handled in forbidden terms
                    if obsolete == "additionally":
                        continue
                    issues.append(
                        {
                            "message": f'Replace "{obsolete}" with "{approved}"',
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Add issues to the result
        result.issues.extend(issues)
        if issues:
            result.success = False
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
        paragraphs = content.split("\n")
        logger.debug(f"Processing {len(paragraphs)} paragraphs")

        # Check USC/CFR formatting
        for i, paragraph in enumerate(paragraphs, 1):
            # Check USC formatting
            if "USC" in paragraph:
                warnings.append(
                    {
                        "line": i,
                        "message": "USC should be U.S.C.",
                        "severity": Severity.WARNING,
                        "category": getattr(self, "category", "terminology"),
                    }
                )
            if "U.S.C " in paragraph:
                warnings.append(
                    {
                        "line": i,
                        "message": "U.S.C should have a final period",
                        "severity": Severity.WARNING,
                        "category": getattr(self, "category", "terminology"),
                    }
                )

            # Check CFR formatting
            if "C.F.R." in paragraph:
                warnings.append(
                    {
                        "line": i,
                        "message": "C.F.R. should be CFR",
                        "severity": Severity.WARNING,
                        "category": getattr(self, "category", "terminology"),
                    }
                )
            if "CFR Part" in paragraph:
                warnings.append(
                    {
                        "line": i,
                        "message": "CFR Part should be CFR part",
                        "severity": Severity.WARNING,
                        "category": getattr(self, "category", "terminology"),
                    }
                )

        # Check gendered terms
        gendered_terms = {"chairman": "chair", "flagman": "flagperson", "manpower": "labor force"}
        for i, paragraph in enumerate(paragraphs, 1):
            for term, replacement in gendered_terms.items():
                if term in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": f"{term} should be {replacement}",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Check plain language
        legalese_terms = [
            "pursuant to",
            "in accordance with",
            "in compliance with",
            "aforementioned",
            "herein",
            "thereto",
        ]
        for i, paragraph in enumerate(paragraphs, 1):
            for term in legalese_terms:
                if term in paragraph.lower():
                    if term in ["pursuant to", "in accordance with", "in compliance with"]:
                        warnings.append(
                            {
                                "line": i,
                                "message": "Use simpler alternatives like 'under' or 'following'",
                                "severity": Severity.WARNING,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )
                    else:
                        warnings.append(
                            {
                                "line": i,
                                "message": "Avoid archaic or legalese terms",
                                "severity": Severity.WARNING,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )

        # Check aviation terminology
        aviation_terms = {
            "flight crew": "flightcrew",
            "cockpit": "flight deck",
            "notice to air missions": "notice to airmen",
        }
        for i, paragraph in enumerate(paragraphs, 1):
            for term, replacement in aviation_terms.items():
                if term in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": f"{term} should be {replacement}",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Check qualifiers
        qualifiers = ["very", "extremely", "quite"]
        for i, paragraph in enumerate(paragraphs, 1):
            for qualifier in qualifiers:
                if qualifier in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": "Avoid unnecessary qualifiers",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Check plural usage
        plural_terms = ["data", "criteria", "phenomena"]
        for i, paragraph in enumerate(paragraphs, 1):
            for term in plural_terms:
                if term in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": "Ensure consistent singular/plural usage",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )

        # Enhanced check for obsolete authority citations
        AUTHORITY_LINE_REGEX = re.compile(r"Authority\s*:(.*)", re.IGNORECASE)
        OBSOLETE_CITATIONS = [
            (
                re.compile(r"(49\s*U\.?S\.?C\.?\s*)?(§\s*)?106\(g\)", re.IGNORECASE),
                "49 U.S.C. 106(g)",
            )
        ]
        for i, paragraph in enumerate(paragraphs, 1):
            m = AUTHORITY_LINE_REGEX.search(paragraph)
            if m:
                text = m.group(1)
                for pattern, citation in OBSOLETE_CITATIONS:
                    if pattern.search(text):
                        # Remove obsolete citation from authority line (quick fix)
                        corrected = re.sub(
                            r"(,?\s*(49\s*U\.?S\.?C\.?\s*)?(§\s*)?106\(g\),?)", "", paragraph
                        )
                        # Clean up double commas/extra spaces
                        corrected = (
                            re.sub(r",\s*,", ",", corrected)
                            .replace(" ,", ",")
                            .replace("  ", " ")
                            .strip(" ,")
                        )
                        warnings.append(
                            {
                                "line": i,
                                "message": f"{citation} is no longer valid; confirm or remove this citation.",
                                "severity": Severity.WARNING,
                                "suggestion": corrected,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )

        return {"has_errors": len(errors) > 0, "errors": errors, "warnings": warnings}

    # ----------------------------------------------------------
    # Proposed-language guardrail
    # ----------------------------------------------------------
    _PROPOSE_REGEX = re.compile(r"\bpropos\w*\b", re.IGNORECASE)
    _PROPOSE_PHASES = {
        "NPRM",  # Notice of Proposed Rulemaking
        "NOTICE_OF_PROPOSED_RULEMAKING",
        "PROPOSED_SC",  # Proposed Special Conditions
        "NOTICE_OF_PROPOSED_SPECIAL_CONDITIONS",
    }

    def _is_proposed_phase(self, doc_type: str) -> bool:
        """Return True if this document type is *supposed* to contain
        proposed-phase language (and thus the guardrail should be skipped)."""
        if not doc_type:
            return False
        normalised = doc_type.strip().upper().replace(" ", "_")
        return normalised in self._PROPOSE_PHASES

    def _check_proposed_wording(
        self,
        paragraphs: list[str],
        doc_type: str,
        results: DocumentCheckResult,
    ) -> None:
        """Flag any occurrence of 'propos*' in non-proposed documents."""
        if self._is_proposed_phase(doc_type):
            logger.debug("Document is in proposed phase – skipping proposed-wording check")
            return

        for idx, text in enumerate(paragraphs, start=1):
            logger.debug(f"_check_proposed_wording: line {idx}: {repr(text)}")
            match = self._PROPOSE_REGEX.search(text)
            logger.debug(f"_check_proposed_wording: regex match: {match}")
            if match:
                results.add_issue(
                    message=TerminologyMessages.PROPOSED_WORDING_INFO,
                    severity=Severity.INFO,
                    line_number=idx,
                    category=getattr(self, "category", "terminology"),
                )
