import logging
from enum import Enum
from typing import Any, Dict, List, Union

from colorama import Fore, Style

from documentcheckertool.models import DocumentCheckResult, Severity

logger = logging.getLogger(__name__)


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

        # Issue categories have been moved to README.md for documentation purposes

    def _setup_style(self):
        """Configure formatting style."""
        style_configs = {
            FormatStyle.PLAIN: ("•", 4),
            FormatStyle.MARKDOWN: ("-", 2),
            FormatStyle.HTML: ("<li>", 0, "</li>"),
        }
        self.bullet_style, self.indent, *self.suffix = style_configs.get(
            self._style, style_configs[FormatStyle.PLAIN]
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
                Fore.CYAN: "#00ffff",  # cyan
                Fore.YELLOW: "#ffff00",  # yellow
                Fore.RED: "#ff0000",  # red
                Fore.GREEN: "#00ff00",  # green
                Fore.BLUE: "#0000ff",  # blue
                Fore.MAGENTA: "#ff00ff",  # magenta
                Fore.WHITE: "#ffffff",  # white
                Fore.BLACK: "#000000",  # black
            }
            html_color = color_map.get(color, "#000000")  # default to black if color not found
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
            f"    ✓ Correct: {example_fix['after']}",
        ]

    def _format_heading_issues(self, result: DocumentCheckResult, doc_type: str) -> List[str]:
        """Format heading check issues consistently."""
        output = []

        for issue in result.issues:
            if issue.get("type") == "missing_headings":
                missing = sorted(issue["missing"])
                output.append(f"\n  Missing Required Headings for {doc_type}:")
                for heading in missing:
                    output.append(f"    • {heading}")
            elif issue.get("type") == "unexpected_headings":
                unexpected = sorted(issue["unexpected"])
                output.append("\n  Unexpected Headings Found:")
                for heading in unexpected:
                    output.append(f"    • {heading}")

        return output

    def _format_period_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format period check issues consistently."""
        output = []

        if result.issues:
            output.append("\n  Heading Period Format Issues:")
            for issue in result.issues:
                if "message" in issue:
                    output.append(f"    • {issue['message']}")

        return output

    def _format_standard_issue(self, issue: Dict[str, Any]) -> str:
        """Format standard issues consistently."""
        if isinstance(issue, str):
            return f"    • {issue}"

        if "incorrect" in issue and "correct" in issue:
            return f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"

        if "incorrect_term" in issue and "correct_term" in issue:
            return f"    • Replace '{issue['incorrect_term']}' with '{issue['correct_term']}'"

        if "sentence" in issue and "word_count" in issue:  # For sentence length check
            return f"    • Review this sentence: \"{issue['sentence']}\""

        if "sentence" in issue:
            return f"    • {issue['sentence']}"

        if "description" in issue:
            return f"    • {issue['description']}"

        if "type" in issue and issue["type"] == "long_paragraph":
            return f"    • {issue['message']}"

        # Fallback for other issue formats
        return f"    • {str(issue)}"

    def _format_accessibility_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format accessibility-specific issues."""
        formatted_issues = []

        for issue in result.issues:
            if issue.get("category") == "508_compliance_heading_structure":
                formatted_issues.append(f"    • {issue['message']}")
                if "context" in issue:
                    formatted_issues.append(f"      Context: {issue['context']}")
                if "recommendation" in issue:
                    formatted_issues.append(f"      Recommendation: {issue['recommendation']}")
            elif issue.get("category") == "image_alt_text":
                formatted_issues.append(f"    • Missing alt text: {issue.get('context', '')}")
            elif issue.get("category") == "hyperlink_accessibility":
                message = issue.get("user_message", issue.get("message", "No description provided"))
                formatted_issues.append(f"    • {message}")
            elif issue.get("category") == "color_contrast":
                formatted_issues.append(f"    • {issue.get('message', '')}")

        return formatted_issues

    def _format_alt_text_issues(self, issue: Dict) -> str:
        """Format image alt text issues."""
        return f"    • {issue.get('message', 'Missing alt text')}: {issue.get('context', '')}"

    def _format_heading_structure_issues(self, issue: Dict) -> str:
        """Format heading structure issues."""
        msg = issue.get("message", "")
        ctx = issue.get("context", "")
        rec = issue.get("recommendation", "")
        return (
            f"    • {msg}"
            + (f"\n      Context: {ctx}" if ctx else "")
            + (f"\n      Fix: {rec}" if rec else "")
        )

    def _add_header(self, output: List[str], metadata: Dict[str, Any] | None) -> None:
        """Add header and optional metadata to the output."""
        if self._style == FormatStyle.HTML:
            output.append('<div class="results-container">')
            output.append(
                '<h1 style="color: #0056b3; text-align: center;">Document Check Summary</h1>'
            )
            if metadata:
                output.append('<div class="metadata">')
                for key, value in metadata.items():
                    label = key.replace("_", " ").title()
                    output.append(f"<p><strong>{label}:</strong> {value}</p>")
                output.append("</div>")
            output.append('<hr style="border: 1px solid #0056b3;">')
        else:
            output.append("=" * 80)
            output.append(self._format_colored_text("📋 DOCUMENT CHECK RESULTS SUMMARY", Fore.CYAN))
            if metadata:
                for key, value in metadata.items():
                    label = key.replace("_", " ").title()
                    output.append(f"{label}: {value}")
            output.append("=" * 80)
            output.append("")

    def _collect_severity_buckets(self, results: Dict[str, Any]) -> Dict[str, List]:
        """Collect and organize issues by severity."""
        severity_buckets = {"error": [], "warning": [], "info": []}
        for category_results in results.values():
            if isinstance(category_results, dict):
                for result in category_results.values():
                    issues = (
                        getattr(result, "issues", [])
                        if hasattr(result, "issues")
                        else result.get("issues", [])
                    )
                    for issue in issues:
                        sev_obj = issue.get("severity")
                        if isinstance(sev_obj, Severity):
                            sev = sev_obj.value_str.lower()
                        else:
                            sev = (sev_obj or "info").lower()
                        if sev in severity_buckets:
                            severity_buckets[sev].append(issue)
                        else:
                            severity_buckets["info"].append(issue)
        return severity_buckets

    def _format_no_issues_message(self, output: List[str]) -> str:
        """Format message when no issues are found."""
        if self._style == FormatStyle.HTML:
            output.append('<p style="color: #006400; text-align: center;">✓ All checks passed!</p>')
            output.append("</div>")
        else:
            output.append(self._format_colored_text("✓ All checks passed!", Fore.GREEN))
            output.append("")
        return "\n".join(output)

    def _format_severity_section(
        self,
        output: List[str],
        sev: str,
        issues: List,
        severity_titles: Dict,
        severity_colors_html: Dict,
        severity_colors_cli: Dict,
        severity_icons: Dict,
    ) -> None:
        """Format a section for a specific severity level."""
        if self._style == FormatStyle.HTML:
            div_style = (
                "margin-bottom: 40px; padding: 20px; "
                "background-color: #f8f9fa; border-radius: 8px;"
            )
            output.append(f'<div class="category-section" style="{div_style}">')
            h2_style = (
                f"color: {severity_colors_html[sev]}; margin-bottom: 20px; "
                f"border-bottom: 2px solid {severity_colors_html[sev]}; padding-bottom: 10px;"
            )
            output.append(f'<h2 style="{h2_style}">{severity_titles[sev]}</h2>')
            output.append('<ul style="list-style-type: none; padding-left: 20px;">')
            for issue in issues:
                message = issue.get("message") or issue.get("error", str(issue))
                span_style = f"color: {severity_colors_html[sev]}; font-weight: bold;"
                li_content = (
                    f"<li style='margin-bottom: 8px;'>"
                    f"<span style='{span_style}'>[{sev.upper()}]</span> "
                    f"{message}</li>"
                )
                output.append(li_content)
            output.append("</ul>")
            output.append("</div>")
        else:
            # CLI formatting
            output.append("-" * 60)
            output.append(
                self._format_colored_text(
                    f"{severity_icons[sev]} {severity_titles[sev].upper()}",
                    severity_colors_cli[sev],
                )
            )
            output.append("-" * 60)
            for issue in issues:
                message = issue.get("message") or issue.get("error", str(issue))
                output.append(f"  • {message}")
            output.append("")

    def _format_by_severity(self, results: Dict[str, Any], output: List[str]) -> str:
        """Format results grouped by severity."""
        severity_buckets = self._collect_severity_buckets(results)
        total_issues = sum(len(lst) for lst in severity_buckets.values())

        if total_issues == 0:
            return self._format_no_issues_message(output)

        if self._style == FormatStyle.HTML:
            html_style = "color: #856404; text-align: center;"
            output.append(f'<p style="{html_style}">Found {total_issues} issues:</p>')
        else:
            output.append(self._format_colored_text(f"Found {total_issues} issues:", Fore.YELLOW))
            output.append("")

        severity_titles = {"error": "Errors", "warning": "Warnings", "info": "Info"}
        severity_colors_html = {"error": "#721c24", "warning": "#856404", "info": "#0c5460"}
        severity_colors_cli = {"error": Fore.RED, "warning": Fore.YELLOW, "info": Fore.CYAN}
        severity_icons = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}

        for sev in ["error", "warning", "info"]:
            issues = severity_buckets[sev]
            if issues:
                self._format_severity_section(
                    output,
                    sev,
                    issues,
                    severity_titles,
                    severity_colors_html,
                    severity_colors_cli,
                    severity_icons,
                )

        if self._style == FormatStyle.HTML:
            output.append("</div>")
        return "\n".join(output)

    def _collect_categories_with_issues(self, results: Dict[str, Any]) -> tuple:
        """Collect categories that have issues."""
        total_issues = 0
        categories_with_issues = []

        for category, category_results in results.items():
            if not category_results:
                continue
            cat_issues = 0
            category_data = []
            for result in category_results.values():
                issues = (
                    getattr(result, "issues", [])
                    if hasattr(result, "issues")
                    else result.get("issues", [])
                )
                cat_issues += len(issues)
                if issues:
                    category_data.append((result, issues))

            if cat_issues > 0:
                total_issues += cat_issues
                categories_with_issues.append((category, category_data, cat_issues))

        return total_issues, categories_with_issues

    def _format_category_section(
        self, output: List[str], category: str, category_data: List, cat_issues: int
    ) -> None:
        """Format a section for a specific category."""
        category_title = category.replace("_", " ").title()

        if self._style == FormatStyle.HTML:
            div_style = (
                "margin-bottom: 40px; padding: 20px; "
                "background-color: #f8f9fa; border-radius: 8px;"
            )
            output.append(f'<div class="category-section" style="{div_style}">')
            h2_style = (
                "color: #0056b3; margin-bottom: 20px; "
                "border-bottom: 2px solid #0056b3; padding-bottom: 10px;"
            )
            output.append(f'<h2 style="{h2_style}">{category_title}</h2>')
            output.append('<ul style="list-style-type: none; padding-left: 20px;">')

            for result, issues in category_data:
                for issue in issues:
                    message = issue.get("message") or issue.get("error", str(issue))
                    check_name = getattr(result, "check_name", "General")
                    span_style = "color: #721c24; font-weight: bold;"
                    check_display = check_name.replace("_", " ").title()
                    li_content = (
                        f"<li style='margin-bottom: 8px;'>"
                        f"<span style='{span_style}'>[{check_display}]</span> "
                        f"{message}</li>"
                    )
                    output.append(li_content)
            output.append("</ul>")
            output.append("</div>")
        else:
            # CLI formatting
            output.append("=" * 80)
            output.append(
                self._format_colored_text(
                    f"📂 {category_title.upper()} ({cat_issues} issues)", Fore.CYAN
                )
            )
            output.append("=" * 80)

            for result, issues in category_data:
                for issue in issues:
                    message = issue.get("message") or issue.get("error", str(issue))
                    check_name = getattr(result, "check_name", "General")
                    check_label = self._format_colored_text(
                        f"[{check_name.replace('_', ' ').title()}]", Fore.RED
                    )
                    output.append(f"  • {check_label} {message}")
            output.append("")

    def _format_by_category(self, results: Dict[str, Any], output: List[str]) -> str:
        """Format results grouped by category."""
        total_issues, categories_with_issues = self._collect_categories_with_issues(results)

        if total_issues == 0:
            if self._style == FormatStyle.HTML:
                output.append(
                    '<p style="color: #006400; text-align: center;">✓ All checks passed!</p>'
                )
                output.append("</div>")
            else:
                output.append(
                    self._format_colored_text("✓ All checks passed successfully!", Fore.GREEN)
                )
                output.append("=" * 80)
            return "\n".join(output)

        # Show summary
        if self._style == FormatStyle.HTML:
            html_style = "color: #856404; text-align: center;"
            output.append(f'<p style="{html_style}">Found {total_issues} issues.</p>')
        else:
            message = (
                f"Found {total_issues} issues across " f"{len(categories_with_issues)} categories:"
            )
            output.append(self._format_colored_text(message, Fore.YELLOW))
            output.append("")

        # Display each category
        for category, category_data, cat_issues in categories_with_issues:
            self._format_category_section(output, category, category_data, cat_issues)

        if self._style == FormatStyle.HTML:
            output.append("</div>")
        else:
            output.append("=" * 80)

        return "\n".join(output)

    def format_results(
        self,
        results: Dict[str, Any],
        doc_type: str,
        *,
        group_by: str = "category",
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """
        Format check results into a detailed, user-friendly report.

        Args:
            results: Dictionary of check results
            doc_type: Type of document being checked
            group_by: 'category' (default) or 'severity' for grouping output

        Returns:
            str: Formatted report with consistent styling
        """
        output: List[str] = []
        self._add_header(output, metadata)

        if group_by == "severity":
            return self._format_by_severity(results, output)
        elif group_by == "category":
            return self._format_by_category(results, output)
        else:
            # Fallback for unknown grouping
            import logging

            logging.error(
                f"ResultFormatter.format_results: No implementation for group_by='{group_by}'."
            )
            if self._style == FormatStyle.HTML:
                error_msg = "[Internal error: No category grouping implemented]"
                output.append(f'<p style="color: #721c24;">{error_msg}</p>')
                output.append("</div>")
            else:
                output.append(
                    self._format_colored_text(
                        f"[Internal error: No implementation for group_by='{group_by}']", Fore.RED
                    )
                )
                output.append("=" * 80)
            return "\n".join(output)

    def save_report(self, results: Dict[str, Any], filepath: str, doc_type: str) -> None:
        """Save the formatted results to a file with proper formatting."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Create a report without color codes
                report = self.format_results(results, doc_type)

                # Strip color codes
                for color in [Fore.CYAN, Fore.GREEN, Fore.YELLOW, Fore.RED, Style.RESET_ALL]:
                    report = report.replace(str(color), "")

                # Convert markdown-style italics to alternative formatting for plain text
                report = report.replace("*", "_")

                f.write(report)
        except Exception as e:
            logger.exception("Error saving report: %s", e)

    def _format_readability_issues(self, result: DocumentCheckResult | Dict[str, Any]) -> List[str]:
        """Format readability issues with clear, actionable feedback."""
        formatted_issues: List[str] = []

        details = getattr(result, "details", None)
        if isinstance(result, dict):
            details = result.get("details")
            issues = result.get("issues", [])
        else:
            issues = result.issues

        if details and "metrics" in details:
            metrics = details["metrics"]
            formatted_issues.append(
                f"Flesch Reading Ease: {metrics['flesch_reading_ease']} "
                "(Aim for 50+; higher is easier to read)"
            )
            formatted_issues.append(
                f"Gunning Fog Index: {metrics['gunning_fog_index']} " "(Aim for 12 or lower)"
            )
            formatted_issues.append(
                f"Grade Level: {metrics['flesch_kincaid_grade']} "
                "(Aim for 10 or lower; 12 acceptable for technical/legal)"
            )
            if "passive_voice_percentage" in metrics:
                formatted_issues.append(
                    f"Passive Voice: {metrics['passive_voice_percentage']}% "
                    "(Aim for 10% or lower)"
                )
            formatted_issues.append("")

        if issues:
            formatted_issues.append("Issues:")
            for issue in issues:
                issue_type = issue.get("type")
                if issue_type == "jargon":
                    formatted_issues.append(
                        f"Replace '{issue['word']}' with '{issue['suggestion']}' "
                        f"in: \"{issue['sentence']}\""
                    )
                elif issue_type in ["readability_score", "passive_voice"]:
                    formatted_issues.append(issue["message"])
                elif "message" in issue:
                    formatted_issues.append(issue["message"])

        return formatted_issues


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
