# TASKS

## Epic 1: Metadata Extraction & Display

### Task 1: Document all metadata fields
- **Priority**: Medium
- **Time Estimate**: 0.5d
- **Acceptance Criteria**:
  - README lists Title, Author, Last Modified By, Created, and Modified as displayed metadata.
  - Installation instructions mention using a single dependency file or Poetry.
- **Labels**: documentation
- **Tests**: [tests/e2e/features/metadata_extraction_display.feature](tests/e2e/features/metadata_extraction_display.feature)

### Task 2: Extend metadata unit tests
- **Priority**: Medium
- **Time Estimate**: 0.5d
- **Acceptance Criteria**:
  - `test_extract_docx_metadata` verifies `created` and `modified` fields.
  - `test_format_results_with_metadata` checks that all metadata fields render in reports.
- **Labels**: testing
- **Tests**: [tests/property/test_extract_docx_metadata.py](tests/property/test_extract_docx_metadata.py)

## Epic 2: Core Document Checks

### Task 3: Review formatting, heading, and accessibility checks
- **Priority**: Low
- **Time Estimate**: 1d
- **Acceptance Criteria**:
  - Confirm existing check modules cover FAA style rules for formatting, headings and accessibility.
  - Update or add tests if gaps are found.
- **Labels**: maintenance

## Epic 3: Document Upload UI

### Task 4: Create upload and results page
- **Priority**: High
- **Time Estimate**: 1d
- **Acceptance Criteria**:
  - React page lets users select and upload a document file
  - Results are displayed in the browser after processing
- **Labels**: frontend
- **Tests**: [tests/e2e/features/upload_results_page.feature](tests/e2e/features/upload_results_page.feature)

### Task 5: Add download options for results
- **Priority**: Medium
- **Time Estimate**: 0.5d
- **Acceptance Criteria**:
  - Users can download the displayed results as DOCX or PDF
- **Labels**: frontend
- **Tests**: [tests/e2e/features/upload_results_page.feature](tests/e2e/features/upload_results_page.feature)

---

ready-for:scenario-gen
