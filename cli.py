#!/usr/bin/env python3
"""Root-level entry point for the GovDocVerify CLI."""

from govdocverify import cli as package_cli


def main() -> int:
    """Delegate to :func:`govdocverify.cli.main`."""
    return package_cli.main()


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
