# Performance Report

## Profiling Summary

- Collected cProfile data for the CLI server launcher (`profile_cli.prof`) and document processing CLI (`profile_doc.prof`).
- Total runtime while processing a sample document was about **0.93s** with most time spent in module import logic.
- Generated artifacts are stored under `perf/artifacts/`.
- Frontend bundle build via Vite produced a **289 kB** JS bundle (99 kB gzip).

## Recommendations

| Recommendation | Impact | Effort | Risk | Priority |
| --- | --- | --- | --- | --- |
| Cache parsed `.docx` documents with `lru_cache` to avoid repeated disk IO during repeated checks | Medium | Low | Low | P1 |
| Investigate high startup cost from imports; consider lazy importing heavy modules in `document_checker` | Medium | Medium | Low | P2 |
| Enable Semgrep offline rules or mirror to comply with network restrictions | Low | Low | Low | P3 |

## Applied Tweaks

- Implemented `lru_cache` for loading docx files in `document_checker.py`.
- Added `perf/artifacts/` directory with profiling output.

No database queries were detected in the code base.
