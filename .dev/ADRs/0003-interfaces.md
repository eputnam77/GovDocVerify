# ADR 3: Multiple user interfaces

Date: 2024-06-14

## Status
Accepted

## Context
The project offers a FastAPI backend with a modern React frontend. A simple Gradio interface is also provided for quick experimentation and for deployment on Hugging Face Spaces. All three interfaces share the same core logic.

## Decision
- Keep the FastAPI service as the primary API layer.
- Maintain the React application in `frontend/` for production use.
- Retain the Gradio UI under `documentcheckertool/interfaces` as an optional legacy interface.

## Consequences
- The core package remains interface-agnostic.
- Tests must cover API routes and CLI behaviour separately from the UIs.
- Future work may consolidate templates and static files under `frontend/`.
