#!/usr/bin/env python3
"""Root-level entry point for the Document Checker CLI."""

from documentcheckertool import cli as package_cli


def main() -> int:
    """Delegate to :func:`documentcheckertool.cli.main`."""
    return package_cli.main()


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
