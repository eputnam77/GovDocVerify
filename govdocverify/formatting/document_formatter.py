import re

from ..models import DocumentCheckResult


class DocumentFormatter:
    """Formats document text according to style guidelines."""

    def __init__(self) -> None:
        """Initialize the document formatter."""
        self.quotation_pattern = re.compile(r'["\'](.*?)["\']')
        self.section_pattern = re.compile(r"§\s*(\d+)")
        self.list_pattern = re.compile(r"^\s*(\d+\.|\*|\-)\s+")

    def format_text(self, text: str) -> str:
        """Format the given text according to style guidelines.

        Args:
            text: The text to format

        Returns:
            The formatted text
        """
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            # Format quotation marks
            line = self._format_quotation_marks(line)

            # Format section symbols
            line = self._format_section_symbols(line)

            # Format lists
            line = self._format_lists(line)

            # Remove extra spaces
            line = re.sub(r"\s+", " ", line).strip()

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_quotation_marks(self, text: str) -> str:
        """Format quotation marks consistently.

        Args:
            text: The text to format

        Returns:
            Text with consistent quotation marks
        """
        # Replace all quotes with double quotes
        text = self.quotation_pattern.sub(r'"\1"', text)
        return text

    def _format_section_symbols(self, text: str) -> str:
        """Format section symbols consistently.

        Args:
            text: The text to format

        Returns:
            Text with consistent section symbols
        """
        # Ensure space after section symbol
        text = self.section_pattern.sub(r"§ \1", text)
        return text

    def _format_lists(self, text: str) -> str:
        """Format lists consistently.

        Args:
            text: The text to format

        Returns:
            Text with consistent list formatting
        """
        # Convert all list markers to numbers
        if self.list_pattern.match(text):
            # Extract the content after the marker
            content = self.list_pattern.sub("", text)
            # Add proper indentation
            text = f"    {content}"
        return text

    def check_formatting(self, text: str) -> DocumentCheckResult:
        """Check text for formatting issues.

        Args:
            text: The text to check

        Returns:
            DocumentCheckResult with formatting issues
        """
        issues = []

        # Check for inconsistent quotation marks
        if "'" in text and '"' in text:
            issues.append(
                {
                    "type": "formatting",
                    "message": "Mixed quotation marks found",
                    "suggestion": "Use consistent quotation marks",
                }
            )

        # Check for section symbol formatting
        if "§" in text and "§ " not in text:
            issues.append(
                {
                    "type": "formatting",
                    "message": "Incorrect section symbol spacing",
                    "suggestion": "Add space after section symbol",
                }
            )

        # Check for list formatting
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if self.list_pattern.match(line) and not line.startswith("    "):
                issues.append(
                    {
                        "type": "formatting",
                        "message": f"Incorrect list indentation on line {i+1}",
                        "suggestion": "Indent list items with 4 spaces",
                    }
                )

        return DocumentCheckResult(
            success=len(issues) == 0, issues=issues, checker_name="DocumentFormatter"
        )
