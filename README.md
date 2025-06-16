---
title: Document Checker Tool
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.27.0
app_file: app.py
pinned: false
---

# Document Checker Tool

A tool for checking and validating documents against FAA standards, with a modern web frontend, FastAPI backend, and legacy Gradio UI.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
    - [Python Environment (Backend & Gradio)](#python-environment-backend--gradio)
    - [Frontend (React App)](#frontend-react-app)
4. [Running the Application](#running-the-application)
    - [Start the Backend API](#start-the-backend-api)
    - [Start the Frontend Website](#start-the-frontend-website)
    - [Run the Gradio App (Legacy/Alternative)](#run-the-gradio-app-legacyalternative)
5. [Running Tests](#running-tests)
6. [Development Tools & Best Practices](#development-tools--best-practices)
7. [Rationale & Architecture](#rationale--architecture)
8. [License](#license)

---

## Project Overview

- **Document validation** against FAA and regulatory standards.
- **Multiple document type support**.
- **Modern web interface** (React + Vite).
- **API backend** (FastAPI).
- **Legacy Gradio UI** for quick local or Hugging Face Spaces use.
- **Detailed error reporting** and structured logging.
- **Displays document metadata** (title, author, last modified by) before the
  results.

---

## What Does the Document Checker Tool Check?

The Document Checker Tool automatically reviews your document for a wide range of common FAA and regulatory issues. Here are the main types of checks it performs, with examples of what it can detect and suggest:

| Issue Type | Description | Example Fix |
|------------|-------------|-------------|
| **Required Headings Check** | Verifies all mandatory section headings are present and correctly formatted. | _Before:_ Missing required heading "PURPOSE."<br>_After:_ Added heading "PURPOSE." at the beginning of the document |
| **Heading Period Format** | Ensures headings have correct punctuation for your document type. | _Before:_ Purpose<br>_After:_ Purpose. |
| **Table and Figure References** | Checks that references to tables/figures are capitalized correctly depending on sentence position. | _Before:_ The DTR values are specified in Table 3-1 and Figure 3-2.<br>_After:_ The DTR values are specified in table 3-1 and figure 3-2. |
| **Acronym Definition Issues** | Ensures every acronym is defined at first use. | _Before:_ This order establishes general FAA organizational policies.<br>_After:_ This order establishes general Federal Aviation Administration (FAA) organizational policies. |
| **Unused Acronym Definitions** | Flags acronyms that are defined but never used. | _Before:_ Operators must comply with airworthiness directives (AD)...<br>_After:_ Operators must comply with airworthiness directives... |
| **Incorrect Terminology** | Flags non-compliant, ambiguous, or outdated terms. | _Before:_ Operators shall comply with ADs...<br>_After:_ Operators must comply with ADs... |
| **Section Symbol (§) Format Issues** | Checks for correct use of section symbols in references. | _Before:_ § 23.3 establishes design criteria.<br>_After:_ Section 23.3 establishes design criteria. |
| **Multiple Period Issues** | Detects accidental double periods at sentence ends. | _Before:_ ...in this document..<br>_After:_ ...in this document. |
| **Spacing Issues** | Ensures proper spacing around references and sentences. | _Before:_ AC25.25 states that  SFAR88...<br>_After:_ AC 25.25 states that SFAR 88... |
| **Date Format Issues** | Checks that dates use the correct format. | _Before:_ ...dated 7/25/2006.<br>_After:_ ...dated July 25, 2006. |
| **Placeholder Content** | Flags incomplete content or placeholders like "TBD". | _Before:_ Pilots must submit the [Insert text] form...<br>_After:_ Pilots must submit the Report of Eye Evaluation form 8500-7... |
| **Parentheses Balance Check** | Ensures all parentheses are properly paired. | _Before:_ The system (as defined in AC 25-11B performs...<br>_After:_ The system (as defined in AC 25-11B) performs... |
| **Paragraph Length Issues** | Flags paragraphs that are too long for readability. | _Before:_ A very long paragraph...<br>_After:_ Multiple shorter paragraphs... |
| **Sentence Length Issues** | Highlights sentences longer than 35 words. | _Before:_ The operator must ensure that all required maintenance procedures are performed...<br>_After:_ The operator must ensure all required maintenance procedures are performed... |
| **Referenced Document Title Format Issues** | Checks formatting of referenced document titles. | _Before:_ See AC 25.1309-1B, System Design and Analysis...<br>_After:_ See AC 25.1309-1B, <i>System Design and Analysis</i>... |
| **Section 508 Compliance Issues** | Checks for accessibility features like alt text, heading structure, and descriptive links. | _Before:_ Image without alt text, skipped heading levels<br>_After:_ Added alt text, fixed heading hierarchy |
| **Hyperlink Issues** | Checks for broken or inaccessible URLs. | _Before:_ See https://broken-link.example.com...<br>_After:_ See https://www.faa.gov... |
| **Cross-Reference Issues** | Checks for missing or invalid cross-references. | _Before:_ See table 5-2 for more information. (no table 5-2)<br>_After:_ Update the table reference or add table 5-2 |
| **Readability Issues** | Analyzes readability and flags passive voice or jargon. | _Before:_ The implementation of the procedure was facilitated by technical personnel.<br>_After:_ Technical staff helped start the procedure. |
| **Accessibility Issues** | Checks for missing accessibility features. | _Before:_ Image without alt text, skipped heading levels<br>_After:_ Added alt text, fixed heading hierarchy |
| **Document Watermark Issues** | Verifies the document has the correct watermark for its stage. | _Before:_ Missing watermark or incorrect watermark "draft"<br>_After:_ Added correct watermark "draft for public comment" |
| **Required Boilerplate Text Issues** | Ensures all required standard text sections are present. | _Before:_ Missing required disclaimer text for Advisory Circular<br>_After:_ Added "This AC is not mandatory and does not constitute a regulation." |
| **Required Language Issues** | Verifies all required standardized language is present. | _Before:_ Missing Paperwork Reduction Act statement<br>_After:_ Added complete Paperwork Reduction Act statement |
| **Table/Figure Caption Format Issues** | Checks that captions follow proper numbering format. | _Before:_ Table 5.<br>_After:_ Table 5-1. |

---

## Detailed Check Descriptions

This section provides comprehensive descriptions of each check performed by the Document Checker Tool, including solutions and detailed examples.

### Required Headings Check
**Description:** Verifies that your document includes all mandatory section headings. Note: The "Cancellation." heading is only required if this document cancels or replaces an existing document. If your document is new or doesn't cancel anything, you can ignore the Cancellation heading warning.

**Solution:** Add all required headings in the correct order using the correct capitalization format. For cancellation warnings, only add the heading if you are actually canceling a document.

**Example Fix:**
- **Before:** Missing required heading "PURPOSE."
- **After:** Added heading "PURPOSE." at the beginning of the document

### Heading Period Format
**Description:** Examines heading punctuation to ensure compliance with FAA document formatting standards. Some FAA documents (like Advisory Circulars and Orders) require periods at the end of headings, while others (like Federal Register Notices) don't.

**Solution:** Format heading periods according to document type requirements.

**Example Fix:**
- **Before:** Purpose
- **After:** Purpose. (For ACs and Orders)

### Table and Figure References
**Description:** Analyzes how tables and figures are referenced within your document text. Capitalize references at the beginning of sentences (e.g., "Table 2-1 shows...") and use lowercase references within sentences (e.g., "...as shown in table 2-1").

**Solution:** Capitalize references at start of sentences, use lowercase within sentences.

**Example Fix:**
- **Before:** The DTR values are specified in Table 3-1 and Figure 3-2.
- **After:** The DTR values are specified in table 3-1 and figure 3-2.

### Acronym Definition Issues
**Description:** Ensures every acronym is properly introduced with its full term at first use. The check identifies undefined acronyms while recognizing common exceptions (like U.S.) that don't require definition.

**Solution:** Define each acronym at its first use, e.g., "Federal Aviation Administration (FAA)".

**Example Fix:**
- **Before:** This order establishes general FAA organizational policies.
- **After:** This order establishes general Federal Aviation Administration (FAA) organizational policies.

### Unused Acronym Definitions
**Description:** Ensures that all acronyms defined in the document are actually used later. If an acronym is defined but never referenced, the definition should be removed to avoid confusion or unnecessary clutter.

**Solution:** Identify acronyms that are defined but not used later in the document and remove their definitions.

**Example Fix:**
- **Before:** Operators must comply with airworthiness directives (AD) to ensure aircraft safety and regulatory compliance.
- **After:** Operators must comply with airworthiness directives to ensure aircraft safety and regulatory compliance.

### Incorrect Terminology
**Description:** Evaluates document text against the various style manuals and orders to identify non-compliant terminology, ambiguous references, and outdated phrases. This includes checking for prohibited relative references (like "above" or "below"), proper legal terminology (like "must" instead of "shall"), and consistent formatting of regulatory citations.

**Solution:** Use explicit references to paragraphs, sections, tables, and figures.

**Example Fix:**
- **Before:** Operators shall comply with ADs to ensure aircraft safety and regulatory compliance
- **After:** Operators must comply with ADs to ensure aircraft safety and regulatory compliance.

### Section Symbol (§) Format Issues
**Description:** Examines the usage of section symbols (§) throughout your document. This includes verifying proper symbol placement in regulatory references, ensuring sections aren't started with the symbol, checking consistency in multiple-section citations, and validating proper CFR citations. For ACs, see FAA Order 1320.46.

**Solution:** Format section symbols correctly and never start sentences with them.

**Example Fix:**
- **Before:** § 23.3 establishes design criteria.
- **After:** Section 23.3 establishes design criteria.

### Multiple Period Issues
**Description:** Examines sentences for accidental double periods that often occur during document editing and revision. While double periods are sometimes found in ellipses (...) or web addresses, they should never appear at the end of standard sentences in FAA documentation.

**Solution:** Remove multiple periods that end sentences.

**Example Fix:**
- **Before:** The following ACs are related to the guidance in this document..
- **After:** The following ACs are related to the guidance in this document.

### Spacing Issues
**Description:** Analyzes document spacing patterns to ensure compliance with FAA formatting standards. This includes checking for proper spacing around regulatory references (like "AC 25-1" not "AC25-1"), section symbols (§ 25.1), paragraph references, and multiple spaces between words.

**Solution:** Fix spacing issues: remove any missing spaces, double spaces, or inadvertent tabs.

**Example Fix:**
- **Before:** AC25.25 states that  SFAR88 and §25.981 require...
- **After:** AC 25.25 states that SFAR 88 and § 25.981 require...

### Date Format Issues
**Description:** Examines all date references in your document. The check automatically excludes technical reference numbers that may look like dates to ensure accurate validation of true date references. Note, though, there might be instances in the heading of the document where the date is formatted as "MM/DD/YYYY", which is acceptable. This applies mostly to date formats within the document body.

**Solution:** Use the format "Month Day, Year" where appropriate.

**Example Fix:**
- **Before:** This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated 7/25/2006.
- **After:** This policy statement cancels Policy Statement PS-AIR100-2006-MMPDS, dated July 25, 2006.

### Placeholder Content
**Description:** Identifies incomplete content and temporary placeholders that must be finalized before document publication. This includes common placeholder text (like "TBD" or "To be determined"), draft markers, and incomplete sections.

**Solution:** Replace all placeholder content with actual content.

**Example Fix:**
- **Before:** Pilots must submit the [Insert text] form to the FAA for approval.
- **After:** Pilots must submit the Report of Eye Evaluation form 8500-7 to the FAA for approval.

### Parentheses Balance Check
**Description:** Ensures that all parentheses in the document are properly paired with matching opening and closing characters.

**Solution:** Add missing opening or closing parentheses where indicated.

**Example Fix:**
- **Before:** The system (as defined in AC 25-11B performs...
- **After:** The system (as defined in AC 25-11B) performs...

### Paragraph Length Issues
**Description:** Flags paragraphs exceeding 6 sentences or 8 lines to enhance readability and clarity. While concise paragraphs are encouraged, with each focusing on a single idea or related points, exceeding these limits doesn't necessarily indicate a problem. Some content may appropriately extend beyond 8 lines, especially if it includes necessary details. Boilerplate language or template text exceeding these limits is not subject to modification or division.

**Solution:** Where possible, split long paragraphs into smaller sections, ensuring each focuses on one primary idea. If restructuring is not feasible or the content is boilerplate text, no changes are needed.

**Example Fix:**
- **Before:** A very long paragraph covering multiple topics and spanning many lines...
- **After:** Multiple shorter paragraphs or restructured paragraphs, each focused on a single topic or related points.

### Sentence Length Issues
**Description:** Analyzes sentence length to ensure readability. While the ideal length varies with content complexity, sentences over 35 words often become difficult to follow. Technical content, regulatory references, notes, warnings, and list items are excluded from this check.

**Solution:** Break long sentences into smaller ones where possible, focusing on one main point per sentence. Consider using lists for complex items.

**Example Fix:**
- **Before:** The operator must ensure that all required maintenance procedures are performed in accordance with the manufacturer's specifications and that proper documentation is maintained throughout the entire process to demonstrate compliance with regulatory requirements.
- **After:** The operator must ensure all required maintenance procedures are performed according to manufacturer specifications. Additionally, proper documentation must be maintained to demonstrate regulatory compliance.

### Referenced Document Title Format Issues
**Description:** Checks document title formatting based on document type. Advisory Circulars require italics without quotes, while all other document types require quotes without italics.

**Solution:** Format document titles according to document type: use italics for Advisory Circulars, quotes for all other document types.

**Example Fix:**
- **Before:** See AC 25.1309-1B, System Design and Analysis, for information on X.
- **After:** See AC 25.1309-1B, <i>System Design and Analysis</i>, for information on X.

### Section 508 Compliance Issues
**Description:** Checks document accessibility features required by Section 508 standards: Image alt text for screen readers, heading structure issues (missing heading 1, skipped heading levels, and out of sequence headings), and hyperlink accessibility (ensuring links have meaningful descriptive text).

**Solution:** Address each accessibility issue: add image alt text for screen readers, fix heading structure, and ensure hyperlinks have descriptive text that indicates their destination.

**Example Fix:**
- **Before:**
  - Image without alt text
  - Heading sequence: H1 → H2 → H4 (skipped H3)
  - Link text: "click here" or "www.example.com"
- **After:**
  - Image with descriptive alt text
  - Proper heading sequence: H1 → H2 → H3 → H4
  - Descriptive link text: "FAA Compliance Guidelines" or "Download the Safety Report"

### Hyperlink Issues
**Description:** Checks for potentially broken or inaccessible URLs in the document. This includes checking response codes and connection issues.

**Solution:** Verify each flagged URL is correct and accessible.

**Example Fix:**
- **Before:** See https://broken-link.example.com for more details.
- **After:** See https://www.faa.gov for more details.

### Cross-Reference Issues
**Description:** Checks for missing or invalid cross-references to paragraphs, tables, figures, and appendices within the document.

**Solution:** Ensure that all referenced elements are present in the document and update or remove any incorrect references.

**Example Fix:**
- **Before:** See table 5-2 for more information. (there is no table 5-2)
- **After:** Either update the table reference or add table 5-2 if missing

### Readability Issues
**Description:** Analyzes document readability using multiple metrics including Flesch Reading Ease, Flesch-Kincaid Grade Level, and Gunning Fog Index. Also checks for passive voice usage and technical jargon. The analysis section reports the overall percentage of passive voice sentences.

**Solution:** Simplify language, reduce passive voice, and replace technical jargon with plain language alternatives.

**Example Fix:**
- **Before:** The implementation of the procedure was facilitated by technical personnel.
- **After:** Technical staff helped start the procedure.

### Accessibility Issues
**Description:** Checks document accessibility including alt text, heading structure, and hyperlinks.

**Solution:** Add missing accessibility features and fix structural issues.

**Example Fix:**
- **Before:** Image without alt text, skipped heading levels
- **After:** Added alt text, fixed heading hierarchy

### Document Watermark Issues
**Description:** Verifies that the document has the appropriate watermark for its current stage (internal review, public comment, AGC review, or final issuance).

**Solution:** Add or update the watermark to match the document's current stage.

**Example Fix:**
- **Before:** Missing watermark or incorrect watermark "draft"
- **After:** Added correct watermark "draft for public comment"

### Required Boilerplate Text Issues
**Description:** Ensures that all required standard text sections are present based on document type (like required disclaimers in ACs and Policy Statements).

**Solution:** Add all required boilerplate text sections from the document template.

**Example Fix:**
- **Before:** Missing required disclaimer text for Advisory Circular
- **After:** Added "This AC is not mandatory and does not constitute a regulation."

### Required Language Issues
**Description:** Verifies that document contains all required standardized language based on document type (like specific statements required in Federal Register notices).

**Solution:** Add all required standard statements for the document type.

**Example Fix:**
- **Before:** Missing Paperwork Reduction Act statement in Federal Register notice
- **After:** Added complete Paperwork Reduction Act statement

### Table/Figure Caption Format Issues
**Description:** Checks that table and figure captions follow proper numbering format based on document type (chapter-based for ACs/Orders, sequential for other documents).

**Solution:** Format captions according to document type requirements.

**Example Fix:**
- **Before:** Table 5.
- **After:** Table 5-1. (For ACs and Orders)

---

## Project Structure

```
project-root/
├── backend/                   # FastAPI backend (API for document processing)
│   ├── main.py
│   ├── api.py
│   └── requirements.txt
├── frontend/faa-doc-checker/  # React frontend (user-facing web app)
│   ├── package.json
│   ├── src/
│   └── ...
├── documentcheckertool/       # Core Python logic, checks, models, utils
├── tests/                     # Python tests (pytest)
├── app.py                     # Gradio app entry point (legacy/alternative)
├── requirements.txt           # Python dependencies (core)
├── pyproject.toml             # Poetry config (preferred for dev)
└── ...
```

---

## Python Requirements: Which File to Use?

**There are two requirements files for Python dependencies:**

- `requirements.txt`: Core runtime requirements. Use this if you only want to *run* the app (Gradio UI or backend API) in production or as an end user.
- `requirements-dev.txt`: Development and testing requirements. Use this if you want to *develop*, *test*, or *contribute* to the project. This file includes everything in `requirements.txt` plus extra tools for testing, linting, and code quality.

**Which should you install?**

- **For development, testing, or contributing:**
  ```bash
  pip install -r requirements-dev.txt
  ```
  This will install all runtime and dev dependencies (no need to install both files).

- **For production or just running the app:**
  ```bash
  pip install -r requirements.txt
  ```
  This installs only the minimal set of packages needed to run the app.

**Tip:** If you're not sure, use `requirements-dev.txt` for the most complete setup.

---

## Setup Instructions

### 1. Python Environment (Backend & Gradio)

**From the project root directory:**

#### a. Using venv + pip
```bash
# In project root
python -m venv docchecker
# On Windows:
docchecker\Scripts\activate
# On Mac/Linux:
source docchecker/bin/activate
pip install -r requirements-dev.txt  # For development/testing
# Or, for production only:
pip install -r requirements.txt
```

#### b. Using Poetry (Recommended for Devs)
```bash
# In project root
poetry install
```

---

### 2. Frontend (React App)

**From the frontend directory:**
```bash
cd frontend/faa-doc-checker
npm install
```

---

## Running the Application

> **Note:** You will need to use **two separate terminals** (or terminal tabs/windows):
> - **Terminal 1:** For running the backend API (FastAPI)
> - **Terminal 2:** For running the frontend (React app)
> This allows both the backend and frontend to run simultaneously. Do **not** close the backend terminal when starting the frontend.

### 1. Start the Backend API

**In Terminal 1, from the backend directory:**
```bash
cd backend
pip install -r requirements.txt  # Only needed once
uvicorn backend.main:app --reload
```
- The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).
- Set `ALLOW_ORIGINS` to a comma-separated list to restrict CORS (defaults to `*`).

### 2. Start the Frontend Website

**In Terminal 2, from the frontend directory:**
```bash
cd frontend/faa-doc-checker
npm run dev
```
- The app will be available at [http://localhost:5173](http://localhost:5173).
- The frontend expects the backend API to be running at `http://127.0.0.1:8000`.

---

### 3. Run the Gradio App (Legacy/Alternative)

**From the project root:**
```bash
python app.py
# Or with Poetry:
poetry run python app.py
```
- Use `--debug` for verbose logging.
- Use `--host` and `--port` to specify the server address.

---

## Running Tests

**From the project root directory:**

### a. With Poetry (Recommended)
```bash
poetry run pytest
```

### b. With pip/venv
```bash
pip install pytest pytest-cov pytest-asyncio
pytest
```

### c. Run a specific test file (e.g., terminology checks)
```bash
pytest -v tests/test_terminology_checks.py --log-cli-level=DEBUG
```

### d. Test Coverage
```bash
poetry run pytest --cov=documentcheckertool
```

**Note:**
If you see `ModuleNotFoundError: No module named 'documentcheckertool'`, run:
```bash
pip install -e .
```
from the project root, or always use `poetry run ...` if using Poetry.

If you encounter a build error like `invalid command 'bdist_wheel'`, ensure the
`wheel` package is installed. This dependency is listed in `requirements.txt`.

---

## Development Tools & Best Practices

- **Pre-commit hooks:**
  ```bash
  poetry run pre-commit install
  ```
- **Linting:**
  ```bash
  poetry run ruff check .
  ```
- **Type Checking:**
  ```bash
  poetry run mypy .
  ```
- **Logging:**
  All major modules use Python's `logging`. Enable debug with `--debug`.
- **Pydantic:**
  Used for runtime type-checking and validation.

---

## Rationale & Architecture

- **Modern React frontend** and **FastAPI backend** for scalability and maintainability.
- **Gradio UI** remains for quick local use or Hugging Face Spaces.
- **Testing** is managed with `pytest` and integrated with Poetry and CI.
- **Frontend and backend are decoupled**: run both for the full web experience, or just the backend/Gradio for API/CLI use.

---

## License

MIT License

---

**If you have any issues or need further help, please open an issue or contact the maintainers.**

---

## 1. Introduction

### Purpose
The **Document Checker Tool** streamlines the review process by:
- Enhancing consistency and compliance with FAA and regulatory standards.
- Automating manual checks for improved speed and accuracy.
- Improving clarity and professionalism in FAA documents.

This tool provides **recommendations** to aid document authors, who retain final decision-making authority.

### Scope
Supports all FAA document types covered by AIR-646, with checks aligned to:
- GPO Style Manual
- FAA Orders
- Document Drafting Handbook
- AIR-600 Quick Reference Guide
- Internal memos, templates, and more

---

## 2. Revision History

- **2/10/2025:** Changed "notice to air missions" to "notice to airmen" per GENOT N 7930.114.
- **1/5/2025:** Added checks for 508 accessibility, heading levels, cross-references, and broken links. Updated the acronym checker for better accuracy.
- **12/8/2024:** Added paragraph and sentence length checks. Reorganized checks for workflow improvements. Updated the date format check to exclude certain AC numbers.
- **11/26/2024:** Initial release with 15 checks.

---

## 3. Checker Categories Overview

### Key Checker Categories
1. Readability Check
2. Heading Title Checks
3. Heading Period Format Check
4. Terminology Checks
5. Acronym Check
6. Acronym Usage Check
7. Section Symbol (§) Checks
8. 508 Compliance Check (basic checks)
9. Cross Reference Check
10. Broken Link Check
11. Date Format Consistency Check
12. Placeholder Content Check
13. Referenced Document Title Format Check
14. Table Caption Check
15. Figure Caption Check
16. Table/Figure Reference Check
17. Parenthesis Balance Check
18. Double Period Check
19. Spacing Check
20. Phone Number Format Check
21. Paragraph Length Check
22. Sentence Length Check

---

## 4. Details of Each Checker

### 1. Readability Check
Analyzes document readability using multiple metrics including Flesch Reading Ease, Flesch-Kincaid Grade Level, and Gunning Fog Index. Also checks for passive voice usage and technical jargon.

---

### Heading Checks

#### 2. Heading Title Check
Verifies required headings are present and formatted according to document type. Note that for ACs, if the AC cancels another AC, you need the Cancellation paragraph. If it doesn't cancel another AC, then you don't need it.

**Examples:**
- **Advisory Circulars:** Purpose, Applicability, Cancellation, Related Material, Definition of Key Terms
- **Federal Register Notice:** Purpose of This Notice, Audience, Where to Find This Notice
- **Orders:** Purpose of This Order, Audience, Where to Find This Order

#### 3. Heading Period Format Check
Verifies if headings include or omit periods based on document type.

**Examples:**
- **Requires Periods:** Advisory Circulars, Orders, Technical Standard Orders
- **No Periods:** Other document types

---

### Terminology Checks

#### 4. Terminology Usage Check
Flags non-compliant or outdated terms, ensuring adherence to FAA terminology standards.

**Examples:**
- Replace "shall" with "must" per GPO Style Manual.
- Replace "flight crew" with "flightcrew" per AIR-600 Quick Reference Guide.

---

### Acronym and Abbreviation Checks

#### 5. Acronym Check
Verifies acronyms are defined upon first use.

**Example:** Federal Aviation Administration (FAA)

#### 6. Acronym Usage Check
Identifies acronyms that are defined but not subsequently used.

---

### Section Symbol (§) Checks

#### 7. Section Symbol Usage Check
Ensures section symbols are formatted correctly.

**Examples:**
- Use "14 CFR 21.21" instead of "14 CFR § 21.21".
- Use "§§ 25.25 and 25.26" for multiple references.

---

### 508 Compliance Check

#### 8. 508 Compliance Checks
- Detects images missing alternative text
- Identifies skipped heading structures
- Flags hyperlinks that lack descriptive text indicating their destination.

---

### Reference Checks

#### 9. Cross Reference Check
Validates that all references to paragraphs, appendices, tables, or figures exist in the document.

#### 10. Broken Link Check
Identifies non-functional or broken hyperlinks.

---

### Date and Placeholder Checks

#### 11. Date Format Consistency Check
Ensures date formatting matches the "Month Day, Year" convention.

**Examples:**
- Correct "1/15/24" to "January 15, 2024".

#### 12. Placeholder Content Check
Flags placeholders like "TBD" or "To be added".

---

### Document Title Checks

#### 13. Referenced Document Title Format Check
Checks formatting of referenced document titles.

**Examples:**
- **Italicized:** Advisory Circulars
- **Quotation Marks:** Other document types

---

### Table and Figure Checks

#### 14. Table Caption Check
Ensures table captions follow numbering conventions by document type.

#### 15. Figure Caption Check
Verifies figure captions adhere to proper numbering.

#### 16. Table/Figure Reference Check
Checks capitalization of references depending on placement in a sentence.

---

### Syntax and Punctuation Checks

#### 17. Parenthesis Balance Check
Ensures parentheses are properly paired.

**Example:** Corrects "(as defined in AC 25-11B performs..." to include a closing parenthesis.

#### 18. Double Period Check
Identifies unintended multiple periods.

**Example:** Corrects "ends with two periods..".

#### 19. Spacing Check
Verifies consistent spacing around references and sentences.

**Examples:**
- Correct "AC25.1" to "AC 25.1".
- Remove extra spaces after periods.

---

### Length Checks

#### 20. Paragraph Length Check
Flags paragraphs exceeding six sentences or eight lines.

#### 21. Sentence Length Check
Highlights sentences longer than 35 words.

#### 22. Section Balance (Section Length) Check

The Section Balance (Section Length) Check analyzes the length of each section in your document to ensure sections are reasonably balanced and not significantly longer than others. **This check uses heading levels to define the start of each section.**

- **How it works:**
  - The checker scans all paragraphs in the document.
  - Whenever it encounters a paragraph styled as a heading (e.g., "Heading 1", "Heading 2"), it starts a new section.
  - All content under that heading—including normal paragraphs, subheadings, and bulleted or numbered lists—is counted as part of the section until the next heading of the same or higher level is found.
  - For each section, the checker records the section name (from the heading) and the number of paragraphs it contains.
  - The checker also determines if a section is a "list section" (based on the heading text or if most paragraphs are bulleted) and uses a higher threshold for flagging long list sections.
  - After processing the document, the checker compares the length of each section to the average for list and non-list sections, flagging any that are much longer than average.

- **What gets flagged:**
  - If a section contains significantly more paragraphs than the average for that type (list or non-list), it is flagged as "significantly longer than average."
  - The warning includes the section name, its length, and the average length for comparison.

- **What content is included in the count:**
  - All paragraphs, subheadings, and bulleted/numbered lists under a heading are included in the section's length.
  - The checker does **not** distinguish between different heading types or between bulleted lists and normal paragraphs—everything under the heading is counted.
  - If you have subheadings or lists under a heading, they are all included in the parent section's length until the next heading of the same or higher level.

**Example:**
If a section titled "Background" contains 50 paragraphs (including text, subheadings, and lists) and the average section length is 10 paragraphs, this section will be flagged as significantly longer than average.

---

**Note:** This tool is a work in progress. Expect more features and updates in the future to meet evolving document requirements.

## Development Setup with Poetry

This project uses [Poetry](https://python-poetry.org/) for dependency management. Follow these steps to set up your development environment:

1. Install Poetry:
   ```bash
   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

   # macOS/Linux
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Run the application:
   ```bash
   poetry run python -m document_checker.main
   ```

### Development Tools

The project includes several development tools configured in Poetry:

- **Linting**: `poetry run ruff check .`
- **Type Checking**: `poetry run mypy .`
- **Security Scanning**: `poetry run bandit -r .`
- **Testing**: `poetry run pytest`
- **Dead Code Detection**: `poetry run vulture .`

### Pre-commit Hooks

Pre-commit hooks are configured to run checks before each commit:

```bash
poetry run pre-commit install
```

## 5. Recent Changes and Advanced Features

### Heading Checks Improvements
- **Stricter heading validation**: Headings are now checked for maximum length, valid heading words, and proper case (uppercase enforced for most types).
- **Conditional/optional headings**: For document types like Advisory Circulars, missing optional headings (e.g., CANCELLATION) are reported as INFO, not errors.
- **Document type normalization**: Document type input is normalized (case, whitespace, etc.) for robust matching, but unknown types are preserved as-is.
- **Detailed error reporting**: Issues now include type, severity, suggestions, and more context.
- **Test coverage**: Extensive tests for heading checks, including edge cases (mixed case, missing/extra periods, length violations, optional headings, etc.).

### Logging and Debugging
- **Structured logging**: All major modules use Python's `logging` with detailed messages at key execution points. Log level can be set via CLI or environment.
- **Debug mode**: Enable debug logging with `--debug` for verbose output, including function entry/exit, decision branches, and error handling.
- **Log file**: Logs are written to `document_checker.log` in addition to console output.

### Pydantic and Validation
- **Pydantic models**: Used for runtime type-checking and validation of inputs/outputs, especially for configuration and result models.
- **Error messaging**: Validation errors are reported with detailed messages for easier debugging.

### Test-Driven Development
- **Comprehensive tests**: All new features are covered by unit and integration tests (see `tests/`).
- **CI integration**: Tests are designed to run in CI pipelines for automated verification.

---

## 6. Changelog

- **2025-06-XX:** Major improvements to heading checks, document type normalization, logging, and Pydantic usage. Expanded test coverage for edge cases and error handling.

# Developer Documentation

# Document Checker Tool Developer Documentation

## Project Structure

```
documentcheckertool/
├── config/
│   └── terminology.json    # Single source of truth for all terminology and patterns
├── utils/
│   ├── terminology_utils.py  # Terminology management and validation
│   ├── text_utils.py        # General text processing utilities
│   ├── check_discovery.py   # Check discovery and validation utilities
│   └── ...
├── checks/
│   ├── check_registry.py    # Central registry for check functions
│   ├── acronym_checks.py    # Acronym-specific checks
│   ├── format_checks.py     # Formatting checks (uses registry)
│   └── ...
└── models/
    └── document_check.py    # Data models for check results
```

## Check Registry and Discovery System

### Overview
The check registry and discovery system provides a robust, maintainable, and extensible way to manage all document check functions. It ensures that all checks are categorized, discoverable, and validated automatically.

### Registering New Checks
To register a new check function or method, use the `@CheckRegistry.register(category)` decorator. This will automatically add the check to the central registry under the specified category.

**Example:**
```python
from documentcheckertool.checks.check_registry import CheckRegistry

class FormatChecks(BaseChecker):
    @CheckRegistry.register('format')
    def _check_date_formats(self, ...):
        ...

    @CheckRegistry.register('format')
    def _check_phone_numbers(self, ...):
        ...
```

- The decorator can be used on any function or method.
- The category string should match the intended check category (e.g., 'format', 'structure', 'terminology').

### Check Discovery
The system includes an auto-discovery utility (`utils/check_discovery.py`) that:
- Scans all check modules for functions/methods named `check_*` or `_check_*`.
- Finds all methods in classes inheriting from `BaseChecker`.
- Maps discovered checks to their categories.

### Validation
The `validate_check_registration()` function compares discovered checks with those registered in the registry:
- Reports missing categories or checks
- Reports extra checks (e.g., test-only or deprecated checks)
- Ensures consistency between code and registry

**Example usage:**
```python
from documentcheckertool.utils.check_discovery import validate_check_registration
results = validate_check_registration()
print(results)
```

### Best Practices for Adding Checks
- Always use the registry decorator for new checks.
- Use clear, descriptive names starting with `check_` or `_check_`.
- Group related checks in a class inheriting from `BaseChecker`.
- Run the validation utility after adding or refactoring checks.
- Add unit tests for new checks in the `tests/` directory.

### Debugging and Logging
- The registry and discovery system uses Python's `logging` for detailed debug output.
- Enable debug logging to trace check registration, discovery, and validation.
- Use log messages to troubleshoot missing or duplicate checks.

### Example: Adding a New Check
```python
from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.checks.base_checker import BaseChecker

class CustomChecks(BaseChecker):
    @CheckRegistry.register('custom')
    def check_custom_rule(self, ...):
        # Implement custom check logic
        ...
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

## Command-Line Arguments

> **Note:** The only supported CLI entry point is the root-level `cli.py` in the project root. Do **not** use any `cli.py` inside the `documentcheckertool` package for CLI usage. You can invoke the CLI in two ways:
>
> ```sh
> # positional arguments
> python cli.py <file> <document type>
> # or with explicit flags
> python cli.py --file <file> --type <document type> [other flags]
> ```

The Document Checker Tool supports the following command-line arguments when run via `python cli.py`:

| Argument                  | Type/Choices           | Description                                         |
|---------------------------|------------------------|-----------------------------------------------------|
| `--file FILE`             | string                 | Path to document file (**required**)                |
| `--type TYPE`             | string (see below)     | Document type (**required**)                        |
| `--group-by`              | category, severity     | Group results by category or severity               |
| `--debug`                 | flag                   | Enable debug mode                                   |
| `--show-all`              | flag                   | Show all sections (default)                         |
| `--hide-readability`      | flag                   | Hide readability metrics                            |
| `--hide-analysis`         | flag                   | Hide readability analysis details                  |
| `--hide-paragraph-length` | flag                   | Hide paragraph and sentence length checks           |
| `--hide-terminology`      | flag                   | Hide terminology checks                             |
| `--hide-acronym`          | flag                   | Hide acronym checks                                 |
| `--hide-headings`         | flag                   | Hide heading checks                                 |
| `--hide-structure`        | flag                   | Hide structure checks                               |
| `--hide-format`           | flag                   | Hide format checks                                  |
| `--hide-accessibility`    | flag                   | Hide accessibility checks                           |
| `--hide-document-status`  | flag                   | Hide document status checks                         |
| `--hide CATEGORY`         | string/list            | Hide the specified categories (comma- or space-separated). Mutually exclusive with --hide-*, --show-only, and --show-all. Categories: readability, analysis, paragraph_length, terminology, acronym, headings, structure, format, accessibility, document_status |
| `--show-only CATEGORY`    | string/list            | Show only the specified categories (comma- or space-separated). Mutually exclusive with --hide-* and --show-all. Categories: readability, analysis, paragraph_length, terminology, acronym, headings, structure, format, accessibility, document_status |

### Document Type Options for `--type`

- `Advisory Circular`
- `Airworthiness Criteria`
- `Deviation Memo`
- `Exemption`
- `Federal Register Notice`
- `Order`
- `Policy Statement`
- `Rule`
- `Special Condition`
- `Technical Standard Order`
- `Other`

### Group By Options for `--group-by`

- `category`
- `severity`

### Group-By Categories

When using `--group-by category`, results are grouped into the following categories:

- **heading**: Headings and heading structure
- **format**: Formatting and style
- **structure**: Document structure and organization
- **terminology**: Terminology and word usage
- **readability**: Readability metrics and checks
- **acronym**: Acronym usage and definitions
- **accessibility**: 508/accessibility checks
- **reference**: Table, figure, and cross-reference checks

**Example usage:**
```sh
python cli.py --file mydoc.docx --type "Advisory Circular" --group-by category
```

### Example CLI Usage

Here are several example commands demonstrating different CLI options:

- **Show only headings:**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only headings
  ```

- **Show only acronyms:**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only acronym
  ```

- **Show only multiple categories (e.g., headings and terminology):**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only headings terminology
  # or
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only headings,terminology
  ```

- **Hide multiple categories (e.g., readability and accessibility):**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --hide readability accessibility
  # or
  python cli.py --file mydoc.docx --type "Advisory Circular" --hide readability,accessibility
  ```

- **Hide acronyms only:**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --hide-acronym
  ```
  > **Note:** You can now use a single `--hide` flag with a comma- or space-separated list. This cannot be combined with any `--hide-*`, `--show-only`, or `--show-all` flags.

- **Basic usage (group by category, all sections shown):**
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --group-by category
  ```

- **Enable debug mode for verbose logging:**
  ```sh
  python cli.py --file mydoc.docx --type "Order" --debug
  ```

- **Hide readability checks:**
  ```sh
  python cli.py --file mydoc.docx --type "Order" --hide-readability
  ```

- **Hide analysis metrics:**
  ```sh
  python cli.py --file mydoc.docx --type "Order" --hide-analysis
  ```

- **Group results by severity:**
  ```sh
  python cli.py --file mydoc.docx --type "Federal Register Notice" --group-by severity
  ```

- **Combine multiple options (debug, hide readability, group by severity):**
  ```sh
  python cli.py --file mydoc.docx --type "Technical Standard Order" --group-by severity --debug --hide-readability
  ```

### Valid Categories for `--show-only`

- readability
- analysis
- paragraph_length
- terminology
- acronym
- headings
- structure
- format
- accessibility
- document_status

**Note:**
- `--show-only` cannot be combined with any `--hide-*` or `--show-all` flags.
- If you specify an invalid category, the CLI will show an error with valid options.

### Specifying the `--file` Argument

The value for `--file` should be the path to your document file. This can be:

- Just the filename (if the file is in your current working directory)
- A relative path (if the file is in a subdirectory)
- An absolute path (if the file is elsewhere on your system)

**Examples:**

| File Location                | Example `--file` Argument                                      |
|------------------------------|---------------------------------------------------------------|
| Current directory            | `--file AC_20-176B_Formal_FAA_Draft_v1a.docx`                 |
| Subdirectory (e.g., Downloads) | `--file Downloads/AC_20-176B_Formal_FAA_Draft_v1a.docx`      |
| Absolute path (Windows)      | `--file "C:\\Users\\computername\\Downloads\\AC_20-176B_Formal_FAA_Draft_v1a.docx"` |
| Absolute path (Unix/Mac)     | `--file "/home/computername/Downloads/AC_20-176B_Formal_FAA_Draft_v1a.docx"`        |

- Quotes are only needed if your path or filename contains spaces.
- Both forward slashes (`/`) and backslashes (`\`) work on Windows in Python.

**In summary:**
- Use just the filename if the file is in your current directory.
- Otherwise, provide a relative or absolute path to the file.

### Hiding vs. Showing Only Categories

| Action                | How to Specify Multiple Categories?         |
|-----------------------|---------------------------------------------|
| Hide categories       | Multiple `--hide-<category>` flags **or** single `--hide` with comma/space list |
| Show only categories  | Single `--show-only` with comma/space list  |

**Examples:**
- Hide readability and accessibility:
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --hide readability accessibility
  # or
  python cli.py --file mydoc.docx --type "Advisory Circular" --hide readability,accessibility
  ```
- Show only readability and accessibility:
  ```sh
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only readability accessibility
  # or
  python cli.py --file mydoc.docx --type "Advisory Circular" --show-only readability,accessibility
  ```
