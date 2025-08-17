"""Plugin interface for :mod:`govdocverify`.

Plugins provide an extension mechanism for :mod:`govdocverify`. A plugin
is expected to expose a ``name`` property and implement the
:meth:`register` hook which allows the plugin to wire itself into the
application (for example by registering new checks with
:class:`govdocverify.checks.check_registry.CheckRegistry`).

Example::

    from govdocverify.plugins import Plugin

    class MyPlugin(Plugin):
        # Example plugin that registers custom checks.

        @property
        def name(self) -> str:
            return "my-plugin"

        def register(self) -> None:
            # registration logic goes here
            ...

Plugins may perform any setup they require inside :meth:`register` but
should avoid side effects at import time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Plugin(ABC):
    """Abstract base class for GovDocVerify plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable name for the plugin."""
        raise NotImplementedError

    @abstractmethod
    def register(self) -> None:
        """Hook for performing plugin registration."""
        raise NotImplementedError
