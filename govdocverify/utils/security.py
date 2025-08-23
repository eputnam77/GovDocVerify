import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict
from urllib.parse import urlparse

import filetype
from fastapi import HTTPException

from govdocverify.config.document_config import (
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_SOURCE_DOMAINS,
    LEGACY_FILE_EXTENSIONS,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
LEGACY_MIME_TYPES = {
    "application/msword": ".doc",
    "application/pdf": ".pdf",
    "text/rtf": ".rtf",
    "text/plain": ".txt",
}


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


def sanitize_file_path(file_path: str, base_dir: str | None = None) -> str:
    """Return a normalized path with optional path traversal protection.

    If ``base_dir`` is provided, the resolved ``file_path`` must be located
    within that directory; otherwise a :class:`SecurityError` is raised. When
    ``base_dir`` is ``None`` (the default), the path is simply normalized.
    """
    normalized_path = Path(file_path).expanduser().resolve()

    if base_dir is not None:
        base_path = Path(base_dir).resolve()
        try:
            normalized_path.relative_to(base_path)
        except ValueError as exc:
            raise SecurityError("Path traversal detected") from exc

    return str(normalized_path)


def validate_file(file_path: str) -> None:
    """
    Validate a file for security concerns.

    Args:
        file_path: Path to the file to validate

    Raises:
        SecurityError: If file validation fails
    """
    try:
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise SecurityError(
                f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Check file type using filetype
        kind = filetype.guess(file_path)
        if kind and kind.mime in LEGACY_MIME_TYPES:
            raise SecurityError(f"Legacy file format: {LEGACY_MIME_TYPES[kind.mime]}")
        if not kind or kind.mime not in ALLOWED_MIME_TYPES:
            raise SecurityError(
                f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES.values())}"
            )

        logger.info(f"File validation successful for {file_path}")

    except Exception as e:
        logger.error(f"File validation failed: {str(e)}")
        raise SecurityError(f"File validation failed: {str(e)}")


class RateLimiter:
    """Simple rate limiter implementation."""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list[float]] = {}

    def is_rate_limited(self, client_id: str) -> bool:
        """Check if a client has exceeded the rate limit."""
        current_time = time.time()

        # Clean up old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id] if current_time - t < self.time_window
            ]

        # Add new request
        if client_id not in self.requests:
            self.requests[client_id] = []

        self.requests[client_id].append(current_time)

        # Check if rate limit exceeded
        if len(self.requests[client_id]) > self.max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return True

        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for rate limiting API endpoints."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # In a real application, you'd get the client IP or API key here
        client_id = "default"  # Replace with actual client identification

        if rate_limiter.is_rate_limited(client_id):
            raise HTTPException(
                status_code=429, detail="Too many requests. Please try again later."
            )

        return await func(*args, **kwargs)

    return wrapper


def _is_allowed_domain(domain: str) -> bool:
    """Return ``True`` if *domain* matches an allowed suffix exactly."""
    domain = domain.lower()
    for allowed in ALLOWED_SOURCE_DOMAINS:
        suffix = allowed.lower().lstrip(".")
        if domain == suffix or domain.endswith("." + suffix):
            return True
    return False


def validate_source(path: str) -> None:
    """Validate that ``path`` is from an approved domain and format."""
    lowered = path.lower()
    _, ext = os.path.splitext(lowered)
    if "://" not in lowered and not ext:
        return
    if not ext:
        raise SecurityError("Missing file extension")
    if ext in LEGACY_FILE_EXTENSIONS:
        raise SecurityError(f"Legacy file format: {ext}")
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise SecurityError(f"Disallowed file format: {ext}")

    if lowered.startswith("http://") or lowered.startswith("https://"):
        domain = urlparse(path).hostname or ""
        if not _is_allowed_domain(domain):
            raise SecurityError(f"Non-government source domain: {domain}")
