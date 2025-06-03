import logging
from functools import wraps
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

class CheckRegistry:
    """Central registry for document check functions."""

    _checks: Dict[str, List[str]] = {}

    @classmethod
    def register(cls, category: str) -> Callable:
        """Decorator to register a check function in a specific category.

        Args:
            category: The category to register the check under

        Returns:
            Decorator function
        """
        logger.debug(f"Registering check in category: {category}")

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.debug(f"Executing registered check: {func.__name__}")
                return func(*args, **kwargs)

            # Register the check
            if category not in cls._checks:
                logger.debug(f"Creating new category: {category}")
                cls._checks[category] = []

            if func.__name__ not in cls._checks[category]:
                logger.debug(f"Adding check {func.__name__} to category {category}")
                cls._checks[category].append(func.__name__)
                logger.debug(f"Current registry state: {cls._checks}")
            else:
                logger.debug(f"Check {func.__name__} already registered in category {category}")

            return wrapper
        return decorator

    @classmethod
    def get_category_mappings(cls) -> Dict[str, List[str]]:
        """Get the current category mappings.

        Returns:
            Dictionary mapping categories to lists of check function names
        """
        logger.debug(f"Getting category mappings. Current state: {cls._checks}")
        return cls._checks

    @classmethod
    def get_checks_for_category(cls, category: str) -> List[str]:
        """Get all registered checks for a specific category.

        Args:
            category: The category to get checks for

        Returns:
            List of check function names in the category
        """
        logger.debug(f"Getting checks for category: {category}")
        checks = cls._checks.get(category, [])
        logger.debug(f"Found checks: {checks}")
        return checks

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the check registry. Mainly used for testing."""
        logger.debug("Clearing check registry")
        logger.debug(f"Previous registry state: {cls._checks}")
        cls._checks.clear()
        logger.debug("Check registry cleared")
        logger.debug(f"New registry state: {cls._checks}")
