from typing import List, Dict, Any, Union
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

logger = logging.getLogger(__name__)

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)
    return wrapper

class AccessibilityChecks(BaseChecker):
    """Class for handling accessibility-related checks."""

    def __init__(self, terminology_manager: TerminologyManager):
        super().__init__(terminology_manager)
        self.validation_config = terminology_manager.terminology_data.get('accessibility', {})
        self.formatter = ResultFormatter(style=FormatStyle.HTML)
        logger.info("Initialized AccessibilityChecks with terminology manager")
        # Add passive voice patterns
        self.passive_patterns = [
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b',
            r'\b(?:has|have|had)\s+been\s+\w+ed\b',
            r'\b(?:has|have|had)\s+been\s+\w+en\b'
        ]
        self.passive_regex = re.compile('|'.join(self.passive_patterns), re.IGNORECASE)
        logger.debug("Initialized passive voice detection patterns")

    def validate_input(self, doc: List[str]) -> bool:
        """Validate input document content."""
        return isinstance(doc, list) and all(isinstance(line, str) for line in doc)

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

    def _check_heading_hierarchy(self, headings, heading_issues):
        """Check heading hierarchy for accessibility issues."""
        min_level = min(level for _, level in headings)
        if min_level > 1:
            heading_issues.append({
                'severity': Severity.ERROR,
                'type': 'missing_h1',
                'message': 'Document should start with a Heading 1',
                'context': f"First heading found is level {headings[0][1]}: '{headings[0][0]}'",
                'recommendation': 'Add a Heading 1 at the start of the document'
            })

        previous_heading = None
        for text, level in headings:
            if previous_heading:
                prev_text, prev_level = previous_heading
                if level > prev_level + 1:
                    missing_levels = list(range(prev_level + 1, level))
                    heading_issues.append({
                        'severity': Severity.ERROR,
                        'type': 'skipped_levels',
                        'message': f"Skipped heading level(s) {', '.join(map(str, missing_levels))} - Found H{level} '{text}' after H{prev_level} '{prev_text}'. Add H{prev_level + 1} before this section.",
                    })
            previous_heading = (text, level)

    def _check_hyperlinks(self, doc, hyperlink_issues):
        """Check hyperlinks for accessibility and validity issues."""
        non_descriptive = ['click here', 'here', 'link', 'this link', 'more',
                          'read more', 'learn more', 'click', 'see this',
                          'see here', 'go', 'url', 'this', 'page']

        # First check for accessibility issues
        for paragraph in doc.paragraphs:
            hyperlinks = self._get_hyperlinks_from_paragraph(paragraph)

            for hyperlink in hyperlinks:
                link_text = self._get_hyperlink_text(hyperlink)
                if not link_text:
                    continue

                self._check_hyperlink_text(link_text, non_descriptive, hyperlink_issues)

                # Extract URL and check for validity
                if hasattr(hyperlink, 'href'):
                    url = hyperlink.href
                    url_check_result = self._validate_url(url)
                    if url_check_result:
                        hyperlink_issues.append(url_check_result)

    def _validate_url(self, url: str) -> Dict[str, str]:
        """Validate a single URL."""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True, headers={'User-Agent': 'CheckerTool/1.0'})
            if response.status_code >= 400:
                return {
                    'category': 'hyperlink_validity',
                    'severity': Severity.ERROR,
                    'message': f"Broken link detected",
                    'context': f"URL: {url} (HTTP {response.status_code})",
                    'recommendation': 'Update or remove the broken link'
                }
        except requests.RequestException:
            return {
                'category': 'hyperlink_validity',
                'severity': Severity.WARNING,
                'message': f"Unable to verify link",
                'context': f"URL: {url}",
                'recommendation': 'Check the link manually'
            }
        return None

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all accessibility-related checks."""
        logger.info(f"Running accessibility checks for document type: {doc_type}")

        self._check_alt_text(document, results)
        self._check_color_contrast(document, results)

    def _check_alt_text(self, document: Document, results: DocumentCheckResult):
        """Check for missing alt text in images."""
        logger.debug("Starting alt text check")
        total_shapes = len(document.inline_shapes)
        logger.debug(f"Found {total_shapes} inline shapes to check")

        for i, shape in enumerate(document.inline_shapes, 1):
            logger.debug(f"Processing shape {i}/{total_shapes}")

            # Skip if not a proper image shape
            if not hasattr(shape, '_inline'):
                logger.debug(f"Shape {i} has no _inline attribute, skipping")
                continue

            if not hasattr(shape._inline, 'docPr'):
                logger.debug(f"Shape {i} has no docPr attribute, skipping")
                continue

            # Get shape properties
            docPr = shape._inline.docPr
            shape_name = docPr.get('name', '').lower()
            logger.debug(f"Shape {i} name: {shape_name}")

            # Log all available properties
            logger.debug(f"Shape {i} properties: {dict(docPr.items())}")

            # Skip decorative elements
            decorative_keywords = [
                'watermark', 'background', 'decoration', 'border', 'line',
                'divider', 'separator', 'icon', 'bullet', 'marker'
            ]
            if any(keyword in shape_name for keyword in decorative_keywords):
                logger.debug(f"Shape {i} identified as decorative element: {shape_name}")
                continue

            # Skip table-related graphics
            table_keywords = ['table', 'grid', 'cell', 'header', 'footer']
            if any(keyword in shape_name for keyword in table_keywords):
                logger.debug(f"Shape {i} identified as table graphic: {shape_name}")
                continue

            # Skip charts and diagrams
            chart_keywords = ['chart', 'graph', 'diagram', 'plot', 'figure']
            if any(keyword in shape_name for keyword in chart_keywords):
                logger.debug(f"Shape {i} identified as chart/diagram: {shape_name}")
                continue

            # Check for alt text
            alt_text = docPr.get('descr') or docPr.get('title')
            logger.debug(f"Shape {i} alt text: {alt_text}")

            if not alt_text:
                logger.debug(f"Shape {i} missing alt text")
                image_name = docPr.get('name', 'unnamed')
                logger.debug(f"Creating issue for image: {image_name}")

                message = f"Image '{image_name}' is missing alt text. Please add a descriptive alt text for accessibility."
                logger.debug(f"Generated message: {message}")

                results.add_issue(
                    message=message,
                    severity=Severity.ERROR
                )
                logger.debug(f"Added issue for image {image_name}")
            else:
                logger.debug(f"Shape {i} has alt text: {alt_text}")

        logger.debug(f"Alt text check complete. Found {len(results.issues)} issues")
        if results.issues:
            logger.debug("Issues found:")
            for issue in results.issues:
                logger.debug(f"  - {issue['message']}")

    def _check_color_contrast(self, content: Union[List[str], DocxDocument], results: DocumentCheckResult):
        """Check for potential color contrast issues."""
        if isinstance(content, DocxDocument):
            lines = [paragraph.text for paragraph in content.paragraphs]
        else:
            lines = content

        color_pattern = re.compile(r'(?:color|background-color):\s*#([A-Fa-f0-9]{6})')

        def relative_luminance(hex_color: str) -> float:
            """Calculate relative luminance from hex color."""
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def contrast_ratio(l1: float, l2: float) -> float:
            """Calculate contrast ratio between two luminance values."""
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)

        for line in lines:
            colors = color_pattern.findall(line)
            if len(colors) >= 2:  # If we found both foreground and background colors
                ratio = contrast_ratio(
                    relative_luminance(colors[0]),
                    relative_luminance(colors[1])
                )
                if ratio < 4.5:  # WCAG AA standard minimum contrast
                    results.add_issue(f"Insufficient color contrast ratio ({ratio:.2f}:1)", Severity.ERROR)

        return results

    def check(self, content: str) -> Dict[str, Any]:
        """Check document for accessibility issues."""
        errors = []
        warnings = []

        # Check for alt text in images
        if '<img' in content and 'alt=' not in content:
            errors.append({
                'line_number': 0,
                'message': 'Images missing alt text',
                'suggestion': 'Add alt text to all images',
                'context': 'Accessibility requirement'
            })

        # Check for proper heading structure
        heading_levels = []
        for line in content.split('\n'):
            if line.startswith('#'):
                level = len(line.split()[0])
                heading_levels.append(level)
                if level > 1 and level - heading_levels[-2] > 1:
                    errors.append({
                        'line_number': 0,
                        'message': f'Invalid heading level: {level}',
                        'suggestion': 'Ensure heading levels are sequential',
                        'context': line
                    })

        # Check for color contrast
        if 'color:' in content or 'background-color:' in content:
            warnings.append({
                'line_number': 0,
                'message': 'Color usage detected',
                'suggestion': 'Ensure sufficient color contrast',
                'context': 'Accessibility requirement'
            })

        return {
            'has_errors': len(errors) > 0,
            'errors': errors,
            'warnings': warnings
        }

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

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text content for accessibility issues."""
        results = DocumentCheckResult()
        lines = content.split('\n')

        # Check heading structure
        heading_results = self.check_heading_structure(lines)
        results.issues.extend(heading_results.issues)

        # Check image accessibility
        image_results = self.check_image_accessibility(lines)
        results.issues.extend(image_results.issues)

        # Check color contrast
        self._check_color_contrast(lines, results)

        results.success = len(results.issues) == 0
        return results