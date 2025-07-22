import logging

from govdocverify.logging_config import setup_logging


def test_setup_logging_debug():
    setup_logging(debug=True)
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


def test_setup_logging_info():
    setup_logging(debug=False)
    assert logging.getLogger().getEffectiveLevel() == logging.INFO


def test_console_stream_encoding_utf8():
    setup_logging(debug=True)
    root_logger = logging.getLogger()
    stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
    assert stream_handlers, "No StreamHandler configured"
    for handler in stream_handlers:
        assert handler.stream.encoding.lower() == "utf-8"
