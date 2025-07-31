"""Utility helpers for :mod:`govdocverify`.

This module *lazily* exposes selected utilities to keep import costs minimal
while still letting callers write
`from govdocverify.utils import extract_docx_metadata`.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

__all__: list[str] = ["extract_docx_metadata"]

# Static analysers / IDEs see the symbol without importing heavy deps
if TYPE_CHECKING:  # pragma: no cover
    from .metadata_utils import extract_docx_metadata

def __getattr__(name: str) -> Any:  # pragma: no cover
    """Lazily import utilities on first access.

    Heavy optional dependencies (e.g. ``python-docx`` via ``metadata_utils``)
    load only when the attribute is actually requested.
    """
    if name == "extract_docx_metadata":
        from .metadata_utils import extract_docx_metadata as func
        return func
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
