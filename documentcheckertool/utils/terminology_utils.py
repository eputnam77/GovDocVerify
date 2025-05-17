import json
from typing import Dict, List, Set, Optional, Any
import re
from dataclasses import dataclass
from pathlib import Path
from ..models import DocumentCheckResult
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class AcronymDefinition:
    """Represents an acronym definition."""
    acronym: str
    definition: str
    is_standard: bool = False
    context: Optional[str] = None

class TerminologyManager:
    """Manages terminology, acronyms, and their definitions from a single source of truth."""

    def __init__(self):
        """Initialize the terminology manager with data from terminology.json."""
        self.terminology_file = Path(__file__).parent.parent / 'config' / 'terminology.json'
        self.terminology_data = self._load_terminology()
        self.defined_acronyms: Set[str] = set()
        self.used_acronyms: Set[str] = set()
        self._validate_config()
        logger.info("Initialized TerminologyManager")

    def _validate_config(self):
        """Validate terminology configuration."""
        required_sections = ['acronyms', 'patterns', 'heading_words']
        for section in required_sections:
            if section not in self.terminology_data:
                raise ValueError(f"Missing required section '{section}' in terminology.json")
        logger.debug("Configuration validation passed")

    def _load_terminology(self) -> Dict[str, Any]:
        """Load terminology data from JSON file.

        Returns:
            Dictionary containing all terminology data
        """
        try:
            with open(self.terminology_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Terminology file not found at {self.terminology_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in terminology file at {self.terminology_file}")

    @lru_cache(maxsize=1000)
    def _is_valid_word(self, word: str) -> bool:
        """Cached check for valid words."""
        return word in self._load_valid_words()

    def _load_valid_words(self) -> set:
        """Load valid words from a file (one word per line, both cases)."""
        valid_words_file = Path(__file__).parent.parent.parent / 'valid_words.txt'
        try:
            with open(valid_words_file, 'r') as f:
                words = set()
                for word in f:
                    word = word.strip()
                    if word:
                        words.add(word.upper())  # Add uppercase version
                        words.add(word.lower())  # Add lowercase version
                return words
        except FileNotFoundError:
            logger.warning(f"Valid words file not found at {valid_words_file}")
            return set()

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text for terminology issues.

        Args:
            content: The text to check

        Returns:
            DocumentCheckResult with any issues found
        """
        logger.debug("Starting acronym check")
        self.defined_acronyms.clear()
        self.used_acronyms.clear()
        issues = []

        # Load all necessary data
        valid_words = self._load_valid_words()
        heading_words = self.terminology_data.get('heading_words', [])
        standard_acronyms = set(self.get_standard_acronyms().keys())
        custom_acronyms = set(self.get_custom_acronyms().keys())
        all_known_acronyms = standard_acronyms | custom_acronyms

        # Get ignore patterns from config
        ignore_patterns = self.terminology_data.get('patterns', {}).get('ignore_patterns', [])
        ignore_regex = '|'.join(f'(?:{pattern})' for pattern in ignore_patterns)
        ignore_pattern = re.compile(ignore_regex)

        # Split into paragraphs
        paragraphs = content.split('\n')
        logger.debug(f"Processing {len(paragraphs)} paragraphs")

        for paragraph in paragraphs:
            # Skip heading lines
            words = paragraph.strip().split()
            if all(word.isupper() for word in words) and any(word in heading_words for word in words):
                logger.debug(f"Skipping heading line: {paragraph}")
                continue

            # Find ignored spans
            ignored_spans = []
            for match in ignore_pattern.finditer(paragraph):
                ignored_spans.append(match.span())

            # Check for definitions first
            defined_matches = re.finditer(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)', paragraph)
            for match in defined_matches:
                full_term, acronym = match.groups()
                # Skip if in ignored span
                if not any(start <= match.start(2) <= end for start, end in ignored_spans):
                    if acronym in standard_acronyms:
                        # Check if the definition matches the standard one
                        standard_def = self.get_standard_acronyms()[acronym]
                        full_term_stripped = full_term.strip()
                        # Remove "The" from the beginning if present
                        if full_term_stripped.lower().startswith('the '):
                            full_term_stripped = full_term_stripped[4:].strip()
                        if full_term_stripped != standard_def:
                            issues.append({
                                "type": "acronym",
                                "message": f"Acronym '{acronym}' defined with non-standard definition",
                                "suggestion": f"Use standard definition: {standard_def}"
                            })
                            logger.warning(f"Non-standard definition for {acronym}: {full_term_stripped} vs {standard_def}")
                    elif acronym not in self.defined_acronyms:
                        self.defined_acronyms.add(acronym)
                        self.add_custom_acronym(acronym, full_term.strip())
                        logger.debug(f"Added new acronym definition: {acronym} -> {full_term.strip()}")
                    else:
                        issues.append({
                            "type": "acronym",
                            "message": f"Acronym '{acronym}' defined multiple times",
                            "suggestion": "Remove duplicate definition"
                        })
                        logger.warning(f"Duplicate acronym definition found: {acronym}")

            # Check for usage
            usage_matches = re.finditer(r'(?<!\()\b[A-Z]{2,}\b(?!\s*[:.]\s*)', paragraph)
            for match in usage_matches:
                acronym = match.group()
                start_pos = match.start()

                # Skip if in ignored span
                if any(start <= start_pos <= end for start, end in ignored_spans):
                    logger.debug(f"Skipping ignored acronym: {acronym}")
                    continue

                # Skip if it's a valid word, predefined acronym, or fails length/character checks
                if (self._is_valid_word(acronym) or
                    acronym in all_known_acronyms or
                    any(not c.isalpha() for c in acronym) or
                    len(acronym) > 10):
                    logger.debug(f"Skipping valid/predefined acronym: {acronym}")
                    continue

                if acronym not in self.defined_acronyms:
                    issues.append({
                        "type": "acronym",
                        "message": f"Confirm '{acronym}' was defined at its first use.",
                        "suggestion": f"Define '{acronym}' before use"
                    })
                    logger.warning(f"Undefined acronym found: {acronym}")
                else:
                    self.used_acronyms.add(acronym)
                    logger.debug(f"Found valid acronym usage: {acronym}")

        logger.debug(f"Found {len(self.defined_acronyms)} defined acronyms")
        logger.debug(f"Found {len(self.used_acronyms)} used acronyms")
        logger.debug(f"Found {len(issues)} issues")

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues
        )

    def get_standard_acronyms(self) -> Dict[str, str]:
        """Get all standard acronym definitions.

        Returns:
            Dictionary of standard acronym definitions
        """
        return self.terminology_data['acronyms']['standard']

    def get_custom_acronyms(self) -> Dict[str, str]:
        """Get all custom acronym definitions.

        Returns:
            Dictionary of custom acronym definitions
        """
        return self.terminology_data['acronyms']['custom']

    def add_custom_acronym(self, acronym: str, definition: str) -> None:
        """Add a custom acronym definition.

        Args:
            acronym: The acronym to add
            definition: The definition of the acronym

        Raises:
            ValueError: If the acronym is not uppercase or if it's a standard acronym
        """
        if not isinstance(acronym, str) or not isinstance(definition, str):
            raise ValueError("Acronym and definition must be strings")
        if not acronym.isupper():
            raise ValueError("Acronym must be uppercase")
        if acronym in self.get_standard_acronyms():
            raise ValueError(f"'{acronym}' is a standard acronym and cannot be redefined")

        self.terminology_data['acronyms']['custom'][acronym] = definition

    def get_all_acronyms(self) -> Dict[str, str]:
        """Get all acronym definitions.

        Returns:
            Dictionary of all acronym definitions
        """
        return {**self.get_standard_acronyms(), **self.get_custom_acronyms()}

    def get_patterns(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get patterns for text checking.

        Args:
            category: Optional category of patterns to retrieve

        Returns:
            Dictionary of patterns, optionally filtered by category
        """
        patterns = self.terminology_data['patterns']
        if category:
            return {category: patterns.get(category, [])}
        return patterns

    def get_required_language(self, doc_type: str) -> List[str]:
        """Get required language for a specific document type.

        Args:
            doc_type: The type of document

        Returns:
            List of required language patterns
        """
        return self.terminology_data['required_language'].get(doc_type, [])

    def get_acronym_definition(self, acronym: str) -> Optional[str]:
        """Get the definition of an acronym.

        Args:
            acronym: The acronym to look up

        Returns:
            The definition if found, None otherwise
        """
        return (self.get_standard_acronyms().get(acronym) or
                self.get_custom_acronyms().get(acronym) or
                None)

    def is_standard_acronym(self, acronym: str) -> bool:
        """Check if an acronym is a standard one.

        Args:
            acronym: The acronym to check

        Returns:
            True if it's a standard acronym, False otherwise
        """
        return acronym in self.get_standard_acronyms()

    def save_changes(self) -> None:
        """Save any changes made to the terminology data back to the JSON file."""
        try:
            with open(self.terminology_file, 'w') as f:
                json.dump(self.terminology_data, f, indent=4)
        except Exception as e:
            raise IOError(f"Failed to save terminology data: {str(e)}")

    def extract_acronyms(self, text: str) -> list:
        """Extract all acronyms from the given text."""
        # Acronyms are defined as two or more uppercase letters
        return re.findall(r'\b[A-Z]{2,}\b', text)

    def find_acronym_definition(self, text: str, acronym: str) -> str:
        """Find the definition of an acronym in the given text."""
        # Look for patterns like 'Full Term (ACRONYM)'
        pattern = re.compile(rf'([A-Za-z\s]+)\s*\(\s*{re.escape(acronym)}\s*\)')
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return self.get_acronym_definition(acronym)

    def load_config(self):
        """Reload the configuration from the config file."""
        # Reload the config file
        self.terminology_data = self._load_terminology()
        # Update the internal state with the new config
        self.defined_acronyms.clear()
        self.used_acronyms.clear()