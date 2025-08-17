import logging
import os
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Any])


def profile_performance(func: F) -> F:
    """Decorator to log the execution time of a function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug("%s took %.4f seconds to execute", func.__name__, execution_time)
        return result

    return cast(F, wrapper)


def retry_transient(
    max_attempts: int | None = None, backoff: float | None = None
) -> Callable[[F], F]:
    """Retry decorated function on transient errors with exponential backoff.

    Defaults are configured via ``GOVDOCVERIFY_MAX_RETRIES`` and
    ``GOVDOCVERIFY_BACKOFF`` environment variables.
    """

    max_attempts = max_attempts or int(os.getenv("GOVDOCVERIFY_MAX_RETRIES", "3"))
    backoff = backoff or float(os.getenv("GOVDOCVERIFY_BACKOFF", "0.1"))

    def decorator(func: F) -> F:
        return cast(
            F,
            retry(
                retry=retry_if_exception_type(Exception),
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=backoff),
                reraise=True,
            )(func),
        )

    return decorator
