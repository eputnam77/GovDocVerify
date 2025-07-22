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
- **Status**: DONE ([README.md](../README.md))

### Task 2: Extend metadata unit tests
- **Priority**: Medium
- **Time Estimate**: 0.5d
- **Acceptance Criteria**:
  - `test_extract_docx_metadata` verifies `created` and `modified` fields.
  - `test_format_results_with_metadata` checks that all metadata fields render in reports.
- **Labels**: testing
- **Tests**: [tests/property/test_extract_docx_metadata.py](tests/property/test_extract_docx_metadata.py)
- **Status**: DONE ([tests/test_result_formatter.py](../tests/test_result_formatter.py))

## Epic 2: Core Document Checks

### Task 3: Review formatting, heading, and accessibility checks
- **Priority**: Low
- **Time Estimate**: 1d
- **Acceptance Criteria**:
  - Confirm existing check modules cover FAA style rules for formatting, headings and accessibility.
  - Update or add tests if gaps are found.
- **Labels**: maintenance
- **Status**: DONE ([govdocverify/checks](../govdocverify/checks))

## Epic 3: Document Upload UI

### Task 4: Create upload and results page
- **Priority**: High
- **Time Estimate**: 1d
- **Acceptance Criteria**:
  - React page lets users select and upload a document file
  - Results are displayed in the browser after processing
- **Labels**: frontend
- **Tests**: [tests/e2e/features/upload_results_page.feature](tests/e2e/features/upload_results_page.feature)
- **Status**: DONE ([frontend/govdocverify/src](../frontend/govdocverify/src))

### Task 5: Add download options for results
- **Priority**: Should
- **Time Estimate**: 4h
- **Acceptance Criteria**:
  - Users can download the displayed results as DOCX or PDF
- **Labels**: frontend
- **Tests**: [tests/e2e/features/upload_results_page.feature](tests/e2e/features/upload_results_page.feature)
- **Status**: DONE ([govdocverify/export.py](../govdocverify/export.py))

## Epic 4: API Backend

### Task 6: Document FastAPI endpoint
- **Priority**: Medium
- **Time Estimate**: 0.5d
- **Acceptance Criteria**:
  - README details parameters for the `/process` endpoint
  - Example `curl` request demonstrates usage
- **Labels**: documentation
- **Tests**: [tests/test_backend_api.py](tests/test_backend_api.py), [tests/e2e/features/api_backend.feature](tests/e2e/features/api_backend.feature)
- **Status**: DONE ([README.md](../README.md))

### Task 7: Start FastAPI service via CLI
- **Priority**: Should
- **Time Estimate**: 4h
- **Acceptance Criteria**:
  - `run.py` launches the FastAPI app with uvicorn
  - Unit test covers CLI invocation
- **Labels**: backend
- **Tests**: [tests/test_backend_api.py](tests/test_backend_api.py), [tests/e2e/features/api_backend.feature](tests/e2e/features/api_backend.feature)
- **Status**: DONE ([backend/cli.py](../backend/cli.py))

---

ready-for:scenario-gen
last_generated: 2025-07-21T14:29:46Z
