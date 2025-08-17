"""Command-line interface for the FastAPI backend."""

from __future__ import annotations

import argparse

from backend.graceful import run
from backend.main import app


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",  # nosec B104 - intended default
        help="Host interface",
    )
    parser.add_argument("--port", type=int, default=8000, help="TCP port")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point to launch the API server."""
    args = _build_parser().parse_args(argv)
    run(app, host=args.host, port=args.port)
    return 0
