---
title: Document Checker Tool
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.19.2
app_file: app.py
pinned: false
---

# Document Checker Tool

A tool for checking documents against FAA style guidelines.

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
20. Paragraph Length Check
21. Sentence Length Check

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

--- 

**Note:** This tool is a work in progress. Expect more features and updates in the future to meet evolving document requirements.
