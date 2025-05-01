import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch
from app import process_document, main, DOCUMENT_TYPES

class TestCLI(unittest.TestCase):
    """Test suite for CLI functionality."""
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write("Test document content")
        self.temp_file.close()
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_process_document(self):
        """Test document processing function."""
        # Test with valid inputs for each document type
        for doc_type in DOCUMENT_TYPES:
            result = process_document(self.temp_file.name, doc_type)
            self.assertIsNotNone(result)
            self.assertIn("results", result.lower())
        
        # Test with invalid file
        result = process_document("nonexistent.txt", "Order")
        self.assertIn("error", result.lower())
    
    def test_cli_arguments(self):
        """Test CLI argument parsing."""
        # Test missing required arguments
        with patch('sys.argv', ['app.py', '--cli']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit):
                    main()
                self.assertIn("--file and --type are required", fake_out.getvalue())
        
        # Test valid command for each document type
        for doc_type in DOCUMENT_TYPES:
            args = ['app.py', '--cli', '--file', self.temp_file.name, '--type', doc_type]
            with patch('sys.argv', args):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    self.assertIn("results", fake_out.getvalue().lower())
    
    def test_document_type_validation(self):
        """Test document type validation."""
        # Test invalid document type
        with patch('sys.argv', ['app.py', '--cli', '--file', self.temp_file.name, '--type', 'Invalid']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit):
                    main()
                self.assertIn("invalid choice", fake_out.getvalue().lower())

if __name__ == '__main__':
    unittest.main() 