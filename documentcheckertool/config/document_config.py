from documentcheckertool.models import DocumentType

# Valid heading words for all document types
HEADING_WORDS = frozenset({
    'APPLICABILITY', 'APPENDIX', 'AUTHORITY', 'BACKGROUND', 'CANCELLATION', 'CAUTION',
    'CHAPTER', 'CONCLUSION', 'DEPARTMENT', 'DEFINITION', 'DEFINITIONS', 'DISCUSSION',
    'DISTRIBUTION', 'EXCEPTION', 'EXPLANATION', 'FIGURE', 'GENERAL', 'GROUPS', 
    'INFORMATION', 'INSERT', 'INTRODUCTION', 'MATERIAL', 'NOTE', 'PARTS', 'PAST', 
    'POLICY', 'PRACTICE', 'PROCEDURES', 'PURPOSE', 'RELEVANT', 'RELATED', 
    'REQUIREMENTS', 'REPORT', 'SCOPE', 'SECTION', 'SUMMARY', 'TABLE', 'WARNING'
})

# Document type configurations
DOC_TYPE_CONFIG = {
    'Advisory Circular': {
        'required_headings': [
            'Purpose.',
            'Applicability.',
            'Cancellation.',
            'Related Material.',
            'Definition of Key Terms.'
        ],
        'skip_title_check': False
    },
    'Federal Register Notice': {
        'required_headings': [
            'Purpose of This Notice',
            'Audience',
            'Where can I Find This Notice'
        ],
        'skip_title_check': False
    },
    'Order': {
        'required_headings': [
            'Purpose of This Order.',
            'Audience.',
            'Where to Find This Order.'
        ],
        'skip_title_check': False
    },
    'Policy Statement': {
        'required_headings': [
            'SUMMARY',
            'CURRENT REGULATORY AND ADVISORY MATERIAL',
            'RELEVANT PAST PRACTICE',
            'POLICY',
            'EFFECT OF POLICY',
            'CONCLUSION'
        ],
        'skip_title_check': False
    },
    'Technical Standard Order': {
        'required_headings': [
            'PURPOSE.',
            'APPLICABILITY.',
            'REQUIREMENTS.',
            'MARKING.',
            'APPLICATION DATA REQUIREMENTS.',
            'MANUFACTURER DATA REQUIREMENTS.',
            'FURNISHED DATA REQUIREMENTS.',
            'HOW TO GET REFERENCED DOCUMENTS.'
        ],
        'skip_title_check': False
    },
    'Airworthiness Criteria': {
        'required_headings': [],
        'skip_title_check': True
    },
    'Deviation Memo': {
        'required_headings': [],
        'skip_title_check': True
    },
    'Exemption': {
        'required_headings': [],
        'skip_title_check': True
    },
    'Rule': {
        'required_headings': [],
        'skip_title_check': True
    },
    'Special Condition': {
        'required_headings': [],
        'skip_title_check': True
    },
    'Other': {
        'required_headings': [],
        'skip_title_check': True
    }
}

# Period requirements by document type
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

# Document template configurations
TEMPLATE_TYPES = {
    'Advisory Circular': [
        'Short AC template AC',
        'Long AC template AC'
    ]
}

# Document validation configurations
VALIDATION_CONFIG = {
    'skip_patterns': [
        r'(?:U\.S\.C\.|USC)\s+(?:§+\s*)?(?:Section|section)?\s*\d+',
        r'Section\s+\d+(?:\([a-z]\))*\s+of\s+(?:the\s+)?(?:United States Code|U\.S\.C\.)',
        r'\d+\s*(?:CFR|C\.F\.R\.)'
    ],
    'allowed_extensions': ['.docx']
}

# Readability thresholds
READABILITY_CONFIG = {
    'max_sentence_length': 25,
    'max_avg_sentence_length': 20,
    'min_flesch_ease': 50,
    'max_flesch_grade': 12,
    'max_fog_index': 12,
    'max_passive_voice_percentage': 10
}

# Document boilerplate/required text
REQUIRED_TEXT = {
    'Advisory Circular': [
        'This is a guidance document. Its content is not legally binding in its own right',
        'The contents of this AC do not have the force and effect of law'
    ],
    'Policy Statement': [
        'This policy statement does not constitute a new regulation',
        'If a proposed method of compliance appears to differ from the guidance expressed in this policy statement'
    ]
}
