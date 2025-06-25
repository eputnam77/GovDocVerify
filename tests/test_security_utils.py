from pathlib import Path

import pytest

from documentcheckertool.utils.security import SecurityError, sanitize_file_path


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
