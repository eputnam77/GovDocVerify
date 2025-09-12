import asyncio
import logging
import os
import re
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
    path_obj = Path(file_path).expanduser()

    if base_dir is not None:
        base_path = Path(base_dir).expanduser().resolve()
        if not path_obj.is_absolute():
            path_obj = base_path / path_obj
        normalized_path = path_obj.resolve()
        try:
            normalized_path.relative_to(base_path)
        except ValueError as exc:
            raise SecurityError("Path traversal detected") from exc
        return str(normalized_path)

    return str(path_obj.resolve())


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

        cutoff = current_time - self.time_window
        # Clean up old requests for all clients to prevent unbounded growth
        for cid, times in list(self.requests.items()):
            self.requests[cid] = [t for t in times if t > cutoff]
            if not self.requests[cid]:
                del self.requests[cid]

        # Add new request for this client
        self.requests.setdefault(client_id, []).append(current_time)

        # Check if rate limit exceeded
        if len(self.requests[client_id]) > self.max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return True

        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for rate limiting API endpoints.

    The original version always produced an ``async`` wrapper and ``await``ed the
    wrapped function.  Decorating a synchronous callable therefore returned a
    coroutine object and failed when executed.  Support both sync and async
    functions by detecting ``func``'s type and creating an appropriate wrapper.
    """

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            client_id = "default"
            if rate_limiter.is_rate_limited(client_id):
                raise HTTPException(
                    status_code=429, detail="Too many requests. Please try again later."
                )
            return await func(*args, **kwargs)

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        client_id = "default"
        if rate_limiter.is_rate_limited(client_id):
            raise HTTPException(
                status_code=429, detail="Too many requests. Please try again later."
            )
        return func(*args, **kwargs)

    return sync_wrapper


def _is_allowed_domain(domain: str) -> bool:
    """Return ``True`` if *domain* matches an allowed suffix exactly."""

    # ``urlparse().hostname`` may include a trailing dot for fully‑qualified
    # domain names (e.g. ``"example.gov."``).  Such names should still be
    # considered valid, so normalise by stripping the trailing dot before
    # comparison.
    domain = domain.lower().rstrip(".")
    for allowed in ALLOWED_SOURCE_DOMAINS:
        suffix = allowed.lower().lstrip(".")
        if domain == suffix or domain.endswith("." + suffix):
            return True
    return False


def _validate_extension(ext: str) -> None:
    """Validate a file extension against allowed and legacy lists."""
    if not ext:
        raise SecurityError("Missing file extension")
    if ext in LEGACY_FILE_EXTENSIONS:
        raise SecurityError(f"Legacy file format: {ext}")
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise SecurityError(f"Disallowed file format: {ext}")


def validate_source(path: str) -> None:
    """Validate that ``path`` is from an approved domain and format."""

    lowered = path.lower()

    # Handle Windows drive paths like ``C:\\path\\file.docx`` which ``urlparse``
    # interprets as having a scheme of "c".  Treat these as local paths.
    if re.match(r"^[a-z]:[\\/]", lowered):
        _, ext = os.path.splitext(lowered)
        _validate_extension(ext)
        return

    # Separate any URL components before extracting the extension.  The
    # previous implementation ran ``os.path.splitext`` directly on the whole
    # URL, which meant query strings or fragments became part of the extension
    # (e.g. ``".docx?download=1"``) and valid URLs were rejected.
    parsed = urlparse(lowered)
    _, ext = os.path.splitext(parsed.path)

    # Allow bare local paths without an extension and without any additional
    # URL components.  Anything else must include a file extension.
    if not parsed.scheme and not ext and not parsed.query and not parsed.fragment:
        return
    _validate_extension(ext)

    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise SecurityError(f"Unsupported URL scheme: {parsed.scheme}")

    if parsed.scheme in {"http", "https"}:
        domain = parsed.hostname or ""
        if not _is_allowed_domain(domain):
            raise SecurityError(f"Non-government source domain: {domain}")
