import logging
import re
from typing import Any, Dict, List

from docx import Document

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.config.document_config import READABILITY_CONFIG
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.utils.boilerplate_utils import is_boilerplate
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.utils.text_utils import (
    calculate_readability_metrics,
    count_syllables,
    count_words,
    split_sentences,
)

from .base_checker import BaseChecker

logger = logging.getLogger(__name__)


class ReadabilityChecks(BaseChecker):
    """Class for handling readability-related checks."""

    def __init__(self, terminology_manager: TerminologyManager):
        super().__init__(terminology_manager)
        self.readability_config = terminology_manager.terminology_data.get("readability", {})
        self.category = "readability"
        logger.info("Initialized ReadabilityChecks with terminology manager")

    @CheckRegistry.register("readability")
    def check_document(self, document: Document, doc_type: str) -> DocumentCheckResult:
        """Check document for readability issues."""
        results = DocumentCheckResult()
        self.run_checks(document, doc_type, results)
        return results

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for readability issues using overall document metrics."""
        results = DocumentCheckResult()

        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

        total_words = 0
        total_sentences = 0
        total_syllables = 0
        passive_count = 0

        passive_patterns = [
            r"\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b",
            r"\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b",
            r"\b(?:has|have|had)\s+been\s+\w+ed\b",
            r"\b(?:has|have|had)\s+been\s+\w+en\b",
        ]
        passive_regex = re.compile("|".join(passive_patterns), re.IGNORECASE)

        for paragraph in paragraphs:
            sentences = split_sentences(paragraph)
            total_sentences += len(sentences)
            words = paragraph.split()
            total_words += len(words)
            total_syllables += sum(self._count_syllables(word) for word in words)

            for sentence in sentences:
                if passive_regex.search(sentence):
                    passive_count += 1

            self._check_paragraph_structure(paragraph, results)

        if total_sentences:
            metrics = calculate_readability_metrics(total_words, total_sentences, total_syllables)
            metrics["passive_voice_percentage"] = round((passive_count / total_sentences) * 100, 1)
            results.details = {"metrics": metrics}
            self._check_document_thresholds(metrics, results)

        return results

    def _check_paragraph_structure(self, text: str, results: DocumentCheckResult) -> None:
        """Check sentence and paragraph length for a single paragraph."""
        try:
            if is_boilerplate(text):
                return

            sentences = split_sentences(text)

            for sentence in sentences:
                word_count = len(sentence.split())
                if word_count > 25:
                    sentence_preview = self._get_text_preview(sentence.strip())
                    message = (
                        f"Sentence '{sentence_preview}' is too long ({word_count} words). "
                        "Split it into shorter sentences for clarity."
                    )
                    results.add_issue(
                        message=message,
                        severity=Severity.WARNING,
                        category=getattr(self, "category", "readability"),
                    )

            sentence_count = len(sentences)
            line_count = len([line for line in text.splitlines() if line.strip()])
            if sentence_count > 6 or line_count > 8:
                paragraph_preview = self._get_text_preview(text.strip())
                results.add_issue(
                    message=(
                        f"Paragraph '{paragraph_preview}' exceeds length limits with "
                        f"{sentence_count} sentences and {line_count} lines. "
                        "Break it into smaller paragraphs for better readability."
                    ),
                    severity=Severity.WARNING,
                    category=getattr(self, "category", "readability"),
                )
        except Exception as e:
            logger.error(f"Error in readability check: {str(e)}")
            results.add_issue(
                message=f"Error calculating readability metrics: {str(e)}",
                severity=Severity.ERROR,
                category=getattr(self, "category", "readability"),
            )

    def _check_document_thresholds(
        self, metrics: Dict[str, float], results: DocumentCheckResult
    ) -> None:
        """Add issues based on overall document readability metrics."""
        flesch_ease = metrics.get("flesch_reading_ease", 0)
        flesch_grade = metrics.get("flesch_kincaid_grade", 0)

        if flesch_ease < 60:
            message = (
                f"Text is hard to read (Flesch Reading Ease: {flesch_ease:.1f}). "
                "Use simpler words and shorter sentences to improve readability."
            )
            results.add_issue(
                message=message,
                severity=Severity.WARNING,
                category=getattr(self, "category", "readability"),
            )

        if flesch_grade > 12:
            message = (
                f"Text is complex (Flesch-Kincaid Grade Level: {flesch_grade:.1f}). "
                "Consider using simpler words and shorter sentences for a wider audience."
            )
            results.add_issue(
                message=message,
                severity=Severity.WARNING,
                category=getattr(self, "category", "readability"),
            )

        passive_pct = metrics.get("passive_voice_percentage", 0)
        if passive_pct > READABILITY_CONFIG.get("max_passive_voice_percentage", 10):
            message = (
                f"Document uses {passive_pct:.1f}% passive voice (target: less than 10%). "
                "Consider using more active voice."
            )
            results.add_issue(
                message=message,
                severity=Severity.WARNING,
                category=getattr(self, "category", "readability"),
            )

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using basic rules."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel

        if word.endswith("e"):
            count -= 1
        if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
            count += 1
        if count == 0:
            count = 1

        return count

    def _get_text_preview(self, text: str, max_words: int = 6) -> str:
        """
        Get a preview of the text showing the first few words.

        Args:
            text: The text to preview
            max_words: Maximum number of words to include in preview

        Returns:
            A string containing the first few words followed by '...' if truncated
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        else:
            preview_words = words[:max_words]
            return " ".join(preview_words) + "..."

    def check(self, content: str) -> Dict[str, Any]:
        """
        Check document content for readability issues.

        Args:
            content: The document content to check

        Returns:
            Dict containing check results
        """
        errors = []
        warnings = []

        # Check sentence length
        sentences = split_sentences(content)
        for i, sentence in enumerate(sentences, 1):
            word_count = count_words(sentence)
            if word_count > self.readability_config.get("max_sentence_length", 20):
                sentence_preview = self._get_text_preview(sentence.strip())
                message = (
                    f"Sentence '{sentence_preview}' is too long ({word_count} words). "
                    "Split it into shorter sentences for clarity."
                )
                warnings.append(
                    {
                        "line": i,
                        "message": message,
                        "severity": Severity.WARNING,
                    }
                )

        # Check paragraph length
        paragraphs = content.split("\n\n")
        for i, paragraph in enumerate(paragraphs, 1):
            sentence_count = len(split_sentences(paragraph))
            if sentence_count > self.readability_config.get("max_paragraph_sentences", 5):
                paragraph_preview = self._get_text_preview(paragraph.strip())
                warnings.append(
                    {
                        "line": i,
                        "message": (
                            f"Paragraph '{paragraph_preview}' contains {sentence_count} sentences. "
                            "Consider breaking it into shorter paragraphs for better readability."
                        ),
                        "severity": Severity.WARNING,
                    }
                )

        # Check for passive voice
        passive_patterns = [
            r"\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b",
            r"\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b",
            r"\b(?:has|have|had)\s+been\s+\w+ed\b",
            r"\b(?:has|have|had)\s+been\s+\w+en\b",
        ]
        passive_regex = re.compile("|".join(passive_patterns), re.IGNORECASE)

        for i, sentence in enumerate(sentences, 1):
            if passive_regex.search(sentence):
                warnings.append(
                    {
                        "line": i,
                        "message": (
                            "Consider using active voice instead of passive voice. "
                            "This is a readability recommendation, not a strict style rule. "
                            "Passive voice may be acceptable depending on the context."
                        ),
                        "severity": Severity.WARNING,
                        "type": "advisory",
                    }
                )

        return {"has_errors": len(errors) > 0, "errors": errors, "warnings": warnings}

    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability metrics."""
        stats = {"total_words": 0, "total_syllables": 0, "total_sentences": 0, "complex_words": 0}

        for paragraph in doc:
            sentences = split_sentences(paragraph)
            stats["total_sentences"] += len(sentences)

            for sentence in sentences:
                words = sentence.split()
                stats["total_words"] += len(words)

                for word in words:
                    syllables = count_syllables(word)
                    stats["total_syllables"] += syllables
                    if syllables >= 3:
                        stats["complex_words"] += 1

        metrics = calculate_readability_metrics(
            stats["total_words"], stats["total_sentences"], stats["total_syllables"]
        )

        metrics_result = DocumentCheckResult()
        self._check_document_thresholds(metrics, metrics_result)
        issues = metrics_result.issues

        return DocumentCheckResult(
            success=len(issues) == 0, issues=issues, details={"metrics": metrics}
        )

    def _check_readability_thresholds_metrics(self, metrics: Dict[str, float]) -> List[Dict]:
        """Check readability metrics against thresholds."""
        logger.debug("Checking readability metrics against thresholds")
        issues = []

        if metrics["flesch_reading_ease"] < READABILITY_CONFIG["min_flesch_ease"]:
            logger.warning(
                f"Flesch Reading Ease score {metrics['flesch_reading_ease']} below threshold "
                f"{READABILITY_CONFIG['min_flesch_ease']}"
            )
            issues.append(
                {
                    "type": "readability_score",
                    "metric": "Flesch Reading Ease",
                    "score": metrics["flesch_reading_ease"],
                    "message": "Document may be too difficult for general audience",
                }
            )

        return issues

    def check_sentence_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check for overly long sentences."""
        DocumentCheckResult()
        # ... existing code ...

    def check_paragraph_length(self, doc: List[str]) -> DocumentCheckResult:
        """Check for overly long paragraphs."""
        DocumentCheckResult()
        # ... existing code ...

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all readability-related checks."""
        logger.info(f"Running readability checks for document type: {doc_type}")
        text = "\n".join([p.text for p in document.paragraphs])
        check_result = self.check_text(text)
        results.issues.extend(check_result.issues)
        results.success = check_result.success
