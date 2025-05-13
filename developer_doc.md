# Document Checker Tool Developer Documentation

## Project Structure

```
documentcheckertool/
├── config/
│   └── terminology.json    # Single source of truth for all terminology and patterns
├── utils/
│   ├── terminology_utils.py  # Terminology management and validation
│   ├── text_utils.py        # General text processing utilities
│   └── ...
├── checks/
│   ├── acronym_checks.py    # Acronym-specific checks
│   └── ...
└── models/
    └── document_check.py    # Data models for check results
```

## Terminology Management

### Single Source of Truth

All terminology, patterns, and validation rules are stored in `config/terminology.json`. This includes:

1. **Acronyms**
   - Standard acronyms (e.g., FAA, CFR)
   - Custom acronyms (document-specific)
   - Definitions and usage rules

2. **Patterns**
   - Terminology patterns
   - Pronoun usage
   - Citation formats
   - Section symbol usage
   - Date formats
   - Placeholder text

3. **Required Language**
   - Document-type specific required text
   - Boilerplate language
   - Standard disclaimers

4. **Valid Words**
   - Standard valid words
   - Custom valid words

### TerminologyManager

The `TerminologyManager` class in `utils/terminology_utils.py` provides:

1. **Data Management**
   - Loading terminology from JSON
   - Saving changes back to JSON
   - Managing custom acronyms

2. **Validation Methods**
   - Checking acronym usage
   - Validating patterns
   - Verifying required language
   - Managing valid words

3. **Access Methods**
   - Getting standard/custom acronyms
   - Retrieving patterns by category
   - Accessing required language

### Usage Example

```python
from documentcheckertool.utils.terminology_utils import TerminologyManager

# Initialize manager
manager = TerminologyManager()

# Check text for issues
result = manager.check_text("The FAA issued an AC...")

# Add custom acronym
manager.add_custom_acronym("AC", "Advisory Circular")
manager.save_changes()
```

## Text Processing

The `text_utils.py` module provides general text processing utilities:

1. **Sentence Splitting**
   - Handles abbreviations
   - Maintains proper sentence boundaries

2. **Word Counting**
   - Handles hyphenated words
   - Processes email addresses
   - Counts syllables

3. **Text Normalization**
   - Reference text normalization
   - Heading text normalization
   - Document type normalization

## Adding New Patterns

To add new patterns or terminology:

1. Edit `config/terminology.json`
2. Add new entries to appropriate sections
3. Use the TerminologyManager to access new patterns

Example:
```json
{
    "patterns": {
        "new_category": [
            {
                "pattern": "regex_pattern",
                "description": "Description of the pattern",
                "is_error": true,
                "replacement": "Optional replacement text"
            }
        ]
    }
}
```

## Best Practices

1. **Terminology Management**
   - Always use TerminologyManager for acronym handling
   - Save changes after adding custom acronyms
   - Use standard patterns when possible

2. **Pattern Development**
   - Test patterns thoroughly
   - Include clear descriptions
   - Specify error status and replacements

3. **Code Organization**
   - Keep text processing separate from terminology management
   - Use appropriate utility functions
   - Follow established patterns

## Testing

1. **Unit Tests**
   - Test individual pattern matching
   - Verify acronym handling
   - Check text processing functions

2. **Integration Tests**
   - Test full document checking
   - Verify pattern combinations
   - Check error reporting

## Contributing

1. **Adding New Features**
   - Update terminology.json
   - Add appropriate tests
   - Update documentation

2. **Bug Fixes**
   - Reproduce the issue
   - Fix in terminology.json if pattern-related
   - Update affected code
   - Add regression tests

## Dependencies

The project requires the following Python packages:
- `gradio>=4.0.0`: For the web interface
- `python-docx>=0.8.11`: For DOCX report generation
- `beautifulsoup4>=4.12.0`: For HTML parsing in DOCX generation
- `pdfkit>=1.0.0`: For PDF report generation
- `nltk>=3.9.1`: For natural language processing
- `pandas>=2.2.1`: For data manipulation
- `numpy>=1.24.3`: For numerical operations
- `pydantic>=2.11.4`: For data validation
- `colorama>=0.4.6`: For terminal coloring
- `typing-extensions>=4.9.0`: For type hints
- `filetype>=1.2.0`: For file type detection
- `python-multipart>=0.0.20`: For file upload handling

### Additional System Requirements

For PDF generation, you need to install `wkhtmltopdf`:
- Windows: Download from https://wkhtmltopdf.org/downloads.html
- Linux: `sudo apt-get install wkhtmltopdf`
- Mac: `brew install wkhtmltopdf`

## File Generation

The application supports generating reports in multiple formats:

### HTML Reports
- Default format
- Includes all styling and formatting
- Saved to `downloads` directory

### PDF Reports
- Requires `wkhtmltopdf` installation
- Maintains formatting and styling
- Saved to `downloads` directory

### DOCX Reports
- Compatible with Microsoft Word
- Preserves document structure
- Includes headings, bullet points, and formatting
- Saved to `downloads` directory

All reports are saved in the `downloads` directory with timestamps in the filename format: `document_check_report_YYYYMMDD_HHMMSS.{format}`