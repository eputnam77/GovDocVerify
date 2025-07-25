"""CLI helper for launching the FastAPI server."""

from __future__ import annotations

import uvicorn


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:  # nosec B104
    """Run the FastAPI app using uvicorn."""
    uvicorn.run("backend.main:app", host=host, port=port)
