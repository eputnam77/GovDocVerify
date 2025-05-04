# python -m pytest tests/test_acronyms.py -v

import pytest
from pathlib import Path

from documentcheckertool.checks.terminology_checks import check_acronyms
from tests.test_base import TestBase

class TestAcronyms(TestBase):
    """Test cases for acronym checking functionality."""
    
    def test_valid_acronym_definition(self):
        """Test that valid acronym definitions pass."""
        content = """
        The Federal Aviation Administration (FAA) is responsible for aviation safety.
        """
        file_path = self.create_test_file(content, "test_acronyms.txt")
        result = check_acronyms(file_path)
        self.assert_no_issues(result)
        
    def test_missing_acronym_definition(self):
        """Test that missing acronym definitions are caught."""
        content = """
        The FAA is responsible for aviation safety.
        """
        file_path = self.create_test_file(content, "test_acronyms.txt")
        result = check_acronyms(file_path)
        self.assert_check_result(
            result,
            expected_issues=[{
                "message": "Acronym 'FAA' used without definition",
                "line_number": 2,
                "severity": "warning"
            }]
        )
        
    def test_multiple_acronym_definitions(self):
        """Test that multiple acronym definitions are caught."""
        content = "The FAA (Federal Aviation Administration) is responsible for aviation safety.\nThe FAA (Federal Aviation Administration) regulates air traffic."
        file_path = self.create_test_file(content, "test_acronyms.txt")
        
        # Debug: Print file contents
        with open(file_path, 'r') as f:
            print("\nFile contents:")
            for i, line in enumerate(f.readlines(), 1):
                print(f"Line {i}: {line.strip()}")
        
        result = check_acronyms(file_path)
        self.assert_check_result(
            result,
            expected_issues=[{
                "message": "Acronym 'FAA' defined multiple times",
                "line_number": 2,
                "severity": "warning"
            }]
        )

if __name__ == '__main__':
    pytest.main() 