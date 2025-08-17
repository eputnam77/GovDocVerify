"""Configuration settings for document checks."""

READABILITY_CONFIG = {
    "max_sentence_length": 20,
    "max_paragraph_length": 100,
    "min_flesch_score": 50,
    "max_flesch_kincaid_grade": 12,
    "max_gunning_fog_index": 12,
    "max_passive_voice_percentage": 10,
}

# Add other document configuration settings as needed

# Acceptable source domains and file extensions
ALLOWED_SOURCE_DOMAINS = [".gov", ".mil"]
ALLOWED_FILE_EXTENSIONS = [".docx"]

# File extensions that are explicitly rejected as legacy formats
LEGACY_FILE_EXTENSIONS = [".doc", ".pdf", ".rtf", ".txt"]
