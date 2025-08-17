# API Reference

The FastAPI backend exposes a single endpoint for document processing.

## POST `/process`
Uploads a document and returns check results.

**Form fields**
- `doc_file` – Word document to analyze.
- `doc_type` – The type of document (e.g. "Advisory Circular").
- `visibility_json` – Optional visibility settings JSON.
- `group_by` – `category` or `severity` grouping.

**Response**
```json
{
  "has_errors": true,
  "rendered": "<html>...",
  "by_category": {"format": []}
  }
  ```

## Python Package API

In addition to the HTTP endpoint, ``govdocverify`` ships a lightweight Python
API for embedding document checks into your own tools.

```python
from govdocverify import DocumentChecker, save_results_as_docx

checker = DocumentChecker()
results = checker.run_all_document_checks("example.docx")
if not results.success:
    save_results_as_docx(results.__dict__, "report.docx")
```

### Exported symbols

* ``DocumentChecker`` – orchestrates the standard suite of checks.
* ``DocumentCheckResult`` – container describing the outcome of a run.
* ``VisibilitySettings`` – toggles groups of checks in rendered output.
* ``Severity`` – enum representing the severity of an issue.
* ``save_results_as_docx`` / ``save_results_as_pdf`` – helpers for persisting
  results.

Everything else in the repository is considered **internal** and may change
without notice.
