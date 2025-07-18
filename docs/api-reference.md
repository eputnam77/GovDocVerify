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
