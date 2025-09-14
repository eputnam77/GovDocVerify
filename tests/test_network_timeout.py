import importlib
import sys

from govdocverify.utils import network


def test_fetch_url_uses_timeout(monkeypatch):
    called = {}

    def fake_get(url, timeout):
        called['timeout'] = timeout
        class Resp:
            text = 'ok'
            def raise_for_status(self):
                pass
        return Resp()

    monkeypatch.setattr(network.httpx, 'get', fake_get)
    assert network.fetch_url('http://example.com') == 'ok'
    assert called['timeout'] == network.DEFAULT_TIMEOUT


def test_invalid_timeout_env_uses_default(monkeypatch):
    monkeypatch.setenv("GOVDOCVERIFY_HTTP_TIMEOUT", "invalid")
    sys.modules.pop("govdocverify.utils.network", None)
    module = importlib.import_module("govdocverify.utils.network")
    assert module.DEFAULT_TIMEOUT == 5.0


def test_negative_timeout_env_uses_default(monkeypatch):
    """Negative timeout values should fall back to the default."""
    monkeypatch.setenv("GOVDOCVERIFY_HTTP_TIMEOUT", "-10")
    sys.modules.pop("govdocverify.utils.network", None)
    module = importlib.import_module("govdocverify.utils.network")
    assert module.DEFAULT_TIMEOUT == 5.0
