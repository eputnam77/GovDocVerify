from pathlib import Path


def test_readme_documents_process_endpoint() -> None:
    """Placeholder test for documenting the /process API endpoint."""
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "/process" in readme and "curl" in readme
