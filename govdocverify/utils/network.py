"""HTTP helpers with retry support."""

from __future__ import annotations

import httpx

from govdocverify.utils.decorators import retry_transient


@retry_transient()
def fetch_url(url: str) -> str:
    """Return the text content from ``url``.

    Requests are retried on transient failures according to configuration
    provided via environment variables.
    """

    response = httpx.get(url)
    response.raise_for_status()
    return response.text
