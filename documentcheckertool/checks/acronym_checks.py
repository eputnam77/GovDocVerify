from typing import Dict, List, Optional
from ..utils.terminology_utils import TerminologyManager
from ..models import DocumentCheckResult

class AcronymChecker:
    """Checks for proper acronym usage and definitions."""

    def __init__(self):
        """Initialize the acronym checker with terminology manager."""
        self.terminology_manager = TerminologyManager()

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text for acronym issues.

        Args:
            content: The text to check

        Returns:
            DocumentCheckResult with any issues found
        """
        return self.terminology_manager.check_text(content)

    def get_acronym_definition(self, acronym: str) -> Optional[str]:
        """Get the definition of an acronym.

        Args:
            acronym: The acronym to look up

        Returns:
            The definition if found, None otherwise
        """
        return self.terminology_manager.get_acronym_definition(acronym)

    def is_standard_acronym(self, acronym: str) -> bool:
        """Check if an acronym is a standard one.

        Args:
            acronym: The acronym to check

        Returns:
            True if it's a standard acronym, False otherwise
        """
        return self.terminology_manager.is_standard_acronym(acronym)

    def add_custom_acronym(self, acronym: str, definition: str) -> None:
        """Add a custom acronym definition.

        Args:
            acronym: The acronym to add
            definition: The definition of the acronym
        """
        self.terminology_manager.add_custom_acronym(acronym, definition)
        self.terminology_manager.save_changes()