from typing import Dict, List, Any, Optional, Union
from enum import Enum
from colorama import Fore, Style
from documentcheckertool.models import DocumentCheckResult, Severity

class FormatStyle(Enum):
    """Output format styles."""
    PLAIN = "plain"
    MARKDOWN = "markdown"
    HTML = "html"

class ResultFormatter:
    """Unified formatter for all document check results."""

    def __init__(self, style: Union[str, FormatStyle] = FormatStyle.PLAIN):
        self._style = FormatStyle(style) if isinstance(style, str) else style
        self._setup_style()

        self.issue_categories = {
            'heading_title_check': {
                'title': 'Required Headings Check',
                'description': 'Verifies that your document includes all mandatory section headings. Note: The "Cancellation." heading is only required if this document cancels or replaces an existing document. If your document is new or doesn\'t cancel anything, you can ignore the Cancellation heading warning.',
                'solution': 'Add all required headings in the correct order using the correct capitalization format. For cancellation warnings, only add the heading if you are actually canceling a document.',
                'example_fix': {
                    'before': 'Missing required heading "PURPOSE."',
                    'after': 'Added heading "PURPOSE." at the beginning of the document'
                }
            },
            'heading_title_period_check': {
                'title': 'Heading Period Format',
                'description': 'Examines heading punctuation to ensure compliance with FAA document formatting standards. Some FAA documents (like Advisory Circulars and Orders) require periods at the end of headings, while others (like Federal Register Notices) don\'t.',
                'solution': 'Format heading periods according to document type requirements.',
                'example_fix': {
                    'before': 'Purpose',
                    'after': 'Purpose.' # For ACs and Orders
                }
            },
            'table_figure_reference_check': {
                'title': 'Table and Figure References',
                'description': 'Analyzes how tables and figures are referenced within your document text. Capitalize references at the beginning of sentences (e.g., "Table 2-1 shows...") and use lowercase references within sentences (e.g., "...as shown in table 2-1").',
                'solution': 'Capitalize references at start of sentences, use lowercase within sentences.',
                'example_fix': {
                    'before': 'The DTR values are specified in Table 3-1 and Figure 3-2.',
                    'after': 'The DTR values are specified in table 3-1 and figure 3-2.'
                }
            },
            'acronym_check': {
                'title': 'Acronym Definition Issues',
                'description': 'Ensures every acronym is properly introduced with its full term at first use. The check identifies undefined acronyms while recognizing common exceptions (like U.S.) that don\'t require definition.',
                'solution': 'Define each acronym at its first use, e.g., "Federal Aviation Administration (FAA)".',
                'example_fix': {
                    'before': 'This order establishes general FAA organizational policies.',
                    'after': 'This order establishes general Federal Aviation Administration (FAA) organizational policies.'
                }
            },
            'acronym_usage_check': {
                'title': 'Unused Acronym Definitions',
                'description': 'Ensures that all acronyms defined in the document are actually used later. If an acronym is defined but never referenced, the definition should be removed to avoid confusion or unnecessary clutter.',
                'solution': 'Identify acronyms that are defined but not used later in the document and remove their definitions.',
                'example_fix': {
                    'before': 'Operators must comply with airworthiness directives (AD) to ensure aircraft safety and regulatory compliance.',
                    'after': 'Operators must comply with airworthiness directives to ensure aircraft safety and regulatory compliance.'
                }
            },
            'terminology_check': {
                'title': 'Incorrect Terminology',
                'description': 'Evaluates document text against the various style manuals and orders to identify non-compliant terminology, ambiguous references, and outdated phrases. This includes checking for prohibited relative references (like "above" or "below"), proper legal terminology (like "must" instead of "shall"), and consistent formatting of regulatory citations.',
                'solution': 'Use explicit references to paragraphs, sections, tables, and figures.',
                'example_fix': {
                    'before': 'Operators shall comply with ADs to ensure aircraft safety and regulatory compliance',
                    'after': 'Operators must comply with ADs to ensure aircraft safety and regulatory compliance.'
                }
            },
            'section_symbol_usage_check': {
                'title': 'Section Symbol (§) Format Issues',
                'description': 'Examines the usage of section symbols (§) throughout your document. This includes verifying proper symbol placement in regulatory references, ensuring sections aren\'t started with the symbol, checking consistency in multiple-section citations, and validating proper CFR citations. For ACs, see FAA Order 1320.46.',
                'solution': 'Format section symbols correctly and never start sentences with them.',
                'example_fix': {
                    'before': '§ 23.3 establishes design criteria.',
                    'after': 'Section 23.3 establishes design criteria.'
                }
            },
            'double_period_check': {
                'title': 'Multiple Period Issues',
                'description': 'Examines sentences for accidental double periods that often occur during document editing and revision. While double periods are sometimes found in ellipses (...) or web addresses, they should never appear at the end of standard sentences in FAA documentation.',
                'solution': 'Remove multiple periods that end sentences.',
                'example_fix': {
                    'before': 'The following ACs are related to the guidance in this document..',
                    'after': 'The following ACs are related to the guidance in this document.'
                }
            },
            'spacing_check': {
                'title': 'Spacing Issues',
                'description': 'Analyzes document spacing patterns to ensure compliance with FAA formatting standards. This includes checking for proper spacing around regulatory references (like "AC 25-1" not "AC25-1"), section symbols (§ 25.1), paragraph references, and multiple spaces between words.',
                'solution': 'Fix spacing issues: remove any missing spaces, double spaces, or inadvertent tabs.',
                'example_fix': {
                    'before': 'AC25.25 states that  SFAR88 and §25.981 require...',
                    'after': 'AC 25.25 states that SFAR 88 and § 25.981 require...'
                }
            },
            'date_formats_check': {
                'title': 'Date Format Issues',
                'description': 'Examines all date references in your document. The check automatically excludes technical reference numbers that may look like dates to ensure accurate validation of true date references. Note, though, there might be instances in the heading of the document where the date is formatted as "MM/DD/YYYY", which is acceptable. This applies mostly to date formats within the document body.',
                'solution': 'Use the format "Month Day, Year" where appropriate.',
                'example_fix': {
                    'before': 'This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated 7/25/2006.',
                    'after': 'This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated July 25, 2006.'
                }
            },
            'placeholders_check': {
                'title': 'Placeholder Content',
                'description': 'Identifies incomplete content and temporary placeholders that must be finalized before document publication. This includes common placeholder text (like "TBD" or "To be determined"), draft markers, and incomplete sections.',
                'solution': 'Replace all placeholder content with actual content.',
                'example_fix': {
                    'before': 'Pilots must submit the [Insert text] form to the FAA for approval.',
                    'after': 'Pilots must submit the Report of Eye Evaluation form 8500-7 to the FAA for approval.'
                }
            },
            'parentheses_check': {
                'title': 'Parentheses Balance Check',
                'description': 'Ensures that all parentheses in the document are properly paired with matching opening and closing characters.',
                'solution': 'Add missing opening or closing parentheses where indicated.',
                'example_fix': {
                    'before': 'The system (as defined in AC 25-11B performs...',
                    'after': 'The system (as defined in AC 25-11B) performs...'
                }
            },
            'paragraph_length_check': {
                'title': 'Paragraph Length Issues',
                'description': 'Flags paragraphs exceeding 6 sentences or 8 lines to enhance readability and clarity. While concise paragraphs are encouraged, with each focusing on a single idea or related points, exceeding these limits doesn\'t necessarily indicate a problem. Some content may appropriately extend beyond 8 lines, especially if it includes necessary details. Boilerplate language or template text exceeding these limits is not subject to modification or division.',
                'solution': 'Where possible, split long paragraphs into smaller sections, ensuring each focuses on one primary idea. If restructuring is not feasible or the content is boilerplate text, no changes are needed.',
                'example_fix': {
                    'before': 'A very long paragraph covering multiple topics and spanning many lines...',
                    'after': 'Multiple shorter paragraphs or restructured paragraphs, each focused on a single topic or related points.'
                }
            },
            'sentence_length_check': {
                'title': 'Sentence Length Issues',
                'description': 'Analyzes sentence length to ensure readability. While the ideal length varies with content complexity, sentences over 35 words often become difficult to follow. Technical content, regulatory references, notes, warnings, and list items are excluded from this check.',
                'solution': 'Break long sentences into smaller ones where possible, focusing on one main point per sentence. Consider using lists for complex items.',
                'example_fix': {
                    'before': 'The operator must ensure that all required maintenance procedures are performed in accordance with the manufacturer\'s specifications and that proper documentation is maintained throughout the entire process to demonstrate compliance with regulatory requirements.',
                    'after': 'The operator must ensure all required maintenance procedures are performed according to manufacturer specifications. Additionally, proper documentation must be maintained to demonstrate regulatory compliance.'
                }
            },
            'document_title_check': {
                'title': 'Referenced Document Title Format Issues',
                'description': 'Checks document title formatting based on document type. Advisory Circulars require italics without quotes, while all other document types require quotes without italics.',
                'solution': 'Format document titles according to document type: use italics for Advisory Circulars, quotes for all other document types.',
                'example_fix': {
                    'before': 'See AC 25.1309-1B, System Design and Analysis, for information on X.',
                    'after': 'See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X.'
                }
            },
            '508_compliance_check': {
                'title': 'Section 508 Compliance Issues',
                'description': 'Checks document accessibility features required by Section 508 standards: Image alt text for screen readers, heading structure issues (missing heading 1, skipped heading levels, and out of sequence headings), and hyperlink accessibility (ensuring links have meaningful descriptive text).',
                'solution': 'Address each accessibility issue: add image alt text for screen readers, fix heading structure, and ensure hyperlinks have descriptive text that indicates their destination.',
                'example_fix': {
                    'before': [
                        'Image without alt text',
                        'Heading sequence: H1 → H2 → H4 (skipped H3)',
                        'Link text: "click here" or "www.example.com"'
                    ],
                    'after': [
                        'Image with descriptive alt text',
                        'Proper heading sequence: H1 → H2 → H3 → H4',
                        'Descriptive link text: "FAA Compliance Guidelines" or "Download the Safety Report"'
                    ]
                }
            },
            'hyperlink_check': {
                'title': 'Hyperlink Issues',
                'description': 'Checks for potentially broken or inaccessible URLs in the document. This includes checking response codes and connection issues.',
                'solution': 'Verify each flagged URL is correct and accessible.',
                'example_fix': {
                    'before': 'See https://broken-link.example.com for more details.',
                    'after': 'See https://www.faa.gov for more details.'
                }
            },
            'cross_references_check': {
                'title': 'Cross-Reference Issues',
                'description': 'Checks for missing or invalid cross-references to paragraphs, tables, figures, and appendices within the document.',
                'solution': 'Ensure that all referenced elements are present in the document and update or remove any incorrect references.',
                'example_fix': {
                    'before': 'See table 5-2 for more information. (there is no table 5-2)',
                    'after': 'Either update the table reference or add table 5-2 if missing'
                }
            },
            'readability_check': {
                'title': 'Readability Issues',
                'description': 'Analyzes document readability using multiple metrics including Flesch Reading Ease, Flesch-Kincaid Grade Level, and Gunning Fog Index. Also checks for passive voice usage and technical jargon.',
                'solution': 'Simplify language, reduce passive voice, and replace technical jargon with plain language alternatives.',
                'example_fix': {
                    'before': 'The implementation of the procedure was facilitated by technical personnel.',
                    'after': 'Technical staff helped start the procedure.'
                }
            },
            'accessibility': {
                'title': 'Accessibility Issues',
                'description': 'Checks document accessibility including alt text, heading structure, and hyperlinks.',
                'solution': 'Add missing accessibility features and fix structural issues.',
                'example_fix': {
                    'before': 'Image without alt text, skipped heading levels',
                    'after': 'Added alt text, fixed heading hierarchy'
                }
            },
            'watermark_check': {
                'title': 'Document Watermark Issues',
                'description': 'Verifies that the document has the appropriate watermark for its current stage (internal review, public comment, AGC review, or final issuance).',
                'solution': 'Add or update the watermark to match the document\'s current stage.',
                'example_fix': {
                    'before': 'Missing watermark or incorrect watermark "draft"',
                    'after': 'Added correct watermark "draft for public comment"'
                }
            },
            'boilerplate_check': {
                'title': 'Required Boilerplate Text Issues',
                'description': 'Ensures that all required standard text sections are present based on document type (like required disclaimers in ACs and Policy Statements).',
                'solution': 'Add all required boilerplate text sections from the document template.',
                'example_fix': {
                    'before': 'Missing required disclaimer text for Advisory Circular',
                    'after': 'Added "This AC is not mandatory and does not constitute a regulation."'
                }
            },
            'required_language_check': {
                'title': 'Required Language Issues',
                'description': 'Verifies that document contains all required standardized language based on document type (like specific statements required in Federal Register notices).',
                'solution': 'Add all required standard statements for the document type.',
                'example_fix': {
                    'before': 'Missing Paperwork Reduction Act statement in Federal Register notice',
                    'after': 'Added complete Paperwork Reduction Act statement'
                }
            },
            'caption_format_check': {
                'title': 'Table/Figure Caption Format Issues',
                'description': 'Checks that table and figure captions follow proper numbering format based on document type (chapter-based for ACs/Orders, sequential for other documents).',
                'solution': 'Format captions according to document type requirements.',
                'example_fix': {
                    'before': 'Table 5.',
                    'after': 'Table 5-1.' # For ACs and Orders
                }
            }
        }

        # Add these two helper methods here, after __init__ and before other methods
    def _setup_style(self):
        """Configure formatting style."""
        style_configs = {
            FormatStyle.PLAIN: ("•", 4),
            FormatStyle.MARKDOWN: ("-", 2),
            FormatStyle.HTML: ("<li>", 0, "</li>")
        }
        self.bullet_style, self.indent, *self.suffix = style_configs.get(
            self._style,
            style_configs[FormatStyle.PLAIN]
        )
        self.suffix = self.suffix[0] if self.suffix else ""

    def _format_colored_text(self, text: str, color: str) -> str:
        """Helper method to format colored text with reset.

        Args:
            text: The text to be colored
            color: The color to apply (from colorama.Fore)

        Returns:
            str: The colored text with reset styling
        """
        if self._style == FormatStyle.HTML:
            # Map colorama colors to HTML colors
            color_map = {
                Fore.CYAN: '#00ffff',  # cyan
                Fore.YELLOW: '#ffff00',  # yellow
                Fore.RED: '#ff0000',    # red
                Fore.GREEN: '#00ff00',  # green
                Fore.BLUE: '#0000ff',   # blue
                Fore.MAGENTA: '#ff00ff', # magenta
                Fore.WHITE: '#ffffff',  # white
                Fore.BLACK: '#000000',  # black
            }
            html_color = color_map.get(color, '#000000')  # default to black if color not found
            return f'<span style="color: {html_color}">{text}</span>'
        else:
            return f"{color}{text}{Style.RESET_ALL}"

    def _format_example(self, example_fix: Dict[str, str]) -> List[str]:
        """Format example fixes consistently.

        Args:
            example_fix: Dictionary containing 'before' and 'after' examples

        Returns:
            List[str]: Formatted example lines
        """
        return [
            f"    ❌ Incorrect: {example_fix['before']}",
            f"    ✓ Correct: {example_fix['after']}"
        ]

    def _format_heading_issues(self, result: DocumentCheckResult, doc_type: str) -> List[str]:
        """Format heading check issues consistently."""
        output = []

        for issue in result.issues:
            if issue.get('type') == 'missing_headings':
                missing = sorted(issue['missing'])
                output.append(f"\n  Missing Required Headings for {doc_type}:")
                for heading in missing:
                    output.append(f"    • {heading}")
            elif issue.get('type') == 'unexpected_headings':
                unexpected = sorted(issue['unexpected'])
                output.append(f"\n  Unexpected Headings Found:")
                for heading in unexpected:
                    output.append(f"    • {heading}")

        return output

    def _format_period_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format period check issues consistently."""
        output = []

        if result.issues:
            output.append(f"\n  Heading Period Format Issues:")
            for issue in result.issues:
                if 'message' in issue:
                    output.append(f"    • {issue['message']}")

        return output

    def _format_caption_issues(self, issues: List[Dict], doc_type: str) -> List[str]:
        """Format caption check issues with clear replacement instructions."""
        formatted_issues = []
        for issue in issues:
            if 'incorrect_caption' in issue:
                caption_parts = issue['incorrect_caption'].split()
                if len(caption_parts) >= 2:
                    caption_type = caption_parts[0]  # "Table" or "Figure"
                    number = caption_parts[1]

                    # Determine correct format based on document type
                    if doc_type in ["Advisory Circular", "Order"]:
                        if '-' not in number:
                            correct_format = f"{caption_type} {number}-1"
                    else:
                        if '-' in number:
                            correct_format = f"{caption_type} {number.split('-')[0]}"
                        else:
                            correct_format = issue['incorrect_caption']

                    formatted_issues.append(
                        f"    • Replace '{issue['incorrect_caption']}' with '{correct_format}'"
                    )

        return formatted_issues

    def _format_reference_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format reference issues with clear, concise descriptions."""
        formatted_issues = []

        for issue in result.issues:
            ref_type = issue.get('type', '')
            ref_num = issue.get('reference', '')
            context = issue.get('context', '').strip()

            if context:  # Only include context if it exists
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} referenced in '{context}' exists in the document"
                )
            else:
                formatted_issues.append(
                    f"    • Confirm {ref_type} {ref_num} exists in the document"
                )

        return formatted_issues

    def _format_standard_issue(self, issue: Dict[str, Any]) -> str:
        """Format standard issues consistently."""
        if isinstance(issue, str):
            return f"    • {issue}"

        if 'incorrect' in issue and 'correct' in issue:
            return f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"

        if 'incorrect_term' in issue and 'correct_term' in issue:
            return f"    • Replace '{issue['incorrect_term']}' with '{issue['correct_term']}'"

        if 'sentence' in issue and 'word_count' in issue:  # For sentence length check
            return f"    • Review this sentence: \"{issue['sentence']}\""

        if 'sentence' in issue:
            return f"    • {issue['sentence']}"

        if 'description' in issue:
            return f"    • {issue['description']}"

        if 'type' in issue and issue['type'] == 'long_paragraph':
            return f"    • {issue['message']}"

        # Fallback for other issue formats
        return f"    • {str(issue)}"

    def _format_unused_acronym_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format unused acronym issues with a simple, clear message.

        Args:
            result: DocumentCheckResult containing acronym issues

        Returns:
            List[str]: Formatted list of unused acronym issues
        """
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                if isinstance(issue, dict) and 'acronym' in issue:
                    formatted_issues.append(f"    • Acronym '{issue['acronym']}' was defined but never used.")
                elif isinstance(issue, str):
                    # Handle case where issue might be just the acronym
                    formatted_issues.append(f"    • Acronym '{issue}' was defined but never used.")

        return formatted_issues

    def _format_parentheses_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format parentheses issues with clear instructions for fixing."""
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                formatted_issues.append(f"    • {issue['message']}")

        return formatted_issues

    def _format_section_symbol_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format section symbol issues with clear replacement instructions."""
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                if 'incorrect' in issue and 'correct' in issue:
                    if issue.get('is_sentence_start'):
                        formatted_issues.append(
                            f"    • Do not begin sentences with the section symbol. "
                            f"Replace '{issue['incorrect']}' with '{issue['correct']}' at the start of the sentence"
                        )
                    else:
                        formatted_issues.append(
                            f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"
                        )

        return formatted_issues

    def _format_paragraph_length_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format paragraph length issues with clear instructions for fixing.

        Args:
            result: DocumentCheckResult containing paragraph length issues

        Returns:
            List[str]: Formatted list of paragraph length issues
        """
        formatted_issues = []

        if result.issues:
            for issue in result.issues:
                if isinstance(issue, str):
                    formatted_issues.append(f"    • {issue}")
                elif isinstance(issue, dict) and 'message' in issue:
                    formatted_issues.append(f"    • {issue['message']}")
                else:
                    # Fallback for unexpected issue format
                    formatted_issues.append(f"    • Review paragraph for length issues: {str(issue)}")

        return formatted_issues

    def _format_accessibility_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format accessibility-specific issues."""
        formatted_issues = []

        for issue in result.issues:
            if issue.get('category') == '508_compliance_heading_structure':
                formatted_issues.append(f"    • {issue['message']}")
                if 'context' in issue:
                    formatted_issues.append(f"      Context: {issue['context']}")
                if 'recommendation' in issue:
                    formatted_issues.append(f"      Recommendation: {issue['recommendation']}")
            elif issue.get('category') == 'image_alt_text':
                formatted_issues.append(f"    • Missing alt text: {issue.get('context', '')}")
            elif issue.get('category') == 'hyperlink_accessibility':
                formatted_issues.append(
                    f"    • {issue.get('user_message', issue.get('message', 'No description provided'))}"
                )
            elif issue.get('category') == 'color_contrast':
                formatted_issues.append(f"    • {issue.get('message', '')}")

        return formatted_issues

    def _format_alt_text_issues(self, issue: Dict) -> str:
        """Format image alt text issues."""
        return f"    • {issue.get('message', 'Missing alt text')}: {issue.get('context', '')}"

    def _format_heading_structure_issues(self, issue: Dict) -> str:
        """Format heading structure issues."""
        msg = issue.get('message', '')
        ctx = issue.get('context', '')
        rec = issue.get('recommendation', '')
        return f"    • {msg}" + (f"\n      Context: {ctx}" if ctx else "") + (f"\n      Fix: {rec}" if rec else "")

    def format_results(self, results: Dict[str, Any], doc_type: str) -> str:
        """
        Format check results into a detailed, user-friendly report.

        Args:
            results: Dictionary of check results
            doc_type: Type of document being checked

        Returns:
            str: Formatted report with consistent styling
        """
        output = []

        # Header
        output.append('<div class="results-container">')
        output.append('<h1 style="color: #0056b3; text-align: center;">Document Check Results Summary</h1>')
        output.append('<hr style="border: 1px solid #0056b3;">')

        # Count total issues
        total_issues = 0
        has_issues = False

        # First pass to count issues and check if any exist
        for category_results in results.values():
            if isinstance(category_results, dict):
                for result in category_results.values():
                    if isinstance(result, DocumentCheckResult):
                        if result.issues:
                            has_issues = True
                            total_issues += len(result.issues)
                    elif isinstance(result, dict) and 'issues' in result:
                        if result['issues']:
                            has_issues = True
                            total_issues += len(result['issues'])

        if not has_issues:
            output.append('<p style="color: #006400; text-align: center;">✓ All checks passed successfully!</p>')
            output.append('</div>')
            return '\n'.join(output)

        output.append(f'<p style="color: #856404; text-align: center;">Found {total_issues} issues that need attention:</p>')

        rendered_any_issues = False
        # Process all check results by category
        for category, category_results in results.items():
            if isinstance(category_results, dict) and category_results:  # Only show categories that have results
                output.append('<div class="category-section" style="margin-bottom: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">')
                output.append(f'<h2 style="color: #0056b3; margin-bottom: 20px; border-bottom: 2px solid #0056b3; padding-bottom: 10px;">{category.replace("_", " ").title()}</h2>')

                # Process each checker in the category
                for check_name, result in category_results.items():
                    if isinstance(result, DocumentCheckResult):
                        if not result.success and result.issues:
                            rendered_any_issues = True
                            # Get category information
                            category_info = self.issue_categories.get(check_name, {})
                            category_title = category_info.get('title', check_name.replace('_', ' ').title())
                            category_description = category_info.get('description', '')
                            category_solution = category_info.get('solution', '')
                            category_example = category_info.get('example_fix', {})

                            output.append('<div class="check-section" style="margin-bottom: 30px; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
                            output.append(f'<h3 style="color: #0056b3; margin-bottom: 15px;">■ {category_title}</h3>')

                            # Add category description and solution
                            if category_description:
                                output.append('<div class="category-info" style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 4px; border-left: 4px solid #0056b3;">')
                                output.append(f'<p style="margin-bottom: 10px;"><strong>Description:</strong> {category_description}</p>')
                                if category_solution:
                                    output.append(f'<p style="margin-bottom: 10px;"><strong>Solution:</strong> {category_solution}</p>')
                                if category_example:
                                    output.append('<div class="example-fix" style="margin-top: 15px; padding: 10px; background-color: #ffffff; border-radius: 4px; border: 1px solid #dee2e6;">')
                                    output.append('<p style="margin-bottom: 10px;"><strong>Example:</strong></p>')
                                    if isinstance(category_example, dict):
                                        output.append(f'<p style="color: #721c24; margin-bottom: 5px;">❌ Incorrect: {category_example.get("before", "")}</p>')
                                        output.append(f'<p style="color: #006400;">✓ Correct: {category_example.get("after", "")}</p>')
                                    elif isinstance(category_example, list):
                                        for example in category_example:
                                            if isinstance(example, dict):
                                                output.append(f'<p style="color: #721c24; margin-bottom: 5px;">❌ Incorrect: {example.get("before", "")}</p>')
                                                output.append(f'<p style="color: #006400;">✓ Correct: {example.get("after", "")}</p>')
                                    output.append('</div>')
                                output.append('</div>')

                            # Group issues by severity within the check
                            errors = []
                            warnings = []
                            info = []

                            for issue in result.issues:
                                severity = issue.get('severity', '')
                                message = issue.get('message') or issue.get('error', '')
                                line = issue.get('line_number')
                                line_info = f" (Line {line})" if line is not None else ""

                                # Format the issue message with proper HTML and severity indicator
                                severity_indicator = ""
                                if severity == Severity.ERROR:
                                    severity_indicator = '<span style="color: #721c24; font-weight: bold;">[ERROR]</span> '
                                elif severity == Severity.WARNING:
                                    severity_indicator = '<span style="color: #856404; font-weight: bold;">[WARNING]</span> '
                                else:
                                    severity_indicator = '<span style="color: #0c5460; font-weight: bold;">[INFO]</span> '

                                formatted_issue = f"<li style='margin-bottom: 8px;'>{severity_indicator}{message}{line_info}</li>"

                                if severity == Severity.ERROR:
                                    errors.append(formatted_issue)
                                elif severity == Severity.WARNING:
                                    warnings.append(formatted_issue)
                                else:
                                    info.append(formatted_issue)

                            # Display all issues for this check, grouped by severity
                            if errors or warnings or info:
                                output.append('<div class="issues-section" style="margin-top: 15px;">')
                                output.append('<h4 style="color: #0056b3; margin-bottom: 10px;">Issues Found:</h4>')
                                output.append('<ul style="list-style-type: none; padding-left: 20px;">')

                                # Display errors first
                                if errors:
                                    output.extend(errors)

                                # Then warnings
                                if warnings:
                                    output.extend(warnings)

                                # Finally info items
                                if info:
                                    output.extend(info)

                                output.append('</ul>')
                                output.append('</div>')

                            output.append('</div>')
                    elif isinstance(result, dict) and 'issues' in result and result['issues']:
                        rendered_any_issues = True
                        # Render generic issues for dicts
                        output.append('<div class="check-section" style="margin-bottom: 30px; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
                        output.append(f'<h3 style="color: #0056b3; margin-bottom: 15px;">■ Issues</h3>')
                        output.append('<div class="issues-section" style="margin-top: 15px;">')
                        output.append('<h4 style="color: #0056b3; margin-bottom: 10px;">Issues Found:</h4>')
                        output.append('<ul style="list-style-type: none; padding-left: 20px;">')
                        for issue in result['issues']:
                            message = issue.get('message') or issue.get('error', str(issue))
                            output.append(f"<li style='margin-bottom: 8px;'><span style='color: #0c5460; font-weight: bold;'>[INFO]</span> {message}</li>")
                        output.append('</ul>')
                        output.append('</div>')
                        output.append('</div>')
                output.append('</div>')

        # Fallback: If no issues rendered, but results['all']['all']['issues'] exists, render them
        if not rendered_any_issues and 'all' in results and 'all' in results['all'] and results['all']['all'].get('issues'):
            output.append('<div class="category-section" style="margin-bottom: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">')
            output.append(f'<h2 style="color: #0056b3; margin-bottom: 20px; border-bottom: 2px solid #0056b3; padding-bottom: 10px;">All Issues</h2>')
            output.append('<div class="check-section" style="margin-bottom: 30px; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
            output.append(f'<h3 style="color: #0056b3; margin-bottom: 15px;">■ Issues</h3>')
            output.append('<div class="issues-section" style="margin-top: 15px;">')
            output.append('<h4 style="color: #0056b3; margin-bottom: 10px;">Issues Found:</h4>')
            output.append('<ul style="list-style-type: none; padding-left: 20px;">')
            for issue in results['all']['all']['issues']:
                message = issue.get('message') or issue.get('error', str(issue))
                output.append(f"<li style='margin-bottom: 8px;'><span style='color: #0c5460; font-weight: bold;'>[INFO]</span> {message}</li>")
            output.append('</ul>')
            output.append('</div>')
            output.append('</div>')
            output.append('</div>')
        output.append('</div>')
        return '\n'.join(output)

    def save_report(self, results: Dict[str, Any], filepath: str, doc_type: str) -> None:
        """Save the formatted results to a file with proper formatting."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Create a report without color codes
                report = self.format_results(results, doc_type)

                # Strip color codes
                for color in [Fore.CYAN, Fore.GREEN, Fore.YELLOW, Fore.RED, Style.RESET_ALL]:
                    report = report.replace(str(color), '')

                # Convert markdown-style italics to alternative formatting for plain text
                report = report.replace('*', '_')

                f.write(report)
        except Exception as e:
            print(f"Error saving report: {e}")

    def _format_readability_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format readability issues with clear, actionable feedback."""
        formatted_issues = []

        if result.details and 'metrics' in result.details:
            metrics = result.details['metrics']
            formatted_issues.append("\n  Readability Scores:")
            formatted_issues.append(f"    • Flesch Reading Ease: {metrics['flesch_reading_ease']} (Aim for 50+; higher is easier to read)")
            formatted_issues.append(f"    • Grade Level: {metrics['flesch_kincaid_grade']} (Aim for 10 or lower; 12 acceptable for technical/legal)")
            formatted_issues.append(f"    • Gunning Fog Index: {metrics['gunning_fog_index']} (Aim for 12 or lower)")
            formatted_issues.append(f"    • Passive Voice: {metrics['passive_voice_percentage']}% (Aim for less than 10%; use active voice for clarity)")

        if result.issues:
            formatted_issues.append("\n  Identified Issues:")
            for issue in result.issues:
                if issue['type'] == 'jargon':
                    formatted_issues.append(
                        f"    • Replace '{issue['word']}' with '{issue['suggestion']}' in: \"{issue['sentence']}\""
                    )
                elif issue['type'] in ['readability_score', 'passive_voice']:
                    formatted_issues.append(f"    • {issue['message']}")

        return formatted_issues

class ValidationFormatting:
    """Handles formatting of validation messages for consistency and clarity."""

    WATERMARK_VALIDATION = {
        'missing': 'Document is missing required watermark',
        'incorrect': 'Incorrect watermark for {stage} stage. Found: "{found}", Expected: "{expected}"',
        'success': 'Watermark validation passed: {watermark}'
    }

    def format_watermark_message(self, result_type: str, **kwargs) -> str:
        """Format watermark validation messages."""
        return self.WATERMARK_VALIDATION[result_type].format(**kwargs)

def format_results_to_html(results: DocumentCheckResult) -> str:
    """Format check results as HTML.

    Args:
        results: The check results to format

    Returns:
        str: HTML formatted results
    """
    # Use the existing to_html method for now
    return results.to_html()

def format_results_to_text(results: Dict[str, Any], doc_type: str) -> str:
    """Format results as plain text."""
    formatter = ResultFormatter(style=FormatStyle.HTML)
    return formatter.format_results(results, doc_type)

class DocumentFormatter:
    """Handles document formatting operations."""

    @staticmethod
    def format_heading(heading: str) -> str:
        """Format a heading according to standards."""
        return heading.strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        return text.strip().lower()

    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """Format error/warning messages."""
        return template.format(**kwargs)