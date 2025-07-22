"""Utilities for ensuring README metadata documentation is complete."""

from __future__ import annotations

from pathlib import Path

__all__ = ["update_metadata_documentation"]


_SUPPORTED_FIELDS = [
    "Title",
    "Author",
    "Last Modified By",
    "Created",
    "Modified",
]


def update_metadata_documentation(readme_path: str) -> None:
    """Ensure the README lists all supported metadata fields.

    Parameters
    ----------
    readme_path:
        Path to the ``README.md`` file to update.
    """
    path = Path(readme_path)
    readme = path.read_text(encoding="utf-8").splitlines()

    bullet = f"- Displays document metadata ({', '.join(_SUPPORTED_FIELDS)})"
    if any(bullet in line for line in readme):
        return

    for idx, line in enumerate(readme):
        if line.strip() == "## Features":
            readme.insert(idx + 1, bullet)
            path.write_text("\n".join(readme) + "\n", encoding="utf-8")
            return

    # Fallback: append at end
    readme.append(bullet)
    path.write_text("\n".join(readme) + "\n", encoding="utf-8")
