import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Dict

import filetype
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
}


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


def sanitize_file_path(file_path: str, base_dir: str | None = None) -> str:
    """Return a normalized path and guard against path traversal."""
    if base_dir is None:
        base_dir = os.getcwd()

    normalized_path = Path(file_path).expanduser().resolve()
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
                f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
            )

        # Check file type using filetype
        kind = filetype.guess(file_path)
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
        self.requests: Dict[str, list] = {}

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


def rate_limit(func):
    """Decorator for rate limiting API endpoints."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # In a real application, you'd get the client IP or API key here
        client_id = "default"  # Replace with actual client identification

        if rate_limiter.is_rate_limited(client_id):
            raise HTTPException(
                status_code=429, detail="Too many requests. Please try again later."
            )

        return await func(*args, **kwargs)

    return wrapper
