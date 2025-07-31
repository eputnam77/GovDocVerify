"""GovDocVerify utilities package."""

# Delay heavy imports (such as ``python-docx``) until needed to make test
# collection lighter when optional dependencies are absent.

# Re-export commonly used helpers for convenient access. This keeps optional
# dependencies from being imported during test collection while allowing modules
# to ``from govdocverify.utils import extract_docx_metadata``.
from .metadata_utils import extract_docx_metadata

__all__ = ["extract_docx_metadata"]
