import logging
from typing import Dict, List, Optional
from docx import Document
from ..utils.terminology_utils import TerminologyManager
from ..models import DocumentCheckResult
from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.checks.base_checker import BaseChecker

logger = logging.getLogger(__name__)

class AcronymChecker(BaseChecker):
    """Class for checking acronym usage and definitions."""

    def __init__(self, terminology_manager: Optional[TerminologyManager] = None):
        """Initialize the acronym checker with terminology manager.

        Args:
            terminology_manager: Optional TerminologyManager instance. If not provided,
                               a new instance will be created.
        """
        super().__init__(terminology_manager)
        self.category = "acronym"
        self.terminology_manager = terminology_manager or TerminologyManager()
        logger.info("Initialized AcronymChecker")

    @CheckRegistry.register('acronym')
    def check_document(self, document, doc_type) -> DocumentCheckResult:
        # Accept Document, list, or str
        if hasattr(document, 'paragraphs'):
            text = '\n'.join([p.text for p in document.paragraphs])
        elif isinstance(document, list):
            text = '\n'.join(document)
        else:
            text = str(document)
        return self.check_text(text)

    @CheckRegistry.register('acronym')
    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text for acronym issues.

        Args:
            content: The text to check

        Returns:
            DocumentCheckResult with any issues found
        """
        logger.debug("Starting acronym text check")
        try:
            result = self.terminology_manager.check_text(content)
            logger.debug(f"Check completed with {len(result.issues)} issues found")
            return result
        except Exception as e:
            logger.error(f"Error during acronym check: {str(e)}", exc_info=True)
            return DocumentCheckResult(
                success=False,
                issues=[{'error': f"Error during acronym check: {str(e)}"}]
            )

    def get_acronym_definition(self, acronym: str) -> Optional[str]:
        """Get the definition of an acronym.

        Args:
            acronym: The acronym to look up

        Returns:
            The definition if found, None otherwise
        """
        logger.debug(f"Looking up definition for acronym: {acronym}")
        definition = self.terminology_manager.get_acronym_definition(acronym)
        if definition:
            logger.debug(f"Found definition: {definition}")
        else:
            logger.debug("No definition found")
        return definition

    def is_standard_acronym(self, acronym: str) -> bool:
        """Check if an acronym is a standard one.

        Args:
            acronym: The acronym to check

        Returns:
            True if it's a standard acronym, False otherwise
        """
        logger.debug(f"Checking if {acronym} is a standard acronym")
        is_standard = self.terminology_manager.is_standard_acronym(acronym)
        logger.debug(f"Result: {is_standard}")
        return is_standard

    def add_custom_acronym(self, acronym: str, definition: str) -> None:
        """Add a custom acronym definition.

        Args:
            acronym: The acronym to add
            definition: The definition of the acronym
        """
        logger.debug(f"Adding custom acronym: {acronym} = {definition}")
        self.terminology_manager.add_custom_acronym(acronym, definition)
        self.terminology_manager.save_changes()
        logger.debug("Custom acronym added and changes saved")

    def reload_config(self):
        """Reload the acronym lists from the config file or update the internal state based on in-memory changes."""
        logger.debug("Reloading acronym configuration")
        self.terminology_manager.load_config()
        logger.debug("Configuration reloaded successfully")