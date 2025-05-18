from typing import List, Dict, Any, Union, Optional, Tuple
from pathlib import Path
from documentcheckertool.utils.text_utils import count_words, count_syllables, split_sentences
from documentcheckertool.models import DocumentCheckResult, Severity
from functools import wraps
import logging
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from docx import Document
from ..utils.formatting import DocumentFormatter
from .base_checker import BaseChecker
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
from docx.document import Document as DocxDocument
from documentcheckertool.checks.base_checker import BaseChecker
from documentcheckertool.utils.terminology_utils import TerminologyManager
from documentcheckertool.checks.check_registry import CheckRegistry

logger = logging.getLogger(__name__)

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)
    return wrapper

class AccessibilityChecks(BaseChecker):
    """Class for handling accessibility-related checks."""

    def __init__(self, terminology_manager: Optional[TerminologyManager] = None):
        """Initialize the accessibility checks.

        Args:
            terminology_manager: Optional TerminologyManager instance. If not provided,
                               a new instance will be created.
        """
        self.terminology_manager = terminology_manager or TerminologyManager()
        logger.info("Initialized AccessibilityChecks")

    @CheckRegistry.register('accessibility')
    def check_document(self, document: Union[str, Path, Document], doc_type: str) -> DocumentCheckResult:
        """Check document for accessibility issues."""
        results = DocumentCheckResult()

        # Handle file path input
        if isinstance(document, (str, Path)):
            try:
                with open(document, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                self.run_checks(content, doc_type, results)
            except Exception as e:
                logger.error(f"Error reading file {document}: {e}")
                results.add_issue(f"Error reading file: {str(e)}", Severity.ERROR)
        else:
            self.run_checks(document, doc_type, results)

        return results

    @CheckRegistry.register('accessibility')
    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for accessibility issues."""
        results = DocumentCheckResult()
        # Convert text to Document-like structure for processing
        lines = text.split('\n')
        self._check_alt_text(lines, results)
        self._check_color_contrast(lines, results)
        self._check_heading_structure(lines, results)
        return results

    def validate_input(self, doc: List[str]) -> bool:
        """Validate input document content."""
        return isinstance(doc, list) and all(isinstance(line, str) for line in doc)

    @CheckRegistry.register('accessibility')
    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability using multiple metrics and plain language standards."""
        results = DocumentCheckResult()

        if not self.validate_input(doc):
            results.add_issue('Invalid input format for readability check', Severity.ERROR)
            results.success = False
            return results

        for line in doc:
            words = line.split()
            if len(words) > 25:  # Check sentence length
                results.add_issue(f'Sentence too long. Word count exceeds recommended limit ({len(words)} words).', Severity.ERROR)

        # Set success to False if any issues were found
        results.success = len(results.issues) == 0
        return results

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using basic rules."""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        on_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel

        if word.endswith('e'):
            count -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        if count == 0:
            count = 1

        return count

    def _calculate_readability_metrics(self, stats: Dict[str, int]) -> DocumentCheckResult:
        """Calculate readability metrics and generate issues."""
        try:
            # Calculate metrics
            flesch_ease = 206.835 - 1.015 * (stats['total_words'] / stats['total_sentences']) - 84.6 * (stats['total_syllables'] / stats['total_words'])
            flesch_grade = 0.39 * (stats['total_words'] / stats['total_sentences']) + 11.8 * (stats['total_syllables'] / stats['total_words']) - 15.59
            fog_index = 0.4 * ((stats['total_words'] / stats['total_sentences']) + 100 * (stats['complex_words'] / stats['total_words']))
            passive_percentage = (stats['passive_voice_count'] / stats['total_sentences']) * 100 if stats['total_sentences'] > 0 else 0

            issues = []
            self._add_readability_issues(issues, flesch_ease, flesch_grade, fog_index, passive_percentage)

            return DocumentCheckResult(
                success=len(issues) == 0,
                issues=issues,
                details={
                    'metrics': {
                        'flesch_reading_ease': round(flesch_ease, 1),
                        'flesch_kincaid_grade': round(flesch_grade, 1),
                        'gunning_fog_index': round(fog_index, 1),
                        'passive_voice_percentage': round(passive_percentage, 1)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error calculating readability metrics: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{'error': f'Error calculating readability metrics: {str(e)}'}]
            )

    def _add_readability_issues(self, issues: List[Dict], flesch_ease: float, flesch_grade: float,
                              fog_index: float, passive_percentage: float) -> None:
        """Add readability issues based on metrics."""
        # Add disclaimer about readability metrics being guidelines
        issues.append({
            'type': 'readability_info',
            'message': 'Note: Readability metrics are guidelines to help improve clarity. Not all documents will meet all targets, and that\'s okay. Use these suggestions to identify areas for potential improvement.'
        })

        if flesch_ease < 50:
            issues.append({
                'type': 'readability_score',
                'metric': 'Flesch Reading Ease',
                'score': round(flesch_ease, 1),
                'message': 'Consider simplifying language where possible to improve readability, but maintain necessary technical terminology.'
            })

        if flesch_grade > 12:
            issues.append({
                'type': 'readability_score',
                'metric': 'Flesch-Kincaid Grade Level',
                'score': round(flesch_grade, 1),
                'message': 'The reading level may be high for some audiences. Where appropriate, consider simpler alternatives while preserving technical accuracy.'
            })

        if fog_index > 12:
            issues.append({
                'type': 'readability_score',
                'metric': 'Gunning Fog Index',
                'score': round(fog_index, 1),
                'message': 'Text complexity is high but may be necessary for your content. Review for opportunities to clarify without oversimplifying.'
            })

        if passive_percentage > 10:
            issues.append({
                'type': 'passive_voice',
                'percentage': round(passive_percentage, 1),
                'message': f'Document uses {round(passive_percentage, 1)}% passive voice. While some passive voice is acceptable and sometimes necessary, consider active voice where it improves clarity.'
            })

    @profile_performance
    @CheckRegistry.register('accessibility')
    def check_section_508_compliance(self, content: Union[str, List[str]]) -> DocumentCheckResult:
        """Perform Section 508 compliance checks focusing on image alt text and heading structure."""
        try:
            if isinstance(content, list):
                # Handle list input
                results = DocumentCheckResult()
                heading_results = self.check_heading_structure(content)
                image_results = self.check_image_accessibility(content)

                results.issues.extend(heading_results.issues)
                results.issues.extend(image_results.issues)

                results.success = len(results.issues) == 0
                return results
            else:
                # Handle file path input
                doc = Document(content)
                issues = []
                images_with_alt = 0
                heading_structure = {}
                heading_issues = []
                hyperlink_issues = []

                # Image alt text check
                self._check_alt_text(doc, results)

                # Enhanced heading structure check
                headings = []
                for paragraph in doc.paragraphs:
                    if paragraph.style.name.startswith('Heading'):
                        try:
                            level = int(paragraph.style.name.split()[-1])
                            text = paragraph.text.strip()
                            if text:
                                headings.append((text, level))
                                heading_structure[level] = heading_structure.get(level, 0) + 1
                        except ValueError:
                            continue

                # Check heading hierarchy
                if headings:
                    self._check_heading_hierarchy(headings, heading_issues)

                # Enhanced Hyperlink Accessibility Check
                self._check_hyperlinks(doc, hyperlink_issues)

                # Combine all issues and create details
                issues.extend(hyperlink_issues)
                issues.extend([{'category': '508_compliance_heading_structure', **issue} for issue in heading_issues])

                details = self._create_compliance_details(doc, images_with_alt, headings, heading_structure, hyperlink_issues)

                return DocumentCheckResult(
                    success=len(issues) == 0,
                    issues=issues,
                    details=details
                )
        except Exception as e:
            logger.error(f"Error during 508 compliance check: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'category': 'error',
                    'message': f'Error performing 508 compliance check: {str(e)}'
                }]
            )

    @CheckRegistry.register('accessibility')
    def _check_heading_hierarchy(self, headings: List[Tuple[str, Union[int, str]]], results: DocumentCheckResult) -> None:
        """Check heading hierarchy for accessibility issues."""
        logger.debug("Checking heading hierarchy")

        # Handle None content
        if headings is None:
            logger.error("Invalid content type for heading hierarchy check: None")
            results.add_issue(
                message="Invalid content type for heading hierarchy check: None",
                severity=Severity.ERROR
            )
            return

        # Filter out invalid heading levels
        valid_headings = []
        for text, level in headings:
            if isinstance(level, int):
                valid_headings.append((text, level))
            else:
                logger.debug(f"Skipping invalid heading level type: {type(level)} for heading '{text}'")
                continue

        if not valid_headings:
            logger.debug("No valid headings found")
            return

        # Only check for missing H1 if we have valid headings
        if valid_headings and not any(level == 1 for _, level in valid_headings):
            logger.warning("Document is missing a top-level heading (H1)")
            results.add_issue(
                message="Document is missing a top-level heading (H1)",
                severity=Severity.WARNING
            )

        # Check for skipped levels
        prev_level = 0
        for text, level in valid_headings:
            if level > prev_level + 1:
                logger.warning(f"Heading level skipped: H{level} '{text}' follows H{prev_level}")
                results.add_issue(
                    message=f"Heading level skipped: H{level} '{text}' follows H{prev_level}",
                    severity=Severity.ERROR
                )
            prev_level = level

    @CheckRegistry.register('accessibility')
    def _check_hyperlinks(self, content: Union[Document, List[str]], results: DocumentCheckResult) -> None:
        """Check hyperlinks for accessibility issues."""
        from docx.document import Document as DocxDocument

        if content is None:
            logger.error("Invalid content type for hyperlink check: None")
            results.add_issue(
                message="Invalid content type for hyperlink check: None",
                severity=Severity.ERROR
            )
            return

        # Handle both Document and Mock objects
        if hasattr(content, 'paragraphs'):  # Check for Document-like object
            links = []
            for paragraph in content.paragraphs:
                for run in paragraph.runs:
                    if hasattr(run, '_element') and hasattr(run._element, 'xpath'):
                        if run._element.xpath('.//w:hyperlink'):
                            links.append(run.text)
        else:
            if not isinstance(content, list):
                logger.error(f"Invalid content type for hyperlink check: {type(content).__name__}")
                results.add_issue(
                    message=f"Invalid content type for hyperlink check: {type(content).__name__}",
                    severity=Severity.ERROR
                )
                return

            link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
            links = [match.group(1) for match in link_pattern.finditer('\n'.join(content))]

        non_descriptive = ['click here', 'here', 'link', 'this link', 'more',
                          'read more', 'learn more', 'click', 'see this',
                          'see here', 'go', 'url', 'this', 'page']

        for link_text in links:
            if link_text.lower() in non_descriptive:
                logger.warning(f"Found non-descriptive link text: '{link_text}'")
                results.add_issue(
                    message=f"Non-descriptive link text: '{link_text}'. Use more descriptive text for better accessibility.",
                    severity=Severity.ERROR
                )

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all accessibility-related checks."""
        logger.info(f"Running accessibility checks for document type: {doc_type}")

        self._check_alt_text(document, results)
        self._check_color_contrast(document, results)

    @CheckRegistry.register('accessibility')
    def _check_alt_text(self, content: Union[Document, List[str]], results: DocumentCheckResult) -> None:
        """Check for missing alt text in images."""
        logger.debug(f"Starting alt text check with content type: {type(content)}")
        logger.debug(f"Content type details: {type(content).__name__}")

        # Check if content is None
        if content is None:
            error_msg = "Invalid content type for alt text check: None. Expected Document or List[str]"
            logger.error(error_msg)
            results.add_issue(
                message=error_msg,
                severity=Severity.ERROR
            )
            return

        # Check if content is one of the valid types
        if not (isinstance(content, DocxDocument) or isinstance(content, list)):
            error_msg = f"Invalid content type for alt text check: {type(content).__name__}. Expected Document or List[str]"
            logger.error(error_msg)
            results.add_issue(
                message=error_msg,
                severity=Severity.ERROR
            )
            return

        if isinstance(content, DocxDocument):
            logger.debug("Processing Document type content")
            shapes = content.inline_shapes
            logger.debug(f"Found {len(shapes)} shapes in document")

            for i, shape in enumerate(shapes, 1):
                if not hasattr(shape, '_inline') or not hasattr(shape._inline, 'docPr'):
                    logger.debug(f"Skipping shape {i} - missing required attributes")
                    continue

                docPr = shape._inline.docPr
                name = docPr.get('name', '').lower()

                # Skip watermarks and table graphics
                if 'watermark' in name or 'table_border' in name:
                    logger.debug(f"Skipping {name} - identified as watermark or table graphic")
                    continue

                alt_text = docPr.get('descr') or docPr.get('title')
                logger.debug(f"Shape {i} alt text: {alt_text}")

                if not alt_text:
                    logger.warning(f"Image '{docPr.get('name', 'unnamed')}' is missing alt text")
                    results.add_issue(
                        message=f"Image '{docPr.get('name', 'unnamed')}' is missing alt text",
                        severity=Severity.ERROR
                    )
        else:  # content is List[str]
            logger.debug("Processing List[str] type content")
            logger.debug(f"Content length: {len(content)} lines")

            # For text input, look for image references
            image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
            for i, line in enumerate(content, 1):
                matches = list(image_pattern.finditer(line))
                if matches:
                    logger.debug(f"Found {len(matches)} image references in line {i}")

                for match in matches:
                    alt_text = match.group(1)
                    logger.debug(f"Line {i} image alt text: {alt_text}")
                    if not alt_text:
                        logger.warning(f"Image at line {i} is missing alt text")
                        results.add_issue(
                            message=f"Image at line {i} is missing alt text",
                            severity=Severity.ERROR
                        )

    @CheckRegistry.register('accessibility')
    def _check_color_contrast(self, content: Union[Document, List[str]], results: DocumentCheckResult) -> None:
        """Check for potential color contrast issues."""
        from docx.document import Document as DocxDocument

        # Handle None content
        if content is None:
            logger.error("Invalid content type for color contrast check: None")
            results.add_issue(
                message="Invalid content type for color contrast check: None",
                severity=Severity.ERROR
            )
            return

        if isinstance(content, DocxDocument):
            lines = [paragraph.text for paragraph in content.paragraphs]
        else:
            lines = content

        color_pattern = re.compile(r'(?:color|background-color):\s*#([A-Fa-f0-9]{6})')

        for i, line in enumerate(lines, 1):
            colors = color_pattern.findall(line)
            if len(colors) >= 2:
                ratio = self._calculate_contrast_ratio(colors[0], colors[1])
                if ratio < 4.5:  # WCAG AA standard
                    results.add_issue(
                        message=f"Insufficient color contrast ratio ({ratio:.2f}:1) at line {i}",
                        severity=Severity.ERROR
                    )

    @CheckRegistry.register('accessibility')
    def _check_heading_structure(self, content: Union[Document, List[str]], results: DocumentCheckResult) -> None:
        """Check heading structure for accessibility issues."""
        from docx.document import Document as DocxDocument

        if content is None:
            logger.error("Invalid content type for heading structure check: None")
            results.add_issue(
                message="Invalid content type for heading structure check: None",
                severity=Severity.ERROR
            )
            return

        # Handle both Document and Mock objects
        if hasattr(content, 'paragraphs'):  # Check for Document-like object
            headings = []
            for p in content.paragraphs:
                if hasattr(p.style, 'name') and p.style.name.startswith('Heading'):
                    try:
                        # Extract level from style name, handling both real and mock objects
                        style_name = str(p.style.name)  # Convert to string to handle mock objects
                        level = int(style_name.split()[-1])
                        text = p.text.strip()
                        if text:
                            headings.append((text, level))
                    except (ValueError, AttributeError, IndexError):
                        logger.debug(f"Skipping invalid heading style: {p.style.name}")
                        continue
        else:
            if not isinstance(content, list):
                logger.error(f"Invalid content type for heading structure check: {type(content).__name__}")
                results.add_issue(
                    message=f"Invalid content type for heading structure check: {type(content).__name__}",
                    severity=Severity.ERROR
                )
                return

            headings = []
            for i, line in enumerate(content, 1):
                if line.strip().startswith('#'):
                    level = len(line.split()[0])
                    text = line.split('#', 1)[1].strip()
                    headings.append((text, level))

        if headings:
            self._check_heading_hierarchy(headings, results)
        else:
            results.add_issue(
                message="Document is missing a top-level heading (H1)",
                severity=Severity.ERROR
            )

    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two hex colors."""
        def relative_luminance(hex_color: str) -> float:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    @CheckRegistry.register('accessibility')
    def check_heading_structure(self, content: List[str]) -> DocumentCheckResult:
        """Check heading structure for accessibility issues."""
        results = DocumentCheckResult()
        heading_levels = []

        for line in content:
            if line.strip().startswith('#'):
                level = len(line.split()[0])
                heading_levels.append(level)
                if level > 1 and len(heading_levels) > 1 and level - heading_levels[-2] > 1:
                    results.add_issue('Inconsistent heading structure', Severity.ERROR)

        return results

    @CheckRegistry.register('accessibility')
    def check_image_accessibility(self, content: List[str]) -> DocumentCheckResult:
        """Check image accessibility including alt text."""
        results = DocumentCheckResult()
        image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')

        for line in content:
            matches = image_pattern.finditer(line)
            for match in matches:
                alt_text = match.group(1)
                if not alt_text:
                    results.add_issue('Missing alt text', Severity.ERROR)

        return results