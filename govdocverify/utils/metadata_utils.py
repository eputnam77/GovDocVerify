import logging
from typing import Any, Dict

from docx import Document

logger = logging.getLogger(__name__)


def extract_docx_metadata(file_path: str) -> Dict[str, Any]:
    """Extract basic metadata from a DOCX file.

    Parameters
    ----------
    file_path : str
        Path to the DOCX file.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing metadata fields such as title, author, and
        last modified by. Empty values are omitted.
    """
    file_path = file_path.strip()

    if not file_path.lower().endswith(".docx"):
        return {}
    try:
        doc = Document(file_path)
        cp = doc.core_properties
        metadata = {
            "title": cp.title,
            "author": cp.author,
            "last_modified_by": cp.last_modified_by,
            "created": cp.created.isoformat() if cp.created else None,
            "modified": cp.modified.isoformat() if cp.modified else None,
        }
        return {k: v for k, v in metadata.items() if v}
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to extract metadata from %s: %s", file_path, exc)
        return {}
