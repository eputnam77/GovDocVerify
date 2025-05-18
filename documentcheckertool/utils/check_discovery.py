import importlib
import inspect
import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def discover_checks() -> Dict[str, List[str]]:
    """Auto-discover all check functions in the codebase.

    Returns:
        Dictionary mapping categories to lists of check function names
    """
    check_modules = [
        'heading_checks',
        'format_checks',
        'structure_checks',
        'terminology_checks',
        'readability_checks',
        'acronym_checks',
        'accessibility_checks'
    ]

    category_mappings = {}
    logger.debug("Starting check discovery process")
    logger.debug(f"Looking for checks in modules: {check_modules}")

    for module_name in check_modules:
        try:
            logger.debug(f"Attempting to import module: {module_name}")
            module = importlib.import_module(f'documentcheckertool.checks.{module_name}')
            category = module_name.replace('_checks', '')
            logger.debug(f"Successfully imported module {module_name}, category: {category}")

            # Find all check functions and classes in the module
            logger.debug(f"Searching for check functions and classes in {module_name}")
            for name, obj in inspect.getmembers(module):
                logger.debug(f"Examining member: {name}, type: {type(obj)}")

                # Check for standalone functions
                if inspect.isfunction(obj):
                    logger.debug(f"Found function: {name}")
                    if name.startswith('check_') or name.startswith('_check_'):
                        logger.debug(f"Found check function: {name}")
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
                            # Get all methods from the class
                            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                                logger.debug(f"Examining method: {method_name}")
                                if method_name.startswith('check_') or method_name.startswith('_check_'):
                                    logger.debug(f"Found check method: {method_name}")
                                    if category not in category_mappings:
                                        category_mappings[category] = []
                                        logger.debug(f"Created new category: {category}")
                                    if method_name not in category_mappings[category]:
                                        category_mappings[category].append(method_name)
                                        logger.debug(f"Added check {method_name} to category {category}")
                                    else:
                                        logger.debug(f"Check {method_name} already registered in category {category}")
                                else:
                                    logger.debug(f"Skipping {method_name} - doesn't match check naming pattern")
                    except ImportError:
                        logger.warning(f"Could not import BaseChecker for class {name}")
                        continue
                else:
                    logger.debug(f"Skipping {name} - not a function or class")

        except ImportError as e:
            logger.warning(f"Could not import module {module_name}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing module {module_name}: {str(e)}", exc_info=True)
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

    validation_results = {
        'missing_categories': [],
        'missing_checks': [],
        'extra_checks': []
    }

    # Check for missing categories
    for category in discovered_checks:
        logger.debug(f"Checking category: {category}")
        if category not in registered_checks:
            logger.debug(f"Category {category} is missing from registry")
            validation_results['missing_categories'].append(category)

    # Check for missing or extra checks in each category
    for category in registered_checks:
        logger.debug(f"Validating category: {category}")
        if category in discovered_checks:
            # Find missing checks
            for check in discovered_checks[category]:
                logger.debug(f"Checking if {check} is registered in {category}")
                if check not in registered_checks[category]:
                    logger.debug(f"Check {check} is missing from registry in category {category}")
                    validation_results['missing_checks'].append(f"{category}.{check}")

            # Find extra checks
            for check in registered_checks[category]:
                logger.debug(f"Checking if {check} exists in discovered checks for {category}")
                if check not in discovered_checks[category]:
                    logger.debug(f"Check {check} is extra in registry for category {category}")
                    validation_results['extra_checks'].append(f"{category}.{check}")
        else:
            # Category is not discovered at all, so all its checks are extra
            logger.debug(f"Category {category} not found in discovered checks; all checks are extra.")
            for check in registered_checks[category]:
                validation_results['extra_checks'].append(f"{category}.{check}")

    logger.debug(f"Validation results: {validation_results}")
    return validation_results