# ADR 3: Multiple user interfaces

Date: 2024-06-14

## Status
Accepted

## Context
The project offers a FastAPI backend with a modern React frontend. A lightweight web interface was previously included for quick experimentation but has since been removed. All interfaces share the same core logic.

## Decision
- Keep the FastAPI service as the primary API layer.
- Maintain the React application in `frontend/` for production use.

## Consequences
- The core package remains interface-agnostic.
- Tests must cover API routes and CLI behaviour separately from the UIs.
- Future work may consolidate templates and static files under `frontend/`.
