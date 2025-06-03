import logging
import logging.config
import os
import sys

log_path = os.path.abspath("document_checker.log")

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': log_path,
            'mode': 'w',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

# Non-debug configuration for normal operation
LOGGING_CONFIG_INFO = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'default',
            'filename': log_path,
            'mode': 'w',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

def setup_logging(debug=False):
    """Set up logging configuration.

    Args:
        debug (bool): If True, use DEBUG level logging. If False, use INFO level.
    """
    if debug:
        logging.config.dictConfig(LOGGING_CONFIG)
    else:
        logging.config.dictConfig(LOGGING_CONFIG_INFO)
