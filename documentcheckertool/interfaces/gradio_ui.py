import logging
import os
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pprint import pformat

import gradio as gr

from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.models import (
    DocumentType,
    VisibilitySettings,
)
from documentcheckertool.utils.formatting import (
    FormatStyle,
    ResultFormatter,
)
from documentcheckertool.utils.security import validate_file

logger = logging.getLogger(__name__)
logger.debug("[UI DEBUG] gradio_ui.py module loaded")
try:
    GRADIO_VERSION = version("gradio")
except PackageNotFoundError:
    GRADIO_VERSION = "unknown"


def create_interface():
    """Create and configure the Gradio interface."""

    # Initialize visibility settings
    VisibilitySettings()

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

    with gr.Blocks(
        css=custom_css,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="blue",
            neutral_hue="slate",
            spacing_size="sm",
            radius_size="lg",
            font=["system-ui", "sans-serif"],
        ),
    ) as demo:
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
                            elem_classes="markdown-body",
                        )

                        with gr.Group(elem_classes="gr-form"):
                            with gr.Row():
                                with gr.Column(scale=1):
                                    file_input = gr.File(
                                        label="📎 Upload Word Document (.docx)",
                                        file_types=[".docx"],
                                        type="binary",
                                        elem_classes="file-upload upload-box",
                                        interactive=True,
                                    )

                                    doc_type = gr.Dropdown(
                                        label="Document Type",
                                        choices=DocumentType.values(),
                                        value=DocumentType.ADVISORY_CIRCULAR.value,
                                        info="Select the type of document you're checking",
                                        elem_classes="gr-box gr-padded",
                                    )

                                    template_type = gr.Radio(
                                        choices=template_types,
                                        label="📑 Template Type",
                                        visible=False,
                                        info="Only applicable for Advisory Circulars",
                                        elem_classes="gr-box gr-padded",
                                    )

                                    group_by = gr.Radio(
                                        choices=["category", "severity"],
                                        value="category",
                                        label="Group Results By",
                                        info="Choose how to group the results: by functional category or by severity.",
                                    )

                                    with gr.Group(elem_classes="visibility-controls"):
                                        gr.Markdown("### 📊 Visibility Controls")
                                        with gr.Row():
                                            with gr.Column():
                                                show_readability = gr.Checkbox(
                                                    label="Readability Metrics",
                                                    value=True,
                                                    info="Show readability metrics and scores",
                                                )
                                                show_paragraph_length = gr.Checkbox(
                                                    label="Paragraph & Sentence Length",
                                                    value=True,
                                                    info="Show paragraph and sentence length checks",
                                                )
                                                show_terminology = gr.Checkbox(
                                                    label="Terminology Checks",
                                                    value=True,
                                                    info="Show terminology and style checks",
                                                )
                                                show_headings = gr.Checkbox(
                                                    label="Heading Checks",
                                                    value=True,
                                                    info="Show heading format and structure checks",
                                                )
                                            with gr.Column():
                                                show_structure = gr.Checkbox(
                                                    label="Structure Checks",
                                                    value=True,
                                                    info="Show document structure checks",
                                                )
                                                show_format = gr.Checkbox(
                                                    label="Format Checks",
                                                    value=True,
                                                    info="Show formatting and style checks",
                                                )
                                                show_accessibility = gr.Checkbox(
                                                    label="Accessibility Checks",
                                                    value=True,
                                                    info="Show accessibility compliance checks",
                                                )
                                                show_document_status = gr.Checkbox(
                                                    label="Document Status Checks",
                                                    value=True,
                                                    info=(
                                                        "Show document status and watermark checks."
                                                    ),
                                                )

                                    submit_btn = gr.Button(
                                        "🔍 Check Document",
                                        variant="primary",
                                        elem_classes="gr-button-primary",
                                    )

                                with gr.Column(scale=2):
                                    results = gr.HTML(elem_classes="results-container")
                                    status_box = gr.Markdown("", elem_id="status-box")
                                    with gr.Row():
                                        download_docx = gr.Button(
                                            "📄 Download Report (DOCX)", visible=False
                                        )
                                        download_pdf = gr.Button(
                                            "📑 Download Report (PDF)", visible=False
                                        )
                                    report_file = gr.File(label="Download Report", visible=False)

                        def format_error_message(error: str) -> str:
                            """Format error messages for display in the UI."""
                            return (
                                f'<div style="color: #721c24; background-color: #f8d7da; padding: 20px; '
                                'border-radius: 8px; margin: 20px 0;">'
                                f'<h3 style="color: #721c24; margin-top: 0;">'
                                'Error Processing Document</h3>'
                                f'<p style="margin-bottom: 0;">{error}</p>'
                                "</div>"
                            )

                        def process_and_format(
                            file_obj,
                            doc_type_value,
                            template_type_value,
                            group_by_value,
                            show_readability_value,
                            show_paragraph_length_value,
                            show_terminology_value,
                            show_headings_value,
                            show_structure_value,
                            show_format_value,
                            show_accessibility_value,
                            show_document_status_value,
                        ):
                            logger.debug("[UI DEBUG] process_and_format called")
                            status = "Checking document..."
                            try:
                                if not file_obj:
                                    return (
                                        "Please upload a document file.",
                                        gr.update(visible=False),
                                        gr.update(visible=False),
                                        None,
                                        "",
                                    )
                                logger.info("Starting document processing...")

                                # Create temporary file for validation
                                with tempfile.NamedTemporaryFile(
                                    delete=False, suffix=".docx"
                                ) as temp_file:
                                    if isinstance(file_obj, bytes):
                                        temp_file.write(file_obj)
                                    else:
                                        with open(file_obj.name, "rb") as f:
                                            temp_file.write(f.read())
                                    temp_file_path = temp_file.name
                                    logger.info(f"Created temporary file: {temp_file_path}")

                                try:
                                    validate_file(temp_file_path)
                                    checker = FAADocumentChecker()
                                    result_obj = checker.run_all_document_checks(
                                        document_path=temp_file_path, doc_type=doc_type_value
                                    )
                                    results_dict = getattr(result_obj, "per_check_results", None)
                                    if not results_dict:
                                        # fallback for legacy
                                        results_dict = {
                                            "all": {
                                                "all": {
                                                    "success": result_obj.success,
                                                    "issues": result_obj.issues,
                                                    "details": getattr(result_obj, "details", {}),
                                                }
                                            }
                                        }
                                    # --- PATCH: Add explicit debug logs for UI display ---
                                    # Count issues in results_dict
                                    total_issues = 0
                                    issues_by_category = {}
                                    for category, category_results in results_dict.items():
                                        cat_issues = 0
                                        if isinstance(category_results, dict):
                                            for result in category_results.values():
                                                if isinstance(result, dict) and "issues" in result:
                                                    cat_issues += len(result["issues"])
                                                elif hasattr(result, "issues"):
                                                    cat_issues += len(result.issues)
                                        issues_by_category[category] = cat_issues
                                        total_issues += cat_issues
                                    logger.debug(
                                        f"[UI DEBUG] Total issues in results_dict: {total_issues}"
                                    )
                                    logger.debug(
                                        f"[UI DEBUG] Issues by category: {issues_by_category}"
                                    )

                                    # --- Filter based on visibility settings with mapping ---
                                    visibility_settings = VisibilitySettings(
                                        show_readability=show_readability_value,
                                        show_paragraph_length=show_paragraph_length_value,
                                        show_terminology=show_terminology_value,
                                        show_headings=show_headings_value,
                                        show_structure=show_structure_value,
                                        show_format=show_format_value,
                                        show_accessibility=show_accessibility_value,
                                        show_document_status=show_document_status_value,
                                    )
                                    logger.debug(
                                        f"[UI DEBUG] Visibility settings: {visibility_settings}"
                                    )

                                    # Mapping from visibility fields to result categories
                                    visibility_to_categories = {
                                        "show_readability": ["readability"],
                                        "show_paragraph_length": [
                                            "paragraph_length",
                                            "sentence_length",
                                        ],
                                        "show_terminology": ["terminology"],
                                        "show_headings": ["heading"],
                                        "show_structure": ["structure"],
                                        "show_format": ["format"],
                                        "show_accessibility": ["accessibility"],
                                        "show_document_status": ["document_status"],
                                    }
                                    # Build a set of categories to show
                                    selected_categories = set()
                                    if visibility_settings.show_readability:
                                        selected_categories.update(
                                            visibility_to_categories["show_readability"]
                                        )
                                    if visibility_settings.show_paragraph_length:
                                        selected_categories.update(
                                            visibility_to_categories["show_paragraph_length"]
                                        )
                                    if visibility_settings.show_terminology:
                                        selected_categories.update(
                                            visibility_to_categories["show_terminology"]
                                        )
                                    if visibility_settings.show_headings:
                                        selected_categories.update(
                                            visibility_to_categories["show_headings"]
                                        )
                                    if visibility_settings.show_structure:
                                        selected_categories.update(
                                            visibility_to_categories["show_structure"]
                                        )
                                    if visibility_settings.show_format:
                                        selected_categories.update(
                                            visibility_to_categories["show_format"]
                                        )
                                    if visibility_settings.show_accessibility:
                                        selected_categories.update(
                                            visibility_to_categories["show_accessibility"]
                                        )
                                    if visibility_settings.show_document_status:
                                        selected_categories.update(
                                            visibility_to_categories["show_document_status"]
                                        )
                                    logger.debug(
                                        "[UI DEBUG] Selected categories for display: "
                                        f"{selected_categories}"
                                    )

                                    filtered_results = {}
                                    for category, category_results in results_dict.items():
                                        if category in selected_categories:
                                            filtered_results[category] = category_results
                                    logger.debug(
                                        f"[UI DEBUG] Filtered categories: {list(filtered_results.keys())}"
                                    )
                                    # --- END PATCH ---

                                    # Format results
                                    formatter = ResultFormatter(style=FormatStyle.HTML)
                                    formatted_results = formatter.format_results(
                                        filtered_results, doc_type_value, group_by=group_by_value
                                    )
                                    if formatted_results is None:
                                        logger.error(
                                            f"ResultFormatter.format_results returned None. Inputs: results_dict={pformat(results_dict)}, doc_type_value={doc_type_value}, group_by_value={group_by_value}"
                                        )
                                        return (
                                            format_error_message(
                                                "Internal error: Could not format results."
                                            ),
                                            gr.update(visible=True),
                                            gr.update(visible=False),
                                            None,
                                            status,
                                        )
                                    logger.debug(
                                        f"Formatted HTML results: {formatted_results[:500]}"
                                    )
                                    # Check if the UI will display 'All checks passed'
                                    if "All checks passed successfully" in formatted_results:
                                        if total_issues > 0:
                                            logger.warning(
                                                "[UI DEBUG] Issues found in results_dict, but UI will display 'All checks passed'. "
                                                "Possible bug in the formatter or results structure."
                                            )
                                        else:
                                            logger.debug(
                                                "[UI DEBUG] No issues found; 'All checks passed'."
                                            )
                                    else:
                                        logger.debug("[UI DEBUG] UI will display issues.")
                                    # --- END PATCH ---
                                    html_results = formatted_results

                                    # Store for download handlers
                                    global _last_results
                                    _last_results = {
                                        "results": results_dict,
                                        "filtered_results": filtered_results,
                                        "visibility": visibility_settings.to_dict(),
                                        "summary": getattr(result_obj, "summary", {}),
                                        "formatted_results": formatted_results,
                                    }
                                    status = "Check complete."
                                    return (
                                        html_results,
                                        gr.update(visible=True),
                                        gr.update(visible=True),
                                        None,
                                        status,
                                    )

                                finally:
                                    try:
                                        os.unlink(temp_file_path)
                                    except Exception as e:
                                        logger.warning(f"Failed to delete temporary file: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error processing document: {str(e)}", exc_info=True)
                                status = f"Error: {str(e)}"
                                return (
                                    format_error_message(str(e)),
                                    gr.update(visible=True),
                                    gr.update(visible=False),
                                    None,
                                    status,
                                )

                        def update_template_visibility(doc_type_value):
                            return gr.update(visible=doc_type_value == "Advisory Circular")

                        doc_type.change(
                            fn=update_template_visibility,
                            inputs=[doc_type],
                            outputs=[template_type],
                        )

                        def generate_report_file(results_data, doc_type_value, format="html"):
                            """Generate downloadable report file."""
                            try:
                                if not _last_results:
                                    logger.error("No results available for report generation")
                                    return None

                                # Extract results and visibility settings
                                results_dict = _last_results["results"]
                                visibility_settings = VisibilitySettings.from_dict(
                                    _last_results["visibility"]
                                )
                                summary = _last_results["summary"]
                                formatted_results = _last_results.get(
                                    "formatted_results"
                                )  # Get formatted results from _last_results

                                # Create a temporary file
                                with tempfile.NamedTemporaryFile(
                                    delete=False, suffix=f".{format}"
                                ) as temp_file:
                                    filepath = temp_file.name

                                # Filter results based on visibility settings
                                filtered_results = {}
                                for category, category_results in results_dict.items():
                                    if getattr(visibility_settings, f"show_{category}", True):
                                        filtered_results[category] = category_results

                                # Defensive: Log the number of issues to be exported
                                total_issues = sum(
                                    len(result["issues"])
                                    for cat in filtered_results.values()
                                    for result in cat.values()
                                    if "issues" in result and result["issues"]
                                )
                                logger.info(f"Exporting {total_issues} issues to DOCX")
                                if not filtered_results:
                                    logger.warning("No filtered results found for DOCX export.")

                                # Format results based on output format
                                if format == "docx":
                                    try:
                                        from docx import Document
                                        from docx.enum.text import WD_ALIGN_PARAGRAPH

                                        doc = Document()

                                        # Add title
                                        title = doc.add_heading("Document Check Results", 0)
                                        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

                                        # Add summary section
                                        doc.add_heading("Summary", level=1)
                                        summary_para = doc.add_paragraph()
                                        summary_para.add_run(
                                            f'Found {summary["total"]} issues that need attention:'
                                        ).bold = True

                                        # Add category summaries
                                        for category, count in summary["by_category"].items():
                                            if count > 0:
                                                doc.add_paragraph(
                                                f'{category.replace("_", " ").title()}: '
                                                f'{count} issues',
                                                    style="List Bullet",
                                                )

                                        # Add detailed results
                                        if total_issues == 0:
                                            doc.add_paragraph(
                                                "No issues found in this document.", style="Normal"
                                            )
                                        else:
                                            for (
                                                category,
                                                category_results,
                                            ) in filtered_results.items():
                                                if category_results:
                                                    doc.add_heading(
                                                        category.replace("_", " ").title(), level=1
                                                    )

                                                    for (
                                                        check_name,
                                                        result,
                                                    ) in category_results.items():
                                                        if result.get("issues"):
                                                            doc.add_heading(
                                                                check_name.replace(
                                                                    "_", " "
                                                                ).title(),
                                                                level=2,
                                                            )

                                                            for issue in result["issues"]:
                                                                p = doc.add_paragraph(
                                                                    style="List Bullet"
                                                                )
                                                                p.add_run(issue["message"])
                                                                if issue.get("line_number"):
                                                                    p.add_run(
                                                                        f' (Line {issue["line_number"]})'
                                                                    ).italic = True

                                        doc.save(filepath)
                                        logger.info(f"DOCX report saved to: {filepath}")
                                        return filepath

                                    except ImportError:
                                        logger.error("python-docx not installed. Please install.")
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
{'''
body { font-family: Arial, sans-serif; margin: 40px; }
h1 { color: #0056b3; text-align: center; }
h2 {
    color: #0056b3;
    border-bottom: 2px solid #0056b3;
    padding-bottom: 10px;
}
.summary {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
}
.category { margin-bottom: 30px; }
.issue { margin: 10px 0; padding-left: 20px; }
'''}
                                            </style>
                                        </head>
                                        <body>
                                            <h1>Document Check Results</h1>

                                            <div class="summary">
                                                <h2>Summary</h2>
                                                <p>Found {summary['total']} issues:</p>
                                                <ul>
                                        """

                                        for category, count in summary["by_category"].items():
                                            if count > 0:
                                                html_content += (
                                f"<li>{category.replace('_', ' ').title()}: {count} issues</li>"
                            )

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
                                                        if result.get("issues"):
                                                            display_name = (
                                                                check_name.replace("_", " ").title()
                                                            )
                                                        html_content += (
                                                            "<h3>"
                                                            f"{display_name}"
                                                            "</h3>\n"
                                                            "<ul>\n"
                                                        )

                                                        for issue in result["issues"]:
                                                            line_info = (
                                                                f" (Line {issue['line_number']})"
                                                                if issue.get("line_number")
                                                                else ""
                                                            )
                                                            html_content += (
                                                                '<li class="issue">'
                                                                f"{issue['message']}{line_info}"
                                                                '</li>\n'
                                                            )

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
                                        logger.error("pdfkit not installed. Please install it.")
                                        return None
                                    except Exception as e:
                                        logger.error(f"Error generating PDF: {str(e)}")
                                        return None
                                else:
                                    # Default to HTML
                                    with open(filepath, "w", encoding="utf-8") as f:
                                        f.write(formatted_results)
                                        logger.info(f"HTML report saved to: {filepath}")
                                        return filepath

                            except Exception as e:
                                logger.error(f"Error generating report: {str(e)}", exc_info=True)
                                return None

                        submit_btn.click(
                            fn=process_and_format,
                            inputs=[
                                file_input,
                                doc_type,
                                template_type,
                                group_by,
                                show_readability,
                                show_paragraph_length,
                                show_terminology,
                                show_headings,
                                show_structure,
                                show_format,
                                show_accessibility,
                                show_document_status,
                            ],
                            outputs=[results, download_docx, download_pdf, report_file, status_box],
                        )

                        download_docx.click(
                            fn=lambda: generate_report_file(None, None, "docx"),
                            inputs=[],
                            outputs=[report_file],
                        )

                        download_pdf.click(
                            fn=lambda: generate_report_file(None, None, "pdf"),
                            inputs=[],
                            outputs=[report_file],
                        )

                        gr.Markdown(
                            """
                            ### 📌 Important Notes
                            - This tool helps you comply with federal documentation standards.
                            - Results are based on current style guides and FAA requirements.
                            - Final editorial decisions are the responsibility of the author.
                            - For FAA documentation questions, contact your senior technical writer.
                            - For tool questions or feedback, contact Eric Putnam.
                            - Results are not stored or saved.
                            """
                        )

                    with gr.Tab("About"):
                        gr.Markdown(get_readme_content(), elem_classes="markdown-body")

    return demo


# Global variable to store the last results
_last_results = None
