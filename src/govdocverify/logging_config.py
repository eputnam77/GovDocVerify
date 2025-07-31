import logging
import logging.config
import os
import sys
from io import TextIOWrapper


def _ensure_utf8(stream: TextIOWrapper) -> TextIOWrapper:
    """Return a text stream guaranteed to use UTF-8 encoding."""
    if hasattr(stream, "reconfigure"):
        try:  # pragma: no cover - platform dependent
            stream.reconfigure(encoding="utf-8", errors="replace")
            return stream
        except Exception:
            pass
    return TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")


log_path = os.path.abspath("document_checker.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filename": log_path,
            "mode": "w",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}

# Non-debug configuration for normal operation
LOGGING_CONFIG_INFO = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": log_path,
            "mode": "w",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}


def setup_logging(debug: bool = False) -> None:
    """Set up logging configuration.

    Args:
        debug (bool): If True, use DEBUG level logging. If False, use INFO level.
    """
    # Ensure stdio streams use UTF-8 and gracefully handle unsupported characters
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        new_stream = _ensure_utf8(stream)
        setattr(sys, stream_name, new_stream)
        # update __stdout__/__stderr__ as well so logging picks up the wrapper
        if hasattr(sys, f"__{stream_name}__"):
            setattr(sys, f"__{stream_name}__", new_stream)

    if debug:
        logging.config.dictConfig(LOGGING_CONFIG)
    else:
        logging.config.dictConfig(LOGGING_CONFIG_INFO)

    # Ensure all StreamHandlers use UTF-8 after configuration
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.stream = _ensure_utf8(handler.stream)
