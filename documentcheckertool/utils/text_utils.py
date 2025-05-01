import re
from typing import List, Tuple

def split_sentences(text: str) -> List[str]:
    """Split text into sentences while handling common abbreviations."""
    # Common abbreviations that shouldn't end sentences
    abbreviations = {
        'e.g.', 'i.e.', 'etc.', 'vs.', 'Dr.', 'Mr.', 'Mrs.', 'Ms.',
        'Prof.', 'Rev.', 'Hon.', 'St.', 'Ave.', 'Blvd.', 'Rd.',
        'U.S.', 'U.S.C.', 'CFR', 'FAA', 'AC', 'TSO', 'PMA'
    }
    
    # Replace abbreviations with placeholders
    placeholder_map = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR_{i}__"
        placeholder_map[placeholder] = abbr
        text = text.replace(abbr, placeholder)
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore abbreviations
    for placeholder, abbr in placeholder_map.items():
        sentences = [s.replace(placeholder, abbr) for s in sentences]
    
    return sentences

def count_words(text: str) -> int:
    """Count words in text, handling hyphenated words and numbers."""
    # Remove punctuation except hyphens and apostrophes
    text = re.sub(r'[^\w\s\-\']', ' ', text)
    # Split on whitespace and count non-empty elements
    return len([w for w in text.split() if w.strip()])

def normalize_reference(ref: str) -> str:
    """Normalize reference text for consistent comparison."""
    # Convert to uppercase
    ref = ref.upper()
    # Remove extra whitespace
    ref = ' '.join(ref.split())
    # Standardize common reference formats
    ref = re.sub(r'§\s*', '§', ref)  # Section symbol
    ref = re.sub(r'PART\s+', 'PART ', ref)  # Part references
    ref = re.sub(r'SUBPART\s+', 'SUBPART ', ref)  # Subpart references
    ref = re.sub(r'APPENDIX\s+', 'APPENDIX ', ref)  # Appendix references
    return ref

def count_syllables(word: str) -> int:
    """Count syllables in a word."""
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index-1] not in vowels:
            count += 1
    if word.endswith('e'):
        count -= 1
    if count == 0:
        count += 1
    return count

def normalize_heading(text: str) -> str:
    """Normalize heading text for consistent comparison."""
    # Remove excess whitespace
    text = ' '.join(text.split())
    # Normalize periods (convert multiple periods to single period)
    text = re.sub(r'\.+$', '.', text.strip())
    # Remove any whitespace before the period
    text = re.sub(r'\s+\.$', '.', text)
    return text 