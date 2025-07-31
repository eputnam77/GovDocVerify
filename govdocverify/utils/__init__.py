"""Utility helpers for :mod:`govdocverify`.

This module lazily exposes selected utilities to keep import costs minimal.
"""

from __future__ import annotations

from typing import Any

# Delay heavy imports (such as ``python-docx``) until explicitly requested
# to keep test collection lightweight when optional dependencies are absent.

__all__ = ["extract_docx_metadata"]


def __getattr__(name: str) -> Any:  # pragma: no cover - thin wrapper
    """Lazily import utilities on first access."""
    if name == "extract_docx_metadata":
        from .metadata_utils import extract_docx_metadata as func

        return func
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
