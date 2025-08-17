# pytest -v tests/test_format_checks.py --log-cli-level=DEBUG

import unittest
from typing import List, TypedDict

from govdocverify.checks.format_checks import FormattingChecker


class _TestCase(TypedDict):
    input: List[str]
    should_flag: bool
    description: str


class TestFormattingChecker(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = FormattingChecker()

    def test_section_symbol_usage(self) -> None:
        test_cases: List[_TestCase] = [
            # Test case 1: Should flag multiple symbols without "or"
            {
                "input": ["Also check §§ 33.87"],
                "should_flag": True,
                "description": "Multiple symbols without 'or' should be flagged",
            },
            # Test case 2: Should not flag single symbol with "or"
            {
                "input": ["Don't forget about § 33.87 or 33.91"],
                "should_flag": False,
                "description": "Single symbol with 'or' should be allowed",
            },
            # Test case 3: Should flag multiple symbols with "or"
            {
                "input": ["Lest I forget about §§ 33.87 or 33.91"],
                "should_flag": True,
                "description": "Multiple symbols with 'or' should be flagged",
            },
            # Test case 4: Should skip U.S.C. citations
            {
                "input": ["See 42 U.S.C. §§ 1981-1983"],
                "should_flag": False,
                "description": "U.S.C. citations should be skipped",
            },
            # Test case 5: Should skip 14 CFR citations
            {
                "input": ["See 14 CFR § 33.87"],
                "should_flag": False,
                "description": "14 CFR citations should be skipped",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            with self.subTest(test_case=test_case["description"]):
                result = self.checker.check_section_symbol_usage(test_case["input"])
                self.assertEqual(
                    len(result.issues) > 0,
                    test_case["should_flag"],
                    f"Test case {i} failed: {test_case['description']}",
                )


if __name__ == "__main__":
    unittest.main()
