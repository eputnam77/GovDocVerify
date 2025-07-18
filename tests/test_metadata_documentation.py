from pathlib import Path

import pytest


def test_readme_lists_all_metadata_fields() -> None:
    """Placeholder test for documenting all metadata fields."""
    readme = Path("README.md").read_text(encoding="utf-8")
    required_fields = ["Title", "Author", "Last Modified By", "Created", "Modified"]
    missing = [field for field in required_fields if field not in readme]
    if missing:
        pytest.fail(f"README missing fields: {', '.join(missing)}")
