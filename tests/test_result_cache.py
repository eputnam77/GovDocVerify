import importlib
import time

import pytest


def test_result_expiration(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("RESULT_TTL", "1")
    monkeypatch.setenv("RESULT_CLEANUP_INTERVAL", "0")
    import backend.api as api
    importlib.reload(api)
    api._RESULTS_DIR = tmp_path
    api._save_result("rid", {"value": 1})
    assert api._load_result("rid") == {"value": 1}
    time.sleep(1.2)
    api._cleanup_results(force=True)
    assert api._load_result("rid") is None
