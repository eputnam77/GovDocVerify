"""Utility helpers for :mod:`govdocverify`.

This module *lazily* exposes selected utilities to keep import costs minimal
while still letting callers write
`from govdocverify.utils import extract_docx_metadata`.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

__all__: list[str] = ["extract_docx_metadata"]

# Allow static analysers / IDEs to see the symbol without importing heavy deps
if TYPE_CHECKING:  # pragma: no cover
    from .metadata_utils import extract_docx_metadata


def __getattr__(name: str) -> Any:  # pragma: no cover
    """Lazily import utilities on first access.

    Heavy optional dependencies (e.g. ``python-docx`` inside
    ``metadata_utils``) are imported only when actually requested, avoiding
    ImportError during lightweight test collection.
    """
    if name == "extract_docx_metadata":
        from .metadata_utils import extract_docx_metadata as func

        return func
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
