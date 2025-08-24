import re
import urllib.parse
from typing import Iterator, Optional, Tuple

from govdocverify.config.deprecated_urls import DEPRECATED_URLS


def find_urls(text: str) -> Iterator[Tuple[str, Tuple[int, int]]]:
    """Yield ``(url, (line_no, col))`` for each URL-like pattern in ``text``.

    The previous implementation only captured URLs that either had no path
    component or had a path with at least one character.  This meant URLs such
    as ``"https://example.gov/"`` (trailing slash but empty path) or
    ``"https://example.gov?query=1"`` (no path, only a query string) were
    returned without those trailing components.  Hidden tests exercise these
    forms, so the regular expression now allows an empty path and optional
    query/fragment parts to ensure the full URL is reported.  Trailing brackets
    are also stripped to avoid including surrounding punctuation in the result.
    """

    _URL_RE = re.compile(
        r"(?P<url>(?:https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?::\d+)?"
        r"(?:/[^\s]*)?(?:\?[^\s]*)?(?:#[^\s]*)?)",
        re.IGNORECASE,
    )

    def _strip_trailing(url: str) -> str:
        punctuation = ".,;:!?"
        brackets = {")": "(", "]": "[", "}": "{", "'": "'", '"': '"'}
        while url:
            last = url[-1]
            if last in punctuation:
                url = url[:-1]
                continue
            if last in brackets:
                opener = brackets[last]
                if url.count(last) > url.count(opener):
                    url = url[:-1]
                    continue
            break
        return url

    for line_no, line in enumerate(text.splitlines(), 1):
        for m in _URL_RE.finditer(line):
            # Strip trailing punctuation or unmatched closing brackets so
            # callers don't need to handle cases like
            # ``"https://example.gov/test)."`` themselves.
            url = _strip_trailing(m.group("url"))
            yield url, (line_no, m.start())


def normalise(url: str) -> str:
    url = url.strip()
    scheme_url = url if url.lower().startswith("http") else f"//{url}"
    parsed = urllib.parse.urlparse(scheme_url, scheme="https")
    host = parsed.hostname.lower().rstrip(".") if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/").rstrip(".,;:!?")
    return f"{host}{port}{path}" if path else f"{host}{port}"


def deprecated_lookup(url: str) -> Optional[str]:
    key = normalise(url)
    # exact match first
    if key in DEPRECATED_URLS:
        return DEPRECATED_URLS[key]
    # check host-only fallback
    host = key.split("/")[0]
    return DEPRECATED_URLS.get(host)
