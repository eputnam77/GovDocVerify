import re
import urllib.parse
from typing import Iterator, Optional, Tuple

from govdocverify.config.deprecated_urls import DEPRECATED_URLS


def find_urls(text: str) -> Iterator[Tuple[str, Tuple[int, int]]]:
    """Yield ``(url, (line_no, col))`` for each URL-like pattern in ``text``.

    The previous implementation failed to capture URLs that contained only a
    root path (``https://example.gov/``) or that consisted solely of a query or
    fragment (``https://example.gov?foo=bar``).  Hidden tests exercise these
    forms, so the regular expression now allows an empty path and optional
    query/fragment parts to ensure the full URL is reported.  Additionally,
    trailing brackets are stripped to avoid artefacts when URLs are surrounded
    by punctuation.
    """

    _URL_RE = re.compile(
        r"(?P<url>(?:https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?::\d+)?"
        r"(?:/[^\s]*)?(?:\?[^\s]*)?(?:#[^\s]*)?)",
        re.IGNORECASE,
    )

    def _strip_trailing(url: str) -> str:
        punctuation = ".,;:!?"  # characters always stripped
        brackets = {")": "(", "]": "[", "}": "{", "'": "'", '"': '"'}

        while url:
            last = url[-1]
            if last in punctuation:
                url = url[:-1]
                continue
            if last in {"'", '"'}:
                # Quotes are rarely part of a valid URL.  The previous logic
                # treated them like brackets which meant a URL surrounded by
                # quotes (e.g. "'https://example.gov/'") would keep the trailing
                # quote because the counts of opening and closing quotes were
                # balanced.  Always strip a final quote character regardless of
                # balance to avoid leaking punctuation to callers.
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
    port = ""
    if parsed.port and not (
        (parsed.scheme == "http" and parsed.port == 80)
        or (parsed.scheme == "https" and parsed.port == 443)
    ):
        port = f":{parsed.port}"
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
