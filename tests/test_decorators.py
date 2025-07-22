import logging
import time

from govdocverify.utils.decorators import profile_performance


def test_profile_performance(caplog):
    @profile_performance
    def sample(x):
        time.sleep(0.01)
        return x * 2

    with caplog.at_level(logging.DEBUG):
        result = sample(3)

    assert result == 6
    assert any("sample took" in record.message for record in caplog.records)
