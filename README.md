# Document Checker Tool

## Overview
This tool helps review and validate Federal Aviation Administration (FAA) documents for compliance with formatting rules and style guidelines. It's designed to catch common errors and inconsistencies that might occur in regulatory documents, making the review process faster and more accurate.

## What Does It Do?
The tool reads Microsoft Word (docx) documents and performs a comprehensive set of checks to ensure they follow FAA documentation standards. Think of it as a specialized proofreader that knows all the specific rules for FAA documents.

## Document Types Supported
- Advisory Circulars (both Short and Long templates)
- Airworthiness Criteria
- Deviation Memos
- Exemptions
- Federal Register Notices
- Handbooks/Manuals
- Orders
- Policy Statements
- Rules
- Special Conditions
- Technical Standard Orders
- Other document types

## What Does It Check For?

### 1. Required Headings
- Verifies that all required section headings are present
- Different document types have different required headings
- For example, Advisory Circulars (AC) must have sections like "PURPOSE.", "APPLICABILITY.", etc.

### 2. Acronym Usage
- Checks if all acronyms are properly defined at their first use
- Example: "Federal Aviation Administration (FAA)" must appear before using just "FAA"
- Identifies any undefined acronyms in the document

### 3. Legal Terminology
- Ensures proper formatting of legal references
- Checks for correct usage of terms like:
  - "U.S.C." instead of "USC"
  - "Title 14" instead of "title 14" when used in body text. Use "Title 14" when begins a sentence.
  - "CFR part" instead of "CFR Part" when used in body text.
- Verifies proper use of "the FAA" instead of "We" or "we"

### 4. Table and Figure Formatting
- Validates table captions (e.g., for ACs, "Table 1-2" or "Table C-1")
- Checks figure captions (e.g., for ACs, "Figure 1-2" or "Figure C-1")
- Ensures proper references to tables and figures within the text

### 5. Document Title Styling
- Checks if document titles are properly formatted based on document type
- Some documents require italics, others require quotation marks
- Ensures consistent styling throughout the document

### 6. Grammar and Formatting
- Catches double periods at the end of sentences
- Checks for proper spacing:
  - Between document type and number (e.g., "AC 20-114")
  - Around section symbols (e.g., "§ 25.301")
  - Around part numbers (e.g., "Part 25")
  - In paragraph indications (e.g., "(a)", "(1)")
- Identifies double spaces between words

### 7. Consistency Checks
- Verifies that abbreviations are used consistently after being defined
- Ensures dates are in the correct format (e.g., "January 1, 2024" instead of "1/1/24" or "1 January 2024")
- Identifies placeholder text that needs to be replaced (e.g., "TBD", "To be determined")

## How to Use the Tool

1. Run the program
2. When prompted, either:
   - Press Enter to use the default document path
   - Type in the full path to your Word document

3. Select your document type from the numbered list

4. If you're checking an Advisory Circular, select the template type:
   - Short AC template
   - Long AC template

5. The tool will process your document and create a file called "check_complete.md" with the results

## Understanding the Results

The results file ("check_complete.md") will show:
- ✅ Passed checks
- ❌ Items that need attention
- Specific examples of what needs to be fixed
- Suggestions for corrections

## Important Notes

- The tool doesn't make any changes to your original document
- It's designed to assist reviewers, not replace human review
- All findings should be verified by a human reviewer
- The tool works best with properly formatted Microsoft Word documents
- Some document types may have "TBD - Need to research" for required headings as these requirements are still being documented

## Technical Requirements

- Microsoft Word must be installed on your computer
- The document must be in .docx format
- Python must be installed with the required libraries:
  - python-docx
  - logging
  - re (regular expressions)
