"""Plugin system for govdocverify.

This package exposes the :class:`~govdocverify.plugins.base.Plugin` base
class used to build extensions that provide additional checks or
processing hooks.
"""

from .base import Plugin

__all__ = ["Plugin"]
