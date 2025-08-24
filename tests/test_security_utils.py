from pathlib import Path

import pytest

from govdocverify.utils.security import (
    SecurityError,
    sanitize_file_path,
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
