import json
from typing import Dict, List, Set, Optional, Any
import re
from dataclasses import dataclass
from pathlib import Path
from ..models import DocumentCheckResult
import logging
from functools import lru_cache
from documentcheckertool.config.boilerplate_texts import BOILERPLATE_PARAGRAPHS

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

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TerminologyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the terminology manager with data from terminology.json."""
        if self._initialized:
            return

        self.terminology_file = Path(__file__).parent.parent / 'config' / 'terminology.json'
        self.terminology_data = self._load_terminology()
        self.defined_acronyms: Dict[str, str] = {}
        self.used_acronyms: Set[str] = set()
        self._validate_config()
        logger.info("Initialized TerminologyManager")
        self.definition_pattern = re.compile(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)')
        self.usage_pattern = re.compile(r'(?<!\()\b[A-Za-z]{2,}\b(?!\s*[:.]\s*)')
        ignore_patterns_raw = self.terminology_data.get('patterns', {}).get('ignore_patterns', [])
        self.ignored_patterns = [re.compile(pattern) for pattern in ignore_patterns_raw]
        self._initialized = True

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

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for acronym definitions and usage."""
        issues = []
        defined_acronyms = set()
        used_acronyms = set()
        defined_acronyms_info = {}  # Track definitions for each acronym
        all_known_acronyms = self.get_all_acronyms()
        valid_words = set(w.lower() for w in self._load_valid_words())
        unused_candidates = set()  # Track acronyms that should be checked for usage

        logger.debug("--- Acronym check start ---")
        logger.debug(f"Initial state - defined_acronyms: {defined_acronyms}")
        logger.debug(f"Initial state - used_acronyms: {used_acronyms}")
        logger.debug(f"Initial state - unused_candidates: {unused_candidates}")
        logger.debug(f"Text to check: {text}")

        # First, check if the entire text matches any ignored patterns
        for pattern in self.ignored_patterns:
            if pattern.search(text):
                logger.debug(f"Text matches ignored pattern: {pattern.pattern}")
                return DocumentCheckResult(success=True, issues=[])

        # Process definitions first
        for match in self.definition_pattern.finditer(text):
            definition = match.group(1).strip()
            acronym = match.group(2)
            full_text = match.group(0)
            logger.debug(f"Processing definition - acronym: {acronym}, length: {len(acronym)}")
            logger.debug(f"Full text of match: {full_text}")

            # Skip long acronyms immediately
            if len(acronym) >= 10:  # Changed from > to >= to ignore 10+ character acronyms
                logger.debug(f"Skipping long acronym definition: {acronym} (length: {len(acronym)})")
                continue

            # Check if the full context matches any ignored patterns
            for pattern in self.ignored_patterns:
                if pattern.search(full_text):
                    logger.debug(f"Skipping ignored pattern definition: {full_text} (matches pattern: {pattern.pattern})")
                    continue

            logger.debug(f"Found definition: '{definition}' ({acronym})")

            # Check if acronym is in standard or custom dictionary
            if acronym in all_known_acronyms:
                standard_def = all_known_acronyms[acronym]
                clean_def = definition.replace("The ", "")
                clean_std_def = standard_def.replace("The ", "")
                if clean_def.lower() != clean_std_def.lower():
                    logger.warning(f"Non-standard definition for {acronym}: {definition} vs {standard_def}")
                    issues.append({
                        "type": "acronym_definition",
                        "message": f"Acronym '{acronym}' defined with non-standard definition",
                        "line": text[:match.start()].count('\n') + 1,
                        "context": full_text
                    })
                defined_acronyms.add(acronym)
                defined_acronyms_info[acronym] = definition
                # Add to unused_candidates if it's explicitly defined in the text
                unused_candidates.add(acronym)
                logger.debug(f"Added '{acronym}' to defined_acronyms and unused_candidates (standard)")
            else:
                # Non-standard acronym
                defined_acronyms.add(acronym)
                defined_acronyms_info[acronym] = definition
                unused_candidates.add(acronym)
                logger.debug(f"Added '{acronym}' to defined_acronyms and unused_candidates (non-standard)")

        logger.debug(f"After definition processing - defined_acronyms: {defined_acronyms}")
        logger.debug(f"After definition processing - unused_candidates: {unused_candidates}")

        # Process usages
        for match in self.usage_pattern.finditer(text):
            acronym = match.group(0)
            full_text = match.group(0)
            logger.debug(f"Processing usage - acronym: {acronym}, length: {len(acronym)}")
            logger.debug(f"Full text of match: {full_text}")

            # Skip long acronyms immediately
            if len(acronym) >= 10:  # Changed from > to >= to ignore 10+ character acronyms
                logger.debug(f"Skipping long acronym usage: {acronym} (length: {len(acronym)})")
                continue

            # Check if the full context matches any ignored patterns
            for pattern in self.ignored_patterns:
                if pattern.search(text):
                    logger.debug(f"Skipping ignored pattern usage: {full_text} (matches pattern: {pattern.pattern})")
                    continue

            # Skip if it's a valid word (case-insensitive)
            if acronym.lower() in valid_words:
                logger.debug(f"Skipping valid word usage: {acronym}")
                continue

            # Check if the lowercase version matches a defined acronym
            defined_lower = {a.lower(): a for a in defined_acronyms}
            logger.debug(f"Checking case-insensitive match for {acronym} against defined acronyms: {defined_lower}")
            if acronym.lower() in defined_lower:
                original_case = defined_lower[acronym.lower()]
                logger.debug(f"Found case-insensitive match: {acronym} -> {original_case}")
                used_acronyms.add(original_case)
                logger.debug(f"Added {original_case} to used_acronyms")
                continue

            # Check if the lowercase version matches a known acronym
            known_lower = {a.lower(): a for a in all_known_acronyms}
            logger.debug(f"Checking case-insensitive match for {acronym} against known acronyms: {known_lower}")
            if acronym.lower() in known_lower:
                original_case = known_lower[acronym.lower()]
                logger.debug(f"Found case-insensitive match in known acronyms: {acronym} -> {original_case}")
                used_acronyms.add(original_case)
                logger.debug(f"Added {original_case} to used_acronyms")
                continue

            # Only consider all-uppercase usages as valid acronym usages if not already matched
            if not acronym.isupper():
                logger.debug(f"Skipping non-uppercase usage: {acronym}")
                continue

            # Check if acronym is defined or in all known acronyms
            if acronym not in defined_acronyms and acronym not in all_known_acronyms:
                logger.warning(f"Undefined acronym found: {acronym}")
                issues.append({
                    "type": "acronym_usage",
                    "message": f"Confirm '{acronym}' was defined at its first use",
                    "line": text[:match.start()].count('\n') + 1,
                    "context": match.group(0)
                })
            used_acronyms.add(acronym)
            logger.debug(f"Added '{acronym}' to used_acronyms")

        logger.debug(f"After usage processing - defined_acronyms: {defined_acronyms}")
        logger.debug(f"After usage processing - used_acronyms: {used_acronyms}")
        logger.debug(f"After usage processing - unused_candidates: {unused_candidates}")

        # Remove all used acronyms from unused_candidates
        unused_candidates -= used_acronyms
        logger.debug(f"After removing used acronyms - unused_candidates: {unused_candidates}")

        # Check for unused acronyms (both standard and non-standard that were explicitly defined)
        for acronym in unused_candidates:
            logger.debug(f"Checking unused acronym: {acronym}, length: {len(acronym)}")
            # Skip long acronyms in unused check
            if len(acronym) >= 10:  # Changed from > to >= to ignore 10+ character acronyms
                logger.debug(f"Skipping long acronym in unused check: {acronym} (length: {len(acronym)})")
                continue
            logger.warning(f"Found unused acronym: {acronym}")
            issues.append({
                "type": "acronym_usage",
                "message": f"Acronym '{acronym}' is defined but never used",
                "line": 1,  # We don't track line numbers for unused acronyms
                "context": f"{defined_acronyms_info[acronym]} ({acronym})"
            })

        logger.debug(f"Final state - issues: {issues}")
        logger.debug("--- Acronym check end ---")
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
        self.defined_acronyms = {}
        self.used_acronyms.clear()