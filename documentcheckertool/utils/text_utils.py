import re
import unicodedata
from typing import List, Optional, Set

def split_sentences(text: str) -> List[str]:
    """Split text into sentences while handling common abbreviations."""
    if not text:
        return [""]
        
    # Common abbreviations that shouldn't end sentences
    abbreviations: Set[str] = {
        'e.g.', 'i.e.', 'etc.', 'vs.', 'dr.', 'mr.', 'mrs.', 'ms.',
        'prof.', 'rev.', 'hon.', 'st.', 'ave.', 'blvd.', 'rd.',
        'u.s.', 'u.s.c.', 'cfr', 'faa', 'ac', 'tso', 'pma'
    }
    
    # Add uppercase versions of abbreviations
    abbreviations.update(abbr.upper() for abbr in abbreviations)
    
    # Create regex pattern for abbreviations
    abbr_pattern = '|'.join(map(re.escape, sorted(abbreviations, key=len, reverse=True)))
    
    # Split text into sentences
    sentences = []
    current_pos = 0
    
    # Find all potential sentence boundaries
    for match in re.finditer(r'[.!?](?=\s+[A-Z0-9]|\s*$|\s*["""\']|\s*[.!?])', text):
        end = match.end()
        period_pos = match.start()
        
        # Look backwards for abbreviation
        prev_text = text[max(0, period_pos-20):period_pos+1].lower()
        is_abbrev = False
        
        # Check if period is part of an abbreviation
        for abbr in abbreviations:
            abbr_lower = abbr.lower()
            if prev_text.strip().endswith(abbr_lower):
                is_abbrev = True
                break
            # Also check if it's at the start of a word
            if re.search(rf'\b{re.escape(abbr_lower)}(?=\s|$)', prev_text):
                is_abbrev = True
                break
        
        if not is_abbrev:
            sentence = text[current_pos:end].strip()
            if sentence:
                sentences.append(sentence)
            # Find start of next sentence
            next_start = re.search(r'\s+[A-Z0-9"""\']', text[end:])
            if next_start:
                current_pos = end + next_start.start() + 1
            else:
                current_pos = end
    
    # Add any remaining text
    if current_pos < len(text):
        remaining = text[current_pos:].strip()
        if remaining:
            sentences.append(remaining)
    
    return [s.strip() for s in sentences if s.strip()] or [""]

def count_words(text: str) -> int:
    """Count words in text, handling hyphenated words, numbers, and email addresses."""
    if not text:
        return 0
        
    # Handle email addresses first
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Remove email addresses from text
    for email in emails:
        text = text.replace(email, '')
    
    # Remove punctuation except hyphens and apostrophes in words
    text = re.sub(r'(?<!\w)[^\w\s]|[^\w\s](?!\w)', ' ', text)
    
    # Count regular words
    words = [w for w in text.split() if w.strip()]
    
    # Return total count (regular words + emails)
    return len(words) + len(emails)

def normalize_reference(text: str) -> str:
    """Normalize a reference text for comparison."""
    if not text:
        return ""
        
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace special characters with spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def count_syllables(word: str) -> int:
    """Count syllables in a word."""
    word = word.lower().strip()
    if not word:
        return 0
        
    # Handle special cases
    if word.isdigit():
        return len(word)
    if len(word) <= 3 and word.isupper():
        return len(word)
        
    # Count syllables
    count = 0
    vowels = 'aeiouy'
    prev_is_vowel = False
    
    for i, char in enumerate(word):
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
            
    # Handle special endings
    if word.endswith('e'):
        if not word.endswith('le') or len(word) < 3:
            count -= 1
    if word.endswith('es') or word.endswith('ed'):
        count -= 1
        
    # Ensure at least one syllable
    return max(1, count)

def normalize_heading(text: str) -> str:
    """Normalize heading text for consistent comparison."""
    # Remove excess whitespace
    text = ' '.join(text.split())
    # Normalize periods (convert multiple periods to single period)
    text = re.sub(r'\.+$', '.', text.strip())
    # Remove any whitespace before the period
    text = re.sub(r'\s+\.$', '.', text)
    return text

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting on common sentence endings
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_acronyms(text: str) -> List[str]:
    """Extract potential acronyms from text."""
    # Match 2 or more uppercase letters
    return re.findall(r'\b[A-Z]{2,}\b', text)

def find_acronym_definition(text: str, acronym: str) -> Optional[str]:
    """Find the definition of an acronym in text."""
    pattern = f"{acronym}\\s*\\(([^)]+)\\)"
    match = re.search(pattern, text)
    return match.group(1) if match else None 