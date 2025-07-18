# ADR 2: Standard repository layout

Date: 2024-06-14

## Status
Accepted

## Context
The current repository places the main package at the top level alongside helper scripts and apps. The `.dev/AGENTS.md` playbook recommends a `src/` based layout to keep packaging clean and to separate dev files from distributable code.

## Decision
- Future development will migrate the Python package into `src/documentcheckertool/`.
- Test modules remain in `tests/`.
- User-facing documentation lives in `docs/` built with MkDocs.
- Helper scripts live in `scripts/` and are excluded from wheels.
- Dev material such as ADRs and product docs remain under `.dev/`.

## Consequences
- `pyproject.toml` is updated so that wheels only include `src` and exclude `tests*` and `.dev*`.
- Existing imports continue to work during the transition because code is not yet moved. Migration will occur in a follow-up task.
