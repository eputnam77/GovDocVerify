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
from typing import Dict, List, Any, Tuple, Optional, Pattern
from dataclasses import dataclass
from functools import wraps
from abc import ABC, abstractmethod

# Third-party imports
import gradio as gr
from docx import Document
from colorama import init, Fore, Style

# Constants
DEFAULT_PORT = 7860
DEFAULT_HOST = "0.0.0.0"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

# Document Type Constants
DOCUMENT_TYPES = [
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

TEMPLATE_TYPES = ["Short AC template AC", "Long AC template AC"]

# Heading Word Constants
HEADING_WORDS = {
    'INFORMATION', 'GENERAL', 'SUMMARY', 'INTRODUCTION', 'BACKGROUND', 
    'DISCUSSION', 'CONCLUSION', 'APPENDIX', 'CHAPTER', 'SECTION',
    'PURPOSE', 'APPLICABILITY', 'CANCELLATION', 'DEFINITION', 'REQUIREMENTS',
    'AUTHORITY', 'POLICY', 'SCOPE', 'RELATED', 'MATERIAL', 'DISTRIBUTION',
    'EXPLANATION', 'PROCEDURES', 'NOTE', 'WARNING', 'CAUTION', 'EXCEPTION',
    'GROUPS', 'PARTS', 'TABLE', 'FIGURE', 'REFERENCES', 'DEFINITIONS'
}

# Predefined Acronyms
PREDEFINED_ACRONYMS = {
    'CFR', 'U.S.', 'USA', 'US', 'U.S.C', 'e.g.', 'i.e.', 'FAQ', 'No.', 'ZIP', 'PDF', 'SSN',
    'DC', 'MD', 'MA', 'WA', 'TX', 'MO', 'FAA IR-M', 'DOT'
}

# Configuration Constants
REQUIRED_CONFIG_KEYS = {'logging', 'checks', 'document_types'}
REQUIRED_LOGGING_KEYS = {'level', 'format'}
REQUIRED_CHECKS_KEYS = {'acronyms', 'terminology_check', 'headings'}

# Document Type Period Requirements
PERIOD_REQUIRED = {
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

# Document formatting rules
DOCUMENT_FORMATTING_RULES = {
    "italics_only": {
        "types": ["Advisory Circular"],
        "italics": True, 
        "quotes": False,
        "description": "For Advisory Circulars, referenced document titles should be italicized but not quoted.",
        "example": "See AC 20-135, *Powerplant Installation and Propulsion System Component Fire Protection Test Methods, Standards, and Criteria* for information on X."
    },
    "quotes_only": {
        "types": [
            "Airworthiness Criteria", "Deviation Memo", "Exemption", 
            "Federal Register Notice", "Order", "Rule", "Special Condition", 
            "Technical Standard Order"
        ],
        "italics": False, 
        "quotes": True,
        "description": "For this document type, referenced document titles should be in quotes without italics.",
        "example": 'See AC 20-135, "Powerplant Installation and Propulsion System Component Fire Protection Test Methods, Standards, and Criteria" for information on X.'
    },
    "no_formatting": {
        "types": ["Policy Statement", "Other"],
        "italics": False, 
        "quotes": False,
        "description": "For this document type, referenced document titles should not use italics or quotes.",
        "example": "See AC 20-135, Powerplant Installation and Propulsion System Component Fire Protection Test Methods, Standards, and Criteria for information on X."
    }
}

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

# 4. Utility Classes
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

# 5. Result Class
@dataclass
class DocumentCheckResult:
    """Structured result for document checks."""
    success: bool
    issues: List[Dict[str, Any]]
    details: Optional[Dict[str, Any]] = None

# 6. Base Document Checker
class DocumentChecker:
    """Base class for document checking with comprehensive configuration and logging."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize DocumentChecker with optional configuration.

        Args:
            config_path (str, optional): Path to configuration file.
        """
        self.config_manager = DocumentCheckerConfig(config_path)
        self.logger = self.config_manager.logger

    @classmethod
    def extract_paragraphs(cls, doc_path: str) -> List[str]:
        """
        Extract plain text paragraphs from a document.

        Args:
            doc_path (str): Path to the document.

        Returns:
            List[str]: List of paragraph texts.
        """
        try:
            doc = Document(doc_path)
            return [para.text for para in doc.paragraphs if para.text.strip()]
        except Exception as e:
            logging.error(f"Error extracting paragraphs: {e}")
            return []

    @staticmethod
    def validate_input(doc: List[str]) -> bool:
        """
        Validate input document.

        Args:
            doc (List[str]): List of paragraphs.

        Returns:
            bool: Whether input is valid.
        """
        return doc is not None and isinstance(doc, list) and len(doc) > 0

# 7. Configuration Manager
class DocumentCheckerConfig:
    """Configuration management for document checks."""
    
    REQUIRED_CONFIG_KEYS = {'logging', 'checks', 'document_types'}
    REQUIRED_LOGGING_KEYS = {'level', 'format'}
    REQUIRED_CHECKS_KEYS = {'acronyms', 'terminology_check', 'headings'}
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with optional config file."""
        self.default_config = {
            "logging": {
                "level": DEFAULT_LOG_LEVEL,  # Use constant defined at top
                "format": DEFAULT_LOG_FORMAT  # Use constant defined at top
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
        return {
            'terminology': [
                PatternConfig(
                    pattern=r'\btitle 14 of the Code of Federal Regulations \(14 CFR\)\b',
                    description="Ignore 'title 14 of the Code of Federal Regulations (14 CFR)'",
                    is_error=False  # Set to False to ignore this phrase
                ),
                PatternConfig(
                    pattern=r'\btitle 14, Code of Federal Regulations \(14 CFR\)\b',
                    description="Ignore 'title 14, Code of Federal Regulations (14 CFR)'",
                    is_error=False
                ),
                PatternConfig(
                    pattern=r'\bUSC\b',
                    description="USC should be U.S.C.",
                    is_error=True,
                    replacement="U.S.C."
                ),
                PatternConfig(
                    pattern=r'\bCFR Part\b',
                    description="CFR Part should be CFR part",
                    is_error=True,
                    replacement="CFR part"
                ),
                PatternConfig(
                    pattern=r'\bC\.F\.R\.\b',
                    description="C.F.R. should be CFR",
                    is_error=True,
                    replacement="CFR"
                ),
                PatternConfig(
                    pattern=r'\bWe\b',
                    description="'We' should be 'The FAA'",
                    is_error=True,
                    replacement="The FAA"
                ),
                PatternConfig(
                    pattern=r'\bwe\b',
                    description="'we' should be 'the FAA'",
                    is_error=True,
                    replacement="the FAA"
                ),
                PatternConfig(
                    pattern=r'\bcancelled\b',
                    description="'cancelled' should be 'canceled'",
                    is_error=True,
                    replacement="canceled"
                ),
                PatternConfig(
                    pattern=r'\bshall\b',
                    description="'shall' should be 'must'",
                    is_error=True,
                    replacement="must"
                ),
                PatternConfig(
                    pattern=r'\b\&\b',
                    description="'&' should be 'and'",
                    is_error=True,
                    replacement="and"
                ),
                PatternConfig(
                    pattern=r'\bflight crew\b',
                    description="'flight crew' should be 'flightcrew'",
                    is_error=True,
                    replacement="flightcrew"
                ),
                PatternConfig(
                    pattern=r'\bchairman\b',
                    description="'chairman' should be 'chair'",
                    is_error=True,
                    replacement="chair"
                ),
                PatternConfig(
                    pattern=r'\bflagman\b',
                    description="'flagman' should be 'flagger' or 'flagperson'",
                    is_error=True,
                    replacement="flagperson"
                ),
                PatternConfig(
                    pattern=r'\bman\b',
                    description="'man' should be 'individual' or 'person'",
                    is_error=True,
                    replacement="person"
                ),
                PatternConfig(
                    pattern=r'\bmanmade\b',
                    description="'manmade' should be 'personmade'",
                    is_error=True,
                    replacement="personmade"
                ),
                PatternConfig(
                    pattern=r'\bmanpower\b',
                    description="'manpower' should be 'labor force'",
                    is_error=True,
                    replacement="labor force"
                ),
                PatternConfig(
                    pattern=r'\bnotice to airman\b',
                    description="'notice to airman' should be 'notice to air missions'",
                    is_error=True,
                    replacement="notice to air missions"
                ),
                PatternConfig(
                    pattern=r'\bnotice to airmen\b',
                    description="'notice to airmen' should be 'notice to air missions'",
                    is_error=True,
                    replacement="notice to air missions"
                ),
                PatternConfig(
                    pattern=r'\bcockpit\b',
                    description="'cockpit' should be 'flight deck'",
                    is_error=True,
                    replacement="flight deck"
                ),
                PatternConfig(
                    pattern=r'\bA321 neo\b',
                    description="'A321 neo' should be 'A321neo'",
                    is_error=True,
                    replacement="A321neo"
                )
            ],
            'section_symbol': [
                PatternConfig(
                    pattern=r'^§',
                    description="Sentence should not start with section symbol",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'\b14 CFR §\s*\d+\.\d+\b',
                    description="14 CFR should not use section symbol",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'§\s*\d+\.\d+\s+(?:and|or)\s+\d+\.\d+',
                    description="Missing section symbol in multiple sections",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'§\s*\d+\.\d+\s+through\s+\d+\.\d+',
                    description="Missing section symbol in range of sections",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'§\s*\d+\.\d+\s+or\s+§?\s*\d+\.\d+',
                    description="Inconsistent section symbol usage with 'or'",
                    is_error=True
                )
            ],
            'spacing': [
                PatternConfig(
                    pattern=r'(?<!\s)(AC|AD|CFR|FAA|N|SFAR)(\d+[-]?\d*)',
                    description="Missing space between document type and number",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<!\s)(§|§§)(\d+\.\d+)',
                    description="Missing space after section symbol (§)",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<!\s)Part(\d+)',
                    description="Missing space between 'Part' and number",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<!\s)(\([a-z](?!\))|\([1-9](?!\)))',
                    description="Missing space before paragraph indication",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'\s{2,}',
                    description="Double spaces between words",
                    is_error=True
                )
            ],
            'dates': [
                PatternConfig(
                    pattern=r'(?<![\w/-])\d{1,2}/\d{1,2}/\d{2,4}(?![\w/-])',
                    description="Use 'Month Day, Year' format instead of MM/DD/YYYY",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<![\w/-])\d{1,2}-\d{1,2}-\d{2,4}(?![\w/-])',
                    description="Use 'Month Day, Year' format instead of MM-DD-YYYY",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<![\w/-])\d{4}-\d{1,2}-\d{1,2}(?![\w/-])',
                    description="Use 'Month Day, Year' format instead of YYYY-MM-DD",
                    is_error=True
                )
            ],
            'placeholders': [
                PatternConfig(
                    pattern=r'\bTBD\b',
                    description="Remove TBD placeholder",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'\bTo be determined\b',
                    description="Remove 'To be determined' placeholder",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'\bTo be added\b',
                    description="Remove 'To be added' placeholder",
                    is_error=True
                )
            ],
            'reference_terms': [
                PatternConfig(
                    pattern=r'\babove\b',
                    description="Avoid using 'above' for references",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'\bbelow\b',
                    description="Avoid using 'below' for references",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?:^|(?<=[.!?]\s))There\s+(?:is|are)\b',
                    description="Avoid starting sentences with 'There is/are'",
                    is_error=True
                )
            ],
            'periods': [
                PatternConfig(
                    pattern=r'\.\.',
                    description="Remove double periods",
                    is_error=True
                )
            ],
            'table_figure_references': [
                PatternConfig(
                    pattern=r'(?<!^)(?<![.!?])\s+[T]able\s+\d+(?:-\d+)?',
                    description="Table reference within sentence should be lowercase",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'(?<!^)(?<![.!?])\s+[F]igure\s+\d+(?:-\d+)?',
                    description="Figure reference within sentence should be lowercase",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'^[t]able\s+\d+(?:-\d+)?',
                    description="Table reference at start of sentence should be capitalized",
                    is_error=True
                ),
                PatternConfig(
                    pattern=r'^[f]igure\s+\d+(?:-\d+)?',
                    description="Figure reference at start of sentence should be capitalized",
                    is_error=True
                )
            ]
        }

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

    # Constructor
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.HEADING_WORDS = HEADING_WORDS
        self.PREDEFINED_ACRONYMS = PREDEFINED_ACRONYMS

    # Core Check Methods
    @profile_performance
    def heading_title_check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        if not self.validate_input(doc):
            self.logger.error("Invalid document input for heading check")
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Validate document type
        doc_type_config = self.config_manager.config['document_types'].get(doc_type)
        if not doc_type_config:
            self.logger.error(f"Unsupported document type: {doc_type}")
            return DocumentCheckResult(
                success=False, 
                issues=[{'error': f'Unsupported document type: {doc_type}'}]
            )

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

        should_have_period = PERIOD_REQUIRED.get(doc_type)
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
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Common words that might appear in uppercase but aren't acronyms
        heading_words = self.config_manager.config.get('heading_words', self.HEADING_WORDS)

        # Standard acronyms that don't need to be defined
        predefined_acronyms = self.config_manager.config.get('predefined_acronyms', self.PREDEFINED_ACRONYMS)

        # Tracking structures
        defined_acronyms = {}  # Stores definition info
        used_acronyms = set()  # Stores acronyms used after definition
        reported_acronyms = set()  # Stores acronyms that have already been noted as issues
        issues = []

        # Patterns
        defined_pattern = re.compile(r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)')
        acronym_pattern = re.compile(r'(?<!\()\b[A-Z]{2,}\b(?!\s*[:.]\s*)')

        for paragraph in doc:
            # Skip lines that appear to be headings (all uppercase with common heading words)
            words = paragraph.strip().split()
            if all(word.isupper() for word in words) and any(word in heading_words for word in words):
                continue

            # Check for acronym definitions first
            defined_matches = defined_pattern.findall(paragraph)
            for full_term, acronym in defined_matches:
                if acronym not in predefined_acronyms:
                    if acronym not in defined_acronyms:
                        defined_acronyms[acronym] = {
                            'full_term': full_term.strip(),
                            'defined_at': paragraph.strip(),
                            'used': False  # Initially not used
                        }

            # Check for acronym usage
            usage_matches = acronym_pattern.finditer(paragraph)
            for match in usage_matches:
                acronym = match.group()

                # Skip predefined acronyms
                if acronym in predefined_acronyms:
                    continue

                # Skip if it's part of a heading or contains non-letter characters
                if (acronym in heading_words or
                    any(not c.isalpha() for c in acronym) or
                    len(acronym) > 10):  # Usually acronyms aren't this long
                    continue

                if acronym not in defined_acronyms and acronym not in reported_acronyms:
                    # Undefined acronym used; report only once
                    issues.append(f"Confirm '{acronym}' was defined at its first use.")
                    reported_acronyms.add(acronym)  # Add to reported list
                elif acronym in defined_acronyms:
                    # Mark as used
                    defined_acronyms[acronym]['used'] = True
                    used_acronyms.add(acronym)

        # Define success based on whether there are any undefined acronyms
        success = len(issues) == 0

        # Return the result with detailed issues
        return DocumentCheckResult(success=success, issues=issues)

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
        """
        Check document terminology and output only unique sentences needing correction.
        
        Args:
            doc (List[str]): List of document paragraphs
            
        Returns:
            DocumentCheckResult: Result containing unique terminology issues with context
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        terminology_patterns = self.config_manager.pattern_registry.get('terminology', [])
        prohibited_patterns = self.config_manager.pattern_registry.get('reference_terms', [])

        sentence_issues = {}

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                current_sentence_issues = []

                for pattern_config in terminology_patterns:
                    matches = list(re.finditer(pattern_config.pattern, sentence))
                    for match in matches:
                        current_sentence_issues.append({
                            'incorrect_term': match.group(),
                            'correct_term': pattern_config.replacement,
                            'description': pattern_config.description,
                            'sentence': sentence
                        })

                for pattern_config in prohibited_patterns:
                    if re.search(pattern_config.pattern, sentence, re.IGNORECASE):
                        current_sentence_issues.append({
                            'description': pattern_config.description,
                            'sentence': sentence
                        })

                if current_sentence_issues:
                    if sentence not in sentence_issues:
                        sentence_issues[sentence] = current_sentence_issues
                    else:
                        sentence_issues[sentence].extend(current_sentence_issues)

        unique_issues = []
        for sentence, sentence_issue_list in sentence_issues.items():
            replacements = []
            for issue in sentence_issue_list:
                if 'incorrect_term' in issue and issue.get('correct_term'):
                    replacements.append(f"'{issue['incorrect_term']}' with '{issue['correct_term']}'")

            replacement_text = "; ".join(replacements)
            formatted_issue = {
                'sentence': f"{sentence} ({'Replace ' + replacement_text})" if replacements else sentence
            }
            unique_issues.append(formatted_issue)

        return DocumentCheckResult(success=not unique_issues, issues=unique_issues)

    @profile_performance
    def check_section_symbol_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check for section symbol (§) usage issues and provide only sentences or matches needing correction."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        section_patterns = self.config_manager.pattern_registry.get('section_symbol', [])

        issues = []

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            for sentence in sentences:
                sentence = sentence.strip()
                for pattern_config in section_patterns:
                    compiled_pattern = re.compile(pattern_config.pattern)

                    if pattern_config.pattern == r'^§':  # Start of sentence with § symbol
                        if compiled_pattern.match(sentence):
                            corrected_sentence = sentence.replace('§', 'Section', 1)
                            issues.append({
                                'sentence': f"{sentence} (Replace § with 'Section')"
                            })

                    elif pattern_config.pattern == r'\b14 CFR §\s*\d+\.\d+\b':  # 14 CFR § format
                        matches = compiled_pattern.findall(sentence)
                        for match in matches:
                            corrected_sentence = sentence.replace('§', '', 1)
                            issues.append({
                                'sentence': f"{sentence} (Remove §)"
                            })

        return DocumentCheckResult(success=not issues, issues=issues)

    @profile_performance
    def caption_check(self, doc: List[str], doc_type: str, caption_type: str) -> DocumentCheckResult:
        """Check for correctly formatted captions (Table or Figure)."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Determine the caption pattern based on document type
        if doc_type in ["Advisory Circular", "Order"]:
            caption_pattern = re.compile(rf'^{caption_type}\s+([A-Z0-9]+)-([A-Z0-9]+)[\.\s]', re.IGNORECASE)
            correct_format = f"{caption_type} X-Y"
        else:
            caption_pattern = re.compile(rf'^{caption_type}\s+([A-Z0-9]+)[\.\s]', re.IGNORECASE)
            correct_format = f"{caption_type} X"

        incorrect_captions = []
        in_toc = False

        for paragraph in doc:
            # Check for start or end of Table of Contents (TOC)
            if "Table of Contents" in paragraph or "Contents" in paragraph:
                in_toc = True
                continue
            elif in_toc and paragraph.strip() == "":
                in_toc = False  # Assume blank line marks the end of TOC

            # If within TOC, skip this paragraph
            if in_toc:
                continue

            # Only check paragraphs that start with "Table" or "Figure" for proper caption format
            paragraph_strip = paragraph.strip()
            if paragraph_strip.lower().startswith(caption_type.lower()):
                if not caption_pattern.match(paragraph_strip):
                    incorrect_captions.append({
                        'incorrect_caption': paragraph_strip,
                        'correct_format': correct_format
                    })

        success = len(incorrect_captions) == 0

        return DocumentCheckResult(success=success, issues=incorrect_captions)

    @profile_performance
    def table_figure_reference_check(self, doc: List[str], doc_type: str) -> DocumentCheckResult:
        """
        Check for incorrect references to tables and figures in the document.
        References should be lowercase within sentences and capitalized at sentence start.
        
        Args:
            doc (List[str]): List of document paragraphs
            doc_type (str): Type of document being checked
            
        Returns:
            DocumentCheckResult: Result of table and figure reference check
        """
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
        
        incorrect_references = []
        
        # Define patterns based on document type
        if doc_type in ["Advisory Circular", "Order"]:
            table_pattern = r'\b([Tt]able)\s+\d+-\d+\b'
            figure_pattern = r'\b([Ff]igure)\s+\d+-\d+\b'
        else:
            table_pattern = r'\b([Tt]able)\s+\d+\b'
            figure_pattern = r'\b([Ff]igure)\s+\d+\b'
        
        # Compile patterns for efficiency
        table_ref_pattern = re.compile(table_pattern)
        figure_ref_pattern = re.compile(figure_pattern)
        
        # Pattern to identify table/figure captions
        caption_pattern = re.compile(r'^(Table|Figure)\s+\d+[-\d]*\.?', re.IGNORECASE)
        
        for paragraph in doc:
            # Skip if this is a caption line
            if caption_pattern.match(paragraph.strip()):
                continue
                
            # Split into sentences while preserving punctuation
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            for sentence in sentences:
                sentence = sentence.strip()
                
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

        success = len(incorrect_references) == 0
        return DocumentCheckResult(success=success, issues=incorrect_references)

    @profile_performance
    def document_title_check(self, doc_path: str, doc_type: str) -> DocumentCheckResult:
        """Check for correct formatting of document titles."""
        try:
            doc = Document(doc_path)
        except Exception as e:
            self.logger.error(f"Error reading the document in title check: {e}")
            return DocumentCheckResult(success=False, issues=[{'error': str(e)}])

        incorrect_titles = []

        # Define formatting rules for different document types
        formatting_rules = {
            "Advisory Circular": {"italics": True, "quotes": False},
            "Airworthiness Criteria": {"italics": False, "quotes": True},
            "Deviation Memo": {"italics": False, "quotes": True},
            "Exemption": {"italics": False, "quotes": True},
            "Federal Register Notice": {"italics": False, "quotes": True},
            "Order": {"italics": False, "quotes": True},
            "Policy Statement": {"italics": False, "quotes": False},
            "Rule": {"italics": False, "quotes": True},
            "Special Condition": {"italics": False, "quotes": True},
            "Technical Standard Order": {"italics": False, "quotes": True},
            "Other": {"italics": False, "quotes": False}
        }

        if doc_type not in formatting_rules:
            self.logger.warning(f"Unsupported document type: {doc_type}. Skipping title check.")
            return DocumentCheckResult(success=True, issues=[])

        required_format = formatting_rules[doc_type]

        ac_pattern = re.compile(r'(AC\s+\d+(?:-\d+)?(?:,|\s)+)(.+?)(?=\.|,|$)')

        for paragraph in doc.paragraphs:
            text = paragraph.text
            matches = ac_pattern.finditer(text)

            for match in matches:
                full_match = match.group(0)
                title_text = match.group(2).strip()

                # Get the position where the title starts
                title_start = match.start(2)
                title_end = match.end(2)

                # Check for any type of quotation marks, including smart quotes
                title_in_quotes = any(q in title_text for q in ['"', "'", '“', '”', '‘', '’'])

                # Check the formatting of the title
                title_is_italicized = False
                current_pos = 0
                for run in paragraph.runs:
                    run_length = len(run.text)
                    run_start = current_pos
                    run_end = current_pos + run_length
                    if run_start <= title_start < run_end:
                        title_is_italicized = run.italic
                        break
                    current_pos += run_length

                # Check if formatting matches the required format
                formatting_incorrect = False
                issue_message = []

                # Check italics requirement
                if required_format["italics"] and not title_is_italicized:
                    formatting_incorrect = True
                    issue_message.append("should be italicized")
                elif not required_format["italics"] and title_is_italicized:
                    formatting_incorrect = True
                    issue_message.append("should not be italicized")

                # Check quotes requirement
                if required_format["quotes"] and not title_in_quotes:
                    formatting_incorrect = True
                    issue_message.append("should be in quotes")
                elif not required_format["quotes"] and title_in_quotes:
                    formatting_incorrect = True
                    issue_message.append("should not be in quotes")

                if formatting_incorrect:
                    incorrect_titles.append({
                        'text': title_text,
                        'issue': ', '.join(issue_message),
                        'sentence': text.strip()
                    })

        success = len(incorrect_titles) == 0

        return DocumentCheckResult(success=success, issues=incorrect_titles)

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

        # Get patterns from registry
        spacing_patterns = self.config_manager.pattern_registry.get('spacing', [])
        
        # Categorize different types of spacing issues
        document_type_spacing_issues = []  # AC25.25, FAA123, etc.
        section_symbol_spacing_issues = []  # §25.25
        part_number_spacing_issues = []     # Part25
        paragraph_spacing_issues = []       # text(a) or text(1)
        double_space_issues = []           # Multiple spaces between words
        
        # Pattern mapping for categorization
        pattern_categories = {
            r'(?<!\s)(AC|AD|CFR|FAA|N|SFAR)(\d+[-]?\d*)': ('document_type_spacing', document_type_spacing_issues),
            r'(?<!\s)(§|§§)(\d+\.\d+)': ('section_symbol_spacing', section_symbol_spacing_issues),
            r'(?<!\s)Part(\d+)': ('part_number_spacing', part_number_spacing_issues),
            r'(?<!\s)(\([a-z](?!\))|\([1-9](?!\)))': ('paragraph_spacing', paragraph_spacing_issues),
            r'\s{2,}': ('double_spacing', double_space_issues)
        }

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                for pattern_config in spacing_patterns:
                    compiled_pattern = re.compile(pattern_config.pattern)
                    
                    # Find the corresponding category for this pattern
                    for pattern_key, (category_name, category_list) in pattern_categories.items():
                        if pattern_config.pattern == pattern_key:
                            matches = compiled_pattern.finditer(sentence)
                            for match in matches:
                                category_list.append({
                                    'text': match.group(),
                                    'sentence': sentence.strip(),
                                    'description': pattern_config.description
                                })

        # Compile issues maintaining the original structure
        issues = []
        
        if document_type_spacing_issues:
            issues.append({
                'issue_type': 'document_type_spacing',
                'description': 'Missing space between document type and number',
                'occurrences': document_type_spacing_issues
            })
        
        if section_symbol_spacing_issues:
            issues.append({
                'issue_type': 'section_symbol_spacing',
                'description': 'Missing space after section symbol',
                'occurrences': section_symbol_spacing_issues
            })
        
        if part_number_spacing_issues:
            issues.append({
                'issue_type': 'part_number_spacing',
                'description': 'Missing space between Part and number',
                'occurrences': part_number_spacing_issues
            })
        
        if paragraph_spacing_issues:
            issues.append({
                'issue_type': 'paragraph_spacing',
                'description': 'Missing space before paragraph indication',
                'occurrences': paragraph_spacing_issues
            })
        
        if double_space_issues:
            issues.append({
                'issue_type': 'double_spacing',
                'description': 'Multiple spaces between words',
                'occurrences': double_space_issues
            })

        success = len(issues) == 0
        return DocumentCheckResult(success=success, issues=issues)

    @profile_performance
    def check_abbreviation_usage(self, doc: List[str]) -> DocumentCheckResult:
        """Check for abbreviation consistency after first definition."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Get patterns from registry - Add a new category in _setup_patterns if not existing
        abbreviation_patterns = self.config_manager.pattern_registry.get('abbreviations', [
            PatternConfig(
                pattern=r'\b([A-Za-z &]+)\s+\((\b[A-Z]{2,}\b)\)',
                description="Acronym definition pattern",
                is_error=False  # Not an error, just a pattern to find definitions
            )
        ])

        # Track abbreviations and their usage
        abbreviations = {}  # Store defined abbreviations
        undefined_uses = []  # Track uses before definition
        inconsistent_uses = []  # Track full term usage after definition
        duplicate_definitions = []  # Track multiple definitions of same acronym

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                # Find definitions using pattern from registry
                for pattern_config in abbreviation_patterns:
                    compiled_pattern = re.compile(pattern_config.pattern)
                    defined_matches = compiled_pattern.finditer(sentence)
                    
                    for match in defined_matches:
                        full_term, acronym = match.groups()
                        full_term = full_term.strip()
                        
                        # Check for duplicate definitions
                        if acronym in abbreviations:
                            if abbreviations[acronym]["full_term"] != full_term:
                                duplicate_definitions.append({
                                    'acronym': acronym,
                                    'first_definition': abbreviations[acronym]["full_term"],
                                    'second_definition': full_term,
                                    'sentence': sentence.strip()
                                })
                        else:
                            abbreviations[acronym] = {
                                "full_term": full_term,
                                "defined": True,
                                "first_occurrence": sentence.strip()
                            }

                # Check for full term usage after definition
                for acronym, data in abbreviations.items():
                    full_term = data["full_term"]
                    if full_term in sentence:
                        # Skip if this is the definition sentence
                        if sentence.strip() == data["first_occurrence"]:
                            continue
                            
                        # Only flag if already defined
                        if not data["defined"]:
                            inconsistent_uses.append({
                                'issue_type': 'full_term_after_acronym',
                                'full_term': full_term,
                                'acronym': acronym,
                                'sentence': sentence.strip(),
                                'definition_context': data["first_occurrence"]
                            })
                        data["defined"] = False  # Mark as used

        # Compile all issues
        issues = []

        if duplicate_definitions:
            issues.append({
                'issue_type': 'duplicate_acronym_definition',
                'description': 'Acronym defined multiple times with different terms',
                'occurrences': duplicate_definitions
            })

        if inconsistent_uses:
            issues.append({
                'issue_type': 'inconsistent_acronym_usage',
                'description': 'Full term used after acronym was defined',
                'occurrences': inconsistent_uses
            })

        # Add summary information
        details = {
            'total_acronyms_defined': len(abbreviations),
            'total_duplicate_definitions': len(duplicate_definitions),
            'total_inconsistent_uses': len(inconsistent_uses),
            'defined_acronyms': [
                {
                    'acronym': acronym,
                    'full_term': data['full_term'],
                    'first_occurrence': data['first_occurrence']
                }
                for acronym, data in abbreviations.items()
            ]
        }

        success = len(issues) == 0
        return DocumentCheckResult(
            success=success,
            issues=issues,
            details=details
        )

    @profile_performance
    def check_date_formats(self, doc: List[str]) -> DocumentCheckResult:
        """Check for inconsistent date formats while ignoring aviation reference numbers."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])
        
        # Get patterns from registry
        date_patterns = self.config_manager.pattern_registry.get('dates', [])
        
        # Patterns to ignore (aviation references)
        ignore_patterns = [
            r'\bAD \d{4}-\d{2}-\d{2}\b',  # Airworthiness Directive references
            r'\bSWPM \d{2}-\d{2}-\d{2}\b',  # Standard Wiring Practices Manual references
            r'\bAMM \d{2}-\d{2}-\d{2}\b',   # Aircraft Maintenance Manual references
            r'\bSOPM \d{2}-\d{2}-\d{2}\b',  # Standard Operating Procedure references
            r'\b[A-Z]{2,4} \d{2}-\d{2}-\d{2}\b'  # Generic manual reference pattern
        ]
        
        # Combine ignore patterns into one
        ignore_regex = '|'.join(ignore_patterns)
        ignore_pattern = re.compile(ignore_regex)
        
        # Track different types of date format issues
        slash_format_dates = []    # MM/DD/YYYY
        hyphen_format_dates = []   # MM-DD-YYYY or YYYY-MM-DD
        
        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                # First, identify and temporarily remove text that should be ignored
                ignored_matches = list(ignore_pattern.finditer(sentence))
                working_sentence = sentence
                
                # Replace ignored patterns with placeholders
                for match in reversed(ignored_matches):
                    start, end = match.span()
                    working_sentence = working_sentence[:start] + 'X' * (end - start) + working_sentence[end:]
                
                # Now check for date patterns
                for pattern_config in date_patterns:
                    compiled_pattern = re.compile(pattern_config.pattern)
                    matches = compiled_pattern.finditer(working_sentence)
                    for match in matches:
                        # Get the original text from the match position
                        original_date = sentence[match.start():match.end()]
                        issue = {
                            'date': original_date,
                            'description': pattern_config.description,
                            'sentence': sentence.strip()
                        }
                        
                        if '/' in original_date:
                            slash_format_dates.append(issue)
                        elif '-' in original_date:
                            hyphen_format_dates.append(issue)

        # Compile issues
        issues = []
        
        if slash_format_dates:
            issues.append({
                'issue_type': 'slash_date_format',
                'description': "Dates should use 'Month Day, Year' format instead of MM/DD/YYYY",
                'occurrences': slash_format_dates
            })
            
        if hyphen_format_dates:
            issues.append({
                'issue_type': 'hyphen_date_format',
                'description': "Dates should use 'Month Day, Year' format instead of MM-DD-YYYY or YYYY-MM-DD",
                'occurrences': hyphen_format_dates
            })

        success = len(issues) == 0
        return DocumentCheckResult(success=success, issues=issues)

    @profile_performance
    def check_placeholders(self, doc: List[str]) -> DocumentCheckResult:
        """Check for placeholders that should be removed."""
        if not self.validate_input(doc):
            return DocumentCheckResult(success=False, issues=[{'error': 'Invalid document input'}])

        # Get patterns from registry
        placeholder_patterns = self.config_manager.pattern_registry.get('placeholders', [])
        
        # Track different types of placeholders
        tbd_placeholders = []
        to_be_determined_placeholders = []
        to_be_added_placeholders = []
        
        # Pattern mapping for categorization
        pattern_categories = {
            r'\bTBD\b': ('tbd', tbd_placeholders),
            r'\bTo be determined\b': ('to_be_determined', to_be_determined_placeholders),
            r'\bTo be added\b': ('to_be_added', to_be_added_placeholders)
        }

        for paragraph in doc:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                for pattern_config in placeholder_patterns:
                    compiled_pattern = re.compile(pattern_config.pattern, re.IGNORECASE)
                    
                    # Find the corresponding category for this pattern
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

        # Add summary information
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

        success = len(issues) == 0
        return DocumentCheckResult(success=success, issues=issues, details=details)

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
            ('acronym_check', lambda: self.acronym_check(doc)),
            ('acronym_usage_check', lambda: self.acronym_usage_check(doc)),
            ('terminology_check', lambda: self.check_terminology(doc)),
            ('section_symbol_usage_check', lambda: self.check_section_symbol_usage(doc)),
            ('caption_check_table', lambda: self.caption_check(doc, doc_type, 'Table')),
            ('caption_check_figure', lambda: self.caption_check(doc, doc_type, 'Figure')),
            ('table_figure_reference_check', lambda: self.table_figure_reference_check(doc, doc_type)),
            ('document_title_check', lambda: self.document_title_check(doc_path, doc_type) if not skip_title_check else DocumentCheckResult(success=True, issues=[])),
            ('double_period_check', lambda: self.double_period_check(doc)),
            ('spacing_check', lambda: self.spacing_check(doc)),
            ('abbreviation_usage_check', lambda: self.check_abbreviation_usage(doc)),
            ('date_formats_check', lambda: self.check_date_formats(doc)),
            ('placeholders_check', lambda: self.check_placeholders(doc))
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

class DocumentCheckResultsFormatter:
    """Formats document check results in a user-friendly way with detailed examples and fixes."""
    
    def __init__(self):
        """Initialize the formatter with colorama for cross-platform color support."""
        init()  # Initialize colorama
        
        # Enhanced issue categories with examples and specific fixes
        self.issue_categories = {
            'heading_title_check': {
                'title': 'Required Headings Check',
                'description': 'Verifies that your document includes all mandatory section headings, with requirements varying by document type. For example, long Advisory Circulars require headings like "Purpose." and "Applicability." with initial caps and periods, while Federal Register Notices use ALL CAPS headings like "SUMMARY" and "BACKGROUND" without periods. This check ensures both the presence of required headings and their correct capitalization format based on document type.',
                'solution': 'Add all required headings in the correct order',
                'example_fix': {
                    'before': 'Missing required heading "PURPOSE."',
                    'after': 'Added heading "PURPOSE." at the beginning of the document'
                }
            },
            'heading_title_period_check': {
                'title': 'Heading Period Format',
                'description': 'Examines heading punctuation to ensure compliance with FAA document formatting standards. Some FAA documents (like Advisory Circulars and Orders) require periods at the end of headings, while others (like Federal Register Notices) explicitly prohibit them. This standardization ensures consistent document formatting across the FAA.',
                'solution': 'Format heading periods according to document type requirements',
                'example_fix': {
                    'before': 'Purpose',
                    'after': 'Purpose.' # For ACs and Orders
                }
            },
            'table_figure_reference_check': {
                'title': 'Table and Figure References',
                'description': 'Analyzes how tables and figures are referenced within your document text to ensure consistent capitalization following FAA style guidelines. Capitalize references at the beginning of sentences (e.g., "Table 2-1 shows...") and use lowercase references within sentences (e.g., "...as shown in table 2-1"). This promotes clear and professional document presentation.',
                'solution': 'Capitalize references at start of sentences, use lowercase within sentences',
                'example_fix': {
                    'before': 'The DTR values are specified in Table 3-1 and Figure 3-2.',
                    'after': 'The DTR values are specified in table 3-1 and figure 3-2.'
                }
            },
            'acronym_check': {
                'title': 'Acronym Definition Issues',
                'description': 'Ensures every acronym is properly introduced with its full term at first use. The check identifies undefined acronyms while recognizing common exceptions (like U.S.) that don\'t require definition.',
                'solution': 'Define each acronym at its first use, e.g., "Federal Aviation Administration (FAA)"',
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
                'description': 'Evaluates document text against the various style manuals and orders to identify non-compliant terminology, ambiguous references, and outdated phrases. This includes checking for prohibited relative references (like "above" or "below"), proper legal terminology (like "must" instead of "shall"), and consistent formatting of regulatory citations. The check ensures precise, unambiguous communication that meets current FAA documentation requirements.',
                'solution': 'Use explicit references to paragraphs, sections, tables, and figures',
                'example_fix': {
                    'before': 'See above section for details | Refer to below table | shall comply with',
                    'after': 'See paragraph 3.2 for details | Refer to table 2-1 | must comply with'
                }
            },
            'section_symbol_usage_check': {
                'title': 'Section Symbol (§) Format Issues',
                'description': 'Examines the usage of section symbols (§) throughout your document against FAA and Federal Register citation standards. This includes verifying proper symbol placement in regulatory references, ensuring sections aren\'t started with the symbol, checking consistency in multiple-section citations, and validating proper CFR citations.',
                'solution': 'Format section symbols correctly and never start sentences with them',
                'example_fix': {
                    'before': '§ 25.25 states | 14 CFR § 21.21',
                    'after': 'Section 25.25 states | 14 CFR 21.21'
                }
            },
            'double_period_check': {
                'title': 'Multiple Period Issues',
                'description': 'Examines sentences for accidental double periods that often occur during document editing and revision. These unintended duplications can appear when combining sentences, after abbreviations, or during collaborative editing. While double periods are sometimes found in ellipses (...) or web addresses, they should never appear at the end of standard sentences in FAA documentation.',
                'solution': 'Remove multiple periods that end sentences',
                'example_fix': {
                    'before': 'The following ACs are related to the guidance in this document..',
                    'after': 'The following ACs are related to the guidance in this document.'
                }
            },
            'spacing_check': {
                'title': 'Spacing Issues',
                'description': 'Analyzes document spacing patterns to ensure compliance with FAA formatting standards. This includes checking for proper spacing around regulatory references (like "AC 25-1" not "AC25-1"), section symbols (§ 25.1), paragraph references, and multiple spaces between words. Special attention is given to common aviation document elements like CFR citations, airworthiness directives (ADs), and advisory circular references where precise spacing affects document searchability and citation accuracy.',
                'solution': 'Fix spacing issues: remove any missing spaces, double spaces, or inadvertent tabs.',
                'example_fix': {
                    'before': 'AC25.25 states that  SFAR88 and §25.981 require... (note double space)',
                    'after': 'AC 25.25 states that SFAR 88 and § 25.981 require...'
                }
            },
            'date_formats_check': {
                'title': 'Date Format Issues',
                'description': 'Examines all date references in your document to ensure adherence to FAA standardized date formatting requirements. This check distinguishes between dates in regulatory references (like airworthiness directive numbers "AD 2023-12-14") and actual calendar dates, which must use the "Month Day, Year" format. The check automatically excludes technical reference numbers that may look like dates to ensure accurate validation of true date references.',
                'solution': 'Use the format "Month Day, Year"',
                'example_fix': {
                    'before': '01/15/2024 | 2024-01-15 | 15 January 2024 | January 15th, 2024',
                    'after': 'January 15, 2024'
                }
            },
            'placeholders_check': {
                'title': 'Placeholder Content',
                'description': 'Identifies incomplete content and temporary placeholders that must be finalized before document publication. This includes common placeholder text (like "TBD" or "To be determined"), draft markers, and incomplete sections. The check helps ensure all required information is properly completed, particularly for critical regulatory and safety information in FAA documentation where incomplete content could affect operational or certification decisions.',
                'solution': 'Replace all placeholder content with actual content',
                'example_fix': {
                    'before': 'TBD | To be determined | [Insert text] | [Pending review] | To be added',
                    'after': 'Actual, specific content relevant to the section\'s purpose'
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

    def _format_reference_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format reference issues consistently."""
        output = []
        
        for issue in result.issues:
            if isinstance(issue, dict):
                reference_text = f"    • {issue['reference']} should be {issue['correct_form']}"
                output.append(reference_text)
                if 'sentence' in issue:
                    context = textwrap.fill(
                        issue['sentence'],
                        width=76,
                        initial_indent='      ',
                        subsequent_indent='      '
                    )
                    output.append(f"{Fore.YELLOW}Context: {context}{Style.RESET_ALL}")
        
        return output

    def _format_unused_acronym_issues(self, result: DocumentCheckResult) -> List[str]:
        """
        Format issues for unused acronyms to display only the acronym.
        
        Args:
            result: The DocumentCheckResult object containing issues.

        Returns:
            List[str]: Formatted lines displaying unused acronyms.
        """
        output = []
        for issue in result.issues:
            if isinstance(issue, dict):
                acronym = issue.get('acronym', 'Unknown Acronym')
                output.append(f"    • Acronym '{acronym}' was defined but never used.")
        return output
    
    def _format_caption_issues(self, result: DocumentCheckResult) -> List[str]:
        """Format caption issues consistently."""
        output = []
        
        for issue in result.issues:
            if isinstance(issue, dict):
                output.append(f"    • {issue.get('incorrect_caption', '')} (correct format: {issue.get('correct_format', '')})")
        
        return output

    def _format_standard_issue(self, issue: Dict[str, Any]) -> str: 
        """Format a standard issue consistently."""
        if isinstance(issue, dict):
            # Handle grouped issues per sentence
            if 'incorrect_terms' in issue and 'sentence' in issue:
                # Build the replacements text
                replacements = '; '.join(
                    f"'{inc}' with '{corr}'" if corr else f"Remove '{inc}'"
                    for inc, corr in sorted(issue['incorrect_terms'])
                )
                # Start building the output lines
                lines = []
                lines.append(f"    • In: {issue['sentence']}")
                lines.append(f"      Replace {replacements}")
                # Format each line individually
                formatted_lines = [
                    textwrap.fill(line, width=76, subsequent_indent='      ')
                    for line in lines
                ]
                return '\n'.join(formatted_lines)
            
            # Handle issues with occurrences list
            if 'occurrences' in issue:
                # Format the first 7 occurrences
                examples = issue['occurrences'][:7]
                formatted_examples = []
                for example in examples:
                    if 'sentence' in example:
                        formatted_examples.append(example['sentence'])
                    elif isinstance(example, str):
                        formatted_examples.append(example)
                
                description = issue.get('description', '')
                return textwrap.fill(
                    f"    • {description} - Examples: {'; '.join(formatted_examples)}",
                    width=76,
                    subsequent_indent='      '
                )
            
            # Handle unused acronym issues
            if issue.get('type') == 'unused_acronym':
                return textwrap.fill(
                    f"    • Acronym '{issue['acronym']}' defined but not used again after definition.",
                    width=76,
                    subsequent_indent='      '
                )
            
            # Handle issues with direct sentence reference
            elif 'sentence' in issue:
                return textwrap.fill(
                    issue['sentence'],
                    width=76,
                    initial_indent='    • ',
                    subsequent_indent='      '
                )
                
            # Handle issues with specific error messages
            elif 'error' in issue:
                return f"    • Error: {issue['error']}"
                
            # Handle issues with description and matches
            elif all(k in issue for k in ['issue_type', 'description', 'matches']):
                matches_str = '; '.join(str(m) for m in issue['matches'][:7])
                return textwrap.fill(
                    f"    • {issue['description']} - Found: {matches_str}",
                    width=76,
                    subsequent_indent='      '
                )
                
            # Handle terminology issues
            if all(k in issue for k in ['incorrect_term', 'correct_term', 'sentence']):
                return textwrap.fill(
                    f"    • Replace '{issue['incorrect_term']}' with '{issue['correct_term']}' in: "
                    f"{issue['sentence']}",
                    width=76,
                    subsequent_indent='      '
                )
                
            # Handle placeholder issues
            elif 'placeholder' in issue:
                return textwrap.fill(
                    f"    • Found placeholder '{issue['placeholder']}' in: {issue.get('sentence', '')}",
                    width=76,
                    subsequent_indent='      '
                )
                
            # Handle other dictionary formats
            else:
                message_parts = []
                for k, v in issue.items():
                    if k not in ['type', 'error']:
                        if isinstance(v, list):
                            if all(isinstance(item, dict) for item in v):
                                # Handle list of dictionaries
                                v_str = '; '.join(str(item.get('sentence', str(item))) for item in v[:7])
                            else:
                                # Handle list of strings
                                v_str = ', '.join(str(item) for item in v[:7])
                            message_parts.append(f"{k}: {v_str}")
                        else:
                            message_parts.append(f"{k}: {v}")
                return f"    • {'; '.join(message_parts)}"
        
        return f"    • {str(issue)}"

    
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
                'description': 'Analyzes table captions to ensure they follow the FAA\'s dual-numbering system, where tables must be numbered according to their chapter or appendix location (X-Y format). The first number (X) indicates the chapter number, while the second number (Y) provides sequential numbering within that chapter. This system ensures clear cross-referencing and helps readers quickly locate tables within large documents.',
                'solution': 'Use the format "Table X-Y" where X is the chapter or appendix number and Y is the sequence number',
                'example_fix': {
                    'before': 'Table 5. | Table A.',
                    'after': 'Table 5-1. | Table A-1.'
                }
            }
            figure_format = {
                'title': 'Figure Caption Format Issues',
                'description': 'Analyzes figure captions to ensure they follow the FAA\'s dual-numbering system, where figures must be numbered according to their chapter or appendix location (X-Y format). The first number (X) indicates the chapter number, while the second number (Y) provides sequential numbering within that chapter. This system allows precise figure references and maintains consistency with table numbering.',
                'solution': 'Use the format "Figure X-Y" where X is the chapter or appendix number and Y is the sequence number',
                'example_fix': {
                    'before': 'Figure 5. | Figure A.',
                    'after': 'Figure 5-1. | Figure A-1.'
                }
            }
        else:
            table_format = {
                'title': 'Table Caption Format Issues',
                'description': f'Analyzes table captions to ensure they follow the FAA\'s sequential numbering system for {doc_type}s. Tables must be numbered consecutively throughout the document using a single-number format. This straightforward numbering system maintains document organization while facilitating clear references to specific tables.',
                'solution': 'Use the format "Table X" where X is a sequential number',
                'example_fix': {
                    'before': 'Table 5-1. | Table A-1',
                    'after': 'Table 5. | Table 1.'
                }
            }
            figure_format = {
                'title': 'Figure Caption Format Issues',
                'description': f'Analyzes figure captions to ensure they follow the FAA\'s sequential numbering system for {doc_type}s. Figures must be numbered consecutively throughout the document using a single-number format. This consistent numbering approach ensures clear figure identification and maintains parallel structure with table numbering.',
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
                "description": "For Advisory Circulars, referenced document titles should be italicized but not quoted",
                "example": "See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X."
            },
            "quotes_only": {
                "types": [
                    "Airworthiness Criteria", "Deviation Memo", "Exemption", 
                    "Federal Register Notice", "Order", "Rule", "Special Condition", 
                    "Technical Standard Order"
                ],
                "italics": False, 
                "quotes": True,
                "description": "For this document type, referenced document titles should be in quotes without italics",
                "example": 'See AC 25.1309-1B, "System Design and Analysis," for information on X.'
            },
            "no_formatting": {
                "types": ["Policy Statement", "Other"],
                "italics": False, 
                "quotes": False,
                "description": "For this document type, referenced document titles should not use italics or quotes",
                "example": "See AC 25.1309-1B, System Design and Analysis, for information on X."
            }
        }

        # Find the formatting group for the current document type
        format_group = None
        for group, rules in formatting_rules.items():
            if doc_type in rules["types"]:
                format_group = rules
                break

        # Use default if document type not found
        if not format_group:
            format_group = formatting_rules["no_formatting"]

        # Update the document title check category
        self.issue_categories['document_title_check'] = {
            'title': 'Referenced Document Title Format Issues',
            'description': format_group['description'],
            'solution': "Format referenced document titles as follows: " + (
                "Italicize the title" if format_group['italics'] else 
                "Put the title in quotes" if format_group['quotes'] else 
                "No special formatting required"
            ),
            'example_fix': {
                'before': 'See AC 20-135, Powerplant Installation for information on X.',
                'after': format_group['example']
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
                
                # Add extra line break before each category
                output.append("\n")
                
                # Category Header
                output.append(self._format_colored_text(f"■ {category['title']}", Fore.YELLOW))
                output.append(f"  {category['description']}")
                output.append(f"  {self._format_colored_text('How to fix: ' + category['solution'], Fore.GREEN)}")
                        
                # Example Fix
                output.append(f"\n  {self._format_colored_text('Example Fix:', Fore.CYAN)}")
                output.extend(self._format_example(category['example_fix']))
                output.append("")  # Add blank line after example
                
                # Actual Issues Found
                output.append(f"  {self._format_colored_text('Issues found in your document:', Fore.CYAN)}")
                
                if check_name == 'heading_title_check':
                    output.extend(self._format_heading_issues(result, doc_type))
                elif check_name == 'heading_title_period_check':
                    output.extend(self._format_period_issues(result))
                elif check_name == 'table_figure_reference_check':
                    output.extend(self._format_reference_issues(result))
                elif check_name in ['caption_check_table', 'caption_check_figure']:
                    output.extend(self._format_caption_issues(result))
                elif check_name == 'acronym_usage_check':
                    output.extend(self._format_unused_acronym_issues(result))
                else:
                    # Standard issue formatting
                    formatted_issues = [self._format_standard_issue(issue) for issue in result.issues[:7]]
                    output.extend(formatted_issues)
                    
                    if len(result.issues) > 7:
                        output.append(f"\n    ... and {len(result.issues) - 7} more similar issues.")
        
        # Summary and Next Steps
        output.append(f"\n{Fore.CYAN}{'='*80}")
        output.append("NEXT STEPS")
        output.append(f"{'='*80}{Style.RESET_ALL}")
        output.append("1. Review each issue category in order of importance:")
        output.append("   - Critical: Heading and terminology issues")
        output.append("   - Important: Acronym definitions and section references")
        output.append("   - Standard: Formatting and spacing issues")
        output.append("\n2. Make corrections using the provided examples as guides")
        output.append("3. Re-run the document check to verify all issues are resolved")
        output.append("\n4. Common tips:")
        output.append("   - Use search/replace for consistent fixes")
        output.append("   - Update your document template to prevent future issues")
        output.append("   - Keep the style manuals and Orders handy while making corrections")
        output.append(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
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

def process_document(file_obj, doc_type: str, template_type: Optional[str] = None) -> str:
    """Process document and run all checks."""
    try:
        checker = FAADocumentChecker()
        
        if isinstance(file_obj, bytes):
            file_obj = io.BytesIO(file_obj)
            
        results = checker.run_all_checks(file_obj, doc_type, template_type)
        return format_markdown_results(results, doc_type)
        
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        traceback.print_exc()
        return f"""
# ❌ Error Processing Document

**Error Details:** {str(e)}

Please ensure:
1. The file is a valid .docx document
2. The file is not corrupted or password protected
3. The file is properly formatted

Try again after checking these issues. If the problem persists, contact support.
"""
    
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
        'acronym_check': {'title': '📝 Acronym Definitions', 'priority': 2},
        'terminology_check': {'title': '📖 Terminology Usage', 'priority': 2},
        'section_symbol_usage_check': {'title': '§ Section Symbol Usage', 'priority': 2},
        'caption_check_table': {'title': '📊 Table Captions', 'priority': 3},
        'caption_check_figure': {'title': '🖼️ Figure Captions', 'priority': 3},
        'table_figure_reference_check': {'title': '🔗 Table/Figure References', 'priority': 3},
        'document_title_check': {'title': '📑 Document Title Format', 'priority': 1},
        'double_period_check': {'title': '⚡ Double Periods', 'priority': 4},
        'spacing_check': {'title': '⌨️ Spacing Issues', 'priority': 4},
        'abbreviation_usage_check': {'title': '📎 Abbreviation Usage', 'priority': 3},
        'date_formats_check': {'title': '📅 Date Formats', 'priority': 3},
        'placeholders_check': {'title': '🚩 Placeholder Content', 'priority': 1}
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

    output.extend([
        "## 📋 Summary and Recommendations",
        "",
        "### Priority Order for Fixes:",
        "1. 🔴 Critical: Heading formats, required content, and document structure",
        "2. 🟡 Important: Terminology, acronyms, and references",
        "3. 🟢 Standard: Formatting, spacing, and style consistency",
        "",
        "### Next Steps:",
        "1. Address issues in priority order",
        "2. Use search/replace for consistent fixes",
        "3. Re-run checker after making changes",
        "4. Update your document template if needed",
        ""
    ])

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
            </style>
            {header_html}
            {issues_html}
        </div>
        """
        
        return full_html

    with gr.Blocks() as demo:
        gr.Markdown(
            """
            # 📑 FAA Document Checker Tool
            
            ## Purpose
            
            This tool checks Word documents for compliance with U.S. federal documentation standards and guidelines, including:
            
            - GPO Style Manual requirements

            - Federal Register Document Drafting Handbook guidelines

            - FAA Orders

            - Plain Language Guidelines per Plain Writing Act of 2010

            - Chicago Manual of Style
            
            ## Validation Checks Include

            - Required heading structure and organization

            - Standard terminology usage
            
            - Proper acronym definitions and usage

            - Correct formatting of citations and references

            - Consistent date and number formats

            - Table and figure caption formatting

            - Section symbol usage

            - Spacing and punctuation

            - Placeholder content detection

            
            ## How to Use

            1. Upload your Word document (.docx format)

            2. Select the document type

            3. Click "Check Document"
            
            > **Note:** Please ensure your document is clean (no track changes or comments)
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
        
        def process_and_format(file_obj, doc_type, template_type):
            """Process document and format results as HTML."""
            try:
                # Get text results from original process_document function
                checker = FAADocumentChecker()
                if isinstance(file_obj, bytes):
                    file_obj = io.BytesIO(file_obj)
                results = checker.run_all_checks(file_obj, doc_type, template_type)
                
                # Format results using DocumentCheckResultsFormatter
                formatter = DocumentCheckResultsFormatter()
                text_results = formatter.format_results(results, doc_type)
                
                # Convert to HTML
                return format_results_as_html(text_results)
                
            except Exception as e:
                logging.error(f"Error processing document: {str(e)}")
                traceback.print_exc()
                return f"""
                    <div style="color: red; padding: 1rem;">
                        ❌ Error processing document: {str(e)}
                        <br><br>
                        Please ensure the file is a valid .docx document and try again.
                    </div>
                """
        
        # Update template type visibility based on document type
        def update_template_visibility(doc_type):
            return gr.update(visible=doc_type == "Advisory Circular")
        
        doc_type.change(
            fn=update_template_visibility,
            inputs=[doc_type],
            outputs=[template_type]
        )
        
        # Handle document processing
        submit_btn.click(
            fn=process_and_format,
            inputs=[file_input, doc_type, template_type],
            outputs=[results]
        )
        
        gr.Markdown(
            """
            ### 📌 Important Notes
            - This tool helps ensure compliance with federal documentation standards
            - Results are based on current style guides and FAA requirements
            - The tool provides suggestions but final editorial decisions rest with the document author
            - For questions or feedback, contact Eric Putnam
            - Results are not stored or saved
            """
        )
    
    return demo

# Initialize and launch the interface
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
        
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        share=False,  # Set to True if you want to generate a public link
        server_name="0.0.0.0",  # Allows external access
        server_port=7860,  # Default Gradio port
        debug=True
    )
