import logging

from documentcheckertool.logging_config import setup_logging


def test_setup_logging_debug():
    setup_logging(debug=True)
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


def test_setup_logging_info():
    setup_logging(debug=False)
    assert logging.getLogger().getEffectiveLevel() == logging.INFO
