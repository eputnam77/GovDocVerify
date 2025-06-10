import time

from documentcheckertool.utils.decorators import profile_performance


def test_profile_performance(capsys):
    @profile_performance
    def sample(x):
        time.sleep(0.01)
        return x * 2

    result = sample(3)
    captured = capsys.readouterr()
    assert result == 6
    assert "sample took" in captured.out
