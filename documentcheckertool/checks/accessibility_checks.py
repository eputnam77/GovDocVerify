from typing import List, Dict, Any
from documentcheckertool.utils.text_utils import count_words, count_syllables, split_sentences
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.config.document_config import VALIDATION_CONFIG
from functools import wraps
import logging
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from docx import Document
from .base_checker import BaseChecker

logger = logging.getLogger(__name__)

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add performance profiling logic here if needed
        return func(*args, **kwargs)
    return wrapper

class AccessibilityChecks(BaseChecker):
    """Class for handling accessibility-related checks."""
    
    def __init__(self, pattern_cache):
        self.pattern_cache = pattern_cache
        logger.info("Initialized AccessibilityChecks with pattern cache")
        # Add passive voice patterns
        self.passive_patterns = [
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b',
            r'\b(?:has|have|had)\s+been\s+\w+ed\b',
            r'\b(?:has|have|had)\s+been\s+\w+en\b'
        ]
        self.passive_regex = re.compile('|'.join(self.passive_patterns), re.IGNORECASE)
        logger.debug("Initialized passive voice detection patterns")

    def check_readability(self, doc: List[str]) -> DocumentCheckResult:
        """Check document readability using multiple metrics and plain language standards."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        text_stats = {
            'total_words': 0,
            'total_syllables': 0,
            'total_sentences': 0,
            'complex_words': 0,
            'passive_voice_count': 0
        }
        
        # Process each paragraph
        for paragraph in doc:
            if not paragraph.strip():
                continue
                
            sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
            text_stats['total_sentences'] += len(sentences)
            
            for sentence in sentences:
                if self.passive_regex.search(sentence):
                    text_stats['passive_voice_count'] += 1
                    
                words = sentence.split()
                text_stats['total_words'] += len(words)
                
                for word in words:
                    word = re.sub(r'[^\w\s]', '', word.lower())
                    if not word:
                        continue
                    
                    syllables = self._count_syllables(word)
                    text_stats['total_syllables'] += syllables
                    if syllables >= 3:
                        text_stats['complex_words'] += 1

        return self._calculate_readability_metrics(text_stats)

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
    def check_section_508_compliance(self, doc_path: str) -> DocumentCheckResult:
        """Perform Section 508 compliance checks focusing on image alt text and heading structure."""
        try:
            doc = Document(doc_path)
            issues = []
            images_with_alt = 0
            heading_structure = {}
            heading_issues = []
            hyperlink_issues = []

            # Image alt text check
            for shape in doc.inline_shapes:
                alt_text = None
                if hasattr(shape, '_inline') and hasattr(shape._inline, 'docPr'):
                    docPr = shape._inline.docPr
                    alt_text = docPr.get('descr') or docPr.get('title')

                if (alt_text):
                    images_with_alt += 1
                else:
                    issues.append({
                        'category': 'image_alt_text',
                        'message': 'Image is missing descriptive alt text.',
                        'context': 'Ensure all images have descriptive alt text.'
                    })

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
                'severity': 'error',
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
                        'severity': 'error',
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
                    'severity': 'error',
                    'message': f"Broken link detected",
                    'context': f"URL: {url} (HTTP {response.status_code})",
                    'recommendation': 'Update or remove the broken link'
                }
        except requests.RequestException:
            return {
                'category': 'hyperlink_validity',
                'severity': 'warning',
                'message': f"Unable to verify link",
                'context': f"URL: {url}",
                'recommendation': 'Check the link manually'
            }
        return None

    def _format_compliance_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format compliance issues with clear, user-friendly descriptions."""
        formatted_issues = []
        
        for issue in result.issues:
            if issue.get('category') == '508_compliance_heading_structure':
                message = issue.get('message', 'No description provided')
                context = issue.get('context', 'No context provided').strip()
                recommendation = issue.get('recommendation', 'No recommendation provided').strip()
                formatted_issues.append(
                    f"    • {message}. Context: {context}. Recommendation: {recommendation}"
                )
            elif issue.get('category') == 'image_alt_text':
                formatted_issues.append(
                    f"    • {issue.get('message', 'No description provided')}. {issue.get('context', '')}"
                )
            elif issue.get('category') == 'hyperlink_validity':
                formatted_issues.append(
                    f"    • {issue.get('message', 'No description provided')} - {issue.get('context', '')}. {issue.get('recommendation', '')}"
                )
            elif issue.get('category') == 'hyperlink_accessibility':
                formatted_issues.append(
                    f"    • {issue.get('user_message', issue.get('message', 'No description provided'))}"
                )
            elif 'context' in issue and issue['context'].startswith('Link text:'):
                link_text = issue['context'].replace('Link text:', '').strip().strip('"')
                if any(phrase == link_text.lower() for phrase in ['here', 'click here', 'more', 'link']):
                    formatted_issues.append(
                        f"    • Replace non-descriptive link text \"{link_text}\" with text that clearly indicates where the link will take the user"
                    )
                elif link_text.lower().startswith(('http', 'www', 'ftp')):
                    formatted_issues.append(
                        f"    • Replace the URL \"{link_text}\" with meaningful text that describes the link destination"
                    )
                elif len(link_text) < 4:
                    formatted_issues.append(
                        f"    • Link text \"{link_text}\" is too short - use descriptive text that clearly indicates the link destination"
                    )
                else:
                    formatted_issues.append(f"    • {issue.get('message', 'No description provided')} {issue['context']}")
            else:
                message = issue.get('message', 'No description provided')
                context = issue.get('context', '').strip()
                formatted_issues.append(
                    f"    • {message} {context}"
                )

        return formatted_issues

    def run_checks(self, document: Document, doc_type: str, results: DocumentCheckResult) -> None:
        """Run all accessibility-related checks."""
        logger.info(f"Running accessibility checks for document type: {doc_type}")
        
        self._check_alt_text(document, results)
        self._check_color_contrast(document, results)
        
    def _check_alt_text(self, document: Document, results: DocumentCheckResult):
        """Check for missing alt text in images."""
        for shape in document.inline_shapes:
            if not hasattr(shape, '_inline') or not hasattr(shape._inline, 'docPr'):
                continue
            if not shape._inline.docPr.get('descr'):
                results.add_issue(
                    message="Image missing alt text",
                    severity=Severity.HIGH
                )
    
    def _check_color_contrast(self, document: Document, results: DocumentCheckResult):
        """Check for potential color contrast issues."""
        # Basic check for now - to be expanded
        for paragraph in document.paragraphs:
            if hasattr(paragraph, '_element'):
                if hasattr(paragraph._element, 'rPr'):
                    if hasattr(paragraph._element.rPr, 'color'):
                        results.add_issue(
                            message="Potential color contrast issue detected",
                            severity=Severity.MEDIUM
                        )