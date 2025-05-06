import gradio as gr
from documentcheckertool.document_checker import FAADocumentChecker
from documentcheckertool.utils.formatting import format_results_to_html
from documentcheckertool.utils.security import validate_file, SecurityError
from documentcheckertool.models import DocumentCheckResult
import logging
import tempfile
import os
import re
import io
import traceback

logger = logging.getLogger(__name__)

def create_interface():
    """Create and configure the Gradio interface."""
    
    document_types = [
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
    ]
    
    template_types = ["Short AC template AC", "Long AC template AC"]

    def format_results_as_html(text_results):
        """Convert the text results into styled HTML."""
        if not text_results:
            return """
                <div class="p-4 text-gray-600">
                    Results will appear here after processing...
                </div>
            """
        
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text_results = ansi_escape.sub('', text_results)
        
        # Split into sections while preserving the header
        sections = text_results.split('■')
        header = sections[0].strip()
        issues = sections[1:]
        
        # Extract the number of issues from the header text
        issues_count_match = re.search(r'Found (\d+) categories', header)
        issues_count = issues_count_match.group(1) if issues_count_match else len(issues)
        
        # Format header with title
        header_html = f"""
            <div class="max-w-4xl mx-auto p-4 bg-white rounded-lg shadow-sm mb-6">
                <h1 class="text-2xl font-bold mb-4">Document Check Results Summary</h1>
                <div class="text-lg text-amber-600">
                    Found {issues_count} categories of issues that need attention.
                </div>
            </div>
        """
        
        # Format each issue section
        issues_html = ""
        for section in issues:
            if not section.strip():
                continue
                
            parts = section.strip().split('\n', 1)
            if len(parts) < 2:
                continue
                
            title = parts[0].strip()
            content = parts[1].strip()
            
            # Special handling for readability metrics
            if "Readability Issues" in title:
                metrics_match = re.search(r'Readability Scores:(.*?)(?=Identified Issues:|$)', content, re.DOTALL)
                issues_match = re.search(r'Identified Issues:(.*?)(?=\Z)', content, re.DOTALL)
                
                metrics_html = ""
                if metrics_match:
                    metrics = metrics_match.group(1).strip().split('\n')
                    metrics_html = """
                        <div class="bg-blue-50 rounded-lg p-4 mb-4">
                            <h3 class="font-medium text-blue-800 mb-2">📊 Readability Metrics</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    """
                    for metric in metrics:
                        if metric.strip():
                            label, value = metric.strip('• ').split(':', 1)
                            metrics_html += f"""
                                <div class="flex flex-col">
                                    <span class="text-sm text-blue-600 font-medium">{label}</span>
                                    <span class="text-lg text-blue-900">{value}</span>
                                </div>
                            """
                    metrics_html += "</div></div>"

                issues_html_section = ""
                if issues_match:
                    issues_list = issues_match.group(1).strip().split('\n')
                    if issues_list:
                        issues_html_section = """
                            <div class="mt-4">
                                <h3 class="font-medium text-gray-800 mb-2">📝 Identified Issues:</h3>
                                <ul class="list-none space-y-2">
                        """
                        for issue in issues_list:
                            if issue.strip():
                                issues_html_section += f"""
                                    <li class="text-gray-600 ml-4">• {issue.strip('• ')}</li>
                                """
                        issues_html_section += "</ul></div>"

                issues_html += f"""
                    <div class="bg-white rounded-lg shadow-sm mb-6 overflow-hidden">
                        <div class="bg-gray-50 px-6 py-4 border-b">
                            <h2 class="text-lg font-semibold text-gray-800">{title}</h2>
                        </div>
                        <div class="px-6 py-4">
                            {metrics_html}
                            {issues_html_section}
                        </div>
                    </div>
                """
                continue

            # Extract description and solution
            description_parts = content.split('How to fix:', 1)
            description = description_parts[0].strip()
            solution = description_parts[1].split('Example Fix:', 1)[0].strip() if len(description_parts) > 1 else ""
            
            # Extract examples and issues
            examples_match = re.search(r'Example Fix:\s*❌[^✓]+✓[^•]+', content, re.MULTILINE | re.DOTALL)
            examples_html = ""
            if examples_match:
                examples_text = examples_match.group(0)
                incorrect = re.search(r'❌\s*Incorrect:\s*([^✓]+)', examples_text)
                correct = re.search(r'✓\s*Correct:\s*([^•\n]+)', examples_text)
                
                if incorrect and correct:
                    examples_html = f"""
                        <div class="mb-4">
                            <h3 class="font-medium text-gray-800 mb-2">Example Fix:</h3>
                            <div class="space-y-2 ml-4">
                                <div class="text-red-600">
                                    ❌ Incorrect:
                                </div>
                                <div class="text-red-600 ml-8">
                                    {incorrect.group(1).strip()}
                                </div>
                                <div class="text-green-600 mt-2">
                                    ✓ Correct:
                                </div>
                                <div class="text-green-600 ml-8">
                                    {correct.group(1).strip()}
                                </div>
                            </div>
                        </div>
                    """
            
            # Extract issues
            issues_match = re.findall(r'•\s*(.*?)(?=•|\Z)', content, re.DOTALL)
            issues_html_section = ""
            if issues_match:
                issues_html_section = """
                    <div class="mt-4">
                        <h3 class="font-medium text-gray-800 mb-2">Issues found in your document:</h3>
                        <ul class="list-none space-y-2">
                """
                for issue in issues_match[:30]:
                    clean_issue = issue.strip().lstrip('•').strip()
                    issues_html_section += f"""
                        <li class="text-gray-600 ml-4">• {clean_issue}</li>
                    """
                if len(issues_match) > 30:
                    issues_html_section += f"""
                        <li class="text-gray-500 italic ml-4">... and {len(issues_match) - 30} more similar issues.</li>
                    """
                issues_html_section += "</ul></div>"
            
            # Combine the section
            issues_html += f"""
                <div class="bg-white rounded-lg shadow-sm mb-6 overflow-hidden">
                    <div class="bg-gray-50 px-6 py-4 border-b">
                        <h2 class="text-lg font-semibold text-gray-800">{title}</h2>
                    </div>
                    
                    <div class="px-6 py-4">
                        <div class="text-gray-600 mb-4">
                            {description}
                        </div>
                        
                        <div class="bg-green-50 rounded p-4 mb-4">
                            <div class="text-green-800">
                                <span class="font-medium">How to fix: </span>
                                {solution}
                            </div>
                        </div>
                        
                        {examples_html}
                        {issues_html_section}
                    </div>
                </div>
            """
        
        # Add CSS classes for styling
        styles = """
            <style>
                .text-2xl { font-size: 1.5rem; line-height: 2rem; }
                .text-lg { font-size: 1.125rem; }
                .text-sm { font-size: 0.875rem; }
                .font-bold { font-weight: 700; }
                .font-semibold { font-weight: 600; }
                .font-medium { font-weight: 500; }
                .text-gray-800 { color: #1f2937; }
                .text-gray-600 { color: #4b5563; }
                .text-gray-500 { color: #6b7280; }
                .text-green-600 { color: #059669; }
                .text-green-800 { color: #065f46; }
                .text-red-600 { color: #dc2626; }
                .text-amber-600 { color: #d97706; }
                .text-blue-600 { color: #2563eb; }
                .text-blue-800 { color: #1e40af; }
                .text-blue-900 { color: #1e3a8a; }
                .bg-white { background-color: #ffffff; }
                .bg-gray-50 { background-color: #f9fafb; }
                .bg-green-50 { background-color: #ecfdf5; }
                .bg-blue-50 { background-color: #eff6ff; }
                .rounded-lg { border-radius: 0.5rem; }
                .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
                .mb-6 { margin-bottom: 1.5rem; }
                .mb-4 { margin-bottom: 1rem; }
                .mb-2 { margin-bottom: 0.5rem; }
                .ml-4 { margin-left: 1rem; }
                .ml-8 { margin-left: 2rem; }
                .mt-2 { margin-top: 0.5rem; }
                .mt-4 { margin-top: 1rem; }
                .p-4 { padding: 1rem; }
                .px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
                .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
                .space-y-2 > * + * { margin-top: 0.5rem; }
                .italic { font-style: italic; }
                .border-b { border-bottom: 1px solid #e5e7eb; }
                .overflow-hidden { overflow: hidden; }
                .list-none { list-style-type: none; }
                .grid { display: grid; }
                .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
                .gap-4 { gap: 1rem; }
                @media (min-width: 768px) {
                    .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                }
            </style>
        """
        
        # Combine all HTML sections
        full_html = f"""
        <div class="mx-auto p-4" style="font-family: system-ui, -apple-system, sans-serif;">
            {styles}
            {header_html}
            {issues_html}
        </div>
        """
        
        return full_html

    def get_readme_content():
        readme_path = "README.md"
        try:
            with open(readme_path, "r", encoding="utf-8") as file:
                readme_content = file.read()
            return readme_content
        except Exception as e:
            logging.error(f"Error reading README.md: {str(e)}")
            return "Error loading help content."
    
    with gr.Blocks() as demo:
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
                > **Note:** Please ensure your document is clean (no track changes or comments).
                """
                )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(
                            label="📎 Upload Word Document (.docx)",
                            file_types=[".docx"],
                            type="binary"
                        )
                        
                        doc_type = gr.Dropdown(
                            choices=document_types,
                            label="📋 Document Type",
                            value="Advisory Circular",
                            info="Select the type of document you're checking"
                        )
                        
                        template_type = gr.Radio(
                            choices=template_types,
                            label="📑 Template Type",
                            visible=False,
                            info="Only applicable for Advisory Circulars"
                        )
                        
                        submit_btn = gr.Button(
                            "🔍 Check Document",
                            variant="primary"
                        )
                    
                    with gr.Column(scale=2):
                        results = gr.HTML()
                
                def process_and_format(file_obj, doc_type_value, template_type_value):
                    """Process document and format results as HTML."""
                    try:
                        if not file_obj:
                            return "Please upload a document file."
                        
                        # Create temporary file for validation
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                            if isinstance(file_obj, bytes):
                                temp_file.write(file_obj)
                            else:
                                with open(file_obj.name, 'rb') as f:
                                    temp_file.write(f.read())
                            temp_file_path = temp_file.name
                        
                        try:
                            # Validate the file
                            validate_file(temp_file_path)
                            
                            # Process the document
                            checker = FAADocumentChecker()
                            results_data = checker.run_all_document_checks(
                                document_path=temp_file_path,
                                doc_type=doc_type_value,
                                template_type=template_type_value if doc_type_value == "Advisory Circular" else None
                            )
                            
                            return format_results_as_html(format_results_to_html(results_data))
                            
                        finally:
                            try:
                                os.unlink(temp_file_path)
                            except Exception as e:
                                logger.warning(f"Failed to delete temporary file: {str(e)}")
                                
                    except Exception as e:
                        logger.error(f"Error processing document: {str(e)}")
                        return f"""
                            <div style="color: red; padding: 1rem;">
                                ❌ Error processing document: {str(e)}
                                <br><br>
                                Please ensure the file is a valid .docx document and try again.
                            </div>
                        """
                
                def update_template_visibility(doc_type_value):
                    return gr.update(visible=doc_type_value == "Advisory Circular")

                doc_type.change(
                    fn=update_template_visibility,
                    inputs=[doc_type],
                    outputs=[template_type]
                )

                submit_btn.click(
                    fn=process_and_format,
                    inputs=[file_input, doc_type, template_type],
                    outputs=[results]
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
                gr.Markdown(get_readme_content())
    
    return demo