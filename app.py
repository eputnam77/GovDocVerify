import gradio as gr
import argparse
import sys
from pathlib import Path
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.constants import DOCUMENT_TYPES
import os
import logging
import traceback
from typing import Dict, Any, Optional
import json
from documentcheckertool.utils.terminology_utils import TerminologyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('document_checker.log')
    ]
)
logger = logging.getLogger(__name__)

# Load document types from config file
config_path = os.path.join(os.path.dirname(__file__), 'documentcheckertool', 'config', 'terminology.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    doc_types = list(config.get('document_types', {}).keys())

# Initialize the document checker
terminology_manager = TerminologyManager()
checker = FAADocumentChecker(terminology_manager)

def process_document(file_path: str, doc_type: str) -> str:
    """Process a document and return formatted results."""
    try:
        logger.info(f"Initializing document checker for type: {doc_type}")
        checker = FAADocumentChecker()

        logger.info(f"Reading file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning("UTF-8 decode failed, trying with different encoding")
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        logger.info("Running document checks")
        results = checker.run_all_document_checks(content, doc_type)

        logger.info("Formatting results")
        formatted_results = format_results_to_html(results)

        logger.info("Document processing completed successfully")
        return formatted_results

    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: red;'>{error_msg}</div>"
    except PermissionError:
        error_msg = f"Permission denied: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: red;'>{error_msg}</div>"
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"<div style='color: red;'>{error_msg}</div>"

def format_results_to_html(results: Dict[str, Any]) -> str:
    """Format results into HTML."""
    html = []
    if results.get('errors'):
        html.append("<h3>Errors</h3>")
        html.append("<ul>")
        for error in results['errors']:
            html.append(f"<li>{error}</li>")
        html.append("</ul>")
    if results.get('warnings'):
        html.append("<h3>Warnings</h3>")
        html.append("<ul>")
        for warning in results['warnings']:
            html.append(f"<li>{warning}</li>")
        html.append("</ul>")
    return "".join(html)

def create_interface() -> gr.Blocks:
    """Create the Gradio interface."""
    try:
        logger.info("Creating Gradio interface")
        with gr.Blocks(title="Document Checker Tool") as demo:
            gr.Markdown("# Document Checker Tool")
            gr.Markdown("Upload a document to check for compliance and formatting issues.")

            with gr.Row():
                with gr.Column():
                    file_input = gr.File(label="Upload Document")
                    doc_type = gr.Dropdown(
                        choices=doc_types,
                        label="Document Type",
                        value=doc_types[0]
                    )
                    submit_btn = gr.Button("Check Document")

                with gr.Column():
                    output = gr.HTML(label="Results")

            submit_btn.click(
                fn=process_document,
                inputs=[file_input, doc_type],
                outputs=output
            )

        logger.info("Gradio interface created successfully")
        return demo
    except Exception as e:
        logger.error(f"Error creating interface: {str(e)}\n{traceback.format_exc()}")
        raise

def main() -> int:
    """Main entry point for the application."""
    try:
        logger.info("Starting Document Checker Tool")
        parser = argparse.ArgumentParser(description='FAA Document Checker')
        parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
        parser.add_argument('--file', type=str, help='Path to document file')
        parser.add_argument('--type', type=str, choices=doc_types,
                          help='Document type')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host')
        parser.add_argument('--port', type=int, default=7860, help='Server port')

        args = parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

        if args.cli:
            if not args.file or not args.type:
                logger.error("Missing required arguments in CLI mode")
                print("Error: --file and --type are required in CLI mode")
                return 1

            try:
                results = process_document(args.file, args.type)
                print(results)
                return 0
            except Exception as e:
                logger.error(f"Error in CLI mode: {str(e)}")
                return 1
        else:
            logger.info("Starting Gradio interface")
            interface = create_interface()

            # Determine if we're running in Hugging Face Spaces
            is_spaces = os.environ.get("SPACE_ID") is not None
            logger.info(f"Running in Hugging Face Spaces: {is_spaces}")

            interface.launch(
                debug=args.debug,
                server_name="0.0.0.0" if is_spaces else args.host,
                server_port=args.port,
                show_error=True,
                share=not is_spaces
            )
            return 0

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())