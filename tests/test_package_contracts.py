"""Tests covering package architecture and public contracts."""

import importlib
import sys

import pytest


def test_public_api_contract() -> None:
    """Ensure only the intended names are exported from :mod:`govdocverify`."""
    # Import the package fresh to ensure submodules are not already loaded.
    sys.modules.pop("govdocverify", None)
    gv = importlib.import_module("govdocverify")

    expected = {
        "DocumentChecker",
        "DocumentCheckResult",
        "VisibilitySettings",
        "Severity",
        "save_results_as_docx",
        "save_results_as_pdf",
    }

    assert set(gv.__all__) == expected


def test_internal_modules_not_exported() -> None:
    """Ensure internal modules are not surfaced as top-level attributes."""
    sys.modules.pop("govdocverify", None)
    gv = importlib.import_module("govdocverify")

    internal_names = {
        "document_checker",
        "checks",
        "cli",
        "utils",
        "config",
    }

    for name in internal_names:
        assert name not in gv.__all__, f"{name} leaked into __all__"
        assert not hasattr(gv, name), f"{name} should not be a top-level attribute"


def test_plugin_interface_contract() -> None:
    """PK-02: plugin interface validates required hooks."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from govdocverify.plugins import Plugin

    class SamplePlugin(Plugin):
        @property
        def name(self) -> str:
            return "sample"

        def register(self) -> None:  # pragma: no cover - no registration logic
            pass

    plugin = SamplePlugin()
    assert plugin.name == "sample"


@pytest.mark.skip("PK-03: serialization versioning not implemented")
def test_serialization_versioning() -> None:
    """PK-03: serialized data includes version metadata."""
    ...
