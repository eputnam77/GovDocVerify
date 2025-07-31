"""GovDocVerify utilities package."""

# Delay heavy imports (such as ``python-docx``) until needed to make test
# collection lighter when optional dependencies are absent.

# Re-export commonly used helpers for convenient access. This avoids importing
# heavy dependencies during test discovery while keeping a stable public API.
from .metadata_utils import extract_docx_metadata

__all__ = ["extract_docx_metadata"]
