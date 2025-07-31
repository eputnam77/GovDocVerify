import logging
import logging.config
import os
import sys
from io import TextIOWrapper

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
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass
        setattr(sys, stream_name, TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))

    if debug:
        logging.config.dictConfig(LOGGING_CONFIG)
    else:
        logging.config.dictConfig(LOGGING_CONFIG_INFO)

    # Ensure all StreamHandlers use UTF-8 after configuration
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            stream = handler.stream
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                    continue
                except Exception:  # pragma: no cover - platform dependent
                    pass
            handler.stream = TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
