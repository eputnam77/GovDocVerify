# pytest -v tests/test_document_checker.py --log-cli-level=DEBUG

import unittest
import logging
from unittest.mock import Mock, patch
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import DocumentCheckResult

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestFAADocumentChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test class - runs once before all tests."""
        logger.debug("Setting up TestFAADocumentChecker class")

    def setUp(self):
        """Set up each test - runs before each test method."""
        logger.debug("Setting up test case")
        self.checker = FAADocumentChecker()
        logger.debug("FAADocumentChecker instance created")

    def tearDown(self):
        """Clean up after each test - runs after each test method."""
        logger.debug("Tearing down test case")

    @classmethod
    def tearDownClass(cls):
        """Clean up test class - runs once after all tests."""
        logger.debug("Tearing down TestFAADocumentChecker class")

    def test_all_check_modules_instantiated(self):
        """Test that all check modules are properly instantiated."""
        logger.debug("Starting test_all_check_modules_instantiated")

        expected_modules = [
            'heading_checks',
            'accessibility_checks',
            'format_checks',
            'structure_checks',
            'terminology_checks',
            'readability_checks',
            'acronym_checker',  # Note: renamed from acronym_checks
            'table_figure_checks'
        ]

        logger.debug(f"Expected modules: {expected_modules}")

        for module_name in expected_modules:
            logger.debug(f"Checking for module: {module_name}")
            self.assertTrue(
                hasattr(self.checker, module_name),
                f"Check module {module_name} not instantiated"
            )
            logger.debug(f"Module {module_name} found")

            # Verify the module is properly initialized
            module = getattr(self.checker, module_name)
            logger.debug(f"Module {module_name} type: {type(module)}")

            # Verify the module has required methods
            if module_name in ['acronym_checker', 'table_figure_checks']:
                self.assertTrue(
                    hasattr(module, 'check_text'),
                    f"Module {module_name} missing check_text method"
                )
                logger.debug(f"Module {module_name} has check_text method")
            else:
                self.assertTrue(
                    hasattr(module, 'run_checks'),
                    f"Module {module_name} missing run_checks method"
                )
                logger.debug(f"Module {module_name} has run_checks method")

        logger.debug("Completed test_all_check_modules_instantiated")

    @patch('documentcheckertool.document_checker.Document')
    def test_all_checks_run(self, mock_document):
        """Test that all check modules are run during document checking."""
        logger.debug("Starting test_all_checks_run")

        # Setup mock document
        mock_doc = Mock()
        mock_document.return_value = mock_doc
        mock_doc.text = "Test document content"
        logger.debug("Mock document created with test content")

        # Create mock check modules
        mock_modules = {}
        standard_modules = [
            'heading_checks',
            'accessibility_checks',
            'format_checks',
            'structure_checks',
            'terminology_checks',
            'readability_checks'
        ]

        logger.debug("Creating mock modules")
        for module_name in standard_modules:
            logger.debug(f"Creating mock for {module_name}")
            mock_module = Mock()
            mock_module.run_checks.return_value = None
            setattr(self.checker, module_name, mock_module)
            mock_modules[module_name] = mock_module
            logger.debug(f"Mock created for {module_name}")

        # Mock special case modules (different interfaces)
        logger.debug("Creating mock for acronym_checker")
        mock_acronym = Mock()
        mock_acronym.check_text.return_value = DocumentCheckResult(success=True)
        self.checker.acronym_checker = mock_acronym
        logger.debug("Mock created for acronym_checker")

        logger.debug("Creating mock for table_figure_checks")
        mock_table_figure = Mock()
        mock_table_figure.check_text.return_value = DocumentCheckResult(success=True)
        self.checker.table_figure_checks = mock_table_figure
        logger.debug("Mock created for table_figure_checks")

        # Run checks
        logger.debug("Running document checks")
        result = self.checker.run_all_document_checks("test.docx")
        logger.debug(f"Document checks completed with success={result.success}")

        # Verify all standard check modules were called
        logger.debug("Verifying standard check module calls")
        for module_name, mock_module in mock_modules.items():
            logger.debug(f"Verifying {module_name}")
            mock_module.run_checks.assert_called_once_with(
                mock_doc, None, unittest.mock.ANY
            )
            logger.debug(f"{module_name} verification complete")

        # Verify special case modules were called
        logger.debug("Verifying special case module calls")
        mock_acronym.check_text.assert_called_once_with(mock_doc.text)
        mock_table_figure.check_text.assert_called_once_with(mock_doc.text)
        logger.debug("Special case module verification complete")

        logger.debug("Completed test_all_checks_run")

if __name__ == '__main__':
    unittest.main()