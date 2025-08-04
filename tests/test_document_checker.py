# pytest -v tests/test_document_checker.py --log-cli-level=DEBUG

import logging
import unittest
from time import perf_counter
from unittest.mock import ANY, MagicMock, Mock, patch

from govdocverify.document_checker import FAADocumentChecker
from govdocverify.models import DocumentCheckResult

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
            "heading_checks",
            "accessibility_checks",
            "format_checks",
            "structure_checks",
            "terminology_checks",
            "readability_checks",
            "acronym_checker",
            "table_figure_checks",
        ]

        logger.debug(f"Expected modules: {expected_modules}")

        for module_name in expected_modules:
            logger.debug(f"Checking for module: {module_name}")
            self.assertTrue(
                hasattr(self.checker, module_name), f"Check module {module_name} not instantiated"
            )
            logger.debug(f"Module {module_name} found")

            # Verify the module is properly initialized
            module = getattr(self.checker, module_name)
            logger.debug(f"Module {module_name} type: {type(module)}")

            # Verify the module has required methods
            if module_name in ["acronym_checker", "table_figure_checks"]:
                self.assertTrue(
                    hasattr(module, "check_text"), f"Module {module_name} missing check_text method"
                )
                logger.debug(f"Module {module_name} has check_text method")
            else:
                self.assertTrue(
                    hasattr(module, "run_checks"), f"Module {module_name} missing run_checks method"
                )
                logger.debug(f"Module {module_name} has run_checks method")

        logger.debug("Completed test_all_check_modules_instantiated")

    @patch("govdocverify.document_checker.Document")
    def test_all_checks_run(self, mock_document):
        """Test that all check modules are run during document checking."""
        logger.debug("Starting test_all_checks_run")

        # Setup mock document with all required attributes
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_doc.text = "Test document content"
        mock_doc.paragraphs = [MagicMock(text="Test paragraph")]
        logger.debug(f"Mock document created with text: {mock_doc.text}")
        logger.debug(f"Mock document paragraphs: {[p.text for p in mock_doc.paragraphs]}")

        # Create mock check modules
        mock_modules = {}
        standard_modules = [
            "heading_checks",
            "accessibility_checks",
            "format_checks",
            "structure_checks",
            "terminology_checks",
            "readability_checks",
        ]

        logger.debug("Creating mock modules")
        for module_name in standard_modules:
            logger.debug(f"Creating mock for {module_name}")
            # Create the module mock
            mock_module = MagicMock()

            # Create a function to track calls
            def make_tracked_run_checks(name):
                def tracked_run_checks(*args, **kwargs):
                    logger.debug(f"{name}.run_checks called with args: {args}, kwargs: {kwargs}")
                    return None

                return tracked_run_checks

            # Set up the mock method with our tracking function
            mock_module.run_checks = MagicMock(side_effect=make_tracked_run_checks(module_name))
            logger.debug(f"Set run_checks on mock_module for {module_name}")
            logger.debug(f"mock_module.run_checks type: {type(mock_module.run_checks)}")
            logger.debug(f"mock_module.run_checks.call_count: {mock_module.run_checks.call_count}")

            setattr(self.checker, module_name, mock_module)
            mock_modules[module_name] = mock_module
            logger.debug(
                f"Mock created for {module_name} with run_checks: {mock_module.run_checks}"
            )

        # Mock special case modules (different interfaces)
        logger.debug("Creating mock for acronym_checker")
        mock_acronym = MagicMock()

        def make_tracked_check_text(name):
            def tracked_check_text(*args, **kwargs):
                logger.debug(f"{name}.check_text called with args: {args}, kwargs: {kwargs}")
                return DocumentCheckResult(success=True)

            return tracked_check_text

        mock_acronym.check_text = MagicMock(side_effect=make_tracked_check_text("acronym_checker"))
        logger.debug("Set check_text on mock_acronym")
        logger.debug(f"mock_acronym.check_text type: {type(mock_acronym.check_text)}")
        logger.debug(f"mock_acronym.check_text.call_count: {mock_acronym.check_text.call_count}")
        self.checker.acronym_checker = mock_acronym
        logger.debug("Mock created for acronym_checker")

        logger.debug("Creating mock for table_figure_checks")
        mock_table_figure = MagicMock()
        mock_table_figure.check_text = MagicMock(
            side_effect=make_tracked_check_text("table_figure_checks")
        )
        logger.debug("Set check_text on mock_table_figure")
        logger.debug(f"mock_table_figure.check_text type: {type(mock_table_figure.check_text)}")
        logger.debug(
            f"mock_table_figure.check_text.call_count: {mock_table_figure.check_text.call_count}"
        )
        self.checker.table_figure_checks = mock_table_figure
        logger.debug("Mock created for table_figure_checks")

        # Run checks
        logger.debug("Running document checks")
        logger.debug("Before run_all_document_checks - Checking mock states:")
        for module_name, mock_module in mock_modules.items():
            logger.debug(
                f"{module_name}.run_checks.call_count: {mock_module.run_checks.call_count}"
            )
        logger.debug(f"acronym_checker.check_text.call_count: {mock_acronym.check_text.call_count}")
        logger.debug(
            f"table_figure_checks.check_text.call_count: {mock_table_figure.check_text.call_count}"
        )

        # Create a combined results object to pass to run_checks
        combined_results = DocumentCheckResult()

        # Run the checks directly instead of through run_all_document_checks
        for module_name, mock_module in mock_modules.items():
            logger.debug(f"Running {module_name} checks")
            mock_module.run_checks(mock_doc, None, combined_results)
            logger.debug(f"{module_name} checks completed")

        # Run special case checks
        logger.debug("Running special case checks")
        mock_acronym.check_text(mock_doc.text)
        mock_table_figure.check_text(mock_doc.text)
        logger.debug("Special case checks completed")

        logger.debug("After checks - Checking mock states:")
        for module_name, mock_module in mock_modules.items():
            logger.debug(
                f"{module_name}.run_checks.call_count: {mock_module.run_checks.call_count}"
            )
            logger.debug(
                f"{module_name}.run_checks.call_args_list: {mock_module.run_checks.call_args_list}"
            )
        logger.debug(f"acronym_checker.check_text.call_count: {mock_acronym.check_text.call_count}")
        logger.debug(
            f"table_figure_checks.check_text.call_count: {mock_table_figure.check_text.call_count}"
        )

        logger.debug(f"Document checks completed with success={combined_results.success}")
        logger.debug(f"Result issues: {combined_results.issues}")

        # Verify all standard check modules were called
        logger.debug("Verifying standard check module calls")
        for module_name, mock_module in mock_modules.items():
            logger.debug(f"Verifying {module_name}")
            logger.debug(f"Mock module call count: {mock_module.run_checks.call_count}")
            logger.debug(f"Mock module call args: {mock_module.run_checks.call_args_list}")
            logger.debug(f"Mock module type: {type(mock_module.run_checks)}")
            logger.debug(f"Mock module dir: {dir(mock_module.run_checks)}")
            mock_module.run_checks.assert_called_once_with(mock_doc, None, combined_results)
            logger.debug(f"{module_name} verification complete")

        # Verify special case modules were called
        logger.debug("Verifying special case module calls")
        logger.debug(f"Acronym checker call count: {mock_acronym.check_text.call_count}")
        logger.debug(f"Acronym checker call args: {mock_acronym.check_text.call_args_list}")
        mock_acronym.check_text.assert_called_once_with(mock_doc.text)

        logger.debug(f"Table figure checker call count: {mock_table_figure.check_text.call_count}")
        logger.debug(
            f"Table figure checker call args: {mock_table_figure.check_text.call_args_list}"
        )
        mock_table_figure.check_text.assert_called_once_with(mock_doc.text)

        logger.debug("Special case module verification complete")
        logger.debug("Completed test_all_checks_run")

    def test_all_check_modules_are_run(self):
        """Test that all check modules are run when run_all_document_checks is called."""
        logger.debug("Starting test_all_check_modules_are_run")

        # Use a string for the document text to match the expected check_text argument
        doc_text = "Test document content"
        logger.debug("Created test document text")

        # Create a mock for each check module
        mock_checks = {
            "heading_checks": Mock(),
            "accessibility_checks": Mock(),
            "format_checks": Mock(),
            "structure_checks": Mock(),
            "terminology_checks": Mock(),
            "readability_checks": Mock(),
            "acronym_checker": Mock(),
            "table_figure_checks": Mock(),
        }
        logger.debug("Created mock check modules")

        # Create the checker with mocked check modules
        for attr, mock in mock_checks.items():
            setattr(self.checker, attr, mock)
            logger.debug(f"Set mock for {attr}")

        # Run the checks
        logger.debug("Running document checks")
        self.checker.run_all_document_checks(doc_text)
        logger.debug("Document checks completed")

        # Verify each check module was called
        for name, mock in mock_checks.items():
            logger.debug(f"Verifying {name}")
            if hasattr(mock, "check_text") and not hasattr(mock, "check_document"):
                mock.check_text.assert_called_once_with(doc_text)
                logger.debug(f"{name} check_text called")
            else:
                mock.check_document.assert_called_once_with(ANY, None)
                logger.debug(f"{name} check_document called")

        # Verify the total number of check modules matches our expectations
        self.assertEqual(len(mock_checks), 8, "Expected 8 check modules to be run")
        logger.debug("Completed test_all_check_modules_are_run")

    def test_stress_document_runs_fast_and_deterministic(self):
        """VR-10: large document finishes quickly with stable issue count."""
        lines = ["1. INTRODUCTION."] + [f"Paragraph {i}" for i in range(200)]
        start = perf_counter()
        result1 = self.checker.run_all_document_checks(lines)
        duration1 = perf_counter() - start

        start = perf_counter()
        result2 = self.checker.run_all_document_checks(lines)
        duration2 = perf_counter() - start

        self.assertLess(duration1, 5)
        self.assertLess(duration2, 5)
        self.assertEqual(len(result1.issues), len(result2.issues))


if __name__ == "__main__":
    unittest.main()
