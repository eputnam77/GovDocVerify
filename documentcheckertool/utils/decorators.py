import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

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
