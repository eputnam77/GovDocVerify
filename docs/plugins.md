# Plugin Interface

GovDocVerify can be extended through a small plugin system. Plugins are
regular Python classes that inherit from
`govdocverify.plugins.Plugin`.

## Required Hooks

Every plugin must implement two pieces:

1. **`name` property** – a human friendly identifier for the plugin.
2. **`register()` method** – called once to allow the plugin to register
   any checks or other behaviors with the application.

## Example

```python
from govdocverify.plugins import Plugin
from govdocverify.checks.check_registry import CheckRegistry

class ExtraChecks(Plugin):
    @property
    def name(self) -> str:
        return "extra-checks"

    def register(self) -> None:
        @CheckRegistry.register("custom")
        def my_check(document: str) -> None:
            ...  # perform additional validation
```

Plugins should avoid side effects at import time and perform all
registration within `register()`.
