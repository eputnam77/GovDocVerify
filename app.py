# Standard library imports
import io
import os
import re
import json
import time
import textwrap
import logging
import traceback
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Any, Tuple, Optional, Pattern, Callable, Set
from dataclasses import dataclass
from functools import wraps
from abc import ABC, abstractmethod
# import tempfile  # For creating temporary files
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Third-party imports
import gradio as gr
from docx import Document
from colorama import init, Fore, Style
# from weasyprint import HTML  # PDF generation related import

# Constants
DEFAULT_PORT = 7860
DEFAULT_HOST = "0.0.0.0"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

# 1. Base Exception Classes
class DocumentCheckError(Exception):
    """Base exception for document checker errors."""
    pass

class ConfigurationError(DocumentCheckError):
    """Raised when configuration is invalid."""
    pass

class DocumentTypeError(DocumentCheckError):
    """Raised when document type is invalid."""
    pass

# 2. Configuration Classes
@dataclass
class PatternConfig:
    """Configuration for pattern matching."""
    pattern: str
    description: str
    is_error: bool
    replacement: Optional[str] = None
    keep_together: bool = False
    
    def compile(self) -> Pattern:
        """Compile the pattern."""
        try:
            return re.compile(self.pattern)
        except re.error as e:
            raise ConfigurationError(f"Invalid pattern '{self.pattern}': {e}")

class DocumentType(Enum):
    """Enumeration of supported document types."""
    ADVISORY_CIRCULAR = auto()
    AIRWORTHINESS_CRITERIA = auto()
    DEVIATION_MEMO = auto()
    EXEMPTION = auto()
    FEDERAL_REGISTER_NOTICE = auto()
    ORDER = auto()
    POLICY_STATEMENT = auto()
    RULE = auto()
    SPECIAL_CONDITION = auto()
    TECHNICAL_STANDARD_ORDER = auto()
    OTHER = auto()

    @classmethod
    def from_string(cls, doc_type: str) -> 'DocumentType':
        """Convert string to DocumentType, case-insensitive."""
        try:
            return cls[doc_type.upper().replace(" ", "_")]
        except KeyError:
            raise DocumentTypeError(f"Unsupported document type: {doc_type}")

# 3. Utility Classes
@dataclass
class TextNormalization:
    """Text normalization utilities."""
    
    @staticmethod
    def normalize_heading(text: str) -> str:
        """Normalize heading text for consistent comparison."""
        # Remove excess whitespace
        text = ' '.join(text.split())
        # Normalize periods (convert multiple periods to single period)
        text = re.sub(r'\.+$', '.', text.strip())
        # Remove any whitespace before the period
        text = re.sub(r'\s+\.$', '.', text)
        return text
    
    @staticmethod
    def normalize_document_type(doc_type: str) -> str:
        """Normalize document type string."""
        return ' '.join(word.capitalize() for word in doc_type.lower().split())

# 4. Result Class
@dataclass
class DocumentCheckResult:
    success: bool
    issues: List[Dict[str, Any]]
    details: Optional[Dict[str, Any]] = None

# 5. Base Document Checker
class DocumentChecker:
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = DocumentCheckerConfig(config_path)
        self.logger = self.config_manager.logger

    @classmethod
    def extract_paragraphs(cls, doc_path: str) -> List[str]:
        try:
            doc = Document(doc_path)
            return [para.text for para in doc.paragraphs if para.text.strip()]
        except Exception as e:
            logging.error(f"Error extracting paragraphs: {e}")
            return []

    @staticmethod
    def validate_input(doc: List[str]) -> bool:
        return doc is not None and isinstance(doc, list) and len(doc) > 0

# 6. Configuration Manager
class DocumentCheckerConfig:
    
    REQUIRED_CONFIG_KEYS = {'logging', 'checks', 'document_types'}
    REQUIRED_LOGGING_KEYS = {'level', 'format'}
    REQUIRED_CHECKS_KEYS = {'acronyms', 'terminology_check', 'headings'}
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with optional config file."""
        self.default_config = {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "checks": {
                "acronyms": True,
                "terminology_check": True,
                "headings": True
            },
            "document_types": {
                "Advisory Circular": {
                    "required_headings": [
                        "Purpose.",
                        "Applicability.",
                        "Cancellation.",
                        "Related Material.",
                        "Definition of Key Terms."
                    ],
                    "skip_title_check": False
                },
                "Federal Register Notice": {
                    "required_headings": [
                        "Purpose of This Notice",
                        "Audience",
                        "Where can I Find This Notice"
                    ],
                    "skip_title_check": False
                },
                "Order": {
                    "required_headings": [
                        "Purpose of This Order.",
                        "Audience.",
                        "Where to Find This Order."
                    ],
                    "skip_title_check": False
                },
                "Policy Statement": {
                    "required_headings": [
                        "SUMMARY",
                        "CURRENT REGULATORY AND ADVISORY MATERIAL",
                        "RELEVANT PAST PRACTICE",
                        "POLICY",
                        "EFFECT OF POLICY",
                        "CONCLUSION"
                    ],
                    "skip_title_check": False
                },
                "Technical Standard Order": {
                    "required_headings": [
                        "PURPOSE.",
                        "APPLICABILITY.",
                        "REQUIREMENTS.",
                        "MARKING.",
                        "APPLICATION DATA REQUIREMENTS.",
                        "MANUFACTURER DATA REQUIREMENTS.",
                        "FURNISHED DATA REQUIREMENTS.",
                        "HOW TO GET REFERENCED DOCUMENTS."
                    ],
                    "skip_title_check": False
                },
                "Airworthiness Criteria": {
                    "required_headings": [],
                    "skip_title_check": True
                },
                "Deviation Memo": {
                    "required_headings": [],
                    "skip_title_check": True
                },
                "Exemption": {
                    "required_headings": [],
                    "skip_title_check": True
                },
                "Rule": {
                    "required_headings": [],
                    "skip_title_check": True
                },
                "Special Condition": {
                    "required_headings": [],
                    "skip_title_check": True
                },
                "Other": {
                    "required_headings": [],
                    "skip_title_check": True
                }        
            }
        }

        self.config = self._load_config(config_path)
        self._validate_config(self.config)
        self.logger = self._setup_logger()
        self.pattern_registry = self._setup_patterns()

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from JSON file or use default settings.
        
        Args:
            config_path (str, optional): Path to configuration file.
            
        Returns:
            Dict[str, Any]: Loaded configuration dictionary.
        """
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge default and user config
                    return self._deep_merge(self.default_config.copy(), user_config)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error loading config: {e}. Using default config.")
                return self.default_config.copy()
        return self.default_config.copy()

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure."""
        # Check required top-level keys
        missing_keys = self.REQUIRED_CONFIG_KEYS - set(config.keys())
        if missing_keys:
            raise ConfigurationError(f"Missing required configuration keys: {missing_keys}")
        
        # Validate logging configuration
        missing_logging = self.REQUIRED_LOGGING_KEYS - set(config['logging'].keys())
        if missing_logging:
            raise ConfigurationError(f"Missing required logging keys: {missing_logging}")
        
        # Validate checks configuration
        missing_checks = self.REQUIRED_CHECKS_KEYS - set(config['checks'].keys())
        if missing_checks:
            raise ConfigurationError(f"Missing required checks keys: {missing_checks}")
        
        # Validate document types
        if not isinstance(config['document_types'], dict):
            raise ConfigurationError("Document types must be a dictionary")
        
        # Validate each document type's configuration
        for doc_type, type_config in config['document_types'].items():
            if not isinstance(type_config, dict):
                raise ConfigurationError(f"Invalid configuration for document type {doc_type}")
            
            # Check for required keys in each document type
            required_keys = {'required_headings', 'skip_title_check'}
            missing_type_keys = required_keys - set(type_config.keys())
            if missing_type_keys:
                raise ConfigurationError(
                    f"Missing required keys {missing_type_keys} for document type {doc_type}"
                )
            
            # Validate required_headings is a list
            if not isinstance(type_config['required_headings'], list):
                raise ConfigurationError(
                    f"required_headings must be a list for document type {doc_type}"
                )
            
            # Validate skip_title_check is boolean
            if not isinstance(type_config['skip_title_check'], bool):
                raise ConfigurationError(
                    f"skip_title_check must be a boolean for document type {doc_type}"
                )

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.

        Args:
            base (Dict): Base dictionary to merge into.
            update (Dict): Dictionary to merge from.

        Returns:
            Dict: Merged dictionary.
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _setup_logger(self) -> logging.Logger:
        """
        Set up and configure logging based on configuration.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(__name__)
        log_level = getattr(logging, self.config['logging']['level'].upper())

        formatter = logging.Formatter(self.config['logging']['format'])

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        logger.addHandler(console_handler)
        logger.setLevel(log_level)

        return logger
    
    def _setup_patterns(self) -> Dict[str, List[PatternConfig]]:
        """
        Set up comprehensive pattern registry for all document checks.
        
        Returns:
            Dict[str, List[PatternConfig]]: Dictionary of pattern configurations by category
        """
        try:
            # Get the directory containing the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            patterns_file = os.path.join(current_dir, 'patterns.json')
            
            # Load patterns from JSON file
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
                
            # Convert JSON data to PatternConfig objects
            patterns = {}
            for category, pattern_list in patterns_data.items():
                patterns[category] = [
                    PatternConfig(
                        pattern=p['pattern'],
                        description=p['description'],
                        is_error=p['is_error'],
                        replacement=p.get('replacement'),
                        keep_together=p.get('keep_together', False)
                    ) for p in pattern_list
                ]
                
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error loading patterns: {e}")
            # Return empty patterns dictionary if file loading fails
            return {}

def profile_performance(func):
    """Decorator to profile function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        # Get logger from the class instance (first argument)
        logger = args[0].logger
        logger.info(
            f"Performance: {func.__name__} took {end_time - start_time:.4f} seconds"
        )
        return result
    return wrapper

# 8. FAA Document Checker
class FAADocumentChecker(DocumentChecker):
    """Document checker implementation for FAA documents."""
    
    # Class Constants
    PERIOD_REQUIRED = {
        DocumentType.ADVISORY_CIRCULAR: True,
        DocumentType.AIRWORTHINESS_CRITERIA: False,
        DocumentType.DEVIATION_MEMO: False,
        DocumentType.EXEMPTION: False,
        DocumentType.FEDERAL_REGISTER_NOTICE: False,
        DocumentType.ORDER: True,
        DocumentType.POLICY_STATEMENT: False,
        DocumentType.RULE: False,
        DocumentType.SPECIAL_CONDITION: False,
        DocumentType.TECHNICAL_STANDARD_ORDER: True,
        DocumentType.OTHER: False
    }
    
    HEADING_WORDS = {
        'APPLICABILITY', 'APPENDIX', 'AUTHORITY', 'BACKGROUND', 'CANCELLATION', 'CAUTION',
        'CHAPTER', 'CONCLUSION', 'DEPARTMENT', 'DEFINITION', 'DEFINITIONS', 'DISCUSSION',
        'DISTRIBUTION', 'EXCEPTION', 'EXPLANATION', 'FIGURE', 'GENERAL', 'GROUPS', 
        'INFORMATION', 'INSERT', 'INTRODUCTION', 'MATERIAL', 'NOTE', 'PARTS', 'PAST', 
        'POLICY', 'PRACTICE', 'PROCEDURES', 'PURPOSE', 'RELEVANT', 'RELATED', 
        'REQUIREMENTS', 'REPORT', 'SCOPE', 'SECTION', 'SUMMARY', 'TABLE', 'WARNING'
    }
    
    PREDEFINED_ACRONYMS = {
        'AGC', 'AIR', 'CFR', 'DC', 'DOT', 'FAA IR-M', 'FAQ', 'i.e.', 'e.g.', 'MA',
        'MD', 'MIL', 'MO', 'No.', 'PDF', 'SSN', 'TX', 'U.S.', 'U.S.C.', 'USA', 'US', 
        'WA', 'XX', 'ZIP'
    }

    # Constructor
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)

    def _get_doc_type_config(self, doc_type: str) -> Tuple[Dict[str, Any], bool]:
        """
        Get document type configuration and validate document type.
        
        Args:
            doc_type: Type of document being checked
            
        Returns:
            Tuple containing:
                - Document type configuration dictionary
                - Boolean indicating if document type is valid
                
        Raises:
            DocumentTypeError: If document type is invalid
        """
        # Validate document type
        doc_type_config = self.config_manager.config['document_types'].get(doc_type)
        if not doc_type_config:
            self.logger.error(f"Unsupported document type: {doc_type}")
            raise DocumentTypeError(f'Unsupported document type: {doc_type}')
            
        return doc_type_config, True

    @profile_performance
    def heading_title_check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        if not self.validate_input(doc):
            self.logger.error("Invalid document input for heading check")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        try:
            # Use the new helper method
            doc_type_config, _ = self._get_doc_type_config(doc_type)
        except DocumentTypeError as e:
            return DocumentCheckResult(success=False, issues=[{'error': str(e)}])

        # Get configuration for document-specific headings
        required_headings = doc_type_config.get('required_headings', [])

        if not required_headings:
            return DocumentCheckResult(
                success=True, 
                issues=[], 
                details={'message': f'No required headings defined for {doc_type}'}
            )

        headings_found = []
        required_headings_set = set(required_headings)

        # Precompile a regex pattern to match headings at the start of the paragraph
        # Escape special characters in headings and allow for optional spaces and periods
        heading_patterns = []
        for heading in required_headings:
            escaped_heading = re.escape(heading.rstrip('.'))
            pattern = rf'^\s*{escaped_heading}\.?\s*'
            heading_patterns.append(pattern)
        combined_pattern = re.compile('|'.join(heading_patterns), re.IGNORECASE)

        for para in doc:
            para_strip = para.strip()
            # Check if paragraph starts with any of the required headings
            match = combined_pattern.match(para_strip)
            if match:
                # Extract the matched heading
                matched_heading = match.group().strip()
                # Normalize the matched heading to compare with required headings
                matched_heading_base = matched_heading.rstrip('.').strip()
                # Find the exact heading from required headings (case-insensitive)
                for required_heading in required_headings:
                    if matched_heading_base.lower() == required_heading.rstrip('.').lower():
                        headings_found.append(required_heading)
                        break

        # Check if all required headings are found
        found_headings_set = set(headings_found)
        missing_headings = required_headings_set - found_headings_set
        unexpected_headings = found_headings_set - required_headings_set

        success = len(missing_headings) == 0
        issues = []
        
        if not success:
            issues.append({
                'type': 'missing_headings',
                'missing': list(missing_headings)
            })

        if unexpected_headings:
            issues.append({
                'type': 'unexpected_headings',
                'unexpected': list(unexpected_headings)
            })

        details = {
            'found_headings': list(found_headings_set),
            'required_headings': required_headings,
            'document_type': doc_type,
            'missing_count': len(missing_headings),
            'unexpected_count': len(unexpected_headings)
        }

        return DocumentCheckResult(success=success, issues=issues, details=details)

    @profile_performance
    def heading_title_period_check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """
        Check if headings end with periods according to document type requirements.
        Enforces both required periods and no periods based on document type.
        
        Args:
            doc (List[str]): List of document paragraphs
            doc_type (str): Type of document being checked
                
        Returns:
            DocumentCheckResult: Result of the heading period check including:
                - success: Boolean indicating if all headings follow period rules
                - issues: List of dicts with heading format issues
                - details: Additional information about the check
        """
        if not self.validate_input(doc):
            self.logger.error("Invalid document input for period check")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Validate document type exists in configuration
        doc_type_config = self.config_manager.config['document_types'].get(doc_type)
        if not doc_type_config:
            self.logger.error(f"Unsupported document type: {doc_type}")
            return DocumentCheckResult(
                success=False, 
                issues=[{'error': f'Unsupported document type: {doc_type}'}]
            )

        # Define document types requiring periods in headings
        period_required = {
            "Advisory Circular": True,
            "Airworthiness Criteria": False,
            "Deviation Memo": False,
            "Exemption": False,
            "Federal Register Notice": False,
            "Order": True,
            "Policy Statement": False,
            "Rule": False,
            "Special Condition": False,
            "Technical Standard Order": True,
            "Other": False
        }

        should_have_period = period_required.get(doc_type)
        if should_have_period is None:
            self.logger.error(f"Period requirement not defined for document type: {doc_type}")
            return DocumentCheckResult(
                success=False, 
                issues=[{'error': f'Period requirement not defined for document type: {doc_type}'}]
            )
        
        # Get the headings configuration for this document type
        required_headings = doc_type_config.get('required_headings', [])
        
        if not required_headings:
            return DocumentCheckResult(
                success=True, 
                issues=[], 
                details={'message': f'No required headings defined for {doc_type}'}
            )

        issues = []
        checked_headings = []

        # Create a set of normalized required headings (without periods)
        # Strip periods from the required headings to allow for flexible matching
        required_headings_set = {h.rstrip('.') for h in required_headings}

        for para in doc:
            para_strip = para.strip()
            para_base = para_strip.rstrip('.')
            
            # Check only if paragraph is a heading (comparing without periods)
            if para_base in required_headings_set:
                ends_with_period = para_strip.endswith('.')
                
                # Check for both cases:
                # 1. Should have period but doesn't
                # 2. Shouldn't have period but does
                if should_have_period and not ends_with_period:
                    issues.append({
                        'heading': para_strip,
                        'issue': 'missing_period',
                        'message': f"Heading should end with a period: '{para_strip}'"
                    })
                elif not should_have_period and ends_with_period:
                    issues.append({
                        'heading': para_strip,
                        'issue': 'unexpected_period',
                        'message': f"Heading should not have a period: '{para_strip}'"
                    })

                checked_headings.append({
                    'heading': para_strip,
                    'has_period': ends_with_period,
                    'needs_period': should_have_period
                })

        # Calculate statistics for the details
        total_checked = len(checked_headings)
        total_issues = len(issues)
        incorrect_period_count = sum(1 for h in checked_headings 
                                if h['has_period'] != h['needs_period'])

        # Detailed results for debugging and reporting
        details = {
            'document_type': doc_type,
            'periods_required': should_have_period,
            'checked_headings': checked_headings,
            'total_checked': total_checked,
            'total_issues': total_issues,
            'incorrect_period_count': incorrect_period_count
        }

        success = len(issues) == 0

        # Log summary for debugging
        self.logger.debug(f"Period check for {doc_type}: "
                        f"checked {total_checked} headings, "
                        f"found {total_issues} issues")

        return DocumentCheckResult(success=success, issues=issues, details=details)

    @profile_performance
    def acronym_check(self, doc: List[str]) -> DocumentCheckResult:
        """Check for acronyms and their definitions."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Load valid words
        valid_words = self._load_valid_words()

        # Common words that might appear in uppercase but aren't acronyms
        heading_words = self.config_manager.config.get('heading_words', self.HEADING_WORDS)

        # Standard acronyms that don't need to be defined
        predefined_acronyms = self.config_manager.config.get('predefined_acronyms', self.PREDEFINED_ACRONYMS)

        # Patterns for references that contain acronyms but should be ignored
        ignore_patterns = [
            r'FAA-\d{4}-\d+',              # FAA docket numbers
            r'\d{2}-\d{2}-\d{2}-SC',       # Special condition numbers
            r'AC\s*\d+(?:[-.]\d+)*[A-Z]*', # Advisory circular numbers
            r'AD\s*\d{4}-\d{2}-\d{2}',     # Airworthiness directive numbers
            r'\d{2}-[A-Z]{2,}',            # Other reference numbers with acronyms
            r'[A-Z]+-\d+',                 # Generic reference numbers
            r'§\s*[A-Z]+\.\d+',            # Section references
            r'Part\s*[A-Z]+',              # Part references
        ]
        
        # Combine ignore patterns
        ignore_regex = '|'.join(f'(?:{pattern})' for pattern in ignore_patterns)
        ignore_pattern = re.compile(ignore_regex)

        # Tracking structures
        defined_acronyms = {}  # Stores definition info
        used_acronyms = set()  # Stores acronyms used after definition
        reported_acronyms = set()  # Stores acronyms that have already been noted as issues

        # Patterns
        defined_pattern = re.compile(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)')
        acronym_pattern = re.compile(r'(?<!\()\b[A-Z]{2,}\b(?!\s*[:.]\s*)')

        issues = []

        for paragraph in doc:
            # Skip lines that appear to be headings
            words = paragraph.strip().split()
            if all(word.isupper() for word in words) and any(word in heading_words for word in words):
                continue

            # First, find all text that should be ignored
            ignored_spans = []
            for match in ignore_pattern.finditer(paragraph):
                ignored_spans.append(match.span())

            # Check for acronym definitions first
            defined_matches = defined_pattern.finditer(paragraph)
            for match in defined_matches:
                full_term, acronym = match.groups()
                # Skip if the acronym is in an ignored span
                if not any(start <= match.start(2) <= end for start, end in ignored_spans):
                    if acronym not in predefined_acronyms:
                        if acronym not in defined_acronyms:
                            defined_acronyms[acronym] = {
                                'full_term': full_term.strip(),
                                'defined_at': paragraph.strip(),
                                'used': False
                            }

            # Check for acronym usage
            usage_matches = acronym_pattern.finditer(paragraph)
            for match in usage_matches:
                acronym = match.group()
                start_pos = match.start()

                # Skip if the acronym is in an ignored span
                if any(start <= start_pos <= end for start, end in ignored_spans):
                    continue

                # Skip predefined acronyms, valid words, and other checks
                if (acronym in predefined_acronyms or
                    acronym in heading_words or
                    acronym.lower() in valid_words or  # Check against valid words list
                    any(not c.isalpha() for c in acronym) or
                    len(acronym) > 10):
                    continue

                if acronym not in defined_acronyms and acronym not in reported_acronyms:
                    # Undefined acronym used; report only once
                    issues.append(f"Confirm '{acronym}' was defined at its first use.")
                    reported_acronyms.add(acronym)
                elif acronym in defined_acronyms:
                    defined_acronyms[acronym]['used'] = True
                    used_acronyms.add(acronym)

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    @profile_performance
    def acronym_usage_check(self, doc: List[str]) -> DocumentCheckResult:
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Pattern to find acronym definitions (e.g., "Environmental Protection Agency (EPA)")
        defined_pattern = re.compile(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)')

        # Pattern to find acronym usage (e.g., "FAA", "EPA")
        acronym_pattern = re.compile(r'\b[A-Z]{2,}\b')

        # Tracking structures
        defined_acronyms = {}
        used_acronyms = set()

        # Step 1: Extract all defined acronyms
        for paragraph in doc:
            defined_matches = defined_pattern.findall(paragraph)
            for full_term, acronym in defined_matches:
                if acronym not in defined_acronyms:
                    defined_acronyms[acronym] = {
                        'full_term': full_term.strip(),
                        'defined_at': paragraph.strip()
                    }

        # Step 2: Check for acronym usage, excluding definitions
        for paragraph in doc:
            # Remove definitions from paragraph for usage checks
            paragraph_excluding_definitions = re.sub(defined_pattern, '', paragraph)

            usage_matches = acronym_pattern.findall(paragraph_excluding_definitions)
            for acronym in usage_matches:
                if acronym in defined_acronyms:
                    used_acronyms.add(acronym)

        # Step 3: Identify unused acronyms
        unused_acronyms = [
            {
                'acronym': acronym,
                'full_term': data['full_term'],
                'defined_at': data['defined_at']
            }
            for acronym, data in defined_acronyms.items()
            if acronym not in used_acronyms
        ]

        # Success is true if no unused acronyms are found
        success = len(unused_acronyms) == 0

        return DocumentCheckResult(success=success, issues=unused_acronyms)

    @profile_performance
    def check_terminology(self, doc: List[str]) -> DocumentCheckResult:
        """Check document terminology and output only unique term replacements needed."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        terminology_patterns = self.config_manager.pattern_registry.get('terminology', [])
        prohibited_patterns = self.config_manager.pattern_registry.get('reference_terms', [])

        unique_issues = set()  # Using a set to avoid duplicate replacements

        # Process each sentence
        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check terminology patterns
                for pattern_config in terminology_patterns:
                    matches = list(re.finditer(pattern_config.pattern, sentence))
                    for match in matches:
                        if pattern_config.replacement:  # Only if there's a replacement term
                            unique_issues.add((match.group(), pattern_config.replacement))

                # Check prohibited patterns
                for pattern_config in prohibited_patterns:
                    if re.search(pattern_config.pattern, sentence, re.IGNORECASE):
                        if pattern_config.replacement:  # Only if there's a replacement term
                            match_text = re.search(pattern_config.pattern, sentence, re.IGNORECASE).group()
                            unique_issues.add((match_text, pattern_config.replacement))

        # Format issues as simple replacement instructions
        formatted_issues = [
            {'incorrect_term': incorrect, 'correct_term': correct}
            for incorrect, correct in sorted(unique_issues)  # Sort for consistent output
        ]

        return DocumentCheckResult(success=not formatted_issues, issues=formatted_issues)

    @profile_performance
    def check_section_symbol_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check for section symbol (§) usage issues."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        issues = []
        
        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # Check 14 CFR citations only
                cfr_matches = re.finditer(r'\b14 CFR §\s*(\d+\.\d+)\b', sentence)
                for match in cfr_matches:
                    # Skip if this is part of a U.S.C. citation
                    if not re.search(r'U\.S\.C\.\s*§', sentence):
                        full_match = match.group(0)
                        section_num = match.group(1)
                        issues.append({
                            'incorrect': full_match,
                            'correct': f'14 CFR {section_num}',
                            'description': f"Replace '{full_match}' with '14 CFR {section_num}'"
                        })

                # Skip any checks for sections that are part of U.S.C. citations
                if re.search(r'U\.S\.C\.\s*(?:§|§§)', sentence):
                    continue

                # Skip any checks for sections that are part of 14 CFR citations
                if re.search(r'14 CFR\s*§', sentence):
                    continue

                # Check section symbol at start of sentence
                if sentence.startswith('§'):
                    match = re.match(r'^§\s*(\d+(?:\.\d+)?)', sentence)
                    if match:
                        section_num = match.group(1)
                        issues.append({
                            'incorrect': f'§ {section_num}',
                            'correct': f'Section {section_num}',
                            'description': f"Replace '§ {section_num}' with 'Section {section_num}'"
                        })

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    @profile_performance
    def caption_check(self, doc: List[str], doc_type: str, caption_type: str) -> DocumentCheckResult:
        """Check for correctly formatted table or figure captions."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        incorrect_captions = []

        for paragraph in doc:
            paragraph_strip = paragraph.strip()
            
            # Check if paragraph starts with the caption type and includes a number
            if paragraph_strip.lower().startswith(caption_type.lower()):
                # Look for any number pattern after the caption type
                number_match = re.search(rf'{caption_type}\s+(\d+(?:-\d+)?)', paragraph_strip, re.IGNORECASE)
                if number_match:
                    number_format = number_match.group(1)
                    if doc_type in ["Advisory Circular", "Order"]:
                        if '-' not in number_format:
                            incorrect_captions.append({
                                'incorrect_caption': f"{caption_type} {number_format}",
                                'doc_type': doc_type,
                                'caption_type': caption_type
                            })
                    else:
                        if '-' in number_format:
                            incorrect_captions.append({
                                'incorrect_caption': f"{caption_type} {number_format}",
                                'doc_type': doc_type,
                                'caption_type': caption_type
                            })

        return DocumentCheckResult(
            success=len(incorrect_captions) == 0,
            issues=incorrect_captions,
            details={
                'document_type': doc_type,
                'caption_type': caption_type
            }
        )

    @profile_performance
    def table_figure_reference_check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """Check for correctly formatted table and figure references."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        incorrect_references = []
        
        # Pattern to identify table/figure captions
        caption_pattern = re.compile(r'^(Table|Figure)\s+\d+[-\d]*\.?', re.IGNORECASE)
        
        # Patterns for references within sentences and at start
        table_ref_pattern = re.compile(r'\b([Tt]able)\s+\d+(?:-\d+)?')
        figure_ref_pattern = re.compile(r'\b([Ff]igure)\s+\d+(?:-\d+)?')

        for paragraph in doc:
            # Skip if this is a caption line
            if caption_pattern.match(paragraph.strip()):
                continue
            
            # Split into sentences while preserving punctuation
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check table references
                for pattern, ref_type in [(table_ref_pattern, "Table"), (figure_ref_pattern, "Figure")]:
                    matches = list(pattern.finditer(sentence))
                    for match in matches:
                        ref = match.group()
                        word = match.group(1)  # The actual "Table" or "Figure" word
                        
                        # Get text before the reference
                        text_before = sentence[:match.start()].strip()
                        
                        # Determine if reference is at start of sentence
                        is_sentence_start = not text_before or text_before.endswith((':',';'))
                        
                        if is_sentence_start and word[0].islower():
                            incorrect_references.append({
                                'reference': ref,
                                'issue': f"{ref_type} reference at sentence start should be capitalized",
                                'sentence': sentence,
                                'correct_form': ref.capitalize()
                            })
                        elif not is_sentence_start and word[0].isupper():
                            incorrect_references.append({
                                'reference': ref,
                                'issue': f"{ref_type} reference within sentence should be lowercase",
                                'sentence': sentence,
                                'correct_form': ref.lower()
                            })

        return DocumentCheckResult(success=len(incorrect_references) == 0, issues=incorrect_references)

    @profile_performance
    def document_title_check(self, doc_path: str, doc_type: str) -> DocumentCheckResult:
        """
        Check for correct formatting of document titles.
        
        For Advisory Circulars: Use italics without quotes
        For all other document types: Use quotes without italics
        
        Args:
            doc_path: Path to the document
            doc_type: Type of document being checked
            
        Returns:
            DocumentCheckResult: Results of document title check
        """
        try:
            doc = Document(doc_path)
        except Exception as e:
            self.logger.error(f"Error reading the document in title check: {e}")
            return DocumentCheckResult(success=False, issues=[{'error': str(e)}])

        incorrect_titles = []

        # Define formatting rules based on document type
        use_italics = doc_type == "Advisory Circular"
        use_quotes = doc_type != "Advisory Circular"

        # Pattern to match document references (e.g., "AC 25.1309-1B, System Design and Analysis")
        doc_ref_pattern = re.compile(
            r'(?:AC|Order|Policy|Notice)\s+[\d.-]+[A-Z]?,\s+([^,.]+)(?:[,.]|$)'
        )

        for paragraph in doc.paragraphs:
            matches = doc_ref_pattern.finditer(paragraph.text)
            
            for match in matches:
                title_text = match.group(1).strip()
                title_start = match.start(1)
                title_end = match.end(1)

                # Check formatting within the matched range
                title_is_italicized = False
                title_in_quotes = False
                current_pos = 0

                for run in paragraph.runs:
                    run_length = len(run.text)
                    run_start = current_pos
                    run_end = current_pos + run_length

                    # Check if this run overlaps with the title
                    if (run_start <= title_start < run_end or 
                        run_start < title_end <= run_end or
                        title_start <= run_start < title_end):
                        title_is_italicized = title_is_italicized or run.italic
                        # Check for any type of quotation marks
                        title_in_quotes = title_in_quotes or any(
                            q in run.text for q in ['"', "'", '"', '"', '"', '"']
                        )

                    current_pos += run_length

                # Determine if formatting is incorrect
                formatting_incorrect = False
                issue_message = []

                if use_italics:
                    if not title_is_italicized:
                        formatting_incorrect = True
                        issue_message.append("should be italicized")
                    if title_in_quotes:
                        formatting_incorrect = True
                        issue_message.append("should not be in quotes")
                else:  # use quotes
                    if title_is_italicized:
                        formatting_incorrect = True
                        issue_message.append("should not be italicized")
                    if not title_in_quotes:
                        formatting_incorrect = True
                        issue_message.append("should be in quotes")

                if formatting_incorrect:
                    incorrect_titles.append({
                        'text': title_text,
                        'issue': ' and '.join(issue_message),
                        'sentence': paragraph.text.strip(),
                        'correct_format': 'italics' if use_italics else 'quotes'
                    })

        success = len(incorrect_titles) == 0

        return DocumentCheckResult(
            success=success,
            issues=incorrect_titles,
            details={
                'document_type': doc_type,
                'formatting_rule': 'italics' if use_italics else 'quotes'
            }
        )

    @profile_performance
    def double_period_check(self, doc: List[str]) -> DocumentCheckResult:
        """Check for sentences that end with two periods."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        incorrect_sentences = []
        
        for paragraph in doc:
            # Split the paragraph into sentences based on common sentence-ending punctuation
            sentences = re.split(r'(?<=[.!?]) +', paragraph)
            for sentence in sentences:
                if sentence.endswith('..'):
                    incorrect_sentences.append({'sentence': sentence.strip()})

        success = len(incorrect_sentences) == 0

        return DocumentCheckResult(success=success, issues=incorrect_sentences)

    @profile_performance
    def spacing_check(self, doc: List[str]) -> DocumentCheckResult:
        """Check for correct spacing in the document."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        issues = []
        
        try:
            for paragraph in doc:
                # Skip empty paragraphs
                if not paragraph.strip():
                    continue
                    
                # Skip paragraphs with tabs
                if '\t' in paragraph:
                    continue
                    
                # Check for multiple spaces between words, but ignore spaces around parentheses
                # First, temporarily replace valid parenthetical patterns to protect them
                working_text = paragraph
                
                # Protect common regulatory reference patterns
                patterns_to_ignore = [
                    r'\d+\(\d+\)\([a-z]\)',  # matches patterns like 25(1)(a)
                    r'\d+\([a-z]\)',         # matches patterns like 25(a)
                    r'\([a-z]\)\(\d+\)',     # matches patterns like (a)(1)
                    r'\(\d+\)\([a-z]\)',     # matches patterns like (1)(a)
                    r'\([a-z]\)',            # matches single letter references like (a)
                    r'\(\d+\)',              # matches number references like (1)
                ]
                
                for pattern in patterns_to_ignore:
                    working_text = re.sub(pattern, lambda m: 'PROTECTED' + str(hash(m.group())), working_text)
                
                # Now check for multiple spaces
                matches = re.finditer(r'[ ]{2,}', working_text)
                for match in matches:
                    issues.append({
                        'incorrect': match.group(),
                        'context': paragraph.strip(),
                        'description': "Remove extra spaces"
                    })

        except Exception as e:
            self.logger.error(f"Error in spacing check: {str(e)}")
            return DocumentCheckResult(success=False, issues=[{'error': f'Spacing check failed: {str(e)}'}])

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def _format_spacing_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format spacing issues with clear instructions for fixing."""
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                if 'error' in issue:
                    formatted_issues.append(f"    • {issue['error']}")
                else:
                    formatted_issues.append(
                        f"    • {issue['description']} in: \"{issue['context']}\""
                    )
        
        return formatted_issues

    @profile_performance
    def check_abbreviation_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check for abbreviation consistency after first definition."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Track abbreviations and their usage
        abbreviations = {}  # Store defined abbreviations
        inconsistent_uses = []  # Track full term usage after definition

        def process_sentence(sentence: str) -> None:
            """Process a single sentence for abbreviation usage."""
            for acronym, data in abbreviations.items():
                full_term = data["full_term"]
                if full_term not in sentence:
                    continue
                    
                # Skip if this is the definition sentence
                if sentence.strip() == data["first_occurrence"]:
                    continue
                    
                # Track inconsistent usage
                if not data["defined"]:
                    inconsistent_uses.append({
                        'issue_type': 'full_term_after_acronym',
                        'full_term': full_term,
                        'acronym': acronym,
                        'sentence': sentence.strip(),
                        'definition_context': data["first_occurrence"]
                    })
                data["defined"] = False  # Mark as used

        # Process each paragraph
        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                process_sentence(sentence.strip())

        success = len(inconsistent_uses) == 0
        return DocumentCheckResult(success=success, issues=inconsistent_uses)

    @profile_performance
    def check_date_formats(self, doc: List[str]) -> DocumentCheckResult:
        """Check for inconsistent date formats while ignoring aviation reference numbers."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
        
        # Get patterns from registry
        date_patterns = self.config_manager.pattern_registry.get('dates', [])
        
        # Patterns to ignore (aviation references)
        ignore_patterns = [
            r'\bAC\s*\d+(?:[-.]\d+)*[A-Z]*\b', # AC reference pattern
            r'\bAD \d{4}-\d{2}-\d{2}\b',      # Airworthiness Directive references
            r'\bSWPM \d{2}-\d{2}-\d{2}\b',    # Standard Wiring Practices Manual references
            r'\bAMM \d{2}-\d{2}-\d{2}\b',     # Aircraft Maintenance Manual references
            r'\bSOPM \d{2}-\d{2}-\d{2}\b',    # Standard Operating Procedure references
            r'\b[A-Z]{2,4} \d{2}-\d{2}-\d{2}\b'  # Generic manual reference pattern
        ]
        
        # Combine ignore patterns into one
        ignore_regex = '|'.join(f'(?:{pattern})' for pattern in ignore_patterns)
        ignore_pattern = re.compile(ignore_regex)
        
        # Track unique issues
        unique_issues = []
        
        # Use _process_sentences helper
        for sentence, paragraph in self._process_sentences(doc, skip_empty=True, skip_headings=True):
            # First, identify and temporarily remove text that should be ignored
            working_sentence = sentence
            
            # Find all matches to ignore
            ignored_matches = list(ignore_pattern.finditer(sentence))
            
            # Replace ignored patterns with placeholders
            for match in reversed(ignored_matches):
                start, end = match.span()
                working_sentence = working_sentence[:start] + 'X' * (end - start) + working_sentence[end:]
            
            # Now check for date patterns in the modified sentence
            for pattern_config in date_patterns:
                matches = list(re.finditer(pattern_config.pattern, working_sentence))
                
                for match in matches:
                    # Get the original text from the match position
                    original_date = sentence[match.start():match.end()]
                    
                    # Create formatted issue with incorrect/correct format
                    formatted_issue = {
                        'incorrect': original_date,
                        'correct': 'Month Day, Year'
                    }
                    unique_issues.append(formatted_issue)

        return DocumentCheckResult(success=len(unique_issues) == 0, issues=unique_issues)

    @profile_performance
    def check_placeholders(self, doc: List[str]) -> DocumentCheckResult:
        """Check for placeholders that should be removed."""
        def process_placeholders(doc: List[str], patterns: List[PatternConfig]) -> DocumentCheckResult:
            tbd_placeholders = []
            to_be_determined_placeholders = []
            to_be_added_placeholders = []
            
            pattern_categories = {
                r'\bTBD\b': ('tbd', tbd_placeholders),
                r'\bTo be determined\b': ('to_be_determined', to_be_determined_placeholders),
                r'\bTo be added\b': ('to_be_added', to_be_added_placeholders)
            }

            # Use _process_sentences helper
            for sentence, paragraph in self._process_sentences(doc, skip_empty=True, skip_headings=True):
                for pattern_config in patterns:
                    compiled_pattern = re.compile(pattern_config.pattern, re.IGNORECASE)
                    
                    for pattern_key, (category_name, category_list) in pattern_categories.items():
                        if pattern_config.pattern == pattern_key:
                            matches = compiled_pattern.finditer(sentence)
                            for match in matches:
                                category_list.append({
                                    'placeholder': match.group().strip(),
                                    'sentence': sentence.strip(),
                                    'description': pattern_config.description
                                })

            # Compile issues
            issues = []
            if tbd_placeholders:
                issues.append({
                    'issue_type': 'tbd_placeholder',
                    'description': 'Remove TBD placeholder',
                    'occurrences': tbd_placeholders
                })
                
            if to_be_determined_placeholders:
                issues.append({
                    'issue_type': 'to_be_determined_placeholder',
                    'description': "Remove 'To be determined' placeholder",
                    'occurrences': to_be_determined_placeholders
                })
                
            if to_be_added_placeholders:
                issues.append({
                    'issue_type': 'to_be_added_placeholder',
                    'description': "Remove 'To be added' placeholder",
                    'occurrences': to_be_added_placeholders
                })

            details = {
                'total_placeholders': len(tbd_placeholders) + 
                                    len(to_be_determined_placeholders) + 
                                    len(to_be_added_placeholders),
                'placeholder_types': {
                    'TBD': len(tbd_placeholders),
                    'To be determined': len(to_be_determined_placeholders),
                    'To be added': len(to_be_added_placeholders)
                }
            }

            return DocumentCheckResult(success=len(issues) == 0, issues=issues, details=details)

        return self._process_patterns(doc, 'placeholders', process_placeholders)

    @profile_performance
    def _process_patterns(
        self,
        doc: List[str],
        pattern_category: str,
        process_func: Optional[Callable] = None
    ) -> DocumentCheckResult:
        """
        Process document text against patterns from a specific category.
        
        Args:
            doc: List of document paragraphs
            pattern_category: Category of patterns to check against
            process_func: Optional custom processing function
            
        Returns:
            DocumentCheckResult with processed issues
        """
        if not self.validate_input(doc):
            self.logger.error("Invalid document input for pattern check")
            return DocumentCheckResult(
                success=False, 
                issues=[{'error': 'Invalid document input'}]
            )

        # Get patterns from registry
        patterns = self.config_manager.pattern_registry.get(pattern_category, [])
        if not patterns:
            self.logger.warning(f"No patterns found for category: {pattern_category}")
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={'message': f'No patterns defined for {pattern_category}'}
            )

        # Use custom processing function if provided
        if process_func:
            return process_func(doc, patterns)

        # Default processing with deduplication
        unique_issues = set()  # Using a set to track unique issues

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                for pattern_config in patterns:
                    matches = list(re.finditer(pattern_config.pattern, sentence))
                    if matches:
                        # Add each match as a tuple to ensure uniqueness
                        for match in matches:
                            unique_issues.add((
                                match.group(),  # The matched text
                                pattern_config.description,  # The issue description
                                pattern_config.replacement if hasattr(pattern_config, 'replacement') else None
                            ))

        # Convert unique issues back to the expected format
        formatted_issues = [
            {
                'incorrect': issue[0],
                'description': issue[1],
                'replacement': issue[2]
            }
            for issue in sorted(unique_issues)  # Sort for consistent output
        ]

        return DocumentCheckResult(success=len(formatted_issues) == 0, issues=formatted_issues)

    def run_all_checks(self, doc_path: str, doc_type: str, template_type: Optional[str] = None) -> Dict[str, DocumentCheckResult]:
        """
        Run all checks on the document.

        Args:
            doc_path (str): Path to the document.
            doc_type (str): Type of the document.
            template_type (str, optional): Template type, if applicable.

        Returns:
            Dict[str, DocumentCheckResult]: Dictionary of check names to results.
        """
        # Read the document
        doc = self.extract_paragraphs(doc_path)

        # Retrieve any specific flags
        checks_config = self.config_manager.config['document_types'].get(doc_type, {})
        skip_title_check = checks_config.get('skip_title_check', False)

        # Initialize results dictionary
        results = {}


        # Define order of checks for better organization
        check_sequence = [
            ('heading_title_check', lambda: self.heading_title_check(doc, doc_type)),
            ('heading_title_period_check', lambda: self.heading_title_period_check(doc, doc_type)),
            ('terminology_check', lambda: self.check_terminology(doc)),
            ('acronym_check', lambda: self.acronym_check(doc)),
            ('acronym_usage_check', lambda: self.acronym_usage_check(doc)),
            ('section_symbol_usage_check', lambda: self.check_section_symbol_usage(doc)),
            ('508_compliance_check', lambda: self.check_508_compliance(doc_path)),
            ('hyperlink_check', lambda: self.check_hyperlinks(doc)),
            ('date_formats_check', lambda: self.check_date_formats(doc)),
            ('placeholders_check', lambda: self.check_placeholders(doc)),
            ('document_title_check', lambda: self.document_title_check(doc_path, doc_type) if not skip_title_check else DocumentCheckResult(success=True, issues=[])),
            ('caption_check_table', lambda: self.caption_check(doc, doc_type, 'Table')),
            ('caption_check_figure', lambda: self.caption_check(doc, doc_type, 'Figure')),
            ('table_figure_reference_check', lambda: self.table_figure_reference_check(doc, doc_type)),
            ('parentheses_check', lambda: self.check_parentheses(doc)),
            ('double_period_check', lambda: self.double_period_check(doc)),
            ('spacing_check', lambda: self.spacing_check(doc)),
            ('paragraph_length_check', lambda: self.check_paragraph_length(doc)),
            ('sentence_length_check', lambda: self.check_sentence_length(doc)),
        ]

        # Run each check and store results
        for check_name, check_func in check_sequence:
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.logger.error(f"Error running {check_name}: {str(e)}")
                results[check_name] = DocumentCheckResult(
                    success=False,
                    issues=[{'error': f'Check failed with error: {str(e)}'}]
                )

        return results

    def _compile_issues(
        self,
        issue_groups: Dict[str, List[Dict[str, Any]]],
        category_descriptions: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Compile issues from different groups into a standardized format.
        
        Args:
            issue_groups: Dictionary of issue type to list of issues
            category_descriptions: Dictionary of issue type to description
            
        Returns:
            List of compiled issues in standardized format
        """
        compiled_issues = []
        
        for issue_type, issues in issue_groups.items():
            if issues:  # Only add groups that have issues
                compiled_issues.append({
                    'issue_type': issue_type,
                    'description': category_descriptions.get(
                        issue_type, 
                        f'Issues found in {issue_type}'
                    ),
                    'occurrences': issues
                })
                
        return compiled_issues

    def _process_sentences(
        self, 
        doc: List[str], 
        skip_empty: bool = True,
        skip_headings: bool = False
    ) -> List[Tuple[str, str]]:
        """
        Process document paragraphs into sentences with their parent paragraphs.
        
        Args:
            doc: List of document paragraphs
            skip_empty: Whether to skip empty sentences
            skip_headings: Whether to skip lines that appear to be headings
            
        Returns:
            List of tuples containing (sentence, parent_paragraph)
        """
        sentences = []
        for paragraph in doc:
            paragraph = paragraph.strip()
            
            # Skip heading-like paragraphs if requested
            if skip_headings:
                words = paragraph.split()
                if all(word.isupper() for word in words) and any(
                    word in self.HEADING_WORDS for word in words
                ):
                    continue
            
            # Split paragraph into sentences
            para_sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            # Process each sentence
            for sentence in para_sentences:
                sentence = sentence.strip()
                if skip_empty and not sentence:
                    continue
                sentences.append((sentence, paragraph))
                
        return sentences  

    @profile_performance
    def check_parentheses(self, doc: List[str]) -> DocumentCheckResult:
        """
        Check for matching parentheses in the document.

        Args:
            doc (List[str]): List of document paragraphs

        Returns:
            DocumentCheckResult: Result containing any mismatched parentheses issues
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        issues = []
        
        for i, paragraph in enumerate(doc, 1):
            if not paragraph.strip():  # Skip empty paragraphs
                continue
            
            stack = []  # Track unmatched opening parentheses
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)  # Split paragraph into sentences
            for sentence in sentences:
                for j, char in enumerate(sentence):
                    if char == '(':
                        stack.append((sentence, j))  # Store sentence and character position
                    elif char == ')':
                        if stack:
                            stack.pop()  # Remove matching opening parenthesis
                        else:
                            # No matching opening parenthesis
                            issues.append({
                                'type': 'missing_opening',
                                'paragraph': i,  # Still tracked but not included in the message
                                'position': j,
                                'text': sentence,
                                'message': f"Add an opening parenthesis to the sentence: \"{sentence.strip()}\""
                            })

            # Check for any unmatched opening parentheses left in the stack
            for unmatched in stack:
                sentence, pos = unmatched
                issues.append({
                    'type': 'missing_closing',
                    'paragraph': i,  # Still tracked but not included in the message
                    'position': pos,
                    'text': sentence,
                    'message': f"Add a closing parenthesis to the sentence: \"{sentence.strip()}\""
                })

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    @profile_performance
    def spacing_check(self, doc: List[str]) -> DocumentCheckResult:
        """Check for correct spacing in the document."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        spacing_patterns = self.config_manager.pattern_registry.get('spacing', [])
        issues = []
        
        try:
            for paragraph in doc:
                if not paragraph.strip() or '\t' in paragraph:
                    continue

                for pattern_config in spacing_patterns:
                    matches = re.finditer(pattern_config.pattern, paragraph)
                    for match in matches:
                        groups = match.groups()
                        description = pattern_config.description.replace('{0}', groups[0]).replace('{1}', groups[1])
                        
                        context_start = max(0, match.start() - 20)
                        context_end = min(len(paragraph), match.end() + 20)
                        context = paragraph[context_start:context_end].strip()
                        
                        issues.append({
                            'type': 'spacing',
                            'incorrect': match.group(),
                            'context': context,
                            'description': description
                        })

        except Exception as e:
            self.logger.error(f"Error in spacing check: {str(e)}")
            return DocumentCheckResult(success=False, issues=[{'error': f'Spacing check failed: {str(e)}'}])

        return DocumentCheckResult(success=len(issues) == 0, issues=issues)

    def _format_spacing_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format spacing issues with clear instructions for fixing."""
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                if 'error' in issue:
                    formatted_issues.append(f"    • {issue['error']}")
                else:
                    formatted_issues.append(
                        f"    • {issue['description']} in: \"{issue['context']}\""
                    )
        
        return formatted_issues

    @profile_performance
    def check_abbreviation_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check for abbreviation consistency after first definition."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Track abbreviations and their usage
        abbreviations = {}  # Store defined abbreviations
        inconsistent_uses = []  # Track full term usage after definition

        def process_sentence(sentence: str) -> None:
            """Process a single sentence for abbreviation usage."""
            for acronym, data in abbreviations.items():
                full_term = data["full_term"]
                if full_term not in sentence:
                    continue
                    
                # Skip if this is the definition sentence
                if sentence.strip() == data["first_occurrence"]:
                    continue
                    
                # Track inconsistent usage
                if not data["defined"]:
                    inconsistent_uses.append({
                        'issue_type': 'full_term_after_acronym',
                        'full_term': full_term,
                        'acronym': acronym,
                        'sentence': sentence.strip(),
                        'definition_context': data["first_occurrence"]
                    })
                data["defined"] = False  # Mark as used

        # Process each paragraph
        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                process_sentence(sentence.strip())

        success = len(inconsistent_uses) == 0
        return DocumentCheckResult(success=success, issues=inconsistent_uses)

    @profile_performance
    def check_date_formats(self, doc: List[str]) -> DocumentCheckResult:
        """Check for inconsistent date formats while ignoring aviation reference numbers."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
        
        # Get patterns from registry
        date_patterns = self.config_manager.pattern_registry.get('dates', [])
        
        # Patterns to ignore (aviation references)
        ignore_patterns = [
            r'\bAD \d{4}-\d{2}-\d{2}\b',      # Airworthiness Directive references
            r'\bSWPM \d{2}-\d{2}-\d{2}\b',    # Standard Wiring Practices Manual references
            r'\bAMM \d{2}-\d{2}-\d{2}\b',     # Aircraft Maintenance Manual references
            r'\bSOPM \d{2}-\d{2}-\d{2}\b',    # Standard Operating Procedure references
            r'\b[A-Z]{2,4} \d{2}-\d{2}-\d{2}\b'  # Generic manual reference pattern
        ]
        
        # Combine ignore patterns into one
        ignore_regex = '|'.join(f'(?:{pattern})' for pattern in ignore_patterns)
        ignore_pattern = re.compile(ignore_regex)
        
        # Track unique issues
        unique_issues = []
        
        # Use _process_sentences helper
        for sentence, paragraph in self._process_sentences(doc, skip_empty=True, skip_headings=True):
            # First, identify and temporarily remove text that should be ignored
            working_sentence = sentence
            
            # Find all matches to ignore
            ignored_matches = list(ignore_pattern.finditer(sentence))
            
            # Replace ignored patterns with placeholders
            for match in reversed(ignored_matches):
                start, end = match.span()
                working_sentence = working_sentence[:start] + 'X' * (end - start) + working_sentence[end:]
            
            # Now check for date patterns in the modified sentence
            for pattern_config in date_patterns:
                matches = list(re.finditer(pattern_config.pattern, working_sentence))
                
                for match in matches:
                    # Get the original text from the match position
                    original_date = sentence[match.start():match.end()]
                    
                    # Create formatted issue with incorrect/correct format
                    formatted_issue = {
                        'incorrect': original_date,
                        'correct': 'Month Day, Year'
                    }
                    unique_issues.append(formatted_issue)

        return DocumentCheckResult(success=len(unique_issues) == 0, issues=unique_issues)

    @profile_performance
    def check_placeholders(self, doc: List[str]) -> DocumentCheckResult:
        """Check for placeholders that should be removed."""
        def process_placeholders(doc: List[str], patterns: List[PatternConfig]) -> DocumentCheckResult:
            tbd_placeholders = []
            to_be_determined_placeholders = []
            to_be_added_placeholders = []
            
            pattern_categories = {
                r'\bTBD\b': ('tbd', tbd_placeholders),
                r'\bTo be determined\b': ('to_be_determined', to_be_determined_placeholders),
                r'\bTo be added\b': ('to_be_added', to_be_added_placeholders)
            }

            # Use _process_sentences helper
            for sentence, paragraph in self._process_sentences(doc, skip_empty=True, skip_headings=True):
                for pattern_config in patterns:
                    compiled_pattern = re.compile(pattern_config.pattern, re.IGNORECASE)
                    
                    for pattern_key, (category_name, category_list) in pattern_categories.items():
                        if pattern_config.pattern == pattern_key:
                            matches = compiled_pattern.finditer(sentence)
                            for match in matches:
                                category_list.append({
                                    'placeholder': match.group().strip(),
                                    'sentence': sentence.strip(),
                                    'description': pattern_config.description
                                })

            # Compile issues
            issues = []
            if tbd_placeholders:
                issues.append({
                    'issue_type': 'tbd_placeholder',
                    'description': 'Remove TBD placeholder',
                    'occurrences': tbd_placeholders
                })
                
            if to_be_determined_placeholders:
                issues.append({
                    'issue_type': 'to_be_determined_placeholder',
                    'description': "Remove 'To be determined' placeholder",
                    'occurrences': to_be_determined_placeholders
                })
                
            if to_be_added_placeholders:
                issues.append({
                    'issue_type': 'to_be_added_placeholder',
                    'description': "Remove 'To be added' placeholder",
                    'occurrences': to_be_added_placeholders
                })

            details = {
                'total_placeholders': len(tbd_placeholders) + 
                                    len(to_be_determined_placeholders) + 
                                    len(to_be_added_placeholders),
                'placeholder_types': {
                    'TBD': len(tbd_placeholders),
                    'To be determined': len(to_be_determined_placeholders),
                    'To be added': len(to_be_added_placeholders)
                }
            }

            return DocumentCheckResult(success=len(issues) == 0, issues=issues, details=details)

        return self._process_patterns(doc, 'placeholders', process_placeholders)

    @profile_performance
    def _process_patterns(
        self,
        doc: List[str],
        pattern_category: str,
        process_func: Optional[Callable] = None
    ) -> DocumentCheckResult:
        """
        Process document text against patterns from a specific category.
        
        Args:
            doc: List of document paragraphs
            pattern_category: Category of patterns to check against
            process_func: Optional custom processing function
            
        Returns:
            DocumentCheckResult with processed issues
        """
        if not self.validate_input(doc):
            self.logger.error("Invalid document input for pattern check")
            return DocumentCheckResult(
                success=False, 
                issues=[{'error': 'Invalid document input'}]
            )

        # Get patterns from registry
        patterns = self.config_manager.pattern_registry.get(pattern_category, [])
        if not patterns:
            self.logger.warning(f"No patterns found for category: {pattern_category}")
            return DocumentCheckResult(
                success=True,
                issues=[],
                details={'message': f'No patterns defined for {pattern_category}'}
            )

        # Use custom processing function if provided
        if process_func:
            return process_func(doc, patterns)

        # Default processing with deduplication
        unique_issues = set()  # Using a set to track unique issues

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                for pattern_config in patterns:
                    matches = list(re.finditer(pattern_config.pattern, sentence))
                    if matches:
                        # Add each match as a tuple to ensure uniqueness
                        for match in matches:
                            unique_issues.add((
                                match.group(),  # The matched text
                                pattern_config.description,  # The issue description
                                pattern_config.replacement if hasattr(pattern_config, 'replacement') else None
                            ))

        # Convert unique issues back to the expected format
        formatted_issues = [
            {
                'incorrect': issue[0],
                'description': issue[1],
                'replacement': issue[2]
            }
            for issue in sorted(unique_issues)  # Sort for consistent output
        ]

        return DocumentCheckResult(success=len(formatted_issues) == 0, issues=formatted_issues)

    @profile_performance
    def check_paragraph_length(self, doc: List[str]) -> DocumentCheckResult:
        """
        Check for overly long paragraphs that may need to be split up.
        
        Args:
            doc (List[str]): List of document paragraphs
            
        Returns:
            DocumentCheckResult: Results of paragraph length check
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
            
        issues = []
        
        for paragraph in doc:
            if not paragraph.strip():  # Skip empty paragraphs
                continue
                
            # Count sentences (split on period, exclamation, question mark followed by space)
            sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
            # Count lines (split on newlines or when length exceeds ~80 characters)
            lines = []
            current_line = ""
            
            for word in paragraph.split():
                if len(current_line) + len(word) + 1 <= 80:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Check if paragraph exceeds either threshold
            if len(sentences) > 6 or len(lines) > 8:
                # Get first sentence for context
                first_sentence = sentences[0].strip()
                issues.append(f"Review the paragraph that starts with: \"{first_sentence}\"")
        
        return DocumentCheckResult(success=len(issues) == 0, issues=issues)
    
    @profile_performance
    def check_sentence_length(self, doc: List[str]) -> DocumentCheckResult:
        """
        Check for overly long sentences that may need to be split for clarity.
        
        Args:
            doc (List[str]): List of document paragraphs
            
        Returns:
            DocumentCheckResult: Results of sentence length check including:
                - success: Boolean indicating if all sentences are acceptable length
                - issues: List of dicts with long sentence details
                - details: Additional statistics about sentence lengths
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
            
        issues = []
        sentence_stats = {
            'total_sentences': 0,
            'long_sentences': 0,
            'max_length': 0,
            'avg_length': 0
        }
        
        # Skip patterns for technical content that might naturally be longer
        skip_patterns = [
            r'^(?:Note:|Warning:|Caution:)',  # Notes and warnings
            r'^\d+\.',  # Numbered lists
            r'^\([a-z]\)',  # Letter lists
            r'^\([0-9]\)',  # Number lists in parentheses
            r'^Table \d',  # Table captions
            r'^Figure \d',  # Figure captions
            r'(?:e\.g\.|i\.e\.|viz\.,)',  # Latin abbreviations often used in complex sentences
            r'\b(?:AC|AD|TSO|SFAR)\s+\d',  # Technical references
            r'\d+\s*(?:CFR|U\.S\.C\.)',  # Regulatory references
        ]
        skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)
        
        total_words = 0
        
        for paragraph in doc:
            if not paragraph.strip():
                continue
                
            # Skip if paragraph matches any skip patterns
            if skip_regex.search(paragraph):
                continue
                
            # Split into sentences while preserving punctuation
            sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Count words (splitting on whitespace)
                words = sentence.split()
                word_count = len(words)
                
                sentence_stats['total_sentences'] += 1
                total_words += word_count
                
                if word_count > sentence_stats['max_length']:
                    sentence_stats['max_length'] = word_count
                
                # Flag sentences over 35 words
                if word_count > 35:
                    sentence_stats['long_sentences'] += 1
                    issues.append({
                        'sentence': sentence,
                        'word_count': word_count
                    })
        
        # Calculate average sentence length
        if sentence_stats['total_sentences'] > 0:
            sentence_stats['avg_length'] = round(total_words / sentence_stats['total_sentences'], 1)
        
        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details=sentence_stats
        )
    
    @profile_performance
    def check_508_compliance(self, doc_path: str) -> DocumentCheckResult:
        """
        Perform Section 508 compliance checks focusing on image alt text and heading structure.
        """
        try:
            doc = Document(doc_path)
            issues = []
            images_with_alt = 0
            heading_structure = {}
            heading_issues = []  # Separate list for heading-specific issues

            # Image alt text check
            for shape in doc.inline_shapes:
                alt_text = None
                if hasattr(shape, '_inline') and hasattr(shape._inline, 'docPr'):
                    docPr = shape._inline.docPr
                    alt_text = docPr.get('descr') or docPr.get('title')

                if alt_text:
                    images_with_alt += 1
                else:
                    issues.append({
                        'category': 'image_alt_text',
                        'message': 'Image is missing descriptive alt text.',
                        'context': 'Ensure all images have descriptive alt text.'
                    })

            # Enhanced heading structure check
            headings = []
            
            for paragraph in doc.paragraphs:
                if paragraph.style.name.startswith('Heading'):
                    try:
                        level = int(paragraph.style.name.split()[-1])
                        text = paragraph.text.strip()
                        
                        if not text:
                            continue
                            
                        headings.append((text, level))
                        heading_structure[level] = heading_structure.get(level, 0) + 1
                        
                    except ValueError:
                        continue

            # Check heading hierarchy
            if headings:
                min_level = min(level for _, level in headings)
                
                if min_level > 1:
                    heading_issues.append({
                        'severity': 'error',
                        'type': 'missing_h1',
                        'message': 'Document should start with a Heading 1',
                        'context': f"First heading found is level {headings[0][1]}: '{headings[0][0]}'",
                        'recommendation': 'Add a Heading 1 at the start of the document'
                    })

                # Check for skipped levels
                previous_heading = None
                for text, level in headings:
                    if previous_heading:
                        prev_text, prev_level = previous_heading
                        
                        if level > prev_level + 1:
                            missing_levels = list(range(prev_level + 1, level))
                            heading_issues.append({
                                'severity': 'error',
                                'type': 'skipped_levels',
                                'message': f"Skipped heading level(s) {', '.join(map(str, missing_levels))} - Found H{level} '{text}' after H{prev_level} '{prev_text}'. Add H{prev_level + 1} before this section.",
                                # 'context': None,  # Removed since we combined it into message
                                # 'recommendation': None,  # Removed since we combined it into message
                                'missing_levels': missing_levels
                            })
                        elif level < prev_level and level != prev_level - 1:
                            heading_issues.append({
                                'severity': 'error',
                                'type': 'out_of_sequence',
                                'message': f"Out of sequence: H{level} '{text}' after H{prev_level} '{prev_text}'. Ensure heading levels follow a logical sequence.",
                                # 'context': None,  # Removed since we combined it into message
                                # 'recommendation': None,  # Removed since we combined it into message
                            })
                    
                    previous_heading = (text, level)

            # Combine all issues
            if heading_issues:
                issues.extend([{
                    'category': '508_compliance_heading_structure',
                    **issue
                } for issue in heading_issues])

            # Enhanced details with heading structure information
            details = {
                'total_images': len(doc.inline_shapes),
                'images_with_alt': images_with_alt,
                'heading_structure': {
                    'total_headings': len(headings),
                    'levels_found': dict(sorted(heading_structure.items())),
                    'hierarchy_depth': max(heading_structure.keys()) if heading_structure else 0,
                    'heading_sequence': [(text[:50] + '...' if len(text) > 50 else text, level) 
                                       for text, level in headings],
                    'issues_found': len(heading_issues)
                }
            }

            return DocumentCheckResult(
                success=len(issues) == 0,
                issues=issues,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Error during 508 compliance check: {str(e)}")
            return DocumentCheckResult(
                success=False,
                issues=[{
                    'category': 'error',
                    'message': f'Error performing 508 compliance check: {str(e)}'
                }]
            )

    def _format_compliance_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format compliance issues with clear, user-friendly descriptions."""
        formatted_issues = []
        
        # Group issues by type
        heading_issues = []
        alt_text_issues = []
        other_issues = []
        
        for issue in result.issues:
            if issue.get('category') == '508_compliance_heading_structure':
                heading_issues.append(issue)
            elif issue.get('category') == 'image_alt_text':
                alt_text_issues.append(issue)
            else:
                other_issues.append(issue)

        # Format heading structure issues
        if heading_issues:
            formatted_issues.append("\n**Heading Structure Issues:**")
            for issue in heading_issues:
                message = issue.get('message', '').strip()
                context = issue.get('context', '').strip()
                recommendation = issue.get('recommendation', '').strip()
                
                formatted_issues.append(f"\n• **Issue**: {message}")
                if context:
                    formatted_issues.append(f"  - **Context**: {context}")
                if recommendation:
                    formatted_issues.append(f"  - **Fix**: {recommendation}")

        # Format alt text issues
        if alt_text_issues:
            formatted_issues.append("\n**Image Accessibility Issues:**")
            formatted_issues.append("• Images found without descriptive alt text")
            formatted_issues.append("  - **Fix**: Add descriptive alt text to all images to ensure screen reader accessibility")

        # Format other issues
        if other_issues:
            formatted_issues.append("\n**Other Accessibility Issues:**")
            for issue in other_issues:
                formatted_issues.append(f"• {issue.get('message', 'Unknown issue')}")

        return formatted_issues

    @profile_performance
    def check_hyperlinks(self, doc: List[str]) -> DocumentCheckResult:
        """
        Enhanced hyperlink checker that identifies potentially broken URLs.
        
        Args:
            doc: List of document paragraphs.
            
        Returns:
            DocumentCheckResult with any potentially broken links.
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        issues = []
        checked_urls = set()
        
        # URL pattern - matches http/https URLs
        url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
        )
        
        # Helper function to check a single URL
        def check_url(url):
            try:
                response = requests.head(url, timeout=5, allow_redirects=True, headers={'User-Agent': 'CheckerTool/1.0'})
                if response.status_code >= 400:
                    return {
                        'url': url,
                        'message': f"Broken link: {url} (HTTP {response.status_code})"
                    }
            except requests.RequestException:
                return {
                    'url': url,
                    'message': f"Check the link or internet connection: {url} (connection error)"
                }
            return None

        # Extract and deduplicate URLs
        for paragraph in doc:
            urls = {match.group() for match in url_pattern.finditer(paragraph)}
            checked_urls.update(urls)
        
        # Concurrently check URLs
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_url, url): url for url in checked_urls}
            for future in as_completed(future_to_url):
                issue = future.result()
                if issue:
                    issues.append(issue)

        return DocumentCheckResult(
            success=len(issues) == 0,
            issues=issues,
            details={
                'total_urls_checked': len(checked_urls),
                'broken_urls': len(issues)
            }
        )

    def _load_valid_words(self) -> Set[str]:
        """
        Load valid English words from valid_words.txt file.
        
        Returns:
            Set[str]: Set of valid English words in lowercase
        """
        try:
            # Get the directory containing the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            words_file = os.path.join(current_dir, 'valid_words.txt')
            
            # Load words from file
            with open(words_file, 'r') as f:
                words = {line.strip().lower() for line in f if line.strip()}
                
            return words
            
        except Exception as e:
            self.logger.warning(f"Error loading word list: {e}")
            return set()  # Return empty set as fallback

class DocumentCheckResultsFormatter:
    
    def __init__(self):
        init()  # Initialize colorama
        
        # Enhanced issue categories with examples and specific fixes
        self.issue_categories = {
            'heading_title_check': {
                'title': 'Required Headings Check',
                'description': 'Verifies that your document includes all mandatory section headings, with requirements varying by document type. For example, long-template Advisory Circulars require headings like "Purpose." and "Applicability." with initial caps and periods, while Federal Register Notices use ALL CAPS headings like "SUMMARY" and "BACKGROUND" without periods. This check ensures both the presence of required headings and their correct capitalization format based on document type.',
                'solution': 'Add all required headings in the correct order using the correct capitalization format.',
                'example_fix': {
                    'before': 'Missing required heading "PURPOSE."',
                    'after': 'Added heading "PURPOSE." at the beginning of the document'
                }
            },
            'heading_title_period_check': {
                'title': 'Heading Period Format',
                'description': 'Examines heading punctuation to ensure compliance with FAA document formatting standards. Some FAA documents (like Advisory Circulars and Orders) require periods at the end of headings, while others (like Federal Register Notices) don\'t.',
                'solution': 'Format heading periods according to document type requirements.',
                'example_fix': {
                    'before': 'Purpose',
                    'after': 'Purpose.' # For ACs and Orders
                }
            },
            'table_figure_reference_check': {
                'title': 'Table and Figure References',
                'description': 'Analyzes how tables and figures are referenced within your document text. Capitalize references at the beginning of sentences (e.g., "Table 2-1 shows...") and use lowercase references within sentences (e.g., "...as shown in table 2-1").',
                'solution': 'Capitalize references at start of sentences, use lowercase within sentences.',
                'example_fix': {
                    'before': 'The DTR values are specified in Table 3-1 and Figure 3-2.',
                    'after': 'The DTR values are specified in table 3-1 and figure 3-2.'
                }
            },
            'acronym_check': {
                'title': 'Acronym Definition Issues',
                'description': 'Ensures every acronym is properly introduced with its full term at first use. The check identifies undefined acronyms while recognizing common exceptions (like U.S.) that don\'t require definition.',
                'solution': 'Define each acronym at its first use, e.g., "Federal Aviation Administration (FAA)".',
                'example_fix': {
                    'before': 'This order establishes general FAA organizational policies.',
                    'after': 'This order establishes general Federal Aviation Administration (FAA) organizational policies.'
                }
            },
            'acronym_usage_check': {
                'title': 'Unused Acronym Definitions',
                'description': 'Ensures that all acronyms defined in the document are actually used later. If an acronym is defined but never referenced, the definition should be removed to avoid confusion or unnecessary clutter.',
                'solution': 'Identify acronyms that are defined but not used later in the document and remove their definitions.',
                'example_fix': {
                    'before': 'Operators must comply with airworthiness directives (AD) to ensure aircraft safety and regulatory compliance.',
                    'after': 'Operators must comply with airworthiness directives to ensure aircraft safety and regulatory compliance.'
                }
            },
            'terminology_check': {
                'title': 'Incorrect Terminology',
                'description': 'Evaluates document text against the various style manuals and orders to identify non-compliant terminology, ambiguous references, and outdated phrases. This includes checking for prohibited relative references (like "above" or "below"), proper legal terminology (like "must" instead of "shall"), and consistent formatting of regulatory citations.',
                'solution': 'Use explicit references to paragraphs, sections, tables, and figures.',
                'example_fix': {
                    'before': 'Operators shall comply with ADs to ensure aircraft safety and regulatory compliance',
                    'after': 'Operators must comply with ADs to ensure aircraft safety and regulatory compliance.'
                }
            },
            'section_symbol_usage_check': {
                'title': 'Section Symbol (§) Format Issues',
                'description': 'Examines the usage of section symbols (§) throughout your document. This includes verifying proper symbol placement in regulatory references, ensuring sections aren\'t started with the symbol, checking consistency in multiple-section citations, and validating proper CFR citations. For ACs, see FAA Order 1320.46.',
                'solution': 'Format section symbols correctly and never start sentences with them.',
                'example_fix': {
                    'before': '§ 23.3 establishes design criteria.',
                    'after': 'Section 23.3 establishes design criteria.'
                }
            },
            'double_period_check': {
                'title': 'Multiple Period Issues',
                'description': 'Examines sentences for accidental double periods that often occur during document editing and revision. While double periods are sometimes found in ellipses (...) or web addresses, they should never appear at the end of standard sentences in FAA documentation.',
                'solution': 'Remove multiple periods that end sentences.',
                'example_fix': {
                    'before': 'The following ACs are related to the guidance in this document..',
                    'after': 'The following ACs are related to the guidance in this document.'
                }
            },
            'spacing_check': {
                'title': 'Spacing Issues',
                'description': 'Analyzes document spacing patterns to ensure compliance with FAA formatting standards. This includes checking for proper spacing around regulatory references (like "AC 25-1" not "AC25-1"), section symbols (§ 25.1), paragraph references, and multiple spaces between words.',
                'solution': 'Fix spacing issues: remove any missing spaces, double spaces, or inadvertent tabs.',
                'example_fix': {
                    'before': 'AC25.25 states that  SFAR88 and §25.981 require...',
                    'after': 'AC 25.25 states that SFAR 88 and § 25.981 require...'
                }
            },
            'date_formats_check': {
                'title': 'Date Format Issues',
                'description': 'Examines all date references in your document. The check automatically excludes technical reference numbers that may look like dates to ensure accurate validation of true date references. Note, though, there might be instances in the heading of the document where the date is formatted as "MM/DD/YYYY", which is acceptable. This applies mostly to date formats within the document body.',
                'solution': 'Use the format "Month Day, Year" where appropriate.',
                'example_fix': {
                    'before': 'This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated 7/25/2006.',
                    'after': 'This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated July 25, 2006.'
                }
            },
            'placeholders_check': {
                'title': 'Placeholder Content',
                'description': 'Identifies incomplete content and temporary placeholders that must be finalized before document publication. This includes common placeholder text (like "TBD" or "To be determined"), draft markers, and incomplete sections.',
                'solution': 'Replace all placeholder content with actual content.',
                'example_fix': {
                    'before': 'Pilots must submit the [Insert text] form to the FAA for approval.',
                    'after': 'Pilots must submit the Report of Eye Evaluation form 8500-7 to the FAA for approval.'
                }
            },
            'parentheses_check': {
                'title': 'Parentheses Balance Check',
                'description': 'Ensures that all parentheses in the document are properly paired with matching opening and closing characters.',
                'solution': 'Add missing opening or closing parentheses where indicated.',
                'example_fix': {
                    'before': 'The system (as defined in AC 25-11B performs...',
                    'after': 'The system (as defined in AC 25-11B) performs...'
                }
            },
            'paragraph_length_check': {
                'title': 'Paragraph Length Issues',
                'description': 'Flags paragraphs exceeding 6 sentences or 8 lines to enhance readability and clarity. While concise paragraphs are encouraged, with each focusing on a single idea or related points, exceeding these limits doesn\'t necessarily indicate a problem. Some content may appropriately extend beyond 8 lines, especially if it includes necessary details. Boilerplate language or template text exceeding these limits is not subject to modification or division.',
                'solution': 'Where possible, split long paragraphs into smaller sections, ensuring each focuses on one primary idea. If restructuring is not feasible or the content is boilerplate text, no changes are needed.',
                'example_fix': {
                    'before': 'A very long paragraph covering multiple topics and spanning many lines...',
                    'after': 'Multiple shorter paragraphs or restructured paragraphs, each focused on a single topic or related points.'
                }
            },
            'sentence_length_check': {
                'title': 'Sentence Length Issues',
                'description': 'Analyzes sentence length to ensure readability. While the ideal length varies with content complexity, sentences over 35 words often become difficult to follow. Technical content, regulatory references, notes, warnings, and list items are excluded from this check.',
                'solution': 'Break long sentences into smaller ones where possible, focusing on one main point per sentence. Consider using lists for complex items.',
                'example_fix': {
                    'before': 'The operator must ensure that all required maintenance procedures are performed in accordance with the manufacturer\'s specifications and that proper documentation is maintained throughout the entire process to demonstrate compliance with regulatory requirements.',
                    'after': 'The operator must ensure all required maintenance procedures are performed according to manufacturer specifications. Additionally, proper documentation must be maintained to demonstrate regulatory compliance.'
                }
            },
            'document_title_check': {
                'title': 'Referenced Document Title Format Issues',
                'description': 'Checks document title formatting based on document type. Advisory Circulars require italics without quotes, while all other document types require quotes without italics.',
                'solution': 'Format document titles according to document type: use italics for Advisory Circulars, quotes for all other document types.',
                'example_fix': {
                    'before': 'See AC 25.1309-1B, System Design and Analysis, for information on X.',
                    'after': 'See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X.'
                }
            },
            '508_compliance_check': {
                'title': 'Section 508 Compliance Issues',
                'description': 'Checks document accessibility features required by Section 508 standards: Image alt text for screen readers and heading structure issues (missing heading 1, skipped heading levels, and out of sequence headings).',
                'solution': 'Address each accessibility issue: add image alt text for screen readers and fix heading structure.',
                'example_fix': {
                    'before': [
                        'Image without alt text',
                        'Heading sequence: H1 → H2 → H4 (skipped H3)'
                    ],
                    'after': [
                        'Image with descriptive alt text',
                        'Proper heading sequence: H1 → H2 → H3 → H4'
                    ]
                }
            },
            'hyperlink_check': {
                'title': 'Hyperlink Issues',
                'description': 'Checks for potentially broken or inaccessible URLs in the document. This includes checking response codes and connection issues.',
                'solution': 'Verify each flagged URL is correct and accessible.',
                'example_fix': {
                    'before': 'See https://broken-link.example.com for more details.',
                    'after': 'See https://www.faa.gov for more details.'
                }
            }
        }

        # Add these two helper methods here, after __init__ and before other methods
    def _format_colored_text(self, text: str, color: str) -> str:
        """Helper method to format colored text with reset.
        
        Args:
            text: The text to be colored
            color: The color to apply (from colorama.Fore)
            
        Returns:
            str: The colored text with reset styling
        """
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
            f"    ✓ Correct: {example_fix['after']}"
        ]
    
    def _format_heading_issues(self, result: DocumentCheckResult, doc_type: str) -> List[str]:
        """Format heading check issues consistently."""
        output = []
        
        for issue in result.issues:
            if issue.get('type') == 'missing_headings':
                missing = sorted(issue['missing'])
                output.append(f"\n  Missing Required Headings for {doc_type}:")
                for heading in missing:
                    output.append(f"    • {heading}")
            elif issue.get('type') == 'unexpected_headings':
                unexpected = sorted(issue['unexpected'])
                output.append(f"\n  Unexpected Headings Found:")
                for heading in unexpected:
                    output.append(f"    • {heading}")
        
        return output

    def _format_period_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format period check issues consistently."""
        output = []
        
        if result.issues:
            output.append(f"\n  Heading Period Format Issues:")
            for issue in result.issues:
                if 'message' in issue:
                    output.append(f"    • {issue['message']}")
        
        return output

    def _format_caption_issues(self, issues: List[Dict], doc_type: str) -> List[str]:
        """Format caption check issues with clear replacement instructions."""
        formatted_issues = []
        for issue in issues:
            if 'incorrect_caption' in issue:
                caption_parts = issue['incorrect_caption'].split()
                if len(caption_parts) >= 2:
                    caption_type = caption_parts[0]  # "Table" or "Figure"
                    number = caption_parts[1]
                    
                    # Determine correct format based on document type
                    if doc_type in ["Advisory Circular", "Order"]:
                        if '-' not in number:
                            correct_format = f"{caption_type} {number}-1"
                    else:
                        if '-' in number:
                            correct_format = f"{caption_type} {number.split('-')[0]}"
                        else:
                            correct_format = issue['incorrect_caption']

                    formatted_issues.append(
                        f"    • Replace '{issue['incorrect_caption']}' with '{correct_format}'"
                    )

        return formatted_issues

    def _format_reference_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format reference-related issues with clear replacement instructions."""
        output = []
        
        if result.issues:
            for issue in result.issues:
                if 'reference' in issue and 'correct_form' in issue:
                    output.append(f"    • Replace '{issue['reference']}' with '{issue['correct_form']}'")

        return output

    def _format_standard_issue(self, issue: Dict[str, Any]) -> str:
        """Format standard issues consistently."""
        if isinstance(issue, str):
            return f"    • {issue}"
        
        if 'incorrect' in issue and 'correct' in issue:
            return f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"
        
        if 'incorrect_term' in issue and 'correct_term' in issue:
            return f"    • Replace '{issue['incorrect_term']}' with '{issue['correct_term']}'"
        
        if 'sentence' in issue and 'word_count' in issue:  # For sentence length check
            return f"    • Review this sentence: \"{issue['sentence']}\""
        
        if 'sentence' in issue:
            return f"    • {issue['sentence']}"
        
        if 'description' in issue:
            return f"    • {issue['description']}"
        
        if 'type' in issue and issue['type'] == 'long_paragraph':
            return f"    • {issue['message']}"
        
        # Fallback for other issue formats
        return f"    • {str(issue)}"

    def _format_unused_acronym_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format unused acronym issues with a simple, clear message.
        
        Args:
            result: DocumentCheckResult containing acronym issues
            
        Returns:
            List[str]: Formatted list of unused acronym issues
        """
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                if isinstance(issue, dict) and 'acronym' in issue:
                    formatted_issues.append(f"    • Acronym '{issue['acronym']}' was defined but never used.")
                elif isinstance(issue, str):
                    # Handle case where issue might be just the acronym
                    formatted_issues.append(f"    • Acronym '{issue}' was defined but never used.")
    
        return formatted_issues

    def _format_parentheses_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format parentheses issues with clear instructions for fixing."""
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                formatted_issues.append(f"    • {issue['message']}")
        
        return formatted_issues

    def _format_section_symbol_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format section symbol issues with clear replacement instructions."""
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                if 'incorrect' in issue and 'correct' in issue:
                    if issue.get('is_sentence_start'):
                        formatted_issues.append(
                            f"    • Do not begin sentences with the section symbol. "
                            f"Replace '{issue['incorrect']}' with '{issue['correct']}' at the start of the sentence"
                        )
                    else:
                        formatted_issues.append(
                            f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'"
                        )
        
        return formatted_issues

    def _format_paragraph_length_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format paragraph length issues with clear instructions for fixing.
        
        Args:
            result: DocumentCheckResult containing paragraph length issues
            
        Returns:
            List[str]: Formatted list of paragraph length issues
        """
        formatted_issues = []
        
        if result.issues:
            for issue in result.issues:
                if isinstance(issue, str):
                    formatted_issues.append(f"    • {issue}")
                elif isinstance(issue, dict) and 'message' in issue:
                    formatted_issues.append(f"    • {issue['message']}")
                else:
                    # Fallback for unexpected issue format
                    formatted_issues.append(f"    • Review paragraph for length issues: {str(issue)}")
        
        return formatted_issues

    def format_results(self, results: Dict[str, Any], doc_type: str) -> str:
        """
        Format check results into a detailed, user-friendly report.
        
        Args:
            results: Dictionary of check results
            doc_type: Type of document being checked
            
        Returns:
            str: Formatted report with consistent styling
        """
        # Determine caption format based on document type
        if doc_type in ["Advisory Circular", "Order"]:
            table_format = {
                'title': 'Table Caption Format Issues',
                'description': 'Analyzes table captions to ensure they follow the FAA\'s dual-numbering system, where tables must be numbered according to their chapter or appendix location (X-Y format). The first number (X) indicates the chapter number, while the second number (Y) provides sequential numbering within that chapter. For more information, see FAA Order 1320.46.',
                'solution': 'Use the format "Table X-Y" where X is the chapter or appendix number and Y is the sequence number',
                'example_fix': {
                    'before': 'Table 5. | Table A.',
                    'after': 'Table 5-1. | Table A-1.'
                }
            }
            figure_format = {
                'title': 'Figure Caption Format Issues',
                'description': 'Analyzes figure captions to ensure they follow the FAA\'s dual-numbering system, where figures must be numbered according to their chapter or appendix location (X-Y format). The first number (X) indicates the chapter number, while the second number (Y) provides sequential numbering within that chapter. For more information, see FAA Order 1320.46.',
                'solution': 'Use the format "Figure X-Y" where X is the chapter or appendix number and Y is the sequence number',
                'example_fix': {
                    'before': 'Figure 5. | Figure A.',
                    'after': 'Figure 5-1. | Figure A-1.'
                }
            }
        else:
            table_format = {
                'title': 'Table Caption Format Issues',
                'description': f'Analyzes table captions to ensure they follow the FAA\'s sequential numbering system for {doc_type}s. Tables must be numbered consecutively throughout the document using a single number format.',
                'solution': 'Use the format "Table X" where X is a sequential number',
                'example_fix': {
                    'before': 'Table 5-1. | Table A-1',
                    'after': 'Table 5. | Table 1.'
                }
            }
            figure_format = {
                'title': 'Figure Caption Format Issues',
                'description': f'Analyzes figure captions to ensure they follow the FAA\'s sequential numbering system for {doc_type}s. Figures must be numbered consecutively throughout the document using a single number format.',
                'solution': 'Use the format "Figure X" where X is a sequential number',
                'example_fix': {
                    'before': 'Figure 5-1. | Figure A-1.',
                    'after': 'Figure 5. | Figure 3.'
                }
            }

        # Update the issue categories with the correct format
        self.issue_categories['caption_check_table'] = table_format
        self.issue_categories['caption_check_figure'] = figure_format

        # Define formatting rules for different document types
        formatting_rules = {
            "italics_only": {
                "types": ["Advisory Circular"],
                "italics": True, 
                "quotes": False,
                "description": "For Advisory Circulars, referenced document titles should be italicized but not quoted. For more information, see FAA Order 1320.46.",
                "example": "See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X."
            },
            "quotes_only": {
                "types": [
                    "Airworthiness Criteria", "Deviation Memo", "Exemption", 
                    "Federal Register Notice", "Order", "Policy Statement", "Rule", 
                    "Special Condition", "Technical Standard Order", "Other"
                ],
                "italics": False, 
                "quotes": True,
                "description": "For this document type, referenced document titles should be in quotes without italics.",
                "example": 'See AC 25.1309-1B, "System Design and Analysis," for information on X.'
            }
        }

        # Find the formatting group for the current document type
        format_group = None
        for group, rules in formatting_rules.items():
            if doc_type in rules["types"]:
                format_group = rules
                break

        # Use quotes_only as default if document type not found
        if not format_group:
            format_group = formatting_rules["quotes_only"]

        # Update document title check category based on document type
        if doc_type == "Advisory Circular":
            self.issue_categories['document_title_check'] = {
                'title': 'Referenced Document Title Format Issues',
                'description': 'For Advisory Circulars, all referenced document titles must be italicized.',
                'solution': 'Format document titles using italics for Advisory Circulars.',
                'example_fix': {
                    'before': 'See AC 25.1309-1B, System Design and Analysis, for information on X.',
                    'after': 'See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X.'
                }
            }
        else:
            self.issue_categories['document_title_check'] = {
                'title': 'Referenced Document Title Format Issues',
                'description': f'For {doc_type}s, all referenced document titles must be enclosed in quotation marks.',
                'solution': 'Format document titles using quotation marks.',
                'example_fix': {
                    'before': 'See AC 25.1309-1B, System Design and Analysis, for information on X.',
                    'after': 'See AC 25.1309-1B, "System Design and Analysis," for information on X.'
                }
            }
        
        output = []
        
        self.issue_categories['acronym_usage_check'] = {
            'title': 'Unused Acronym Definitions',
            'description': 'Ensures that all acronyms defined in the document are actually used later. If an acronym is defined but never referenced, the definition should be removed to avoid confusion or unnecessary clutter.',
            'solution': 'Identify acronyms that are defined but not used later in the document and remove their definitions.',
            'example_fix': {
                'before': 'Operators must comply with airworthiness directives (AD) to ensure aircraft safety and regulatory compliance.',
                'after': 'Operators must comply with airworthiness directives to ensure aircraft safety and regulatory compliance.'
            }
        }

        output = []
        
        # Header
        output.append(f"\n{Fore.CYAN}{'='*80}")
        output.append(f"Document Check Results Summary")
        output.append(f"{'='*80}{Style.RESET_ALL}\n")
        
        # Count total issues
        total_issues = sum(1 for r in results.values() if not r.success)
        if total_issues == 0:
            output.append(f"{self._format_colored_text('✓ All checks passed successfully!', Fore.GREEN)}\n")
            return '\n'.join(output)
        
        output.append(f"{Fore.YELLOW}Found {total_issues} categories of issues that need attention:{Style.RESET_ALL}\n")
        
        # Process all check results consistently
        for check_name, result in results.items():
            if not result.success and check_name in self.issue_categories:
                category = self.issue_categories[check_name]
                
                output.append("\n")
                output.append(self._format_colored_text(f"■ {category['title']}", Fore.YELLOW))
                output.append(f"  {category['description']}")
                output.append(f"  {self._format_colored_text('How to fix: ' + category['solution'], Fore.GREEN)}")
                        
                output.append(f"\n  {self._format_colored_text('Example Fix:', Fore.CYAN)}")
                output.extend(self._format_example(category['example_fix']))
                output.append("")
                
                output.append(f"  {self._format_colored_text('Issues found in your document:', Fore.CYAN)}")
                
                # Special handling for date format issues
                if check_name == 'date_formats_check':
                    for issue in result.issues:
                        output.append(f"    • Replace '{issue['incorrect']}' with '{issue['correct']}'")
                # Handle other check types
                elif check_name == 'heading_title_check':
                    output.extend(self._format_heading_issues(result, doc_type))
                elif check_name == 'heading_title_period_check':
                    output.extend(self._format_period_issues(result))
                elif check_name == 'table_figure_reference_check':
                    output.extend(self._format_reference_issues(result))
                elif check_name in ['caption_check_table', 'caption_check_figure']:
                    output.extend(self._format_caption_issues(result.issues, doc_type))
                elif check_name == 'acronym_usage_check':
                    output.extend(self._format_unused_acronym_issues(result))
                elif check_name == 'section_symbol_usage_check':
                    output.extend(self._format_section_symbol_issues(result))
                elif check_name == 'parentheses_check':
                    output.extend(self._format_parentheses_issues(result))
                elif check_name == '508_compliance_check':
                    if not result.success:
                        # Handle heading structure issues
                        heading_issues = [i for i in result.issues 
                                        if i.get('category') == '508_compliance_heading_structure']
                        if heading_issues:
                            output.append("\n  Heading Structure Issues:")
                            for issue in heading_issues:
                                output.append(f"    • {issue['message']}")
                                if 'context' in issue:
                                    output.append(f"      Context: {issue['context']}")
                                if 'recommendation' in issue:
                                    output.append(f"      Recommendation: {issue['recommendation']}")
                        
                        # Handle alt text issues
                        alt_text_issues = [i for i in result.issues 
                                         if i.get('category') == 'image_alt_text']
                        if alt_text_issues:
                            output.append("\n  Image Accessibility Issues:")
                            output.append("    • Confirm that all images in your document have descriptive alt text.")
                            for issue in alt_text_issues:
                                if 'context' in issue:
                                    output.append(f"      {issue['context']}")
                elif check_name == 'hyperlink_check':
                    for issue in result.issues:
                        output.append(f"    • {issue['message']}")
                        if 'status_code' in issue:
                            output.append(f"      (HTTP Status: {issue['status_code']})")
                        elif 'error' in issue:
                            output.append(f"      (Error: {issue['error']})")
                else:
                    formatted_issues = [self._format_standard_issue(issue) for issue in result.issues[:15]]
                    output.extend(formatted_issues)
                    
                    if len(result.issues) > 10:
                        output.append(f"\n    ... and {len(result.issues) - 15} more similar issues.")
        
        return '\n'.join(output)

    def save_report(self, results: Dict[str, Any], filepath: str, doc_type: str) -> None:
        """Save the formatted results to a file with proper formatting."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Create a report without color codes
                report = self.format_results(results, doc_type)
                
                # Strip color codes
                for color in [Fore.CYAN, Fore.GREEN, Fore.YELLOW, Fore.RED, Style.RESET_ALL]:
                    report = report.replace(str(color), '')
                
                # Convert markdown-style italics to alternative formatting for plain text
                report = report.replace('*', '_')
                
                f.write(report)
        except Exception as e:
            print(f"Error saving report: {e}")
    
def format_markdown_results(results: Dict[str, DocumentCheckResult], doc_type: str) -> str:
    """Format check results into a Markdown string for Gradio display."""
    output = []
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output.extend([
        f"# Document Check Results - {current_time}",
        f"## Document Type: {doc_type}",
        "---\n"
    ])

    total_issues = sum(1 for r in results.values() if not r.success)
    
    if total_issues == 0:
        output.append("✅ **All checks passed successfully!**\n")
        return "\n".join(output)
    
    output.append(f"❗ Found issues in {total_issues} check categories\n")

    check_categories = {
        'heading_title_check': {'title': '📋 Required Headings', 'priority': 1},
        'heading_title_period_check': {'title': '🔍 Heading Period Usage', 'priority': 1},
        'terminology_check': {'title': '📖 Terminology Usage', 'priority': 1},
        'acronym_check': {'title': '📝 Acronym Definitions', 'priority': 1},
        'acronym_usage_check': {'title': '📎 Acronym Usage', 'priority': 1},
        'section_symbol_usage_check': {'title': '§ Section Symbol Usage', 'priority': 2},
        'date_formats_check': {'title': '📅 Date Formats', 'priority': 2},
        'placeholders_check': {'title': '🚩 Placeholder Content', 'priority': 2},
        'document_title_check': {'title': '📑 Document Title Format', 'priority': 2},
        'caption_check_table': {'title': '📊 Table Captions', 'priority': 3},
        'caption_check_figure': {'title': '🖼️ Figure Captions', 'priority': 3},
        'table_figure_reference_check': {'title': '🔗 Table/Figure References', 'priority': 3},
        'parentheses_check': {'title': '🔗 Parentheses Usage', 'priority': 4},
        'double_period_check': {'title': '⚡ Double Periods', 'priority': 4},
        'spacing_check': {'title': '⌨️ Spacing Issues', 'priority': 4},
        'paragraph_length_check': {'title': '📏 Paragraph Length', 'priority': 5},
        'sentence_length_check': {'title': '📏 Sentence Length', 'priority': 5}
    }

    sorted_checks = sorted(
        [(name, result) for name, result in results.items()],
        key=lambda x: check_categories.get(x[0], {'priority': 999})['priority']
    )

    for check_name, result in sorted_checks:
        if not result.success:
            category = check_categories.get(check_name, {'title': check_name.replace('_', ' ').title()})
            
            output.append(f"### {category['title']}")
            
            if isinstance(result.issues, list):
                for issue in result.issues[:5]:
                    if isinstance(issue, dict):
                        for key, value in issue.items():
                            if isinstance(value, list):
                                output.extend([f"- {item}" for item in value])
                            else:
                                output.append(f"- {key}: {value}")
                    else:
                        output.append(f"- {issue}")
                
                if len(result.issues) > 5:
                    output.append(f"\n*...and {len(result.issues) - 5} more similar issues*")
            
            output.append("")

    return "\n".join(output)

def create_interface():
    """Create and configure the Gradio interface."""
    
    document_types = [
        "Advisory Circular",
        "Airworthiness Criteria",
        "Deviation Memo",
        "Exemption",
        "Federal Register Notice",
        "Order",
        "Policy Statement",
        "Rule",
        "Special Condition",
        "Technical Standard Order",
        "Other"
    ]
    
    template_types = ["Short AC template AC", "Long AC template AC"]

    def format_results_as_html(text_results):
        """Convert the text results into styled HTML."""
        if not text_results:
            return """
                <div class="p-4 text-gray-600">
                    Results will appear here after processing...
                </div>
            """
        
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text_results = ansi_escape.sub('', text_results)
        
        # Split into sections while preserving the header
        sections = text_results.split('■')
        header = sections[0].strip()
        issues = sections[1:]
        
        # Extract the number of issues from the header text
        issues_count_match = re.search(r'Found (\d+) categories', header)
        issues_count = issues_count_match.group(1) if issues_count_match else len(issues)
        
        # Format header with title
        header_html = f"""
            <div class="max-w-4xl mx-auto p-4 bg-white rounded-lg shadow-sm mb-6">
                <h1 class="text-2xl font-bold mb-4">Document Check Results Summary</h1>
                <div class="text-lg text-amber-600">
                    Found {issues_count} categories of issues that need attention.
                </div>
            </div>
        """
        
        # Format each issue section
        issues_html = ""
        for section in issues:
            if not section.strip():
                continue
                
            parts = section.strip().split('\n', 1)
            if len(parts) < 2:
                continue
                
            title = parts[0].strip()
            content = parts[1].strip()
            
            # Extract description and solution
            description_parts = content.split('How to fix:', 1)
            description = description_parts[0].strip()
            solution = description_parts[1].split('Example Fix:', 1)[0].strip() if len(description_parts) > 1 else ""
            
            # Extract examples and issues
            examples_match = re.search(r'Example Fix:\s*❌[^✓]+✓[^•]+', content, re.MULTILINE | re.DOTALL)
            examples_html = ""
            if examples_match:
                examples_text = examples_match.group(0)
                incorrect = re.search(r'❌\s*Incorrect:\s*([^✓]+)', examples_text)
                correct = re.search(r'✓\s*Correct:\s*([^•\n]+)', examples_text)
                
                if incorrect and correct:
                    examples_html = f"""
                        <div class="mb-4">
                            <h3 class="font-medium text-gray-800 mb-2">Example Fix:</h3>
                            <div class="space-y-2 ml-4">
                                <div class="text-red-600">
                                    ❌ Incorrect:
                                </div>
                                <div class="text-red-600 ml-8">
                                    {incorrect.group(1).strip()}
                                </div>
                                <div class="text-green-600 mt-2">
                                    ✓ Correct:
                                </div>
                                <div class="text-green-600 ml-8">
                                    {correct.group(1).strip()}
                                </div>
                            </div>
                        </div>
                    """
            
            # Extract issues
            issues_match = re.findall(r'•\s*(.*?)(?=•|\Z)', content, re.DOTALL)
            issues_html_section = ""
            if issues_match:
                issues_html_section = """
                    <div class="mt-4">
                        <h3 class="font-medium text-gray-800 mb-2">Issues found in your document:</h3>
                        <ul class="list-none space-y-2">
                """
                for issue in issues_match[:7]: 
                    # Remove any existing bullet points from the issue text
                    clean_issue = issue.strip().lstrip('•').strip()
                    issues_html_section += f"""
                        <li class="text-gray-600 ml-4">• {clean_issue}</li>
                    """
                if len(issues_match) > 7: 
                    issues_html_section += f"""
                        <li class="text-gray-500 italic ml-4">... and {len(issues_match) - 7} more similar issues.</li>
                    """
                issues_html_section += "</ul></div>"
            
            # Combine the section
            issues_html += f"""
                <div class="bg-white rounded-lg shadow-sm mb-6 overflow-hidden">
                    <div class="bg-gray-50 px-6 py-4 border-b">
                        <h2 class="text-lg font-semibold text-gray-800">{title}</h2>
                    </div>
                    
                    <div class="px-6 py-4">
                        <div class="text-gray-600 mb-4">
                            {description}
                        </div>
                        
                        <div class="bg-green-50 rounded p-4 mb-4">
                            <div class="text-green-800">
                                <span class="font-medium">How to fix: </span>
                                {solution}
                            </div>
                        </div>
                        
                        {examples_html}
                        {issues_html_section}
                    </div>
                </div>
            """
        
        # Format summary section
        summary_html = f"""
            <div class="bg-white rounded-lg shadow-sm mb-6 overflow-hidden">
                <div class="bg-gray-50 px-6 py-4 border-b">
                    <h2 class="text-lg font-semibold text-gray-800">📋 Next Steps</h2>
                </div>
                <div class="px-6 py-4">
                    <div class="space-y-4">
                        <div>
                            <h3 class="font-medium text-gray-800 mb-2">1. Review and Address Issues:</h3>
                            <ul class="list-none space-y-2 ml-4">
                                <li class="text-gray-600">• Review each issue category systematically</li>
                                <li class="text-gray-600">• Make corrections using the provided examples as guides</li>
                                <li class="text-gray-600">• Re-run document check to verify all issues are resolved</li>
                            </ul>
                        </div>
                        
                        <div>
                            <h3 class="font-medium text-gray-800 mb-2">2. Best Practices:</h3>
                            <ul class="list-none space-y-2 ml-4">
                                <li class="text-gray-600">• Use search/replace for consistent fixes</li>
                                <li class="text-gray-600">• Update your document template to prevent future issues</li>
                                <li class="text-gray-600">• Keep the style manuals and Orders handy while making corrections</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        """

        # Final HTML with styling
        full_html = f"""
        <div class="mx-auto p-4" style="font-family: system-ui, -apple-system, sans-serif;">
            <style>
                .text-2xl {{ font-size: 1.5rem; line-height: 2rem; }}
                .text-lg {{ font-size: 1.125rem; }}
                .font-bold {{ font-weight: 700; }}
                .font-semibold {{ font-weight: 600; }}
                .font-medium {{ font-weight: 500; }}
                .text-gray-800 {{ color: #1f2937; }}
                .text-gray-600 {{ color: #4b5563; }}
                .text-gray-500 {{ color: #6b7280; }}
                .text-green-600 {{ color: #059669; }}
                .text-green-800 {{ color: #065f46; }}
                .text-red-600 {{ color: #dc2626; }}
                .text-amber-600 {{ color: #d97706; }}
                .bg-white {{ background-color: #ffffff; }}
                .bg-gray-50 {{ background-color: #f9fafb; }}
                .bg-green-50 {{ background-color: #ecfdf5; }}
                .rounded-lg {{ border-radius: 0.5rem; }}
                .shadow-sm {{ box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }}
                .mb-6 {{ margin-bottom: 1.5rem; }}
                .mb-4 {{ margin-bottom: 1rem; }}
                .mb-2 {{ margin-bottom: 0.5rem; }}
                .ml-4 {{ margin-left: 1rem; }}
                .ml-8 {{ margin-left: 2rem; }}
                .mt-2 {{ margin-top: 0.5rem; }}
                .mt-4 {{ margin-top: 1rem; }}
                .p-4 {{ padding: 1rem; }}
                .px-6 {{ padding-left: 1.5rem; padding-right: 1.5rem; }}
                .py-4 {{ padding-top: 1rem; padding-bottom: 1rem; }}
                .space-y-2 > * + * {{ margin-top: 0.5rem; }}
                .italic {{ font-style: italic; }}
                .border-b {{ border-bottom: 1px solid #e5e7eb; }}
                .overflow-hidden {{ overflow: hidden; }}
                .list-none {{ list-style-type: none; }}
                .space-y-4 > * + * {{ margin-top: 1rem; }}
                .text-red-600 {{ color: #dc2626; }}
                .text-amber-600 {{ color: #d97706; }}
                .text-green-600 {{ color: #059669; }}
            </style>
            {header_html}
            {issues_html}
            {summary_html}
        </div>
        """
        
        return full_html

    # Define the function to read the README content
    def get_readme_content():
        readme_path = "README.md"
        try:
            with open(readme_path, "r", encoding="utf-8") as file:
                readme_content = file.read()
            return readme_content
        except Exception as e:
            logging.error(f"Error reading README.md: {str(e)}")
            return "Error loading help content."
    
    with gr.Blocks() as demo:
        with gr.Tabs():
            with gr.Tab("Document Checker"):
                gr.Markdown(
                    """
                # 📑 FAA Document Checker Tool

                This tool performs multiple **validation checks** on Word documents to ensure compliance with U.S. federal documentation standards. See the About tab for more information.

                ## How to Use

                1. Upload your Word document (`.docx` format).
                2. Select the document type.
                3. Click **Check Document**.

                > **Note:** Please ensure your document is clean (no track changes or comments).
                """
                )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(
                            label="📎 Upload Word Document (.docx)",
                            file_types=[".docx"],
                            type="binary"
                        )
                        
                        doc_type = gr.Dropdown(
                            choices=document_types,
                            label="📋 Document Type",
                            value="Advisory Circular",
                            info="Select the type of document you're checking"
                        )
                        
                        template_type = gr.Radio(
                            choices=template_types,
                            label="📑 Template Type",
                            visible=False,
                            info="Only applicable for Advisory Circulars"
                        )
                        
                        submit_btn = gr.Button(
                            "🔍 Check Document",
                            variant="primary"
                        )
                    
                    with gr.Column(scale=2):
                        results = gr.HTML()
                
                # Download button
                # with gr.Row():
                #     download_btn = gr.Button(
                #         "⬇️ Download Results as PDF",
                #         variant="secondary",
                #         visible=False
                #     )
                #
                #     pdf_file = gr.File(
                #         label="Download PDF",
                #         visible=False,
                #         interactive=False,
                #         file_types=[".pdf"]
                #     )
                
                def process_and_format(file_obj, doc_type_value, template_type_value):
                    """Process document and format results as HTML."""
                    try:
                        # Get text results from your original process_document function
                        checker = FAADocumentChecker()
                        if isinstance(file_obj, bytes):
                            file_obj = io.BytesIO(file_obj)
                        results_data = checker.run_all_checks(file_obj, doc_type_value, template_type_value)
                        
                        # Format results using DocumentCheckResultsFormatter
                        formatter = DocumentCheckResultsFormatter()
                        text_results = formatter.format_results(results_data, doc_type_value)

                        # Convert to HTML
                        html_results = format_results_as_html(text_results)

                        # Return only the HTML results
                        return html_results
                        
                    except Exception as e:
                        logging.error(f"Error processing document: {str(e)}")
                        traceback.print_exc()
                        error_html = f"""
                            <div style="color: red; padding: 1rem;">
                                ❌ Error processing document: {str(e)}
                                <br><br>
                                Please ensure the file is a valid .docx document and try again.
                            </div>
                        """
                        return error_html
                
                # Update template type visibility based on document type
                def update_template_visibility(doc_type_value):
                    if doc_type_value == "Advisory Circular":
                        return gr.update(visible=True)
                    else:
                        return gr.update(visible=False)

                doc_type.change(
                    fn=update_template_visibility,
                    inputs=[doc_type],
                    outputs=[template_type]
                )

                # Handle document processing
                submit_btn.click(
                    fn=process_and_format,
                    inputs=[file_input, doc_type, template_type],
                    outputs=[results]  # Only output the results
                )

                # Function to generate PDF and provide it for download
                # def generate_pdf(html_content):
                #     try:
                #         # Use a temporary file to store the PDF
                #         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                #             # Convert HTML to PDF using WeasyPrint
                #             HTML(string=html_content, base_url='.').write_pdf(tmp_pdf.name)
                #
                #         # Return the path to the PDF file
                #         return gr.update(value=tmp_pdf.name, visible=True)
                #     except Exception as e:
                #         logging.error(f"Error generating PDF with WeasyPrint: {str(e)}")
                #         traceback.print_exc()
                #         return gr.update(value=None, visible=False)


                # When the download button is clicked, generate the PDF
                # download_btn.click(
                #     fn=generate_pdf,
                #     inputs=[results],
                #     outputs=[pdf_file]
                # )

                
                gr.Markdown(
                    """
                    ### 📌 Important Notes
                    - This tool helps ensure compliance with federal documentation standards
                    - Results are based on current style guides and FAA requirements
                    - The tool provides suggestions but final editorial decisions rest with the document author
                    - For questions or feedback on the FAA documentation standards, contact the AIR-646 Senior Technical Writers
                    - For questions or feedback on the tool, contact Eric Putnam
                    - Results are not stored or saved
                    """
                )
            
            with gr.Tab("About"):
                readme_content = get_readme_content()
                gr.Markdown(readme_content)

    return demo

# Initialize and launch the interface
if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        share=False,  # Set to True if you want to generate a public link
        server_name="0.0.0.0",  # Allows external access
        server_port=7860,  # Default Gradio port
        debug=True
    )
