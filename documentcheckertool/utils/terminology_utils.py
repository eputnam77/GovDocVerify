import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..models import DocumentCheckResult

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

        self.terminology_file = Path(__file__).parent.parent / "config" / "terminology.json"
        self.terminology_data = self._load_terminology()
        self.defined_acronyms: Dict[str, str] = {}
        self.used_acronyms: Set[str] = set()
        # Precompute a set of common roman numerals (1-50) to avoid false
        # positives for section numbers like "Section II".
        self.roman_numerals = self._generate_roman_numerals(50)
        self._validate_config()
        logger.info("Initialized TerminologyManager")
        self.definition_pattern = re.compile(r"\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)")
        self.usage_pattern = re.compile(r"(?<!\()\b[A-Za-z]{2,}\b(?!\s*[:.]\s*)")
        ignore_patterns_raw = self.terminology_data.get("patterns", {}).get("ignore_patterns", [])
        self.ignored_patterns = [re.compile(pattern) for pattern in ignore_patterns_raw]
        self._initialized = True

    def _validate_config(self):
        """Validate terminology configuration."""
        required_sections = ["acronyms", "patterns", "heading_words"]
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
            with open(self.terminology_file, "r") as f:
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
        valid_words_file = Path(__file__).parent.parent.parent / "valid_words.txt"
        try:
            with open(valid_words_file, "r") as f:
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

    @staticmethod
    def _generate_roman_numerals(limit: int) -> Set[str]:
        """Generate a set of roman numerals up to a limit."""
        numerals = []
        mapping = [
            (50, "L"),
            (40, "XL"),
            (10, "X"),
            (9, "IX"),
            (5, "V"),
            (4, "IV"),
            (1, "I"),
        ]

        def to_roman(num: int) -> str:
            result = ""
            for val, sym in mapping:
                while num >= val:
                    result += sym
                    num -= val
            return result

        for i in range(1, limit + 1):
            numerals.append(to_roman(i))
        return set(numerals)

    @staticmethod
    def _add_issue(check_state: Dict, issue: Dict) -> None:
        """Add an issue if one with the same message hasn't been recorded."""
        key = (issue.get("type"), issue.get("message"))
        if key not in check_state["issue_keys"]:
            check_state["issues"].append(issue)
            check_state["issue_keys"].add(key)

    def check_text(self, text: str) -> DocumentCheckResult:
        """Check text for acronym definitions and usage."""
        logger.debug("--- Acronym check start ---")
        logger.debug(f"Text to check: {text}")

        # Don't ignore the entire text if it happens to contain an
        # ignored pattern.  Instead, handle the skip logic for each
        # potential acronym so valid issues elsewhere are still
        # reported.

        # Initialize tracking variables
        check_state = self._initialize_check_state()

        # Process definitions and usages
        self._process_definitions(text, check_state)
        self._process_usages(text, check_state)

        # Check for unused acronyms
        issues = self._check_unused_acronyms(check_state)

        logger.debug(f"Final state - issues: {issues}")
        logger.debug("--- Acronym check end ---")
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def _should_ignore_text(self, text: str) -> bool:
        """Check if text should be ignored based on patterns."""
        for pattern in self.ignored_patterns:
            if pattern.search(text):
                logger.debug(f"Text matches ignored pattern: {pattern.pattern}")
                return True
        return False

    def _initialize_check_state(self) -> Dict:
        """Initialize the state for acronym checking."""
        return {
            "issues": [],
            "issue_keys": set(),
            "defined_acronyms": set(),
            "used_acronyms": set(),
            "defined_acronyms_info": {},
            "all_known_acronyms": self.get_all_acronyms(),
            "valid_words": set(w.lower() for w in self._load_valid_words()),
            "unused_candidates": set(),
        }

    def _process_definitions(self, text: str, check_state: Dict) -> None:
        """Process acronym definitions in the text."""
        logger.debug("Processing definitions...")

        for match in self.definition_pattern.finditer(text):
            definition = match.group(1).strip()
            acronym = match.group(2)
            full_text = match.group(0)

            if self._should_skip_acronym(acronym, full_text, "definition"):
                continue

            logger.debug(f"Found definition: '{definition}' ({acronym})")
            self._handle_acronym_definition(
                acronym, definition, full_text, match, text, check_state
            )

        logger.debug(
            f"After definition processing - defined_acronyms: {check_state['defined_acronyms']}"
        )
        logger.debug(
            f"After definition processing - unused_candidates: {check_state['unused_candidates']}"
        )

    def _process_usages(self, text: str, check_state: Dict) -> None:
        """Process acronym usages in the text."""
        logger.debug("Processing usages...")

        for match in self.usage_pattern.finditer(text):
            acronym = match.group(0)
            # Provide some surrounding context so ignored patterns that span
            # beyond the acronym itself can be detected.
            context_window = text[max(0, match.start() - 20) : match.end() + 20]

            if self._should_skip_acronym(acronym, context_window, "usage"):
                # If we skip due to an ignore pattern but the acronym was
                # previously defined, consider it used so the definition is
                # not flagged as unused later.
                if acronym in check_state["defined_acronyms"]:
                    check_state["used_acronyms"].add(acronym)
                continue

            if self._handle_acronym_usage(acronym, match, text, check_state):
                continue

        logger.debug(
            f"After usage processing - defined_acronyms: {check_state['defined_acronyms']}"
        )
        logger.debug(f"After usage processing - used_acronyms: {check_state['used_acronyms']}")

    def _should_skip_acronym(self, acronym: str, full_text: str, context: str) -> bool:
        """Check if an acronym should be skipped."""
        logger.debug(f"Processing {context} - acronym: {acronym}, length: {len(acronym)}")
        logger.debug(f"Full text of match: {full_text}")

        # Skip long acronyms immediately
        if len(acronym) >= 10:
            logger.debug(f"Skipping long acronym {context}: {acronym} (length: {len(acronym)})")
            return True

        # Skip common roman numerals (e.g. "II", "III") to avoid false positives
        if acronym in self.roman_numerals:
            logger.debug(f"Skipping roman numeral {context}: {acronym}")
            return True

        # Skip "Washington, DC" style location references
        if acronym == "DC" and re.search(r"Washington", full_text):
            logger.debug("Skipping location reference for DC")
            return True

        # Skip references to USC without periods to avoid false positives
        if acronym == "USC":
            logger.debug("Skipping unpunctuated USC reference")
            return True

        # Check if the full context matches any ignored patterns
        for pattern in self.ignored_patterns:
            if pattern.search(full_text):
                logger.debug(
                    f"Skipping ignored pattern {context}: {full_text} "
                    f"(matches pattern: {pattern.pattern})"
                )
                return True

        return False

    def _handle_acronym_definition(
        self, acronym: str, definition: str, full_text: str, match, text: str, check_state: Dict
    ) -> None:
        """Handle processing of an acronym definition."""
        all_known_acronyms = check_state["all_known_acronyms"]

        if acronym in all_known_acronyms:
            self._validate_standard_definition(
                acronym, definition, full_text, match, text, check_state
            )

        # Add to tracking sets
        check_state["defined_acronyms"].add(acronym)
        check_state["defined_acronyms_info"][acronym] = definition
        check_state["unused_candidates"].add(acronym)

        status = "standard" if acronym in all_known_acronyms else "non-standard"
        logger.debug(f"Added '{acronym}' to defined_acronyms and unused_candidates ({status})")

    def _validate_standard_definition(
        self, acronym: str, definition: str, full_text: str, match, text: str, check_state: Dict
    ) -> None:
        """Validate a standard acronym definition."""
        standard_def = check_state["all_known_acronyms"][acronym]
        clean_def = definition.replace("The ", "")
        clean_std_def = standard_def.replace("The ", "")

        if clean_def.lower() != clean_std_def.lower():
            logger.warning(f"Non-standard definition for {acronym}: {definition} vs {standard_def}")
            self._add_issue(
                check_state,
                {
                    "type": "acronym_definition",
                    "message": f"Acronym '{acronym}' defined with non-standard definition",
                    "line": text[: match.start()].count("\n") + 1,
                    "context": full_text,
                    "category": "acronym",
                },
            )

    def _handle_acronym_usage(self, acronym: str, match, text: str, check_state: Dict) -> bool:
        """Handle processing of an acronym usage. Returns True if processing should continue."""
        # Skip if it's a valid word (case-insensitive)
        if acronym.lower() in check_state["valid_words"]:
            logger.debug(f"Skipping valid word usage: {acronym}")
            return True

        # Try case-insensitive matching with defined acronyms
        if self._try_match_defined_acronym(acronym, check_state):
            return True

        # Try case-insensitive matching with known acronyms
        if self._try_match_known_acronym(acronym, check_state):
            return True

        # Only consider all-uppercase usages as valid acronym usages if not already matched
        if not acronym.isupper():
            logger.debug(f"Skipping non-uppercase usage: {acronym}")
            return True

        # Check if acronym is defined or in all known acronyms
        self._validate_acronym_usage(acronym, match, text, check_state)
        check_state["used_acronyms"].add(acronym)
        logger.debug(f"Added '{acronym}' to used_acronyms")
        return False

    def _try_match_defined_acronym(self, acronym: str, check_state: Dict) -> bool:
        """Try to match acronym with defined acronyms (case-insensitive)."""
        defined_lower = {a.lower(): a for a in check_state["defined_acronyms"]}
        logger.debug(
            f"Case-insensitive match for {acronym} against defined acronyms: {defined_lower}"
        )

        if acronym.lower() in defined_lower:
            original_case = defined_lower[acronym.lower()]
            logger.debug(f"Found case-insensitive match: {acronym} -> {original_case}")
            check_state["used_acronyms"].add(original_case)
            logger.debug(f"Added {original_case} to used_acronyms")
            return True
        return False

    def _try_match_known_acronym(self, acronym: str, check_state: Dict) -> bool:
        """Try to match acronym with known acronyms (case-insensitive)."""
        known_lower = {a.lower(): a for a in check_state["all_known_acronyms"]}
        logger.debug(f"Case-insensitive match for {acronym} against known acronyms: {known_lower}")

        if acronym.lower() in known_lower:
            original_case = known_lower[acronym.lower()]
            logger.debug(
                f"Found case-insensitive match in known acronyms: {acronym} -> {original_case}"
            )
            check_state["used_acronyms"].add(original_case)
            logger.debug(f"Added {original_case} to used_acronyms")
            return True
        return False

    def _validate_acronym_usage(self, acronym: str, match, text: str, check_state: Dict) -> None:
        """Validate that an acronym usage is properly defined."""
        if (
            acronym not in check_state["defined_acronyms"]
            and acronym not in check_state["all_known_acronyms"]
        ):
            logger.warning(f"Undefined acronym found: {acronym}")
            self._add_issue(
                check_state,
                {
                    "type": "acronym_usage",
                    "message": f"Confirm '{acronym}' was defined at its first use",
                    "line": text[: match.start()].count("\n") + 1,
                    "context": match.group(0),
                    "category": "acronym",
                },
            )

    def _check_unused_acronyms(self, check_state: Dict) -> List:
        """Check for unused acronyms and return all issues."""
        # Remove all used acronyms from unused_candidates
        check_state["unused_candidates"] -= check_state["used_acronyms"]
        logger.debug(
            f"After removing used acronyms - unused_candidates: {check_state['unused_candidates']}"
        )

        # Check for unused acronyms (both standard and non-standard that were explicitly defined)
        for acronym in check_state["unused_candidates"]:
            logger.debug(f"Checking unused acronym: {acronym}, length: {len(acronym)}")
            # Skip long acronyms in unused check
            if len(acronym) >= 10:
                logger.debug(
                    f"Skipping long acronym in unused check: {acronym} (length: {len(acronym)})"
                )
                continue

            logger.warning(f"Found unused acronym: {acronym}")
            self._add_issue(
                check_state,
                {
                    "type": "acronym_usage",
                    "message": f"Acronym '{acronym}' is defined but never used",
                    "line": 1,
                    "context": f"{check_state['defined_acronyms_info'][acronym]} ({acronym})",
                    "category": "acronym",
                },
            )

        return check_state["issues"]

    def get_standard_acronyms(self) -> Dict[str, str]:
        """Get all standard acronym definitions.

        Returns:
            Dictionary of standard acronym definitions
        """
        return self.terminology_data["acronyms"]["standard"]

    def get_custom_acronyms(self) -> Dict[str, str]:
        """Get all custom acronym definitions.

        Returns:
            Dictionary of custom acronym definitions
        """
        return self.terminology_data["acronyms"]["custom"]

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

        self.terminology_data["acronyms"]["custom"][acronym] = definition

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
        patterns = self.terminology_data["patterns"]
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
        return self.terminology_data["required_language"].get(doc_type, [])

    def get_acronym_definition(self, acronym: str) -> Optional[str]:
        """Get the definition of an acronym.

        Args:
            acronym: The acronym to look up

        Returns:
            The definition if found, None otherwise
        """
        return (
            self.get_standard_acronyms().get(acronym)
            or self.get_custom_acronyms().get(acronym)
            or None
        )

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
            with open(self.terminology_file, "w") as f:
                json.dump(self.terminology_data, f, indent=4)
        except Exception as e:
            raise IOError(f"Failed to save terminology data: {str(e)}")

    def extract_acronyms(self, text: str) -> list:
        """Extract all acronyms from the given text."""
        # Acronyms are defined as two or more uppercase letters
        return re.findall(r"\b[A-Z]{2,}\b", text)

    def find_acronym_definition(self, text: str, acronym: str) -> Optional[str]:
        """Find the definition of an acronym in the given text."""
        logger = logging.getLogger(__name__)
        if not text:
            logger.debug(f"find_acronym_definition: empty text for acronym={acronym}")
            return None
        # Only match in this text instance, do not use cache or dictionary fallback
        pattern_before = rf"\b({acronym})\s*\(\s*([^)]+?)\s*\)"
        pattern_after = rf"\b([A-Za-z][A-Za-z ,&-]+?)\s*\(\s*{acronym}\s*\)"
        m = re.search(pattern_before, text)
        if m:
            return m.group(2).strip()
        m = re.search(pattern_after, text)
        if m:
            return m.group(1).strip()
        return None

    def load_config(self):
        """Reload the configuration from the config file."""
        # Reload the config file
        self.terminology_data = self._load_terminology()
        # Update the internal state with the new config
        self.defined_acronyms = {}
        self.used_acronyms.clear()
