import gradio as gr
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import ResultFormatter, FormatStyle, format_results_to_html
from documentcheckertool.utils.security import validate_file, SecurityError
from documentcheckertool.models import DocumentCheckResult, Severity, DocumentType, VisibilitySettings
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
logger.debug("[UI DEBUG] gradio_ui.py module loaded")
GRADIO_VERSION = pkg_resources.get_distribution('gradio').version

def create_interface():
    """Create and configure the Gradio interface."""

    # Initialize visibility settings
    visibility_settings = VisibilitySettings()

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

    /* Visibility controls styling */
    .visibility-controls {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }

    .visibility-controls h3 {
        color: #0056b3;
        margin-bottom: 15px;
    }

    .visibility-controls .checkbox-group {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
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

                                    with gr.Group(elem_classes="visibility-controls"):
                                        gr.Markdown("### 📊 Visibility Controls")
                                        with gr.Row():
                                            with gr.Column():
                                                show_readability = gr.Checkbox(
                                                    label="Readability Metrics",
                                                    value=True,
                                                    info="Show readability metrics and scores"
                                                )
                                                show_paragraph_length = gr.Checkbox(
                                                    label="Paragraph & Sentence Length",
                                                    value=True,
                                                    info="Show paragraph and sentence length checks"
                                                )
                                                show_terminology = gr.Checkbox(
                                                    label="Terminology Checks",
                                                    value=True,
                                                    info="Show terminology and style checks"
                                                )
                                                show_headings = gr.Checkbox(
                                                    label="Heading Checks",
                                                    value=True,
                                                    info="Show heading format and structure checks"
                                                )
                                            with gr.Column():
                                                show_structure = gr.Checkbox(
                                                    label="Structure Checks",
                                                    value=True,
                                                    info="Show document structure checks"
                                                )
                                                show_format = gr.Checkbox(
                                                    label="Format Checks",
                                                    value=True,
                                                    info="Show formatting and style checks"
                                                )
                                                show_accessibility = gr.Checkbox(
                                                    label="Accessibility Checks",
                                                    value=True,
                                                    info="Show accessibility compliance checks"
                                                )
                                                show_document_status = gr.Checkbox(
                                                    label="Document Status Checks",
                                                    value=True,
                                                    info="Show document status and watermark checks"
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
                            logger.debug("[UI DEBUG] process_and_format called")
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
                                    result_obj = checker.run_all_document_checks(
                                        document_path=temp_file_path,
                                        doc_type=doc_type_value
                                    )
                                    results_dict = getattr(result_obj, 'per_check_results', None)
                                    if not results_dict:
                                        # fallback for legacy
                                        results_dict = {"all": {"all": {
                                            "success": result_obj.success,
                                            "issues": result_obj.issues,
                                            "details": getattr(result_obj, "details", {})
                                        }}}
                                    # --- PATCH: Add explicit debug logs for UI display ---
                                    # Count issues in results_dict
                                    total_issues = 0
                                    issues_by_category = {}
                                    for category, category_results in results_dict.items():
                                        cat_issues = 0
                                        if isinstance(category_results, dict):
                                            for result in category_results.values():
                                                if isinstance(result, dict) and 'issues' in result:
                                                    cat_issues += len(result['issues'])
                                                elif hasattr(result, 'issues'):
                                                    cat_issues += len(result.issues)
                                        issues_by_category[category] = cat_issues
                                        total_issues += cat_issues
                                    logger.debug(f"[UI DEBUG] Total issues in results_dict: {total_issues}")
                                    logger.debug(f"[UI DEBUG] Issues by category: {issues_by_category}")
                                    # Format results
                                    formatter = ResultFormatter(style=FormatStyle.HTML)
                                    formatted_results = formatter.format_results(results_dict, doc_type_value)
                                    logger.debug(f"Formatted HTML results: {formatted_results[:500]}")
                                    # Check if the UI will display 'All checks passed'
                                    if 'All checks passed successfully' in formatted_results:
                                        if total_issues > 0:
                                            logger.warning("[UI DEBUG] Issues present in results_dict, but UI will display 'All checks passed'! Possible formatter/structure bug.")
                                        else:
                                            logger.debug("[UI DEBUG] No issues found; UI will display 'All checks passed'.")
                                    else:
                                        logger.debug("[UI DEBUG] UI will display issues.")
                                    # --- END PATCH ---
                                    html_results = formatted_results

                                    # Store for download handlers
                                    global _last_results
                                    _last_results = results_dict

                                    return html_results, gr.update(visible=True), gr.update(visible=True), None

                                finally:
                                    try:
                                        os.unlink(temp_file_path)
                                    except Exception as e:
                                        logger.warning(f"Failed to delete temporary file: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error processing document: {str(e)}", exc_info=True)
                                # Always show the error message in the results HTML output
                                return format_error_message(str(e)), gr.update(visible=True), gr.update(visible=False), None

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
                                if not _last_results:
                                    logger.error("No results available for report generation")
                                    return None

                                # Extract results and visibility settings
                                results_dict = _last_results['results']
                                visibility_settings = VisibilitySettings.from_dict(_last_results['visibility'])
                                summary = _last_results['summary']
                                formatted_results = _last_results.get('formatted_results')  # Get formatted results from _last_results

                                # Create a temporary file
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as temp_file:
                                    filepath = temp_file.name

                                # Filter results based on visibility settings
                                filtered_results = {}
                                for category, category_results in results_dict.items():
                                    if getattr(visibility_settings, f"show_{category}", True):
                                        filtered_results[category] = category_results

                                # Defensive: Log the number of issues to be exported
                                total_issues = sum(
                                    len(result['issues'])
                                    for cat in filtered_results.values()
                                    for result in cat.values()
                                    if 'issues' in result and result['issues']
                                )
                                logger.info(f"Exporting {total_issues} issues to DOCX")
                                if not filtered_results:
                                    logger.warning("No filtered results found for DOCX export. The report will be empty except for the header.")

                                # Format results based on output format
                                if format == "docx":
                                    try:
                                        from docx import Document
                                        from docx.shared import Inches, Pt, RGBColor
                                        from docx.enum.text import WD_ALIGN_PARAGRAPH

                                        doc = Document()

                                        # Add title
                                        title = doc.add_heading('Document Check Results', 0)
                                        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

                                        # Add summary section
                                        doc.add_heading('Summary', level=1)
                                        summary_para = doc.add_paragraph()
                                        summary_para.add_run(f'Found {summary["total"]} issues that need attention:').bold = True

                                        # Add category summaries
                                        for category, count in summary['by_category'].items():
                                            if count > 0:
                                                doc.add_paragraph(
                                                    f'{category.replace("_", " ").title()}: {count} issues',
                                                    style='List Bullet'
                                                )

                                        # Add detailed results
                                        if total_issues == 0:
                                            doc.add_paragraph("No issues found in this document.", style='Normal')
                                        else:
                                            for category, category_results in filtered_results.items():
                                                if category_results:
                                                    doc.add_heading(category.replace('_', ' ').title(), level=1)

                                                    for check_name, result in category_results.items():
                                                        if result.get('issues'):
                                                            doc.add_heading(check_name.replace('_', ' ').title(), level=2)

                                                            for issue in result['issues']:
                                                                p = doc.add_paragraph(style='List Bullet')
                                                                p.add_run(issue['message'])
                                                                if issue.get('line_number'):
                                                                    p.add_run(f' (Line {issue["line_number"]})').italic = True

                                        doc.save(filepath)
                                        logger.info(f"DOCX report saved to: {filepath}")
                                        return filepath

                                    except ImportError:
                                        logger.error("python-docx not installed. Please install it with: pip install python-docx")
                                        return None
                                    except Exception as e:
                                        logger.error(f"Error generating DOCX: {str(e)}")
                                        return None

                                elif format == "pdf":
                                    try:
                                        import pdfkit

                                        # Create HTML content
                                        html_content = f"""
                                        <html>
                                        <head>
                                            <style>
                                                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                                                h1 {{ color: #0056b3; text-align: center; }}
                                                h2 {{ color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }}
                                                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                                                .category {{ margin-bottom: 30px; }}
                                                .issue {{ margin: 10px 0; padding-left: 20px; }}
                                            </style>
                                        </head>
                                        <body>
                                            <h1>Document Check Results</h1>

                                            <div class="summary">
                                                <h2>Summary</h2>
                                                <p>Found {summary['total']} issues that need attention:</p>
                                                <ul>
                                        """

                                        for category, count in summary['by_category'].items():
                                            if count > 0:
                                                html_content += f"""
                                                    <li>{category.replace('_', ' ').title()}: {count} issues</li>
                                                """

                                        html_content += """
                                                </ul>
                                            </div>
                                        """

                                        for category, category_results in filtered_results.items():
                                            if category_results:
                                                html_content += f"""
                                                <div class="category">
                                                    <h2>{category.replace('_', ' ').title()}</h2>
                                                """

                                                for check_name, result in category_results.items():
                                                    if result.get('issues'):
                                                        html_content += f"""
                                                        <h3>{check_name.replace('_', ' ').title()}</h3>
                                                        <ul>
                                                        """

                                                        for issue in result['issues']:
                                                            line_info = f" (Line {issue['line_number']})" if issue.get('line_number') else ""
                                                            html_content += f"""
                                                            <li class="issue">{issue['message']}{line_info}</li>
                                                            """

                                                        html_content += "</ul>"

                                                html_content += "</div>"

                                        html_content += """
                                        </body>
                                        </html>
                                        """

                                        pdfkit.from_string(html_content, filepath)
                                        logger.info(f"PDF report saved to: {filepath}")
                                        return filepath

                                    except ImportError:
                                        logger.error("pdfkit not installed. Please install it with: pip install pdfkit")
                                        return None
                                    except Exception as e:
                                        logger.error(f"Error generating PDF: {str(e)}")
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