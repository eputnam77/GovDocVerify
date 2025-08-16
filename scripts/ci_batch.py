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
import glob
from typing import Iterable

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


def main() -> int:  # pragma: no cover - exercised via tests
    """Entry point for running the batch processor from the command line."""
    parser = argparse.ArgumentParser(description="Run GovDocVerify in batch mode")
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="File paths or glob patterns to process",
    )
    parser.add_argument("--type", required=True, help="Document type to check")
    args = parser.parse_args()
    return run_batch(args.files, args.type)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
