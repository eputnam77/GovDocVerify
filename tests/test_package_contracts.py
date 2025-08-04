"""Placeholder tests for package architecture and contracts."""

import pytest


@pytest.mark.skip("PK-01: public API contract enforcement not implemented")
def test_public_api_contract() -> None:
    """PK-01: ensure only intended modules are exported."""
    ...


@pytest.mark.skip("PK-02: plugin interface contract not implemented")
def test_plugin_interface_contract() -> None:
    """PK-02: plugin interface validates required hooks."""
    ...


@pytest.mark.skip("PK-03: serialization versioning not implemented")
def test_serialization_versioning() -> None:
    """PK-03: serialized data includes version metadata."""
    ...
