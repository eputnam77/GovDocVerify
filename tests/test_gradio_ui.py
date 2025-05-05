# python -m pytest tests/test_gradio_ui.py -v

import unittest
import tempfile
import os
import gradio as gr
from documentcheckertool.interfaces.gradio_ui import create_interface
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.constants import DOCUMENT_TYPES

class TestGradioUI(unittest.TestCase):
    """Test suite for Gradio UI functionality."""
    
    def setUp(self):
        self.interface = create_interface()
        self.checker = FAADocumentChecker()
    
    def test_interface_creation(self):
        """Test that the interface is created with correct components."""
        self.assertIsNotNone(self.interface)
        # Check that all expected components are present
        components = [c for c in self.interface.blocks]
        self.assertTrue(any(isinstance(c, gr.File) for c in components))
        self.assertTrue(any(isinstance(c, gr.Dropdown) for c in components))
        self.assertTrue(any(isinstance(c, gr.Button) for c in components))
        self.assertTrue(any(isinstance(c, gr.HTML) for c in components))
        
        # Check document type dropdown choices
        doc_type_dropdown = next(c for c in components if isinstance(c, gr.Dropdown) and c.label == "Document Type")
        self.assertEqual(set(doc_type_dropdown.choices), set(DOCUMENT_TYPES))
    
    def test_document_processing(self):
        """Test document processing functionality."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test document content")
            temp_path = f.name
        
        try:
            # Test processing with valid inputs for each document type
            for doc_type in DOCUMENT_TYPES:
                result = self.interface.fns[0](temp_path, doc_type)
                self.assertIsNotNone(result)
                self.assertIn("results", result.lower())
            
            # Test error handling
            result = self.interface.fns[0]("nonexistent.txt", "Order")
            self.assertIn("error", result.lower())
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()