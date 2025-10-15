"""Utility to summarise ``trace`` based coverage data.

The container environment used for these exercises does not provide the
``coverage`` module or the ``pytest-cov`` plugin.  To keep the workflow close
to the project's expectations we execute the tests under ``python -m trace``
and then aggregate the ``*.cover`` files that are generated for the
``govdocverify`` package.  This script reads those files, computes the line
coverage for each module (excluding blank lines and comments), and prints a
human-readable summary together with the overall percentage.

Example::

    python scripts/compute_trace_coverage.py trace_cov

"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ModuleCoverage:
    """Coverage information for a single module."""

    path: Path
    executed: int
    total: int

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.executed / self.total) * 100.0


def _parse_cover_file(cover_path: Path) -> set[int]:
    """Return the set of executed line numbers for ``cover_path``.

    The ``trace`` module outputs each source line prefixed by the number of
    executions.  We recreate the original line numbers by enumerating the
    ``*.cover`` file itself; any line with a numeric prefix greater than zero is
    considered executed.
    """

    executed: set[int] = set()
    with cover_path.open("r", encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, start=1):
            stripped = raw_line.lstrip()
            if not stripped or ":" not in stripped:
                continue
            prefix, _ = stripped.split(":", 1)
            prefix = prefix.strip()
            if not prefix.isdigit():
                continue
            if int(prefix) > 0:
                executed.add(lineno)
    return executed


def _candidate_lines(source: Path) -> set[int]:
    """Return the set of executable line numbers for ``source``.

    Using the AST ensures we only count real statements (matching the behaviour
    of coverage.py) while gracefully handling multi-line literals and
    collections that ``trace`` flattens without per-line execution counts.
    """

    tree = ast.parse(source.read_text(encoding="utf-8"))
    candidates: set[int] = set()
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
        candidates.add(lineno)
    return candidates


def _iter_project_modules(coverage_dir: Path) -> Iterable[ModuleCoverage]:
    """Yield ``ModuleCoverage`` entries for the project modules."""

    for cover_path in sorted(coverage_dir.glob("govdocverify*.cover")):
        module_path = Path(cover_path.stem.replace(".", "/") + ".py")
        if not module_path.exists():
            continue
        executed_lines = _parse_cover_file(cover_path)
        candidate_lines = _candidate_lines(module_path)
        executed = len(candidate_lines & executed_lines)
        total = len(candidate_lines)
        yield ModuleCoverage(module_path, executed, total)


def _format_module_row(module: ModuleCoverage) -> str:
    formatted_path = module.path.as_posix()
    return (
        f"{formatted_path:<60} {module.percentage:6.2f}% "
        f"({module.executed}/{module.total})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "coverage_dir",
        type=Path,
        help="Directory containing trace *.cover files",
    )
    args = parser.parse_args()

    modules = list(_iter_project_modules(args.coverage_dir))
    if not modules:
        raise SystemExit("No coverage data found for govdocverify modules")

    total_executed = sum(module.executed for module in modules)
    total_lines = sum(module.total for module in modules)
    overall = (total_executed / total_lines) * 100.0 if total_lines else 100.0

    print("Module Coverage Summary")
    print("=" * 80)
    for module in modules:
        print(_format_module_row(module))
    print("=" * 80)
    print(f"Overall coverage: {overall:.2f}% ({total_executed}/{total_lines})")


if __name__ == "__main__":
    main()

