import gradio as gr
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle
from documentcheckertool.utils.security import validate_file, SecurityError
from documentcheckertool.models import DocumentCheckResult, Severity, DocumentType
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
                                        label="Document Type",
                                        choices=DocumentType.values(),
                                        value=DocumentType.ADVISORY_CIRCULAR.value,
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
                                    formatter = ResultFormatter(style=FormatStyle.HTML)

                                    logger.info(f"Running checks for document type: {doc_type_value}")
                                    results_data = checker.run_all_document_checks(
                                        document_path=temp_file_path,
                                        doc_type=doc_type_value
                                    )

                                    # Debug the raw results structure
                                    logger.debug(f"Raw results type: {type(results_data)}")
                                    logger.debug(f"Raw results dir: {dir(results_data)}")
                                    logger.debug(f"Raw results dict: {results_data.__dict__ if hasattr(results_data, '__dict__') else 'No __dict__'}")

                                    # Create a dictionary with check results organized by category
                                    results_dict = {}
                                    total_issues = 0

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

                                    # First, check if we have direct issues on the results object
                                    if hasattr(results_data, 'issues') and results_data.issues:
                                        logger.debug(f"Found {len(results_data.issues)} direct issues")
                                        logger.debug(f"Direct issues: {results_data.issues}")
                                        # Create a general category for direct issues
                                        results_dict['general_issues'] = {
                                            'document_check': {
                                                'success': False,
                                                'issues': results_data.issues,
                                                'details': {}
                                            }
                                        }
                                        total_issues += len(results_data.issues)

                                    # Then process each category
                                    for category, checkers in category_mappings.items():
                                        category_results = {}
                                        for checker in checkers:
                                            if hasattr(results_data, checker):
                                                result = getattr(results_data, checker)
                                                logger.debug(f"Processing {checker} in {category}")
                                                logger.debug(f"  Result type: {type(result)}")
                                                logger.debug(f"  Result dir: {dir(result)}")

                                                # Convert DocumentCheckResult to dict format
                                                if hasattr(result, 'issues') and result.issues:
                                                    logger.debug(f"  Found {len(result.issues)} issues in {checker}")
                                                    logger.debug(f"  Issues: {result.issues}")
                                                    total_issues += len(result.issues)
                                                    category_results[checker] = {
                                                        'success': False,
                                                        'issues': result.issues,
                                                        'details': getattr(result, 'details', {}) if hasattr(result, 'details') else {}
                                                    }

                                        if category_results:
                                            results_dict[category] = category_results
                                            logger.debug(f"Added {len(category_results)} results for category {category}")

                                    logger.info(f"Total issues organized: {total_issues}")
                                    logger.debug(f"Final results dictionary structure: {json.dumps(results_dict, indent=2, default=str)}")

                                    # Create a simple HTML output if no issues were found
                                    if total_issues == 0:
                                        formatted_results = """
                                        <div style="color: #006400; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                                            <h2>✓ All checks passed successfully!</h2>
                                            <p>No issues were found in your document.</p>
                                        </div>
                                        """
                                    else:
                                        # Create a basic HTML structure for the results
                                        formatted_results = f"""
                                        <div style="font-family: system-ui, -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px;">
                                            <h1 style="color: #0056b3; text-align: center;">Document Check Results</h1>
                                            <p style="color: #856404; text-align: center;">Found {total_issues} issues that need attention:</p>
                                            <div style="margin-top: 20px;">
                                        """

                                        # Process each category
                                        for category, category_results in results_dict.items():
                                            if category_results:  # Only show categories that have results
                                                formatted_results += f"""
                                                <div style="margin-bottom: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                                                    <h2 style="color: #0056b3; margin-bottom: 20px; border-bottom: 2px solid #0056b3; padding-bottom: 10px;">
                                                        {category.replace('_', ' ').title()}
                                                    </h2>
                                                """

                                                # Process each checker in the category
                                                for check_name, result in category_results.items():
                                                    if result['issues']:
                                                        formatted_results += f"""
                                                        <div style="margin-bottom: 30px; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                                            <h3 style="color: #0056b3; margin-bottom: 15px;">■ {check_name.replace('_', ' ').title()}</h3>
                                                            <ul style="list-style-type: none; padding-left: 20px;">
                                                        """

                                                        for issue in result['issues']:
                                                            severity = issue.get('severity', '')
                                                            message = issue.get('message', '')
                                                            line = issue.get('line_number')
                                                            line_info = f" (Line {line})" if line is not None else ""

                                                            # Format the issue message with proper HTML and severity indicator
                                                            severity_indicator = ""
                                                            if severity == Severity.ERROR:
                                                                severity_indicator = '<span style="color: #721c24; font-weight: bold;">[ERROR]</span> '
                                                            elif severity == Severity.WARNING:
                                                                severity_indicator = '<span style="color: #856404; font-weight: bold;">[WARNING]</span> '
                                                            else:
                                                                severity_indicator = '<span style="color: #0c5460; font-weight: bold;">[INFO]</span> '

                                                            formatted_results += f"""
                                                            <li style="margin-bottom: 8px;">
                                                                {severity_indicator}{message}{line_info}
                                                            </li>
                                                            """

                                                        formatted_results += """
                                                            </ul>
                                                        </div>
                                                        """

                                                formatted_results += """
                                                </div>
                                                """

                                        formatted_results += """
                                            </div>
                                        </div>
                                        """

                                        logger.debug(f"Formatted results length: {len(formatted_results)}")
                                        logger.debug(f"Formatted results preview: {formatted_results[:500]}...")

                                    # Store the results dictionary for report generation
                                    global _last_results
                                    _last_results = results_dict

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

                        def generate_report_file(results_data, doc_type_value, format="html"):
                            """Generate downloadable report file."""
                            try:
                                global _last_results
                                if not _last_results:
                                    logger.warning("No results data available for report generation")
                                    return None

                                logger.debug(f"Generating report with format: {format}")
                                logger.debug(f"Using stored results data")

                                # Create downloads directory if it doesn't exist
                                downloads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads")
                                os.makedirs(downloads_dir, exist_ok=True)

                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"document_check_report_{timestamp}.{format}"
                                filepath = os.path.join(downloads_dir, filename)

                                formatter = ResultFormatter(style=FormatStyle.HTML)
                                formatted_results = formatter.format_results(_last_results, doc_type_value)
                                logger.debug(f"Generated formatted results length: {len(formatted_results)}")

                                if format == "pdf":
                                    # Convert HTML to PDF using pdfkit
                                    try:
                                        import pdfkit
                                        pdfkit.from_string(formatted_results, filepath)
                                        logger.info(f"PDF report saved to: {filepath}")
                                        return filepath
                                    except ImportError:
                                        logger.error("pdfkit not installed. Please install it with: pip install pdfkit")
                                        return None
                                    except Exception as e:
                                        logger.error(f"Error generating PDF: {str(e)}")
                                        return None
                                elif format == "docx":
                                    # Convert HTML to DOCX using python-docx
                                    try:
                                        from docx import Document
                                        from docx.shared import Inches
                                        from bs4 import BeautifulSoup

                                        doc = Document()
                                        soup = BeautifulSoup(formatted_results, 'html.parser')

                                        # Add title
                                        title = soup.find('h1')
                                        if title:
                                            doc.add_heading(title.text, 0)

                                        # Add total issues
                                        total_issues = soup.find('p', {'style': 'color: #856404;'})
                                        if total_issues:
                                            doc.add_paragraph(total_issues.text)

                                        # Process each category
                                        for category in soup.find_all('div', {'style': 'margin-bottom: 40px;'}):
                                            # Add category heading
                                            category_title = category.find('h2')
                                            if category_title:
                                                doc.add_heading(category_title.text.strip(), 1)

                                            # Process each check
                                            for check in category.find_all('div', {'style': 'margin-bottom: 30px;'}):
                                                check_title = check.find('h3')
                                                if check_title:
                                                    doc.add_heading(check_title.text.strip(), 2)

                                                # Add issues
                                                for issue in check.find_all('li'):
                                                    doc.add_paragraph(issue.text.strip(), style='List Bullet')

                                        doc.save(filepath)
                                        logger.info(f"DOCX report saved to: {filepath}")
                                        return filepath

                                    except ImportError:
                                        logger.error("Required packages not installed. Please install with: pip install python-docx beautifulsoup4")
                                        return None
                                    except Exception as e:
                                        logger.error(f"Error generating DOCX: {str(e)}")
                                        return None
                                else:
                                    # Default to HTML
                                    with open(filepath, 'w', encoding='utf-8') as f:
                                        f.write(formatted_results)
                                        logger.info(f"HTML report saved to: {filepath}")
                                        return filepath

                            except Exception as e:
                                logger.error(f"Error generating report: {str(e)}", exc_info=True)
                                return None

                        submit_btn.click(
                            fn=process_and_format,
                            inputs=[file_input, doc_type, template_type],
                            outputs=[results, download_docx, download_pdf, report_file]
                        )

                        download_docx.click(
                            fn=lambda: generate_report_file(None, None, "docx"),
                            inputs=[],
                            outputs=[report_file]
                        )

                        download_pdf.click(
                            fn=lambda: generate_report_file(None, None, "pdf"),
                            inputs=[],
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

# Global variable to store the last results
_last_results = None