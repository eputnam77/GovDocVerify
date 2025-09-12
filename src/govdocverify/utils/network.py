"""HTTP helpers with retry support."""
from __future__ import annotations

import os

import httpx

from govdocverify.utils.decorators import retry_transient

try:
    DEFAULT_TIMEOUT = float(os.getenv("GOVDOCVERIFY_HTTP_TIMEOUT", "5"))
except ValueError:
    DEFAULT_TIMEOUT = 5.0


@retry_transient()
def fetch_url(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Return the text content from ``url``.

    Requests are retried on transient failures according to configuration
    provided via environment variables.

    Parameters
    ----------
    url: str
        The URL to fetch.
    timeout: float
        Timeout in seconds for the request. Defaults to ``DEFAULT_TIMEOUT`` and
        may be overridden via ``GOVDOCVERIFY_HTTP_TIMEOUT``.
    """

    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text
