# pytest -v tests/test_check_registry.py --log-cli-level=DEBUG

import logging

from documentcheckertool.checks.check_registry import CheckRegistry
from documentcheckertool.utils.check_discovery import discover_checks, validate_check_registration

logger = logging.getLogger(__name__)

def test_check_registration():
    """Test the check registration decorator."""
    logger.debug("Starting test_check_registration")

    # Clear the registry before testing
    CheckRegistry.clear_registry()
    logger.debug("Registry cleared")

    # Define a test check function
    @CheckRegistry.register('test')
    def test_check():
        pass

    # Verify the check was registered
    logger.debug("Verifying check registration")
    category_mappings = CheckRegistry.get_category_mappings()
    logger.debug(f"Category mappings: {category_mappings}")

    assert 'test' in category_mappings, "Test category not found in registry"
    assert 'test_check' in category_mappings['test'], "Test check not found in test category"

    # Test duplicate registration
    logger.debug("Testing duplicate registration")
    @CheckRegistry.register('test')
    def test_check():
        pass

    # Verify no duplicate was added
    logger.debug("Verifying no duplicate was added")
    assert category_mappings['test'].count('test_check') == 1, "Duplicate check found in registry"

    logger.debug("test_check_registration completed successfully")

def test_check_discovery():
    """Test the check discovery functionality."""
    logger.debug("Starting test_check_discovery")

    # Clear the registry before testing
    CheckRegistry.clear_registry()
    logger.debug("Registry cleared")

    # Discover checks
    discovered = discover_checks()
    logger.debug(f"Discovered checks: {discovered}")

    # Verify we found some checks
    assert len(discovered) > 0, "No checks discovered"
    logger.debug(f"Found {len(discovered)} categories")

    # Verify each category has checks
    for category, checks in discovered.items():
        logger.debug(f"Checking category: {category}")
        assert len(checks) > 0, f"No checks found in category {category}"
        logger.debug(f"Category {category} has {len(checks)} checks")

        # Verify check names follow the expected pattern
        for check in checks:
            logger.debug(f"Verifying check name pattern: {check}")
            assert check.startswith('check_') or check.startswith('_check_'), \
                f"Check {check} does not follow naming pattern"

    logger.debug("test_check_discovery completed successfully")

def test_validation():
    """Test the check validation functionality."""
    logger.debug("Starting test_validation")

    # Clear the registry
    CheckRegistry.clear_registry()
    logger.debug("Registry cleared")

    # Register a test check
    @CheckRegistry.register('test')
    def test_check():
        pass

    logger.debug("Test check registered")

    # Run validation
    validation_results = validate_check_registration()
    logger.debug(f"Validation results: {validation_results}")

    # Verify validation found our test check as an extra check
    assert 'test.test_check' in validation_results['extra_checks'], \
        "Test check not found in extra_checks"
    logger.debug("Verified test check is in extra_checks")

    # Verify validation found missing categories from discovery
    discovered = discover_checks()
    logger.debug(f"Discovered checks: {discovered}")

    for category in discovered:
        if category != 'test':
            logger.debug(f"Checking category: {category}")
            assert category in validation_results['missing_categories'], \
                f"Category {category} not found in missing_categories"

    logger.debug("test_validation completed successfully")

def test_get_checks_for_category():
    """Test getting checks for a specific category."""
    logger.debug("Starting test_get_checks_for_category")

    # Clear the registry
    CheckRegistry.clear_registry()
    logger.debug("Registry cleared")

    # Register some test checks
    @CheckRegistry.register('test')
    def test_check1():
        pass

    @CheckRegistry.register('test')
    def test_check2():
        pass

    logger.debug("Test checks registered")

    # Verify we can get checks for the category
    checks = CheckRegistry.get_checks_for_category('test')
    logger.debug(f"Retrieved checks for 'test' category: {checks}")

    assert len(checks) == 2, f"Expected 2 checks, got {len(checks)}"
    assert 'test_check1' in checks, "test_check1 not found"
    assert 'test_check2' in checks, "test_check2 not found"

    # Verify empty list for non-existent category
    nonexistent_checks = CheckRegistry.get_checks_for_category('nonexistent')
    logger.debug(f"Retrieved checks for 'nonexistent' category: {nonexistent_checks}")

    assert len(nonexistent_checks) == 0, "Expected empty list for nonexistent category"

    logger.debug("test_get_checks_for_category completed successfully")
