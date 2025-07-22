# pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG

import logging
import re
from typing import Any, Dict

from docx.document import Document as DocxDocument

from govdocverify.checks.check_registry import CheckRegistry
from govdocverify.config.terminology_rules import (
    FORBIDDEN_TERMS,
    TERM_REPLACEMENTS,
    TERMINOLOGY_VARIANTS,
    TerminologyMessages,
)
from govdocverify.models import DocumentCheckResult, Severity

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)

# Match 'above' or 'below' when used as vague cross references, such as
# "see above" or "the section below". This avoids flagging phrases like
# "above the threshold" that are not references.
ABOVE_BELOW_REF_PATTERN = re.compile(
    r"\b(?:see|refer to|as(?:\s+(?:mentioned|stated|discussed|noted|described))?|"
    r"mentioned|stated|discussed|noted|described)\s+(above|below)\b|"
    r"\b(?:paragraph|section|figure|table|chapter|item|list)s?\s+(above|below)\b|"
    r"\bthe\s+(above|below)(?:-(?:mentioned|listed|referenced))?\s+(?:paragraph|section|figure|table|chapter|item|list)\b|"
    r"\b(?:above|below)-(?:mentioned|listed|referenced)\b",
    re.IGNORECASE,
)


class TerminologyChecks(BaseChecker):
    """Class for handling terminology-related checks."""

    def __init__(self, terminology_manager: Any | None = None) -> None:
        super().__init__(terminology_manager)
        self.category: str = "terminology"
        self.heading_words: list[str] = (
            terminology_manager.terminology_data.get("heading_words", [])
            if terminology_manager is not None
            else []
        )
        logger.info("Initialized TerminologyChecks with terminology manager")

    @CheckRegistry.register("terminology")
    def check_document(self, document: DocxDocument, doc_type: str) -> DocumentCheckResult:
        """Check document for terminology issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    def run_checks(
        self, document: DocxDocument, doc_type: str, results: DocumentCheckResult
    ) -> None:
        """Run all terminology-related checks."""
        logger.info(f"Running terminology checks for document type: {doc_type}")

        text_content = [p.text for p in document.paragraphs]
        self._check_proposed_wording(text_content, doc_type, results)
        self._check_consistency(text_content, results)
        self._check_forbidden_terms(text_content, results)
        self._check_term_replacements(text_content, results)

    def _check_consistency(self, paragraphs: list[str], results: DocumentCheckResult) -> None:
        """Check for consistent terminology usage."""
        for i, text in enumerate(paragraphs):
            logger.debug(f"[Terminology] Checking line {i+1}: {text!r}")
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                for variant in variants:
                    pattern = rf"\b{re.escape(variant)}\b"
                    flags = 0 if variant.lower() == standard.lower() else re.IGNORECASE
                    if re.search(pattern, text, flags):
                        logger.debug(
                            f"[Terminology] Matched variant '{variant}' (should use '{standard}') "
                            f"in line {i+1}"
                        )
                        results.add_issue(
                            message=TerminologyMessages.INCONSISTENT_TERMINOLOGY.format(
                                standard=standard, variant=variant
                            ),
                            severity=Severity.INFO,
                            line_number=i + 1,
                            category=getattr(self, "category", "terminology"),
                        )

    def _check_forbidden_terms(self, paragraphs: list[str], results: DocumentCheckResult) -> None:
        """Check for forbidden or discouraged terms."""
        for i, text in enumerate(paragraphs):
            logger.debug(f"[Terminology] Checking forbidden terms in line {i+1}: {text!r}")
            if ABOVE_BELOW_REF_PATTERN.search(text):
                logger.debug(f"[Terminology] Matched relative reference in line {i+1}")
                results.add_issue(
                    message=TerminologyMessages.ABOVE_BELOW_WARNING,
                    severity=Severity.WARNING,
                    line_number=i + 1,
                    category=getattr(self, "category", "terminology"),
                )
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

    def _check_term_replacements(self, paragraphs: list[str], results: DocumentCheckResult) -> None:
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
                        message=f'Change "{obsolete}" to "{approved}"',
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

        # Run individual check methods
        issues.extend(self._check_split_infinitives(lines))
        issues.extend(self._check_forbidden_terms_in_lines(lines))
        issues.extend(self._check_terminology_variants_in_lines(lines))
        issues.extend(self._check_obsolete_terms_in_lines(lines))

        # Add issues to the result
        result.issues.extend(issues)
        if issues:
            result.success = False
        logger.debug(f"Terminology checks completed. Found {len(issues)} issues.")
        return result

    def _check_split_infinitives(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Check for split infinitives in text lines."""
        issues: list[Dict[str, Any]] = []
        split_infinitive_pattern = re.compile(r"\bto\s+(?:\w+\s+){1,3}\w+\b", re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            logger.debug(f"[Terminology] Checking line {i}: {line!r}")
            for match in split_infinitive_pattern.finditer(line):
                issues.append(
                    {
                        "message": "Split infinitive detected (may be acceptable in some contexts)",
                        "severity": Severity.INFO,
                        "category": getattr(self, "category", "terminology"),
                    }
                )
        return issues

    def _check_forbidden_terms_in_lines(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Check for forbidden terms in text lines."""
        issues: list[Dict[str, Any]] = []
        for i, line in enumerate(lines, 1):
            if ABOVE_BELOW_REF_PATTERN.search(line):
                logger.debug(f"[Terminology] Matched relative reference in line {i}")
                issues.append(
                    {
                        "message": TerminologyMessages.ABOVE_BELOW_WARNING,
                        "severity": Severity.WARNING,
                        "category": getattr(self, "category", "terminology"),
                    }
                )
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
        return issues

    def _check_terminology_variants_in_lines(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Check for terminology variants in text lines."""
        issues: list[Dict[str, Any]] = []
        for i, line in enumerate(lines, 1):
            for standard, variants in TERMINOLOGY_VARIANTS.items():
                for variant in variants:
                    pattern = rf"\b{re.escape(variant)}\b"
                    flags = 0 if variant.lower() == standard.lower() else re.IGNORECASE
                    if re.search(pattern, line, flags):
                        logger.debug(
                            f"[Terminology] Matched variant '{variant}' (should use '{standard}') "
                            f"in line {i}"
                        )
                        issues.append(
                            {
                                "message": f'Change "{variant}" to "{standard}".',
                                "severity": Severity.WARNING,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )
        return issues

    def _check_obsolete_terms_in_lines(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Check for obsolete terms that need replacement."""
        issues: list[Dict[str, Any]] = []
        for i, line in enumerate(lines, 1):
            for obsolete, approved in TERM_REPLACEMENTS.items():
                pattern = self._get_pattern_for_obsolete_term(obsolete)
                if re.search(pattern, line, re.IGNORECASE):
                    logger.debug(f"[Terminology] Matched obsolete term '{obsolete}' in line {i}")
                    issues.append(
                        {
                            "message": f'Change "{obsolete}" to "{approved}"',
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )
        return issues

    def _get_pattern_for_obsolete_term(self, obsolete: str) -> str:
        """Get the appropriate regex pattern for an obsolete term."""
        special_cases = [
            "CFR Part",
            "U.S.C",
            "USC",
            "in accordance with",
            "in compliance with",
        ]

        if obsolete in special_cases:
            if obsolete == "CFR Part":
                return r"\bCFR\s+Part\b"
            elif obsolete == "U.S.C":
                return r"\bU\.S\.C(?!\.)(?=\s|$)"
            elif obsolete == "USC":
                return r"\bUSC\b"
            elif obsolete in ["in accordance with", "in compliance with"]:
                return rf"\b{re.escape(obsolete)}\b"
            else:
                return rf"\b{re.escape(obsolete)}\b"
        else:
            return rf"\b{re.escape(obsolete)}\b"

    def check(self, content: str) -> Dict[str, Any]:
        """
        Check document content for terminology issues.

        Args:
            content: The document content to check

        Returns:
            Dict containing check results
        """
        errors: list[Dict[str, Any]] = []
        warnings: list[Dict[str, Any]] = []

        # Split content into paragraphs
        paragraphs = content.split("\n")
        logger.debug(f"Processing {len(paragraphs)} paragraphs")

        # Run individual check methods
        warnings.extend(self._check_usc_cfr_formatting(paragraphs))
        warnings.extend(self._check_gendered_terms(paragraphs))
        warnings.extend(self._check_plain_language(paragraphs))
        warnings.extend(self._check_aviation_terminology(paragraphs))
        warnings.extend(self._check_qualifiers(paragraphs))
        warnings.extend(self._check_plural_usage(paragraphs))
        warnings.extend(self._check_obsolete_citations(paragraphs))

        return {"has_errors": len(errors) > 0, "errors": errors, "warnings": warnings}

    def _check_usc_cfr_formatting(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check USC/CFR formatting in paragraphs."""
        warnings: list[Dict[str, Any]] = []
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
        return warnings

    def _check_gendered_terms(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check for gendered terms in paragraphs."""
        warnings: list[Dict[str, Any]] = []
        gendered_terms = {"chairman": "chair", "flagman": "flagperson", "manpower": "labor force"}
        for i, paragraph in enumerate(paragraphs, 1):
            for term, replacement in gendered_terms.items():
                if term in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": f"Change {term} to {replacement}",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )
        return warnings

    def _check_plain_language(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check for legalese terms that should be simplified."""
        warnings: list[Dict[str, Any]] = []
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
                                "message": (
                                    "Change '{term}' to an alternative like 'under' or 'following'"
                                ),
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
        return warnings

    def _check_aviation_terminology(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check aviation terminology usage."""
        warnings: list[Dict[str, Any]] = []
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
                            "message": f"Change {term} to {replacement}",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )
        return warnings

    def _check_qualifiers(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check for unnecessary qualifiers."""
        warnings: list[Dict[str, Any]] = []
        qualifiers = ["very", "extremely", "quite"]
        for i, paragraph in enumerate(paragraphs, 1):
            for qualifier in qualifiers:
                if qualifier in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": "Remove the unnecessary qualifier: '{qualifier}'.",
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )
        return warnings

    def _check_plural_usage(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check plural noun usage."""
        warnings: list[Dict[str, Any]] = []
        plural_terms = ["data", "criteria", "phenomena"]
        for i, paragraph in enumerate(paragraphs, 1):
            for term in plural_terms:
                if term in paragraph.lower():
                    warnings.append(
                        {
                            "line": i,
                            "message": (
                                f"Use '{term}' as a plural noun (e.g., 'criteria are'). "
                                "Note: 'data is' is now widely accepted."
                            ),
                            "severity": Severity.WARNING,
                            "category": getattr(self, "category", "terminology"),
                        }
                    )
        return warnings

    def _check_obsolete_citations(self, paragraphs: list[str]) -> list[Dict[str, Any]]:
        """Check for obsolete authority citations."""
        warnings: list[Dict[str, Any]] = []
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
                                "message": (
                                    f"Remove '{citation}'. This authority citation was deleted "
                                    f"by the FAA Reauthorization."
                                ),
                                "severity": Severity.WARNING,
                                "suggestion": corrected,
                                "category": getattr(self, "category", "terminology"),
                            }
                        )
        return warnings

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
