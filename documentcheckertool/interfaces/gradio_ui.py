import gradio as gr
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import ResultFormatter
from documentcheckertool.utils.security import validate_file, SecurityError
from documentcheckertool.models import DocumentCheckResult, Severity
from documentcheckertool.constants import DOCUMENT_TYPES
import logging
import tempfile
import os
import re
import io
import traceback
import pkg_resources
from pprint import pformat
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)
GRADIO_VERSION = pkg_resources.get_distribution('gradio').version

def create_interface():
    """Create and configure the Gradio interface."""

    # Base CSS styles for the entire interface
    custom_css = """
    #document-checker-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        font-family: system-ui, -apple-system, sans-serif;
    }

    /* Enhanced file upload styling */
    .upload-box {
        border: 2px dashed #e5e7eb !important;
        border-radius: 8px !important;
        background: #f8fafc !important;
        transition: all 0.3s ease !important;
        min-height: 150px !important;
        position: relative !important;
    }

    .upload-box:hover {
        border-color: #2563eb !important;
        background: #eff6ff !important;
    }

    /* Fix for file upload container */
    .file-upload {
        padding: 20px !important;
        border: none !important;
        background: transparent !important;
        height: 100% !important;
    }

    .file-upload > div {
        height: 100% !important;
        border: none !important;
        background: transparent !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Additional upload styling */
    .file-upload label span {
        font-size: 1rem !important;
        color: #4b5563 !important;
    }

    .file-upload .upload-text {
        text-align: center !important;
        width: 100% !important;
    }

    .gr-form {
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .gr-button-primary {
        background: #2563eb !important;
        border: none !important;
        color: white !important;
    }

    .gr-button-primary:hover {
        background: #1d4ed8 !important;
    }

    .gr-form > div {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }

    .gr-box {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: white;
    }

    .gr-padded {
        padding: 15px;
    }

    .markdown-body {
        padding: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    """

    template_types = ["Short AC template AC", "Long AC template AC"]

    def get_readme_content():
        readme_path = "README.md"
        try:
            with open(readme_path, "r", encoding="utf-8") as file:
                readme_content = file.read()
            return readme_content
        except Exception as e:
            logging.error(f"Error reading README.md: {str(e)}")
            return "Error loading help content."

    with gr.Blocks(css=custom_css, theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="blue",
        neutral_hue="slate",
        spacing_size="sm",
        radius_size="lg",
        font=["system-ui", "sans-serif"]
    )) as demo:
        with gr.Row(elem_id="document-checker-container"):
            with gr.Column():
                with gr.Tabs():
                    with gr.Tab("Document Checker"):
                        gr.Markdown(
                            """
                            # 📑 FAA Document Checker Tool
                            This tool performs multiple **validation checks** on Word documents to ensure compliance with U.S. federal documentation standards. See the About tab for more information.
                            ## How to Use
                            1. Upload your Word document (`.docx` format).
                            2. Select the document type.
                            3. Click **Check Document**.
                            > **Note:** Please ensure your document is clean (no track changes or comments). If your document contains track changes and comments, you might get several false positives.
                            """,
                            elem_classes="markdown-body"
                        )

                        with gr.Group(elem_classes="gr-form"):
                            with gr.Row():
                                with gr.Column(scale=1):
                                    file_input = gr.File(
                                        label="📎 Upload Word Document (.docx)",
                                        file_types=[".docx"],
                                        type="binary",
                                        elem_classes="file-upload upload-box",
                                        interactive=True
                                    )

                                    doc_type = gr.Dropdown(
                                        choices=DOCUMENT_TYPES,
                                        label="📋 Document Type",
                                        value="Advisory Circular",
                                        info="Select the type of document you're checking",
                                        elem_classes="gr-box gr-padded"
                                    )

                                    template_type = gr.Radio(
                                        choices=template_types,
                                        label="📑 Template Type",
                                        visible=False,
                                        info="Only applicable for Advisory Circulars",
                                        elem_classes="gr-box gr-padded"
                                    )

                                    submit_btn = gr.Button(
                                        "🔍 Check Document",
                                        variant="primary",
                                        elem_classes="gr-button-primary"
                                    )

                                with gr.Column(scale=2):
                                    results = gr.HTML(elem_classes="results-container")
                                    with gr.Row():
                                        download_docx = gr.Button("📄 Download Report (DOCX)", visible=False)
                                        download_pdf = gr.Button("📑 Download Report (PDF)", visible=False)
                                    report_file = gr.File(label="Download Report", visible=False)

                        def format_error_message(error: str) -> str:
                            """Format error messages for display in the UI."""
                            return f"""
                            <div style="color: #721c24; background-color: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #721c24; margin-top: 0;">Error Processing Document</h3>
                                <p style="margin-bottom: 0;">{error}</p>
                            </div>
                            """

                        def process_and_format(file_obj, doc_type_value, template_type_value):
                            """Process document and format results as HTML."""
                            try:
                                if not file_obj:
                                    return "Please upload a document file.", gr.update(visible=False), gr.update(visible=False), None

                                logger.info("Starting document processing...")

                                # Create temporary file for validation
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                                    if isinstance(file_obj, bytes):
                                        temp_file.write(file_obj)
                                    else:
                                        with open(file_obj.name, 'rb') as f:
                                            temp_file.write(f.read())
                                    temp_file_path = temp_file.name
                                    logger.info(f"Created temporary file: {temp_file_path}")

                                try:
                                    validate_file(temp_file_path)
                                    checker = FAADocumentChecker()
                                    formatter = ResultFormatter(style="html")

                                    logger.info(f"Running checks for document type: {doc_type_value}")
                                    results_data = checker.run_all_document_checks(
                                        document_path=temp_file_path,
                                        doc_type=doc_type_value
                                    )

                                    logger.info(f"Number of issues found: {len(results_data.issues) if results_data and results_data.issues else 0}")
                                    logger.debug(f"Raw results type: {type(results_data)}")
                                    logger.debug(f"Raw results dir: {dir(results_data)}")

                                    if not results_data or not results_data.issues:
                                        return """
                                            <div class="p-4 bg-yellow-50 text-yellow-700 rounded-lg">
                                                ⚠️ No issues were found in the document. This could mean either:
                                                <ul class="list-disc ml-4 mt-2">
                                                    <li>The document is perfectly formatted</li>
                                                    <li>The document processing encountered an issue</li>
                                                    <li>The document type selected doesn't match the document</li>
                                                </ul>
                                                Please verify your document and try again if needed.
                                            </div>
                                        """, gr.update(visible=False), gr.update(visible=False), None

                                    # Create a dictionary with check results organized by category
                                    results_dict = {}

                                    # Define category mappings
                                    category_mappings = {
                                        'heading_checks': ['heading_title_check', 'heading_title_period_check'],
                                        'reference_checks': ['table_figure_reference_check', 'cross_references_check', 'document_title_check'],
                                        'acronym_checks': ['acronym_check', 'acronym_usage_check'],
                                        'terminology_checks': ['terminology_check', 'section_symbol_usage_check', 'double_period_check', 'spacing_check', 'date_formats_check', 'parentheses_check'],
                                        'structure_checks': ['paragraph_length_check', 'sentence_length_check', 'placeholders_check', 'boilerplate_check'],
                                        'accessibility_checks': ['508_compliance_check', 'hyperlink_check', 'accessibility'],
                                        'document_status_checks': ['watermark_check'],
                                        'readability_checks': ['readability_check']
                                    }

                                    # Organize results by category
                                    total_issues = 0
                                    for category, checkers in category_mappings.items():
                                        category_results = {}
                                        for checker in checkers:
                                            if hasattr(results_data, checker):
                                                result = getattr(results_data, checker)
                                                logger.debug(f"Processing {checker} in {category}")
                                                logger.debug(f"  Result type: {type(result)}")
                                                logger.debug(f"  Has issues attr: {hasattr(result, 'issues')}")
                                                if hasattr(result, 'issues'):
                                                    issues = result.issues
                                                    logger.debug(f"  Number of issues: {len(issues)}")
                                                    total_issues += len(issues)
                                                    # Convert DocumentCheckResult to dict format expected by formatter
                                                    category_results[checker] = {
                                                        'success': False if issues else True,  # Set success based on presence of issues
                                                        'issues': issues,
                                                        'details': result.details if hasattr(result, 'details') else {}
                                                    }
                                        if category_results:
                                            results_dict[category] = category_results
                                            logger.debug(f"Added {len(category_results)} results for category {category}")

                                    logger.info(f"Total issues organized: {total_issues}")
                                    logger.debug(f"Final results dictionary structure: {json.dumps(results_dict, indent=2, default=str)}")

                                    # Use the unified formatter
                                    formatted_results = formatter.format_results(results_dict, doc_type_value)
                                    logger.debug(f"Formatted results length: {len(formatted_results)}")

                                    # Return all required values for Gradio
                                    return formatted_results, gr.update(visible=True), gr.update(visible=True), None

                                finally:
                                    try:
                                        os.unlink(temp_file_path)
                                    except Exception as e:
                                        logger.warning(f"Failed to delete temporary file: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error processing document: {str(e)}", exc_info=True)
                                return format_error_message(str(e)), gr.update(visible=False), gr.update(visible=False), None

                        def update_template_visibility(doc_type_value):
                            return gr.update(visible=doc_type_value == "Advisory Circular")

                        doc_type.change(
                            fn=update_template_visibility,
                            inputs=[doc_type],
                            outputs=[template_type]
                        )

                        def generate_report_file(results_data, doc_type_value, format="docx"):
                            """Generate downloadable report file."""
                            if not results_data:
                                return None

                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"document_check_report_{timestamp}.{format}"

                            formatter = ResultFormatter(style=format)
                            formatted_results = formatter.format_results({"document_check": results_data}, doc_type_value)

                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}", mode="w", encoding="utf-8") as temp_file:
                                temp_file.write(formatted_results)
                                return temp_file.name

                        submit_btn.click(
                            fn=process_and_format,
                            inputs=[file_input, doc_type, template_type],
                            outputs=[results, download_docx, download_pdf, report_file]
                        )

                        download_docx.click(
                            fn=generate_report_file,
                            inputs=[results, doc_type],
                            outputs=[report_file]
                        )

                        download_pdf.click(
                            fn=generate_report_file,
                            inputs=[results, doc_type],
                            outputs=[report_file]
                        )

                        gr.Markdown(
                            """
                            ### 📌 Important Notes
                            - This tool helps ensure compliance with federal documentation standards
                            - Results are based on current style guides and FAA requirements
                            - The tool provides suggestions but final editorial decisions rest with the document author
                            - For questions or feedback on the FAA documentation standards, contact the AIR-646 Senior Technical Writers
                            - For questions or feedback on the tool, contact Eric Putnam
                            - Results are not stored or saved
                            """
                        )

                    with gr.Tab("About"):
                        gr.Markdown(
                            get_readme_content(),
                            elem_classes="markdown-body"
                        )

    return demo