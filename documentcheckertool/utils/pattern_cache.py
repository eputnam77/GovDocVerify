import json
import re
import threading
import warnings
from pathlib import Path
from typing import Any, Dict, List, cast


class PatternCache:
    """Thread-safe cache for compiled regex patterns and pattern registry."""

    def __init__(self, patterns_file: str | None = None) -> None:
        self._cache: Dict[str, re.Pattern[str]] = {}
        self._lock = threading.Lock()
        self._pattern_registry: Dict[str, Dict[str, List[str]]] = {}
        # Default to config/terminology.json
        if patterns_file is None:
            patterns_file = str(Path(__file__).parent.parent / "config" / "terminology.json")
        elif patterns_file.endswith("patterns.json"):
            warnings.warn("patterns.json is deprecated. Use config/terminology.json instead.")
        self._load_patterns(patterns_file)

    def _load_patterns(self, patterns_file: str) -> None:
        """Load patterns from JSON file into the registry."""
        try:
            with open(patterns_file, "r") as f:
                patterns_data: Dict[str, Any] = json.load(f)

            # Support both top-level and nested under 'patterns'
            for category in ["required_language", "boilerplate"]:
                if category in patterns_data:
                    self._pattern_registry[category] = cast(
                        Dict[str, List[str]], patterns_data[category]
                    )
                elif "patterns" in patterns_data and category in patterns_data["patterns"]:
                    self._pattern_registry[category] = cast(
                        Dict[str, List[str]], patterns_data["patterns"][category]
                    )
            # Pre-compile and cache all patterns
            for category in ["required_language", "boilerplate"]:
                if category in self._pattern_registry:
                    for doc_type, patterns in self._pattern_registry[category].items():
                        for pattern in patterns:
                            self.get_pattern(pattern)
        except Exception as e:
            raise ValueError(f"Failed to load patterns from {patterns_file}: {str(e)}")

    def get_pattern(self, pattern_str: str) -> re.Pattern[str]:
        """Get a compiled pattern from cache or compile and cache it."""
        with self._lock:
            if pattern_str not in self._cache:
                try:
                    self._cache[pattern_str] = re.compile(pattern_str)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern: {pattern_str}") from e
            return self._cache[pattern_str]

    def get_required_language_patterns(self, doc_type: str) -> List[re.Pattern[str]]:
        """Get compiled patterns for required language by document type."""
        patterns: List[re.Pattern[str]] = []
        if "required_language" in self._pattern_registry:
            doc_patterns = self._pattern_registry["required_language"].get(doc_type, [])
            patterns = [self.get_pattern(p) for p in doc_patterns]
        return patterns

    def get_boilerplate_patterns(self, doc_type: str) -> List[re.Pattern[str]]:
        """Get compiled patterns for boilerplate text by document type."""
        patterns: List[re.Pattern[str]] = []
        if "boilerplate" in self._pattern_registry:
            doc_patterns = self._pattern_registry["boilerplate"].get(doc_type, [])
            patterns = [self.get_pattern(p) for p in doc_patterns]
        return patterns

    def clear(self) -> None:
        """Clear the pattern cache."""
        with self._lock:
            self._cache.clear()
