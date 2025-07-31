"""GovDocVerify package."""

# Avoid importing the CLI at module import time so that unit tests can run
# without pulling in heavy optional dependencies (e.g. ``docx`` or ``uvicorn``).
__all__ = []
