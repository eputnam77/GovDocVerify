# Known Issues

## Type Checking Failures

```
tests/test_checker_result_model.py:4: error: Function is missing a return type annotation  [no-untyped-def]
tests/test_checker_result_model.py:4: note: Use "-> None" if function does not return a value
tests/test_models_root.py:9: error: Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"  [arg-type]
tests/test_models_root.py:10: error: Item "None" of "ModuleSpec | None" has no attribute "loader"  [union-attr]
tests/test_models_root.py:10: error: Item "None" of "Loader | Any | None" has no attribute "exec_module"  [union-attr]
tests/test_models_root.py:13: error: Function is missing a return type annotation  [no-untyped-def]
tests/test_models_root.py:13: note: Use "-> None" if function does not return a value
tests/test_models_root.py:18: error: Function is missing a return type annotation  [no-untyped-def]
tests/test_models_root.py:18: note: Use "-> None" if function does not return a value
tests/test_models_root.py:28: error: Function is missing a return type annotation  [no-untyped-def]
```

Found 1071 errors
