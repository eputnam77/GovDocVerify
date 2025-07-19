# ADR 4: Display document metadata in reports

Date: 2025-07-19

## Status
Accepted

## Context
The product requirements introduce metadata extraction so that a document's key
properties appear at the top of every results report. This information helps
users verify the correct file was analyzed and improves traceability.

## Decision
- The processing pipeline extracts `title`, `author`, `last_modified_by`,
  `created`, and `modified` fields from uploaded documents.
- Report rendering functions include these fields in a dedicated metadata
  section before listing style issues.
- Tests cover metadata extraction and the presence of these fields in formatted
  output.

## Consequences
- Existing result formatting functions need minor updates but the core checking
  logic remains unaffected.
- Future interfaces (CLI, API and UI) should display the metadata section when
  presenting results.

