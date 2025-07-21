from pathlib import Path

import pytest

from documentcheckertool.docs import update_metadata_documentation


def test_readme_lists_all_metadata_fields() -> None:
    """Placeholder test for documenting all metadata fields."""
    readme = Path("README.md").read_text(encoding="utf-8")
    required_fields = ["Title", "Author", "Last Modified By", "Created", "Modified"]
    missing = [field for field in required_fields if field not in readme]
    if missing:
        pytest.fail(f"README missing fields: {', '.join(missing)}")


def test_update_metadata_documentation(tmp_path: Path) -> None:
    """Ensure the helper inserts a bullet when missing."""
    readme = tmp_path / "README.md"
    readme.write_text("## Features\n", encoding="utf-8")
    update_metadata_documentation(str(readme))
    content = readme.read_text(encoding="utf-8")
    assert "Displays document metadata" in content
