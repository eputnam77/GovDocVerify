import asyncio
import time
from pathlib import Path

import pytest
from fastapi import HTTPException

import govdocverify.utils.security as security_module
from govdocverify.utils.security import (
    RateLimiter,
    SecurityError,
    rate_limit,
    sanitize_file_path,
    validate_file,
    validate_source,
)


def test_sanitize_allows_absolute_paths(tmp_path: Path) -> None:
    outside = tmp_path / "outside" / "file.docx"
    outside.parent.mkdir(parents=True)
    outside.write_text("test")
    result = sanitize_file_path(str(outside))
    assert Path(result) == outside.resolve()


def test_sanitize_base_dir_enforced(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    inside = base / "file.docx"
    inside.write_text("test")
    assert Path(sanitize_file_path(str(inside), base_dir=str(base))) == inside.resolve()
    outside = tmp_path / "outside" / "file.docx"
    outside.parent.mkdir()
    outside.write_text("test")
    with pytest.raises(SecurityError):
        sanitize_file_path(str(outside), base_dir=str(base))


def test_sanitize_handles_relative_paths(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    (base / "sub").mkdir()
    rel_path = Path("sub/file.docx")
    abs_path = (base / rel_path).resolve()
    assert Path(sanitize_file_path(str(rel_path), base_dir=str(base))) == abs_path


def test_sanitize_handles_nonexistent_paths(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    missing = base / "missing.docx"
    # Should not raise even though the target doesn't exist
    result = sanitize_file_path(str(missing), base_dir=str(base))
    assert Path(result) == missing.resolve()


@pytest.mark.parametrize("path", ["file.doc", "file.pdf", "file.rtf"])
def test_validate_source_rejects_legacy_formats(path: str) -> None:
    with pytest.raises(SecurityError, match="Legacy file format"):
        validate_source(path)


@pytest.mark.parametrize(
    "url",
    ["HTTPS://example.com/file.docx", "HTTP://example.com/file.docx"],
)
def test_validate_source_handles_uppercase_schemes(url: str) -> None:
    with pytest.raises(SecurityError, match="Non-government"):
        validate_source(url)


def test_validate_source_requires_extension_with_query() -> None:
    with pytest.raises(SecurityError, match="Missing file extension"):
        validate_source("file?download=1")


def test_validate_source_rejects_unsupported_scheme() -> None:
    """Non-HTTP schemes like FTP should be rejected explicitly."""
    with pytest.raises(SecurityError, match="Unsupported URL scheme"):
        validate_source("ftp://example.gov/file.docx")


def test_validate_source_accepts_windows_paths() -> None:
    """Windows-style absolute paths should be treated as local files."""
    validate_source("C:\\gov\\docs\\file.docx")


def test_validate_source_allows_scheme_less_domain() -> None:
    """Bare domains without an explicit scheme should be treated as paths."""
    validate_source("agency.gov/file.docx")


def test_validate_source_trims_whitespace() -> None:
    """Surrounding whitespace should not cause valid sources to fail."""
    validate_source("  https://agency.gov/file.docx  ")


def test_validate_source_protocol_relative_urls() -> None:
    """Protocol-relative URLs must still validate the target domain."""
    validate_source("//agency.gov/file.docx")
    with pytest.raises(SecurityError, match="Non-government"):
        validate_source("//example.com/file.docx")


def test_validate_source_rejects_disallowed_extension() -> None:
    """Extensions outside the approved list should be rejected."""
    with pytest.raises(SecurityError, match="Disallowed file format"):
        validate_source("https://agency.gov/file.exe")


def test_validate_source_requires_extension_for_urls() -> None:
    """Remote resources must include an extension for validation."""
    with pytest.raises(SecurityError, match="Missing file extension"):
        validate_source("https://agency.gov/download")


def test_validate_source_allows_uppercase_extension() -> None:
    """Uppercase extensions should normalise successfully."""
    validate_source("//agency.gov/file.DOCX")


def test_validate_source_rejects_windows_disallowed_extension() -> None:
    """Windows paths should still enforce allowed extensions."""
    with pytest.raises(SecurityError, match="Disallowed file format"):
        validate_source("C:\\gov\\docs\\file.exe")


def test_rate_limiter_prunes_stale_clients() -> None:
    limiter = RateLimiter(max_requests=1, time_window=1)
    limiter.requests["old"] = [time.time() - 2]
    limiter.is_rate_limited("new")
    assert "old" not in limiter.requests


def test_rate_limiter_zero_disables() -> None:
    """A max_requests value of 0 should disable limiting."""
    limiter = RateLimiter(max_requests=0, time_window=1)
    assert not limiter.is_rate_limited("a")
    assert not limiter.is_rate_limited("a")


def test_validate_file_accepts_allowed_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A small file with an allowed MIME type should pass validation."""
    file_path = tmp_path / "doc.docx"
    file_path.write_bytes(b"content")

    class Kind:
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    monkeypatch.setattr(security_module.os.path, "getsize", lambda _: 512)
    monkeypatch.setattr(security_module.filetype, "guess", lambda _: Kind())

    validate_file(str(file_path))


def test_validate_file_rejects_large_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files larger than the configured maximum should be rejected."""
    file_path = tmp_path / "large.docx"
    file_path.write_bytes(b"content")

    monkeypatch.setattr(security_module.os.path, "getsize", lambda _: 10 * 1024 * 1024)
    monkeypatch.setattr(security_module.filetype, "guess", lambda _: None)

    with pytest.raises(SecurityError, match="File size exceeds"):
        validate_file(str(file_path))


def test_validate_file_rejects_legacy_mime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy MIME types should trigger a security error."""
    file_path = tmp_path / "legacy.doc"
    file_path.write_bytes(b"content")

    class Kind:
        mime = "application/pdf"

    monkeypatch.setattr(security_module.os.path, "getsize", lambda _: 512)
    monkeypatch.setattr(security_module.filetype, "guess", lambda _: Kind())

    with pytest.raises(SecurityError, match="Legacy file format"):
        validate_file(str(file_path))


def test_validate_file_rejects_unknown_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown MIME types should not be accepted."""
    file_path = tmp_path / "unknown.bin"
    file_path.write_bytes(b"content")

    monkeypatch.setattr(security_module.os.path, "getsize", lambda _: 512)
    monkeypatch.setattr(security_module.filetype, "guess", lambda _: None)

    with pytest.raises(SecurityError, match="Invalid file type"):
        validate_file(str(file_path))


def test_rate_limit_sync_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """The synchronous rate limiter should raise once the limit is exceeded."""
    limiter = RateLimiter(max_requests=1, time_window=60)
    monkeypatch.setattr(security_module, "rate_limiter", limiter)

    calls: list[int] = []

    @rate_limit
    def handler(value: int) -> int:
        calls.append(value)
        return value

    assert handler(1) == 1
    with pytest.raises(HTTPException) as exc:
        handler(2)
    assert exc.value.status_code == 429
    assert calls == [1]


def test_rate_limit_async_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Async callables wrapped with ``rate_limit`` should also honour the limit."""
    limiter = RateLimiter(max_requests=1, time_window=60)
    monkeypatch.setattr(security_module, "rate_limiter", limiter)

    @rate_limit
    async def handler() -> str:
        return "ok"

    assert asyncio.run(handler()) == "ok"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(handler())
    assert exc.value.status_code == 429
