"""Run pytest while collecting lightweight coverage information.

The sandbox environment used here cannot install the `coverage` package, so we
fall back to Python's tracing hooks to record executed lines for a curated set
of modules.  The script is intentionally small but produces deterministic
numbers that we can use to prove that the updated tests exercise the new logic.

Usage
-----

```
python scripts/run_pytest_with_coverage.py \
    govdocverify/utils/security.py \
    govdocverify/utils/terminology_utils.py \
    govdocverify/utils/text_utils.py
```

Additional arguments after a standalone ``--`` are forwarded to pytest.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pytest


@dataclass(frozen=True)
class CoverageFile:
    path: Path
    executed: set[int]

    def candidate_lines(self) -> set[int]:
        tree = ast.parse(self.path.read_text(encoding="utf-8"))
        lines: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.stmt):
                continue
            lineno = getattr(node, "lineno", None)
            if lineno is None:
                continue
            if isinstance(node, ast.Expr) and isinstance(
                getattr(node, "value", None), ast.Constant
            ):
                if isinstance(node.value.value, str):
                    continue
            lines.add(lineno)
        return lines

    def percentage(self) -> float:
        candidates = self.candidate_lines()
        if not candidates:
            return 100.0
        executed = len(candidates & self.executed)
        return (executed / len(candidates)) * 100.0


def _resolve_targets(targets: Iterable[str]) -> list[CoverageFile]:
    files: list[CoverageFile] = []
    for raw in targets:
        path = Path(raw)
        resolved = path.resolve()
        if resolved.is_dir():
            for child in sorted(resolved.rglob("*.py")):
                files.append(CoverageFile(child, set()))
        else:
            files.append(CoverageFile(resolved, set()))
    return files


def _make_tracer(files: list[CoverageFile]):
    file_map = {str(file.path): file for file in files}
    resolution_cache: dict[str, tuple[bool, CoverageFile | None]] = {}

    def tracer(frame, event, arg):  # type: ignore[override]
        filename = frame.f_code.co_filename
        cached = resolution_cache.get(filename)
        if cached is None:
            resolved = Path(filename).resolve()
            coverage_file = file_map.get(str(resolved))
            cached = (coverage_file is not None, coverage_file)
            resolution_cache[filename] = cached
        tracked, coverage_file = cached
        if tracked and event == "line" and coverage_file is not None:
            coverage_file.executed.add(frame.f_lineno)
        return tracer

    return tracer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", help="Files or directories to cover")
    parser.add_argument("--show-missing", action="store_true", help="List uncovered line numbers")
    parser.add_argument("--", dest="pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    coverage_files = _resolve_targets(args.targets)
    tracer = _make_tracer(coverage_files)

    pytest_args = ["-q", "--disable-warnings"]
    if args.pytest_args:
        pytest_args.extend(arg for arg in args.pytest_args if arg)

    sys.settrace(tracer)
    try:
        exit_code = pytest.main(pytest_args)
    finally:
        sys.settrace(None)

    print("\nCoverage Summary")
    print("=" * 60)
    for cov_file in coverage_files:
        rel_path = cov_file.path.relative_to(Path.cwd())
        percent = cov_file.percentage()
        print(f"{rel_path!s:<50} {percent:6.2f}%")
        if args.show_missing:
            candidates = cov_file.candidate_lines()
            missing = sorted(candidates - cov_file.executed)
            if missing:
                print(f"    missing: {missing}")

    overall_candidates = 0
    overall_executed = 0
    for cov_file in coverage_files:
        candidates = cov_file.candidate_lines()
        executed = len(candidates & cov_file.executed)
        overall_candidates += len(candidates)
        overall_executed += executed

    overall = (overall_executed / overall_candidates) * 100.0 if overall_candidates else 100.0
    print("=" * 60)
    print(f"Overall: {overall:.2f}% ({overall_executed}/{overall_candidates})")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

