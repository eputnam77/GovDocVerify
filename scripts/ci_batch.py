"""Batch processing helper for CI runs.

This script allows the CI pipeline to process multiple documents in a
single invocation, mirroring how developers might run the CLI locally
with a glob pattern. Each file is processed in sequence and the script
returns a non-zero exit code if any document fails or raises an
exception. The implementation is intentionally lightweight so that it
can be imported from tests without requiring the ``scripts`` directory to
be installed as a package.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

from govdocverify.cli import process_document


def run_batch(patterns: Iterable[str], doc_type: str) -> int:
    """Process all files matching ``patterns``.

    Parameters
    ----------
    patterns:
        An iterable of file paths or glob patterns to process.
    doc_type:
        The document type understood by :func:`govdocverify.cli.process_document`.

    Returns
    -------
    int
        ``0`` if all documents were processed successfully, ``1`` if any
        document produced errors or raised an exception.
    """
    exit_code = 0
    for pattern in patterns:
        # ``glob`` expands both explicit files and patterns. Sorting ensures
        # deterministic ordering which simplifies testing.
        for file_path in sorted(glob.glob(pattern)):
            try:
                result = process_document(file_path, doc_type)
                if result.get("has_errors", False):
                    exit_code = 1
            except Exception:
                exit_code = 1
    return exit_code


def get_changed_files(
    base_ref: str,
    patterns: Sequence[str] | None = None,
    repo_root: str | Path | None = None,
) -> list[str]:
    """Return files changed since ``base_ref``.

    Parameters
    ----------
    base_ref:
        Git reference to compare against ``HEAD``.
    patterns:
        Optional glob patterns used to filter the returned files.
    repo_root:
        Path to the Git repository. Defaults to the current working directory.
    """

    root = Path(repo_root or Path.cwd())
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "HEAD"],
        capture_output=True,
        text=True,
        cwd=root,
        check=True,
    )
    files = result.stdout.strip().splitlines()
    if patterns:
        files = [f for f in files if any(fnmatch.fnmatch(f, pattern) for pattern in patterns)]
    return [str(root / f) for f in files]


def main() -> int:  # pragma: no cover - exercised via tests
    """Entry point for running the batch processor from the command line."""
    parser = argparse.ArgumentParser(description="Run GovDocVerify in batch mode")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--files",
        nargs="+",
        help="File paths or glob patterns to process",
    )
    group.add_argument(
        "--changed-from",
        help="Git ref to diff against HEAD for incremental runs",
    )
    parser.add_argument(
        "--pattern",
        default="*.docx",
        help="Glob pattern used with --changed-from to filter files",
    )
    parser.add_argument("--type", required=True, help="Document type to check")
    args = parser.parse_args()

    if args.files:
        targets = args.files
    else:
        targets = get_changed_files(args.changed_from, [args.pattern])

    return run_batch(targets, args.type)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
