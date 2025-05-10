import json
from typing import Dict, List, Set, Optional, Any
import re
from dataclasses import dataclass
from pathlib import Path
from ..models import DocumentCheckResult

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

    def check_text(self, content: str) -> DocumentCheckResult:
        """Check text for terminology issues.

        Args:
            content: The text to check

        Returns:
            DocumentCheckResult with any issues found
        """
        self.defined_acronyms.clear()
        self.used_acronyms.clear()
        issues = []

        # Check acronym definitions and usage
        definition_pattern = r'([A-Z][A-Z]+)\s*\(([^)]+)\)'
        for match in re.finditer(definition_pattern, content):
            acronym = match.group(1)
            definition = match.group(2)

            if acronym in self.defined_acronyms:
                issues.append({
                    "type": "acronym",
                    "message": f"Acronym '{acronym}' defined multiple times",
                    "suggestion": "Remove duplicate definition"
                })
            else:
                self.defined_acronyms.add(acronym)
                if acronym not in self.get_standard_acronyms():
                    self.add_custom_acronym(acronym, definition)

        # Check acronym usage
        usage_pattern = r'\b([A-Z][A-Z]+)\b'
        for match in re.finditer(usage_pattern, content):
            acronym = match.group(1)
            if len(acronym) >= 2:
                self.used_acronyms.add(acronym)
                if (acronym not in self.defined_acronyms and
                    acronym not in self.get_all_acronyms()):
                    issues.append({
                        "type": "acronym",
                        "message": f"Acronym '{acronym}' used without definition",
                        "suggestion": f"Define '{acronym}' before use"
                    })

        # Check patterns
        for category, patterns in self.get_patterns().items():
            for pattern in patterns:
                if pattern.get('is_error', False):
                    for match in re.finditer(pattern['pattern'], content):
                        issues.append({
                            "type": category,
                            "message": pattern['description'],
                            "suggestion": pattern.get('replacement', '')
                        })

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            checker_name="TerminologyManager"
        )

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