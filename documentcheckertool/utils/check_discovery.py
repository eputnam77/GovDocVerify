import importlib
import inspect
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def discover_checks() -> Dict[str, List[str]]:
    """Auto-discover all check functions in the codebase.

    Returns:
        Dictionary mapping categories to lists of check function names
    """
    check_modules = [
        "heading_checks",
        "format_checks",
        "structure_checks",
        "terminology_checks",
        "readability_checks",
        "acronym_checks",
        "accessibility_checks",
        "reference_checks",
    ]

    category_mappings = {}
    logger.debug("Starting check discovery process")
    logger.debug(f"Looking for checks in modules: {check_modules}")

    for module_name in check_modules:
        try:
            logger.debug(f"Attempting to import module: {module_name}")
            module = importlib.import_module(f"documentcheckertool.checks.{module_name}")
            default_category = module_name.replace("_checks", "")
            logger.debug(
                f"Successfully imported module {module_name}, default category: {default_category}"
            )

            # Find all check functions and classes in the module
            logger.debug(f"Searching for check functions and classes in {module_name}")
            for name, obj in inspect.getmembers(module):
                logger.debug(f"Examining member: {name}, type: {type(obj)}")

                # Check for standalone functions
                if inspect.isfunction(obj):
                    logger.debug(f"Found function: {name}")
                    if name.startswith("check_") or name.startswith("_check_"):
                        logger.debug(f"Found check function: {name}")
                        # Use default category for standalone functions
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

                # Check for classes that inherit from BaseChecker
                elif inspect.isclass(obj):
                    logger.debug(f"Found class: {name}")
                    try:
                        from documentcheckertool.checks.base_checker import BaseChecker

                        if issubclass(obj, BaseChecker) and obj != BaseChecker:
                            logger.debug(f"Found checker class: {name}")
                            # Check if the class has a category attribute
                            class_instance = None
                            try:
                                class_instance = obj()
                                class_category = getattr(
                                    class_instance, "category", default_category
                                )
                                logger.debug(f"Class {name} has category: {class_category}")
                            except Exception as e:
                                logger.debug(f"Could not instantiate {name} to get category: {e}")
                                class_category = default_category

                            # Get all methods from the class
                            for method_name, method in inspect.getmembers(
                                obj, predicate=inspect.isfunction
                            ):
                                logger.debug(f"Examining method: {method_name}")
                                # Only include public check methods and specific private methods that are registered
                                # Public methods: check_text, check_document, run_checks
                                # Specific private methods: _check_paragraph_length, _check_sentence_length (from structure)
                                if method_name in [
                                    "check_text",
                                    "check_document",
                                    "run_checks",
                                ] or method_name in [
                                    "_check_paragraph_length",
                                    "_check_sentence_length",
                                ]:
                                    logger.debug(f"Found registered check method: {method_name}")
                                    # Use the class's category instead of default
                                    category = class_category
                                    if category not in category_mappings:
                                        category_mappings[category] = []
                                        logger.debug(f"Created new category: {category}")
                                    if method_name not in category_mappings[category]:
                                        category_mappings[category].append(method_name)
                                        logger.debug(
                                            f"Added check {method_name} to category {category}"
                                        )
                                    else:
                                        logger.debug(
                                            f"Check {method_name} already registered in category {category}"
                                        )
                                else:
                                    logger.debug(
                                        f"Skipping {method_name} - not a registered check method"
                                    )
                    except ImportError:
                        logger.warning(f"Could not import BaseChecker for class {name}")
                        continue
                else:
                    logger.debug(f"Skipping {name} - not a function or class")

        except ImportError as e:
            logger.warning(f"Could not import module {module_name}: {str(e)}")
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error processing module {module_name}: {str(e)}", exc_info=True
            )
            continue

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

    validation_results = {"missing_categories": [], "missing_checks": [], "extra_checks": []}

    # Create a flat list of all discovered checks across all categories
    all_discovered_checks = set()
    for category_checks in discovered_checks.values():
        all_discovered_checks.update(category_checks)

    # Create a flat list of all registered checks across all categories
    all_registered_checks = set()
    for category_checks in registered_checks.values():
        all_registered_checks.update(category_checks)

    logger.debug(f"All discovered checks: {all_discovered_checks}")
    logger.debug(f"All registered checks: {all_registered_checks}")

    # Check for missing categories
    for category in discovered_checks:
        logger.debug(f"Checking category: {category}")
        if category not in registered_checks:
            logger.debug(f"Category {category} is missing from registry")
            validation_results["missing_categories"].append(category)

    # Check for missing or extra checks in each category
    for category in registered_checks:
        logger.debug(f"Validating category: {category}")
        if category in discovered_checks:
            # Find missing checks (checks discovered in this category but not registered in this category)
            for check in discovered_checks[category]:
                logger.debug(f"Checking if {check} is registered in {category}")
                if check not in registered_checks[category]:
                    # Check if it's registered in a different category (cross-category registration)
                    found_in_other_category = any(
                        check in other_checks
                        for other_cat, other_checks in registered_checks.items()
                        if other_cat != category
                    )
                    if not found_in_other_category:
                        logger.debug(
                            f"Check {check} is missing from registry in category {category}"
                        )
                        validation_results["missing_checks"].append(f"{category}.{check}")
                    else:
                        logger.debug(
                            f"Check {check} is registered in a different category (cross-category registration)"
                        )

            # Find extra checks (checks registered in this category but not discovered in this category)
            for check in registered_checks[category]:
                logger.debug(f"Checking if {check} exists in discovered checks for {category}")
                if check not in discovered_checks[category]:
                    # Check if it exists in any discovered category (cross-category registration)
                    found_in_other_category = any(
                        check in other_checks
                        for other_cat, other_checks in discovered_checks.items()
                        if other_cat != category
                    )
                    if not found_in_other_category:
                        logger.debug(f"Check {check} is extra in registry for category {category}")
                        validation_results["extra_checks"].append(f"{category}.{check}")
                    else:
                        logger.debug(
                            f"Check {check} is discovered in a different category (cross-category registration)"
                        )
        else:
            # Category is not discovered at all, check if any of its checks exist in other categories
            logger.debug(
                f"Category {category} not found in discovered checks; checking for cross-category registrations."
            )
            for check in registered_checks[category]:
                found_in_other_category = any(
                    check in other_checks for other_cat, other_checks in discovered_checks.items()
                )
                if not found_in_other_category:
                    validation_results["extra_checks"].append(f"{category}.{check}")
                else:
                    logger.debug(
                        f"Check {check} from category {category} found in another discovered category (cross-category registration)"
                    )

    logger.debug(f"Validation results: {validation_results}")
    return validation_results
