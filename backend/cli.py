"""Command-line interface for the FastAPI backend."""

import argparse

import uvicorn

from backend.main import app


def main() -> int:
    """Launch the FastAPI service using uvicorn."""
    parser = argparse.ArgumentParser(description="FAA Document Checker API")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0
