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
