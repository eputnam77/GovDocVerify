# Phone number validation patterns
PHONE_PATTERNS = [
    r'\b\d{3}[-\.]\d{3}[-\.]\d{4}\b',
    r'\b\(\d{3}\)\s*\d{3}[-\.]\d{4}\b'
]

# Placeholder text patterns
PLACEHOLDER_PATTERNS = [
    r'\bTBD\b',
    r'\bto be determined\b',
    r'\bXXX\b',
    r'\[.*?\]',
    r'\{.*?\}'
]

# Date format validation patterns
DATE_PATTERNS = {
    'incorrect': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    'correct': r'\b\d{4}-\d{2}-\d{2}\b',
    'skip_patterns': [
        r'(?:AD|SFAR|AC|Order|Notice|Policy|Memo|TSO)\s*\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b',
        r'\bTSO-[A-Z]?\d{1,3}[a-zA-Z]?\b',
        r'\bDocket\s+(?:No\\.?|Number)\s*\d{2,4}[-/][xX]{1,2}[-/][xX]{1,2}\b'
    ]
}

# Heading validation patterns
HEADING_PATTERNS = {
    'numbered': r'^(\d+\.)+\s',
    'sequence': r'^(\d+\.)+\s*',
    'levels': r'Heading \d+'
}

# Add passive voice patterns (moved from readability checks)
PASSIVE_VOICE_PATTERNS = [
    r'\b(?:am|is|are|was|were|be|been|being)\s+\w+ed\b',
    r'\b(?:am|is|are|was|were|be|been|being)\s+\w+en\b',
    r'\b(?:has|have|had)\s+been\s+\w+ed\b',
    r'\b(?:has|have|had)\s+been\s+\w+en\b'
]

# Terminology patterns (keep only validation patterns, not rules)
ACRONYM_PATTERNS = {
    'defined': r'\b([\w\s&]+?)\s*\((\b[A-Z]{2,}\b)\)',
    'usage': r'(?<!\()\b[A-Z]{2,}\b(?!\s*[:.]\s*)',
    'ignore_patterns': [
        r'FAA-\d{4}-\d+',              # FAA docket numbers
        r'\d{2}-\d{2}-\d{2}-SC',       # Special condition numbers
        r'AC\s*\d+(?:[-.]\d+)*[A-Z]*', # Advisory circular numbers
        r'AD\s*\d{4}-\d{2}-\d{2}',     # Airworthiness directive numbers
        r'\d{2}-[A-Z]{2,}',            # Other reference numbers with acronyms
        r'[A-Z]+-\d+',                 # Generic reference numbers
        r'§\s*[A-Z]+\.\d+',            # Section references
        r'Part\s*[A-Z]+',              # Part references
    ]
}
