import gradio as gr
from document_checker import FAADocumentChecker
from utils.formatting import format_results_to_html
from utils.security import validate_file, SecurityError
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

def create_interface():
    """Create the Gradio interface."""
    checker = FAADocumentChecker()
    
    with gr.Blocks() as interface:
        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="Upload Document",
                    file_types=[".docx", ".doc"],
                    file_count="single"
                )
                doc_type = gr.Dropdown(
                    choices=[
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
                        "Other"
                    ],
                    label="Document Type"
                )
                check_btn = gr.Button("Check Document")
            
            with gr.Column():
                results = gr.HTML(label="Results")
        
        def process_and_format(file_obj, doc_type_value):
            try:
                if not file_obj:
                    return "Please upload a document file."
                
                # Create a temporary file for validation
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[1]) as temp_file:
                    temp_file.write(file_obj.read())
                    temp_file_path = temp_file.name
                
                try:
                    # Validate the file
                    validate_file(temp_file_path)
                    
                    # Process the document
                    results_data = checker.run_all_document_checks(file_obj, doc_type_value)
                    html_results = format_results_to_html(results_data)
                    return html_results
                    
                except SecurityError as e:
                    logger.error(f"Security validation failed: {str(e)}")
                    return f"Security validation failed: {str(e)}"
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                return f"Error processing document: {str(e)}"
        
        check_btn.click(
            process_and_format,
            inputs=[file_input, doc_type],
            outputs=results
        )
    
    return interface 