import h11
from packaging import version


def test_h11_min_version():
    assert version.parse(h11.__version__) >= version.parse("0.16.0")
