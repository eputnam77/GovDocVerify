import gradio as gr
import os
import json
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.terminology_utils import TerminologyManager

# Load document types from config file
config_path = os.path.join(os.path.dirname(__file__), 'documentcheckertool', 'config', 'terminology.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    doc_types = list(config.get('document_types', {}).keys())

# Initialize the document checker
terminology_manager = TerminologyManager()
checker = FAADocumentChecker(terminology_manager)

def check_document(file, doc_type):
    if file is None:
        return "Please upload a document.", ""
    try:
        result = checker.check_document(file.name, doc_type)
        errors = result.errors
        warnings = result.warnings
        return f"Errors: {errors}", f"Warnings: {warnings}"
    except Exception as e:
        return f"Error: {str(e)}", ""

# Create Gradio interface
demo = gr.Interface(
    fn=check_document,
    inputs=[
        gr.File(label="Upload Document"),
        gr.Dropdown(choices=doc_types, label="Document Type")
    ],
    outputs=[
        gr.Textbox(label="Errors"),
        gr.Textbox(label="Warnings")
    ],
    title="Document Checker Tool",
    description="Upload a document and select its type to check for errors and warnings."
)

if __name__ == "__main__":
    demo.launch()