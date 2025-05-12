# python app.py
# python app.py --host 127.0.0.1 --port 7860 --debug
# python app.py --host 127.0.0.1 --port 7861 --debug

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
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
import mimetypes

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

def process_document(file_path: str, doc_type: str) -> str:
    """Process a document and return formatted results."""
    try:
        logger.info(f"Processing document of type: {doc_type}")
        formatter = ResultFormatter(style=FormatStyle.HTML)

        # Initialize the document checker
        terminology_manager = TerminologyManager()
        checker = FAADocumentChecker(terminology_manager)

        # Detect file type using mimetypes and file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        logger.info(f"Detected MIME type: {mime_type}")

        # If DOCX, pass file path directly to checker
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_path.lower().endswith('.docx'):
            logger.info("Processing as DOCX file")
            results = checker.run_all_document_checks(file_path, doc_type)
        else:
            logger.info(f"Reading file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.warning("UTF-8 decode failed, trying with different encoding")
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            logger.info("Running document checks (text file)")
            results = checker.run_all_document_checks(content, doc_type)

        logger.info("Formatting results")
        logger.debug(f"Raw results type: {type(results)}")
        logger.debug(f"Raw results dir: {dir(results)}")

        # Get total issues from the main results object
        total_issues = len(results.issues) if hasattr(results, 'issues') else 0
        logger.info(f"Total issues found: {total_issues}")

        # Start building the HTML output
        html_output = ['<div class="results-container">']
        html_output.append('<h1 style="color: #0056b3; text-align: center;">Document Check Results</h1>')
        html_output.append('<hr style="border: 1px solid #0056b3;">')

        if total_issues == 0:
            html_output.append('<div style="color: #006400; text-align: center; padding: 20px;">✓ All checks passed successfully!</div>')
        else:
            # Group issues by severity
            errors = []
            warnings = []
            info = []

            for issue in results.issues:
                # Handle severity as enum
                severity = issue.get('severity')
                if isinstance(severity, str):
                    severity = severity.lower()
                elif hasattr(severity, 'value'):
                    severity = severity.value.lower()
                else:
                    severity = 'info'  # default to info if severity is not recognized

                message = issue.get('message', '')
                line = issue.get('line_number')
                line_info = f" (Line {line})" if line is not None else ""

                if severity == 'error':
                    errors.append(f"{message}{line_info}")
                elif severity == 'warning':
                    warnings.append(f"{message}{line_info}")
                else:  # info or unknown
                    info.append(f"{message}{line_info}")

            # Add issues to HTML output
            if errors:
                html_output.append("<h3 style='color: #721c24;'>Errors</h3>")
                html_output.append("<ul>")
                for error in errors:
                    html_output.append(f"<li>{error}</li>")
                html_output.append("</ul>")

            if warnings:
                html_output.append("<h3 style='color: #856404;'>Warnings</h3>")
                html_output.append("<ul>")
                for warning in warnings:
                    html_output.append(f"<li>{warning}</li>")
                html_output.append("</ul>")

            if info:
                html_output.append("<h3 style='color: #0c5460;'>Info</h3>")
                html_output.append("<ul>")
                for item in info:
                    html_output.append(f"<li>{item}</li>")
                html_output.append("</ul>")

        html_output.append('</div>')
        logger.info("Document processing completed successfully")
        return '\n'.join(html_output)

    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    except PermissionError:
        error_msg = f"Permission denied: {file_path}"
        logger.error(error_msg)
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"<div style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;'>{error_msg}</div>"

def format_results_to_html(results: Any) -> str:
    """Format results into HTML."""
    html = []

    # Convert DocumentCheckResult to dict if needed
    if hasattr(results, 'to_dict'):
        results = results.to_dict()

    # Group issues by severity
    errors = []
    warnings = []
    info = []

    for issue in results.get('issues', []):
        severity = issue.get('severity', '').lower()
        message = issue.get('message', '')
        line = issue.get('line_number')
        line_info = f" (Line {line})" if line is not None else ""

        if severity == 'error':
            errors.append(f"{message}{line_info}")
        elif severity == 'warning':
            warnings.append(f"{message}{line_info}")
        elif severity == 'info':
            info.append(f"{message}{line_info}")

    if errors:
        html.append("<h3 style='color: red;'>Errors</h3>")
        html.append("<ul>")
        for error in errors:
            html.append(f"<li>{error}</li>")
        html.append("</ul>")

    if warnings:
        html.append("<h3 style='color: orange;'>Warnings</h3>")
        html.append("<ul>")
        for warning in warnings:
            html.append(f"<li>{warning}</li>")
        html.append("</ul>")

    if info:
        html.append("<h3 style='color: blue;'>Info</h3>")
        html.append("<ul>")
        for item in info:
            html.append(f"<li>{item}</li>")
        html.append("</ul>")

    if not (errors or warnings or info):
        html.append("<p>No issues found.</p>")

    return "".join(html)

def create_interface() -> gr.Blocks:
    """Create the Gradio interface."""
    try:
        logger.info("Creating Gradio interface")
        with gr.Blocks(
            title="Document Checker Tool",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="blue",
                neutral_hue="slate",
                font=["Inter", "sans-serif"]
            )
        ) as demo:
            gr.Markdown("""
            # Document Checker Tool
            Upload a document to check for compliance and formatting issues.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="Upload Document",
                        file_types=[".docx", ".txt"],
                        type="filepath"
                    )
                    doc_type = gr.Dropdown(
                        choices=doc_types,
                        label="Document Type",
                        value=doc_types[0],
                        info="Select the type of document you're checking"
                    )
                    submit_btn = gr.Button(
                        "Check Document",
                        variant="primary"
                    )

                with gr.Column(scale=2):
                    output = gr.HTML(
                        label="Results",
                        elem_classes=["results-container"]
                    )

            # Add custom CSS
            gr.HTML("""
            <style>
            .results-container {
                padding: 20px;
                border-radius: 8px;
                background-color: #ffffff;
                max-height: 600px;
                overflow-y: auto;
                border: 1px solid #e5e7eb;
            }
            .results-container h1 {
                color: #0056b3;
                text-align: center;
                margin-bottom: 1em;
            }
            .results-container h2 {
                color: #0056b3;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }
            .results-container h3 {
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }
            .results-container ul {
                margin: 0;
                padding-left: 1.5em;
                list-style-type: none;
            }
            .results-container li {
                margin: 0.5em 0;
                line-height: 1.5;
            }
            .error-section h3 {
                color: #721c24;
            }
            .warning-section h3 {
                color: #856404;
            }
            .info-section h3 {
                color: #0c5460;
            }
            </style>
            """)

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