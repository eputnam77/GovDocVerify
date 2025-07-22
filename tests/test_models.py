# pytest -v tests/test_models.py --log-cli-level=DEBUG

import logging
import re
import statistics
import sys
import time
import unittest

from govdocverify.models import DocumentType, DocumentTypeError

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDocumentType(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        logger.debug("Setting up test fixtures")
        self.all_doc_types = [
            "Advisory Circular",
            "Airworthiness Criteria",
            "Deviation Memo",
            "Exemption",
            "Federal Register Notice",
            "Order",
            "Policy Statement",
            "Rule",
            "Special Condition",
            "Technical Standard Order",
            "Other",
        ]
        logger.debug(f"Initialized with {len(self.all_doc_types)} document types")
        logger.debug(f"Memory usage at setup: {sys.getsizeof(self.all_doc_types)} bytes")

    def test_from_string_valid(self):
        """Test converting valid strings to DocumentType enum."""
        logger.debug("Testing valid string conversions")
        test_cases = [
            ("Advisory Circular", DocumentType.ADVISORY_CIRCULAR),
            ("Federal Register Notice", DocumentType.FEDERAL_REGISTER_NOTICE),
            ("Order", DocumentType.ORDER),
            ("Airworthiness Criteria", DocumentType.AIRWORTHINESS_CRITERIA),
            ("Deviation Memo", DocumentType.DEVIATION_MEMO),
            ("Exemption", DocumentType.EXEMPTION),
            ("Policy Statement", DocumentType.POLICY_STATEMENT),
            ("Rule", DocumentType.RULE),
            ("Special Condition", DocumentType.SPECIAL_CONDITION),
            ("Technical Standard Order", DocumentType.TECHNICAL_STANDARD_ORDER),
            ("Other", DocumentType.OTHER),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                logger.debug(f"Testing conversion of '{input_str}'")
                result = DocumentType.from_string(input_str)
                self.assertEqual(result, expected)
                logger.debug(f"Successfully converted '{input_str}' to {result}")

    def test_from_string_invalid(self):
        """Test converting invalid strings raises DocumentTypeError."""
        logger.debug("Testing invalid string conversions")
        invalid_types = [
            "Invalid Type",
            "Unknown",
            "Test",
            "Advisory",  # Partial match
            "Circular",  # Partial match
            "Advisory-Circular",  # Wrong format
            "Advisory_Circular",  # Wrong format
            "",  # Empty string
            " ",  # Whitespace
            None,  # None value
            123,  # Non-string value
            ["Advisory Circular"],  # List
            {"type": "Advisory Circular"},  # Dict
        ]

        for invalid_type in invalid_types:
            with self.subTest(invalid_type=invalid_type):
                logger.debug(f"Testing invalid type: '{invalid_type}'")
                with self.assertRaises(DocumentTypeError) as context:
                    DocumentType.from_string(invalid_type)
                logger.debug(
                    f"Successfully caught DocumentTypeError for '{invalid_type}': "
                    f"{str(context.exception)}"
                )

    def test_values(self):
        """Test that values() returns all document type strings."""
        logger.debug("Testing values() method")
        values = DocumentType.values()

        # Test basic properties
        self.assertIsInstance(values, list)
        self.assertEqual(len(values), len(DocumentType))
        logger.debug(f"Found {len(values)} document types")

        # Check that all values are strings
        for value in values:
            self.assertIsInstance(value, str)
            logger.debug(f"Verified string type for: {value}")

        # Check that all enum members are represented
        enum_values = {member.value for member in DocumentType}
        self.assertEqual(set(values), enum_values)
        logger.debug(f"All enum values are represented in values(): {enum_values}")

        # Verify against expected list
        self.assertEqual(set(values), set(self.all_doc_types))
        logger.debug("Values match expected document types")

    def test_enum_members(self):
        """Test individual enum members and their properties."""
        logger.debug("Testing enum members")
        for member in DocumentType:
            logger.debug(f"Testing enum member: {member}")
            logger.debug(f"  - Name: {member.name}")
            logger.debug(f"  - Value: {member.value}")
            logger.debug(f"  - Hash: {hash(member)}")
            logger.debug(f"  - Memory address: {id(member)}")

            # Test member properties
            self.assertIsInstance(member.name, str)
            self.assertIsInstance(member.value, str)
            self.assertTrue(member.name.isupper())
            self.assertTrue(member.value.istitle())

            # Test string representation
            str_rep = str(member)
            logger.debug(f"  - String representation: '{str_rep}'")
            self.assertEqual(str_rep, member.value)
            logger.debug(
                f"  - Verified string representation matches value: '{str_rep}' == '{member.value}'"
            )

    def test_case_sensitivity(self):
        """Test case sensitivity in string conversion."""
        logger.debug("Testing case sensitivity")
        test_cases = [
            ("advisory circular", DocumentType.ADVISORY_CIRCULAR),
            ("ADVISORY CIRCULAR", DocumentType.ADVISORY_CIRCULAR),
            ("Advisory Circular", DocumentType.ADVISORY_CIRCULAR),
            ("Advisory circular", DocumentType.ADVISORY_CIRCULAR),
            ("aDvIsOrY cIrCuLaR", DocumentType.ADVISORY_CIRCULAR),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                logger.debug(f"Testing case sensitivity for: '{input_str}'")
                result = DocumentType.from_string(input_str)
                self.assertEqual(result, expected)
                logger.debug(f"Successfully handled case variation: '{input_str}' -> '{result}'")

    def test_whitespace_handling(self):
        """Test handling of whitespace in string conversion."""
        logger.debug("Testing whitespace handling")
        test_cases = [
            (" Advisory Circular ", DocumentType.ADVISORY_CIRCULAR),
            ("Advisory  Circular", DocumentType.ADVISORY_CIRCULAR),
            ("\tAdvisory Circular\t", DocumentType.ADVISORY_CIRCULAR),
            ("Advisory\nCircular", DocumentType.ADVISORY_CIRCULAR),
            ("  Advisory   Circular  ", DocumentType.ADVISORY_CIRCULAR),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                logger.debug(f"Testing whitespace handling for: '{input_str}'")
                logger.debug(f"Input length: {len(input_str)} chars")
                logger.debug(f"Whitespace chars: {[c for c in input_str if c.isspace()]}")

                stripped = input_str.strip()
                logger.debug(f"After strip: '{stripped}' (length: {len(stripped)})")

                normalized = re.sub(r"\s+", " ", stripped)
                logger.debug(
                    f"After regex normalization: '{normalized}' (length: {len(normalized)})"
                )

                title_cased = normalized.title()
                logger.debug(f"After title case: '{title_cased}' (length: {len(title_cased)})")

                result = DocumentType.from_string(input_str)
                self.assertEqual(result, expected)
                logger.debug(
                    f"Successfully handled whitespace variation: '{input_str}' -> '{result}'"
                )

    def test_edge_cases(self):
        """Test edge cases and special inputs."""
        logger.debug("Testing edge cases")

        # Test with extra spaces and mixed case
        test_cases = [
            ("  advisory  circular  ", DocumentType.ADVISORY_CIRCULAR),
            ("\nAdvisory\nCircular\n", DocumentType.ADVISORY_CIRCULAR),
            ("\tAdvisory\tCircular\t", DocumentType.ADVISORY_CIRCULAR),
            ("Advisory\t\nCircular", DocumentType.ADVISORY_CIRCULAR),
            ("  Advisory   Circular  ", DocumentType.ADVISORY_CIRCULAR),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                logger.debug(f"Testing edge case: '{input_str}'")
                normalized = re.sub(r"\s+", " ", input_str.strip())
                logger.debug(f"Normalized input: '{normalized}'")
                result = DocumentType.from_string(input_str)
                self.assertEqual(result, expected)
                logger.debug(f"Successfully handled edge case: '{input_str}' -> '{result}'")

    def test_string_normalization(self):
        """Test string normalization in detail."""
        logger.debug("Testing string normalization")
        test_cases = [
            ("  advisory  circular  ", "Advisory Circular"),
            ("\nAdvisory\nCircular\n", "Advisory Circular"),
            ("\tAdvisory\tCircular\t", "Advisory Circular"),
            ("Advisory\t\nCircular", "Advisory Circular"),
            ("  Advisory   Circular  ", "Advisory Circular"),
            ("advisory  circular", "Advisory Circular"),
            ("ADVISORY  CIRCULAR", "Advisory Circular"),
            ("Advisory  Circular", "Advisory Circular"),
        ]

        for input_str, expected_normalized in test_cases:
            with self.subTest(input_str=input_str):
                logger.debug(f"Testing normalization for: '{input_str}'")
                normalized = re.sub(r"\s+", " ", input_str.strip()).title()
                logger.debug(f"Normalized to: '{normalized}'")
                self.assertEqual(normalized, expected_normalized)
                logger.debug(f"Successfully normalized: '{input_str}' -> '{normalized}'")

    def test_performance(self):
        """Test performance with large numbers of document type conversions."""
        logger.debug("Starting performance test")

        # Test cases with various input formats
        test_cases = [
            "Advisory Circular",
            "  Advisory  Circular  ",
            "ADVISORY CIRCULAR",
            "advisory circular",
            "Advisory\nCircular",
        ]

        iterations = 1000
        logger.debug(f"Running {iterations} iterations for each test case")

        # Track timing for each iteration
        all_times = []

        start_time = time.time()
        start_memory = sys.getsizeof(test_cases)

        for test_case in test_cases:
            case_times = []
            case_start = time.time()

            for i in range(iterations):
                iter_start = time.time()
                result = DocumentType.from_string(test_case)
                iter_end = time.time()
                case_times.append(iter_end - iter_start)
                self.assertIsInstance(result, DocumentType)

            case_end = time.time()
            case_duration = case_end - case_start
            all_times.extend(case_times)

            logger.debug(f"Test case '{test_case}':")
            logger.debug(f"  - Total time: {case_duration:.3f} seconds")
            logger.debug(f"  - Average time: {statistics.mean(case_times):.6f} seconds")
            logger.debug(f"  - Min time: {min(case_times):.6f} seconds")
            logger.debug(f"  - Max time: {max(case_times):.6f} seconds")
            logger.debug(f"  - Std dev: {statistics.stdev(case_times):.6f} seconds")

        end_time = time.time()
        end_memory = sys.getsizeof(test_cases)
        total_time = end_time - start_time

        logger.debug("Performance Summary:")
        logger.debug(f"  - Total test time: {total_time:.3f} seconds")
        logger.debug(f"  - Average time per conversion: {statistics.mean(all_times):.6f} seconds")
        logger.debug(f"  - Memory usage change: {end_memory - start_memory} bytes")
        logger.debug(f"  - Total iterations: {iterations * len(test_cases)}")

        # Assert that the total time is reasonable (under 2 seconds)
        self.assertLess(
            total_time,
            2.0,
            f"Performance test took {total_time:.3f} seconds, which exceeds the 2 second threshold",
        )

        # Assert that average time per conversion is reasonable (under 1ms)
        avg_time = statistics.mean(all_times)
        self.assertLess(
            avg_time,
            0.001,
            f"Average time per conversion ({avg_time:.6f} seconds) exceeds 1ms threshold",
        )
