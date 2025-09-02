from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from govdocverify.plugins import Plugin


class GoodPlugin(Plugin):
    """Example plugin implementing the required hooks."""

    @property
    def name(self) -> str:
        return "good"

    def register(self) -> None:  # pragma: no cover - no behavior
        pass


def test_plugin_instantiation() -> None:
    plugin = GoodPlugin()
    assert plugin.name == "good"


def test_missing_register_raises() -> None:
    class NoRegister(Plugin):
        @property
        def name(self) -> str:  # pragma: no cover - not executed
            return "no-register"

    with pytest.raises(TypeError):
        NoRegister()


def test_missing_name_raises() -> None:
    class NoName(Plugin):
        def register(self) -> None:  # pragma: no cover - not executed
            pass

    with pytest.raises(TypeError):
        NoName()
