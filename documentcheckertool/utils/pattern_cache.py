import re
from typing import Pattern, Dict, List
import threading
import json
from pathlib import Path

class PatternCache:
    """Thread-safe cache for compiled regex patterns and pattern registry."""
    
    def __init__(self, patterns_file: str = "patterns.json"):
        self._cache = {}
        self._lock = threading.Lock()
        self._pattern_registry = {}
        self._load_patterns(patterns_file)
    
    def _load_patterns(self, patterns_file: str) -> None:
        """Load patterns from JSON file into the registry."""
        try:
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
                
            # Load required language patterns
            if 'required_language' in patterns_data:
                self._pattern_registry['required_language'] = patterns_data['required_language']
            
            # Load boilerplate patterns
            if 'boilerplate' in patterns_data:
                self._pattern_registry['boilerplate'] = patterns_data['boilerplate']
                
            # Pre-compile and cache all patterns
            for category in ['required_language', 'boilerplate']:
                if category in self._pattern_registry:
                    for doc_type, patterns in self._pattern_registry[category].items():
                        for pattern in patterns:
                            self.get_pattern(pattern)
                            
        except Exception as e:
            raise ValueError(f"Failed to load patterns from {patterns_file}: {str(e)}")
    
    def get_pattern(self, pattern_str: str) -> Pattern:
        """Get a compiled pattern from cache or compile and cache it."""
        with self._lock:
            if pattern_str not in self._cache:
                try:
                    self._cache[pattern_str] = re.compile(pattern_str)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern: {pattern_str}") from e
            return self._cache[pattern_str]
    
    def get_required_language_patterns(self, doc_type: str) -> List[Pattern]:
        """Get compiled patterns for required language by document type."""
        patterns = []
        if 'required_language' in self._pattern_registry:
            doc_patterns = self._pattern_registry['required_language'].get(doc_type, [])
            patterns = [self.get_pattern(p) for p in doc_patterns]
        return patterns
    
    def get_boilerplate_patterns(self, doc_type: str) -> List[Pattern]:
        """Get compiled patterns for boilerplate text by document type."""
        patterns = []
        if 'boilerplate' in self._pattern_registry:
            doc_patterns = self._pattern_registry['boilerplate'].get(doc_type, [])
            patterns = [self.get_pattern(p) for p in doc_patterns]
        return patterns
    
    def clear(self) -> None:
        """Clear the pattern cache."""
        with self._lock:
            self._cache.clear() 