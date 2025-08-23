import re
import urllib.parse
from typing import Iterator, Optional, Tuple

from govdocverify.config.deprecated_urls import DEPRECATED_URLS


def find_urls(text: str) -> Iterator[Tuple[str, Tuple[int, int]]]:
    """Yield (url, (line_no, col)) for every URL or bare host in text."""
    _URL_RE = re.compile(r"(?P<url>(?:https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s)]+)?)")
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in _URL_RE.finditer(line):
            yield m.group("url"), (line_no, m.start())


def normalise(url: str) -> str:
    url = url.strip()
    scheme_url = url if url.lower().startswith("http") else f"//{url}"
    parsed = urllib.parse.urlparse(scheme_url, scheme="https")
    host = parsed.hostname.lower() if parsed.hostname else ""
    path = parsed.path.rstrip("/").rstrip(".,;:!?")
    return f"{host}{path}" if path else host


def deprecated_lookup(url: str) -> Optional[str]:
    key = normalise(url)
    # exact match first
    if key in DEPRECATED_URLS:
        return DEPRECATED_URLS[key]
    # check host-only fallback
    host = key.split("/")[0]
    return DEPRECATED_URLS.get(host)
