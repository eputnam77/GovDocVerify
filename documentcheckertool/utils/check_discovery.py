import importlib
import inspect
import logging
from types import ModuleType
from typing import Any, Callable, Dict, List, Type

logger = logging.getLogger(__name__)


def _process_function(
    obj: Callable[..., Any],
    name: str,
    default_category: str,
    category_mappings: Dict[str, List[str]],
) -> None:
    """Process a function to determine if it's a check function."""
    if name.startswith("check_") or name.startswith("_check_"):
        category = default_category
        if category not in category_mappings:
            category_mappings[category] = []
            logger.debug(f"Created new category: {category}")
        if name not in category_mappings[category]:
            category_mappings[category].append(name)
            logger.debug(f"Added check {name} to category {category}")
        else:
            logger.debug(f"Check {name} already registered in category {category}")
    else:
        logger.debug(f"Skipping {name} - doesn't match check naming pattern")


def _get_class_category(obj: Type[Any], name: str, default_category: str) -> str:
    """Get the category for a checker class."""
    try:
        class_instance = obj()
        class_category = getattr(class_instance, "category", default_category)
        logger.debug(f"Class {name} has category: {class_category}")
        return class_category
    except Exception as e:
        logger.debug(f"Could not instantiate {name} to get category: {e}")
        return default_category


def _is_valid_check_method(method_name: str) -> bool:
    """Return ``True`` if ``method_name`` represents a check implementation."""

    standard_methods = {"check_text", "check_document"}
    special_methods = {"_check_paragraph_length", "_check_sentence_length"}

    if method_name in standard_methods or method_name in special_methods:
        return True

    return method_name.startswith("check_") or method_name.startswith("_check_")


def _process_class_methods(
    obj: Type[Any], class_category: str, category_mappings: Dict[str, List[str]]
) -> None:
    """Process methods of a checker class."""
    for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
        logger.debug(f"Examining method: {method_name}")
        if _is_valid_check_method(method_name):
            if class_category not in category_mappings:
                category_mappings[class_category] = []
                logger.debug(f"Created new category: {class_category}")
            if method_name not in category_mappings[class_category]:
                category_mappings[class_category].append(method_name)
                logger.debug(f"Added check {method_name} to category {class_category}")
            else:
                logger.debug(f"Check {method_name} already registered in {class_category}")
        else:
            logger.debug(f"Skipping {method_name} - not a registered check method")


def _process_class(
    obj: Type[Any],
    name: str,
    default_category: str,
    category_mappings: Dict[str, List[str]],
) -> None:
    """Process a class to determine if it's a checker class."""
    try:
        from documentcheckertool.checks.base_checker import BaseChecker

        if issubclass(obj, BaseChecker) and obj != BaseChecker:
            logger.debug(f"Found checker class: {name}")
            class_category = _get_class_category(obj, name, default_category)
            _process_class_methods(obj, class_category, category_mappings)
    except ImportError:
        logger.warning(f"Could not import BaseChecker for class {name}")


def _process_module_members(
    module: ModuleType, default_category: str, category_mappings: Dict[str, List[str]]
) -> None:
    """Process all members of a module."""
    for name, obj in inspect.getmembers(module):
        logger.debug(f"Examining member: {name}, type: {type(obj)}")
        if inspect.isfunction(obj):
            _process_function(obj, name, default_category, category_mappings)
        elif inspect.isclass(obj):
            _process_class(obj, name, default_category, category_mappings)
        else:
            logger.debug(f"Skipping {name} - not a function or class")


def _process_module(module_name: str, category_mappings: Dict[str, List[str]]) -> None:
    """Process a single module to discover checks."""
    try:
        logger.debug(f"Attempting to import module: {module_name}")
        module = importlib.import_module(f"documentcheckertool.checks.{module_name}")
        default_category = module_name.replace("_checks", "")
        logger.debug(
            f"Successfully imported module {module_name}, default category: {default_category}"
        )
        logger.debug(f"Searching for check functions and classes in {module_name}")
        _process_module_members(module, default_category, category_mappings)
    except ImportError as e:
        logger.warning(f"Could not import module {module_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing module {module_name}: {str(e)}", exc_info=True)


def _get_check_modules() -> List[str]:
    """Get the list of check modules to process."""
    return [
        "heading_checks",
        "format_checks",
        "structure_checks",
        "terminology_checks",
        "readability_checks",
        "acronym_checks",
        "accessibility_checks",
        "reference_checks",
    ]


def discover_checks() -> Dict[str, List[str]]:
    """Auto-discover all check functions in the codebase.

    Returns:
        Dictionary mapping categories to lists of check function names
    """
    check_modules = _get_check_modules()
    category_mappings: Dict[str, List[str]] = {}
    logger.debug("Starting check discovery process")
    logger.debug(f"Looking for checks in modules: {check_modules}")

    for module_name in check_modules:
        _process_module(module_name, category_mappings)

    logger.debug(f"Check discovery complete. Found categories: {list(category_mappings.keys())}")
    for category, checks in category_mappings.items():
        logger.debug(f"Category {category} has checks: {checks}")
    return category_mappings


def validate_check_registration() -> Dict[str, List[str]]:
    """Validate that all discovered checks are properly registered.

    Returns:
        Dictionary of validation results with any discrepancies found
    """
    from documentcheckertool.checks.check_registry import CheckRegistry

    logger.debug("Starting check registration validation")

    discovered_checks = discover_checks()
    logger.debug(f"Discovered checks: {discovered_checks}")

    registered_checks = CheckRegistry.get_category_mappings()
    logger.debug(f"Registered checks: {registered_checks}")

    validation_results: Dict[str, List[str]] = {
        "missing_categories": [],
        "missing_checks": [],
        "extra_checks": [],
    }

    # Check for missing categories
    _check_missing_categories(discovered_checks, registered_checks, validation_results)

    # Check for missing or extra checks in each category
    _validate_checks_in_categories(discovered_checks, registered_checks, validation_results)

    logger.debug(f"Validation results: {validation_results}")
    return validation_results


def _check_missing_categories(
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Check for categories that are discovered but not registered."""
    for category in discovered_checks:
        logger.debug(f"Checking category: {category}")
        if category not in registered_checks:
            logger.debug(f"Category {category} is missing from registry")
            validation_results["missing_categories"].append(category)


def _validate_checks_in_categories(
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Validate checks within each registered category."""
    for category in registered_checks:
        logger.debug(f"Validating category: {category}")
        if category in discovered_checks:
            _validate_existing_category(
                category, discovered_checks, registered_checks, validation_results
            )
        else:
            _validate_missing_category(
                category, discovered_checks, registered_checks, validation_results
            )


def _validate_existing_category(
    category: str,
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Validate checks in a category that exists in both discovered and registered."""
    # Check for missing checks
    _check_missing_checks_in_category(
        category, discovered_checks, registered_checks, validation_results
    )

    # Check for extra checks
    _check_extra_checks_in_category(
        category, discovered_checks, registered_checks, validation_results
    )


def _check_missing_checks_in_category(
    category: str,
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Check for checks discovered in category but not registered in category."""
    for check in discovered_checks[category]:
        logger.debug(f"Checking if {check} is registered in {category}")
        if check not in registered_checks[category]:
            # Check if it's registered in a different category (cross-category registration)
            found_in_other_category = _is_check_in_other_categories(
                check, category, registered_checks
            )
            if not found_in_other_category:
                logger.debug(f"Check {check} is missing from registry in category {category}")
                validation_results["missing_checks"].append(f"{category}.{check}")
            else:
                logger.debug(f"Check {check} is registered in a different category")


def _check_extra_checks_in_category(
    category: str,
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Check for checks registered in category but not discovered in category."""
    for check in registered_checks[category]:
        logger.debug(f"Checking if {check} exists in discovered checks for {category}")
        if check not in discovered_checks[category]:
            # Check if it exists in any discovered category
            found_in_other_category = _is_check_in_other_categories(
                check, category, discovered_checks
            )
            if not found_in_other_category:
                logger.debug(f"Check {check} is extra in registry for category {category}")
                validation_results["extra_checks"].append(f"{category}.{check}")
            else:
                logger.debug(f"Check {check} is discovered in a different category")


def _validate_missing_category(
    category: str,
    discovered_checks: Dict[str, List[str]],
    registered_checks: Dict[str, List[str]],
    validation_results: Dict[str, List[str]],
) -> None:
    """Validate a category that is registered but not discovered."""
    logger.debug(f"Category {category} not found in discovered checks")
    for check in registered_checks[category]:
        found_in_other_category = any(
            check in other_checks for other_cat, other_checks in discovered_checks.items()
        )
        if not found_in_other_category:
            validation_results["extra_checks"].append(f"{category}.{check}")
        else:
            logger.debug(f"Check {check} from category {category} found in another category")


def _is_check_in_other_categories(
    check: str, current_category: str, check_mappings: Dict[str, List[str]]
) -> bool:
    """Check if a check exists in categories other than the current one."""
    return any(
        check in other_checks
        for other_cat, other_checks in check_mappings.items()
        if other_cat != current_category
    )
