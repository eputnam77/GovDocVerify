# Document Checker Tool  
**Ensuring FAA Document Compliance and Consistency**

---

## 1. Introduction

### Purpose  
The **Document Checker Tool** aims to:  
- Improve consistency and compliance with FAA and regulatory guidelines.  
- Automate tedious manual checks, providing faster and more accurate results.  
- Enhance clarity and professionalism in FAA documentation.

This tool provides **suggestions**, but the final editorial decisions rest with the document author.  

### Scope  
The tool supports all FAA document types AIR-646 supports and includes multiple categories of checks. 

The tool adheres to style and guidelines derived from:  
- GPO Style Manual  
- FAA Orders  
- Document Drafting Handbook  
- AIR-600 Quick Reference Guide  
- Internal memos, templates, and more  

---

## 2. Revision History

12/8/2024: Added checks for paragraph length and sentence length. Reordered existing checks for improved workflow. Updated the date format check to exclude certain AC numbers.

11/26/2024: Initial release with 15 checks.

---

## 3. Checker Categories Overview  

### 17 Key Checker Categories  
1. **Heading Title Checks**  
2. **Heading Period Format Check**
3. **Terminology Checks**
4. **Acronym Check**  
5. **Acronym Usage Check**  
6. **Section Symbol (§) Checks**  
7. **Date Format Check**
8. **Placeholder Content Check**
9. **Referenced Document Title Format Check**  
10. **Table Caption Check**  
11. **Figure Caption Check**  
12. **Table/Figure Reference Check**  
13. **Parenthesis Balance Check**
14. **Double Period Check**
15. **Spacing Check**  
16. **Paragraph Length Check**  
17. **Sentence Length Check**

---

## 4. Details of Each Checker  

### Heading Checks  

#### 1. Required Heading Title Check  
Verifies required headings are present and properly formatted based on document type.  

**Examples:**  

- **Advisory Circulars:**  
  - Purpose  
  - Applicability  
  - Cancellation  
  - Related Material  
  - Definition of Key Terms  

- **Federal Register Notice:**  
  - Purpose of This Notice  
  - Audience  
  - Where Can I Find This Notice  

- **Order:**  
  - Purpose of This Order  
  - Audience  
  - Where to Find This Order  

#### 2. Heading Period Format Check  
Ensures headings have or do not have periods based on document type.  

**Examples:**  
- **Required Period:** Advisory Circular, Order, Technical Standard Order  
- **No Period:** All other document types  

---

### Terminology Checks  

#### 3. Terminology Usage Check  
Flags outdated or vague terms and enforces FAA terminology standards.  

**Examples:**  
- Replace "shall" with "must" per GPO Style Manual.  
- Replace "flight crew" with "flightcrew" per AIR-600 Quick Reference Guide.  

---

### Acronym and Abbreviation Checks  

#### 4. Acronym Check  
Ensures acronyms are defined at first use.  
- **Example:** Federal Aviation Administration (FAA)  

#### 5. Acronym Usage Check  
Identifies acronyms defined but not used.  

---

### Section Symbol (§) Checks  

#### 6. Section Symbol Usage Check  
Ensures proper formatting for section symbols.  

**Examples:**  
- Replace "14 CFR § 21.21" with "14 CFR 21.21".  
- Replace "§ 25.25 and 25.26" with "§§ 25.25 and 25.26".  

---

### Date Format and Placeholder Checks  

#### 7. Date Format Consistency Check  
Ensures dates follow the "Month Day, Year" format in the document body.  

**Examples:**  
- Replace "1/15/24" with "January 15, 2024".  

#### 8. Placeholder Content Check  
Flags placeholders like "TBD" or "To be added."  

---

### Document Title Checks  

#### 9. Referenced Document Title Format Check  
Verifies correct formatting of referenced document titles.  

- **Italicize:** Advisory Circulars  
- **Quotation Marks:** Airworthiness Criteria, Deviation Memo, Exemption, Federal Register Notice, Order, Rule, Special Condition, Technical Standard Order
- **No Formatting:** Policy Statement and all others 

---

### Table and Figure Checks  

#### 10 & 11. Table/Figure Caption Checks  
Verifies captions follow correct numbering conventions based on document type.

**Examples:**  
- Table X-Y and Figure X-Y for Advisory Circulars and Orders.  
- Table X and Figure X for all other document types.

#### 12. Table/Figure Reference Check  
Ensures references are lowercase mid-sentence and capitalized at the start of a sentence.  

---

### Parenthesis Balance Check  

#### 13. Parenthesis Balance Check  
Verifies that all parentheses are properly opened and closed.  

**Examples:**  
- Add a missing closing parenthesis to "The system (as defined in AC 25-11B performs...".

---

### Punctuation and Spacing Checks  

#### 14. Double Period Check  
Flags unintended multiple periods.  

**Example:**  
- Corrects: "This sentence ends with two periods..".  

#### 15. Spacing Check  
Ensures proper spacing around references.  

**Examples:**  
- Replace "AC25.1" with "AC 25.1".  
- Remove double spaces between words or after periods.  

---

### Length Checks  

#### 16. Paragraph Length Check  
Flags paragraphs exceeding 6 sentences or 8 lines.  

#### 17. Sentence Length Check  
Flags sentences exceeding 35 words.  

---

## 5. Practical Applications  

1. **Efficient Document Review:** Automated checks save time and reduce errors.  
2. **Consistency Across Documents:** Ensures adherence to FAA standards.  
3. **Enhanced Collaboration:** Simplifies document updates for teams.  

---

## 6. Conclusion and Future Updates  

### Key Takeaways  
- Automated checkers enhance accuracy and compliance.  
- Tailored for FAA documentation needs.  
- Saves time while improving document quality.  

### What's Next?  
- Continue refining the tool to improve accuracy and functionality.  
- Explore adding new checks based on user feedback and evolving guidelines.    

**Note:** This tool is a work in progress. Expect more features and updates in the future to meet evolving document requirements.
