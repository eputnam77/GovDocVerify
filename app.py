import gradio as gr
import logging
import re
from docx import Document
import io
import traceback

def heading_title_check(paragraphs, required_headings):
    headings_found = []
    required_headings_set = set(required_headings)
    
    for para in paragraphs:
        para_strip = para.strip()
        if para_strip in required_headings_set:
            headings_found.append(para_strip)
    
    all_headings_present = set(headings_found) == required_headings_set
    return all_headings_present, headings_found

def acronym_check(paragraphs):
    defined_acronyms = set()
    undefined_acronyms = set()
    acronym_pattern = re.compile(r'(\b[A-Z]{2,}\b)')
    defined_pattern = re.compile(r'(\b\w+\b) \((\b[A-Z]{2,}\b)\)')

    for paragraph in paragraphs:
        defined_matches = defined_pattern.findall(paragraph)
        for full_term, acronym in defined_matches:
            defined_acronyms.add(acronym)

        usage_matches = acronym_pattern.findall(paragraph)
        for acronym in usage_matches:
            if acronym not in defined_acronyms:
                undefined_acronyms.add(acronym)

    return len(undefined_acronyms) == 0, undefined_acronyms

def legal_check(paragraphs):
    incorrect_variations = {
        r"\bUSC\b": "U.S.C.",
        r"\bCFR Part\b": "CFR part",
        r"\bC\.F\.R\.\b": "CFR",
        r"\bWe\b": "The FAA",
        r"\bwe\b": "the FAA",
        r"\bcancelled\b": "canceled",
        r"\bshall\b": "must or will",
        r"\b&\b": "and"
    }
    incorrect_legal_references = []
    
    for paragraph in paragraphs:
        title_14_pattern = r"(?P<prefix>^|[.!?\s])\s*(?P<title>title 14|Title 14)\b"
        matches = re.finditer(title_14_pattern, paragraph)
        
        for match in matches:
            prefix = match.group('prefix')
            current_title = match.group('title')
            if prefix in ('.', '!', '?', '') and current_title.lower() == "title 14":
                if current_title != "Title 14":
                    incorrect_legal_references.append((current_title, "Title 14"))
            elif prefix.isspace() and current_title != "title 14":
                incorrect_legal_references.append((current_title, "title 14"))
        
        for incorrect_pattern, correct_term in incorrect_variations.items():
            matches = re.finditer(incorrect_pattern, paragraph)
            for match in matches:
                incorrect_legal_references.append((match.group(), correct_term))
    
    return len(incorrect_legal_references) == 0, incorrect_legal_references

def table_caption_check(paragraphs, doc_type):
    if doc_type in ["Advisory Circular", "Order"]:
        table_caption_pattern = re.compile(r'^Table\s+([A-Z0-9]+)-([A-Z0-9]+)[\.\s]', re.IGNORECASE)
    else:
        table_caption_pattern = re.compile(r'^Table\s+([A-Z0-9]+)[\.\s]', re.IGNORECASE)
    
    incorrect_captions = []

    for paragraph in paragraphs:
        paragraph_strip = paragraph.strip()
        if paragraph_strip.lower().startswith("table"):
            if not table_caption_pattern.match(paragraph_strip):
                incorrect_captions.append(paragraph_strip)

    return len(incorrect_captions) == 0, incorrect_captions

def figure_caption_check(paragraphs, doc_type):
    if doc_type in ["Advisory Circular", "Order"]:
        figure_caption_pattern = re.compile(r'^Figure\s+([A-Z0-9]+)-([A-Z0-9]+)[\.\s]', re.IGNORECASE)
    else:
        figure_caption_pattern = re.compile(r'^Figure\s+([A-Z0-9]+)[\.\s]', re.IGNORECASE)
    
    incorrect_fig_captions = []
    for paragraph in paragraphs:
        paragraph_strip = paragraph.strip()
        if paragraph_strip.lower().startswith("figure"):
            if not figure_caption_pattern.match(paragraph_strip):
                incorrect_fig_captions.append(paragraph_strip)
                
    return len(incorrect_fig_captions) == 0, incorrect_fig_captions

def table_figure_reference_check(paragraphs, doc_type):
    incorrect_table_figure_references = []
    
    if doc_type in ["Advisory Circular", "Order"]:
        incorrect_table_ref_pattern = re.compile(r'\bTable\s+\d+(?!-\d+)\b', re.IGNORECASE)
        incorrect_figure_ref_pattern = re.compile(r'\bFigure\s+\d+(?!-\d+)\b', re.IGNORECASE)
    else:
        incorrect_table_ref_pattern = re.compile(r'\bTable\s+\d+(-\d+)?\b', re.IGNORECASE)
        incorrect_figure_ref_pattern = re.compile(r'\bFigure\s+\d+(-\d+)?\b', re.IGNORECASE)
    
    for paragraph in paragraphs:
        paragraph_strip = paragraph.strip()
        starts_with_table_or_figure = paragraph_strip.lower().startswith('table') or paragraph_strip.lower().startswith('figure')
        if not starts_with_table_or_figure:
            incorrect_tables = incorrect_table_ref_pattern.findall(paragraph)
            if incorrect_tables:
                incorrect_table_figure_references.extend(incorrect_tables)
            incorrect_figures = incorrect_figure_ref_pattern.findall(paragraph)
            if incorrect_figures:
                incorrect_table_figure_references.extend(incorrect_figures)
    
    return len(incorrect_table_figure_references) == 0, incorrect_table_figure_references

def document_title_check(doc_path, doc_type):
    incorrect_titles = []
    doc = Document(doc_path)
    
    # Updated pattern to capture titles correctly
    ac_pattern = re.compile(r'AC\s+\d+(?:-\d+)?(?:,|\s)+(.+?)(?=\.|,|$)')
    
    # Define formatting rules for different document types
    formatting_rules = {
        "Advisory Circular": {"italics": True, "quotes": False},
        "Airworthiness Criteria": {"italics": False, "quotes": True},
        "Deviation Memo": {"italics": False, "quotes": True},
        "Exemption": {"italics": False, "quotes": True},
        "Federal Register Notice": {"italics": False, "quotes": True},
        "Handbook/Manual": {"italics": False, "quotes": False},
        "Order": {"italics": False, "quotes": True},
        "Policy Statement": {"italics": False, "quotes": False},
        "Rule": {"italics": False, "quotes": True},
        "Special Condition": {"italics": False, "quotes": True},
        "Technical Standard Order": {"italics": False, "quotes": True},
        "Other": {"italics": False, "quotes": False}
    }
    
    # Get the rules for the current document type
    if doc_type not in formatting_rules:
        raise ValueError(f"Unsupported document type: {doc_type}")
    
    required_format = formatting_rules[doc_type]
    
    for paragraph in doc.paragraphs:
        text = paragraph.text
        matches = ac_pattern.finditer(text)
        
        for match in matches:
            full_match = match.group(0)
            title_text = match.group(1).strip()
            
            # Get the position where the title starts
            title_start = match.start(1)
            
            # Check for any type of quotation marks, including smart quotes
            title_in_quotes = any(q in title_text for q in ['"', "'", '"', '"', ''', '''])
            
            # Check the formatting of the title
            title_is_italicized = False
            current_pos = 0
            for run in paragraph.runs:
                run_length = len(run.text)
                if current_pos <= title_start < current_pos + run_length:
                    relative_pos = title_start - current_pos
                    title_is_italicized = run.italic
                    break
                current_pos += run_length
            
            # Check if formatting matches the required format
            formatting_incorrect = False
            issue_message = []
            
            # Check italics requirement
            if required_format["italics"] and not title_is_italicized:
                formatting_incorrect = True
                issue_message.append("should be italicized")
            elif not required_format["italics"] and title_is_italicized:
                formatting_incorrect = True
                issue_message.append("should not be italicized")
            
            # Check quotes requirement
            if required_format["quotes"] and not title_in_quotes:
                formatting_incorrect = True
                issue_message.append("should be in quotes")
            elif not required_format["quotes"] and title_in_quotes:
                formatting_incorrect = True
                issue_message.append("should not be in quotes")
            
            if formatting_incorrect:
                incorrect_titles.append({
                    'text': full_match,
                    'issue': ', '.join(issue_message)
                })
    
    return len(incorrect_titles) == 0, incorrect_titles

def get_document_checks(doc_type, template_type):
    """Return the required headings and other checks based on document type."""
    document_checks = {
        "Advisory Circular": {
            "Short AC template AC": {
                "required_headings": [
                    "PURPOSE.",
                    "APPLICABILITY.",
                    "CANCELLATION.",
                    "RELATED MATERIAL.",
                    "DEFINITION OF KEY TERMS."
                ]
            },
            "Long AC template AC": {
                "required_headings": [
                    "Purpose.",
                    "Applicability.",
                    "Cancellation.",
                    "Related Material.",
                    "Definition of Key Terms."
                ]
            }
        },
        "Airworthiness Criteria": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Deviation Memo": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Exemption": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Federal Register Notice": {
            "required_headings": [
                "Purpose of This Notice",
                "Audience",
                "Where can I Find This Notice"
            ]
        },
        "Handbook/Manual": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Order": {
            "required_headings": [
                "Purpose of This Order.",
                "Audience.",
                "Where to Find This Order."
            ]
        },
        "Policy Statement": {
            "required_headings": [
                "SUMMARY",
                "CURRENT REGULATORY AND ADVISORY MATERIAL",
                "RELEVANT PAST PRACTICE",
                "POLICY",
                "EFFECT OF POLICY",
                "CONCLUSION"
            ]
        },
        "Rule": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Special Condition": {
            "required_headings": [
                "TBD - Need to research"
            ]
        },
        "Technical Standard Order": {
            "required_headings": [
                "PURPOSE.",
                "APPLICABILITY.",
                "REQUIREMENTS.",
                "MARKING.",
                "APPLICATION DATA REQUIREMENTS.",
                "MANUFACTURER DATA REQUIREMENTS.",
                "FURNISHED DATA REQUIREMENTS.",
                "HOW TO GET REFERENCED DOCUMENTS."
            ]
        },
        "Other": {
            "required_headings": [
                "N/A"
            ]
        }
    }
    
    # Add debugging logs
    logger = logging.getLogger(__name__)
    logger.info(f"Requested document type: {doc_type}")
    logger.info(f"Requested template type: {template_type}")
    
    if doc_type == "Advisory Circular":
        checks = document_checks.get(doc_type, {}).get(template_type, {})
    else:
        checks = document_checks.get(doc_type, {})
    
    logger.info(f"Retrieved checks: {checks}")
    return checks

def double_period_check(paragraphs):
    incorrect_sentences = []

    for paragraph in paragraphs:
        sentences = re.split(r'(?<=[.!?]) +', paragraph)
        for sentence in sentences:
            if sentence.endswith('..'):
                incorrect_sentences.append(sentence.strip())

    return len(incorrect_sentences) == 0, incorrect_sentences

def spacing_check(paragraphs):
    incorrect_spacing = []
    doc_type_pattern = re.compile(r'(?<!\s)(AC|AD|CFR|FAA|N|SFAR)(\d+[-]?\d*)', re.IGNORECASE)
    section_symbol_pattern = re.compile(r'(?<!\s)(§|§§)(\d+\.\d+)', re.IGNORECASE)
    part_number_pattern = re.compile(r'(?<!\s)Part(\d+)', re.IGNORECASE)
    paragraph_pattern = re.compile(r'(?<!\s)(\([a-z](?!\))|\([1-9](?!\)))', re.IGNORECASE)
    double_space_pattern = re.compile(r'\s{2,}')

    for paragraph in paragraphs:
        if doc_type_pattern.search(paragraph) or \
           section_symbol_pattern.search(paragraph) or \
           part_number_pattern.search(paragraph) or \
           paragraph_pattern.search(paragraph) or \
           double_space_pattern.search(paragraph):
            incorrect_spacing.append(paragraph)

    return len(incorrect_spacing) == 0, incorrect_spacing

def check_prohibited_phrases(paragraphs):
    prohibited_phrases = [
        r'\babove\b',
        r'\bbelow\b',
        r'\bthere is\b',
        r'\bthere are\b'
    ]
    issues = []
    for paragraph in paragraphs:
        for phrase in prohibited_phrases:
            if re.search(phrase, paragraph, re.IGNORECASE):
                issues.append((phrase.strip(r'\b'), paragraph.strip()))
    return issues

def check_abbreviation_usage(paragraphs):
    """Check for abbreviation consistency after first definition."""
    abbreviations = {}
    issues = []
    for paragraph in paragraphs:
        # Find definitions like "Federal Aviation Administration (FAA)"
        defined_matches = re.findall(r'\b([A-Za-z &]+)\s+\((\b[A-Z]{2,}\b)\)', paragraph)
        for full_term, acronym in defined_matches:
            if acronym not in abbreviations:
                abbreviations[acronym] = {"full_term": full_term.strip(), "defined": True}
        
        # Check for full term usage after definition
        for acronym, data in abbreviations.items():
            full_term = data["full_term"]
            if full_term in paragraph:
                # Ignore first usage where it's defined
                if data["defined"]:
                    data["defined"] = False  # Mark it as now defined
                else:
                    # Only flag subsequent occurrences
                    issues.append((full_term, acronym, paragraph.strip()))
                    
    return issues

def check_date_formats(paragraphs):
    """Check for inconsistent date formats."""
    date_issues = []
    correct_date_pattern = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b')
    date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')  # MM/DD/YYYY
    for paragraph in paragraphs:
        if date_pattern.search(paragraph):
            dates = date_pattern.findall(paragraph)
            for date in dates:
                if not correct_date_pattern.match(date):
                    date_issues.append((date, paragraph.strip()))
    return date_issues

def check_placeholders(paragraphs):
    """Check for placeholders that should be removed."""
    placeholder_phrases = [
        r'\bTBD\b',
        r'\bTo be determined\b',
        r'\bTo be added\b'
    ]
    issues = []
    for paragraph in paragraphs:
        for phrase in placeholder_phrases:
            if re.search(phrase, paragraph, re.IGNORECASE):
                issues.append((phrase.strip(r'\b'), paragraph.strip()))
    return issues

def process_document(file_obj, doc_type, template_type):
    try:
        doc = Document(file_obj)
        paragraphs = [para.text for para in doc.paragraphs]
        required_headings = get_document_checks(doc_type, template_type).get("required_headings", [])
        
        # Perform each check with `paragraphs` as input
        heading_valid, headings_found = heading_title_check(paragraphs, required_headings)
        acronyms_valid, undefined_acronyms = acronym_check(paragraphs)
        legal_valid, incorrect_legal_references = legal_check(paragraphs)
        table_valid, incorrect_captions = table_caption_check(paragraphs, doc_type)
        figure_valid, incorrect_fig_captions = figure_caption_check(paragraphs, doc_type)
        references_valid, incorrect_table_figure_references = table_figure_reference_check(paragraphs, doc_type)
        title_style_valid, incorrect_titles = document_title_check(file_obj, doc_type) if doc_type in ["Advisory Circular", "Order"] else (True, [])
        double_period_valid, incorrect_sentences = double_period_check(paragraphs)
        spacing_valid, incorrect_spacing = spacing_check(paragraphs)
        date_issues = check_date_formats(paragraphs)  # Pass paragraphs here
        placeholder_issues = check_placeholders(paragraphs)  # Pass paragraphs here
        
        # Format results
        results = format_results_for_gradio(
            heading_valid=heading_valid, headings_found=headings_found,
            acronyms_valid=acronyms_valid, undefined_acronyms=undefined_acronyms,
            legal_valid=legal_valid, incorrect_legal_references=incorrect_legal_references,
            table_valid=table_valid, incorrect_captions=incorrect_captions,
            figure_valid=figure_valid, incorrect_fig_captions=incorrect_fig_captions,
            references_valid=references_valid, incorrect_table_figure_references=incorrect_table_figure_references,
            title_style_valid=title_style_valid, incorrect_titles=incorrect_titles,
            double_period_valid=double_period_valid, incorrect_sentences=incorrect_sentences,
            spacing_valid=spacing_valid, incorrect_spacing=incorrect_spacing,
            date_issues=date_issues,  # Added date_issues
            placeholder_issues=placeholder_issues,  # Added placeholder_issues
            required_headings=required_headings, doc_type=doc_type
        )
        return results
    except Exception as e:
        print(f"Error in process_document: {str(e)}")
        return f"An error occurred while processing the document: {str(e)}"

def format_results_for_gradio(**kwargs):
    """Format the results for display in Gradio."""
    results = []
    results.append("# Document Check Results\n")
    
    # Required Headings Check
    results.append("## Required Headings Check")
    if kwargs['heading_valid']:
        results.append("✅ All required headings are present.\n")
    else:
        missing_headings = set(kwargs['required_headings']) - set(kwargs['headings_found'])
        results.append("❌ Missing Required Headings:")
        for heading in missing_headings:
            results.append(f"- {heading}")
    results.append("")
    
    # Acronym Check
    results.append("## Acronym Check")
    if kwargs['acronyms_valid']:
        results.append("✅ All acronyms are properly defined.\n")
    else:
        results.append("❌ The following acronyms need to be defined at first use:")
        for acronym in kwargs['undefined_acronyms']:
            results.append(f"- {acronym}")
    results.append("")

    # Legal Check
    results.append("## Legal Terminology Check")
    if kwargs['legal_valid']:
        results.append("✅ All legal references are properly formatted.\n")
    else:
        results.append("❌ Incorrect Legal Terminology:")
        for incorrect_term, correct_term in kwargs['incorrect_legal_references']:
            results.append(f"- Use '{correct_term}' instead of '{incorrect_term}'")
    results.append("")
    
    # Table Caption Check
    results.append("## Table Caption Check")
    if kwargs['table_valid']:
        results.append("✅ All table captions are correctly formatted.\n")
    else:
        results.append("❌ Incorrect Table Captions:")
        for caption in kwargs['incorrect_captions']:
            results.append(f"- {caption}")
    results.append("")

    # Figure Caption Check
    results.append("## Figure Caption Check")
    if kwargs['figure_valid']:
        results.append("✅ All figure captions are correctly formatted.\n")
    else:
        results.append("❌ Incorrect Figure Captions:")
        for caption in kwargs['incorrect_fig_captions']:
            results.append(f"- {caption}")
    results.append("")

    # Table and Figure References Check
    results.append("## Table and Figure References Check")
    if kwargs['references_valid']:
        results.append("✅ All table and figure references are correctly formatted.\n")
    else:
        results.append("❌ Incorrect Table/Figure References:")
        for ref in kwargs['incorrect_table_figure_references']:
            results.append(f"- {ref}")
    results.append("")

    # Document Title Style Check
    results.append("## Document Title Style Check")
    if kwargs['title_style_valid']:
        results.append("✅ All document title references are properly styled.\n")
    else:
        results.append("❌ Incorrect Document Title Styling:")
        for title in kwargs['incorrect_titles']:
            results.append(f"- {title['text']}")
            results.append(f"  - Issue: {title['issue']}")
        
        # Add formatting guidance
        formatting_notes = {
            "Advisory Circular": "Document titles should be italicized, not in quotation marks.",
            "Order": "Document titles should be in quotation marks, not italicized.",
            "Federal Register Notice": "Document titles should be in quotation marks, not italicized.",
            "Policy Statement": "Document titles should not have any special formatting (no italics, no quotation marks)."
        }
        
        doc_type = kwargs.get('doc_type', 'Unknown')
        if doc_type in formatting_notes:
            results.append(f"\nNote: {formatting_notes[doc_type]}")
        else:
            results.append("\nNote: Please verify the correct formatting style for this document type.")
    results.append("")

    # Double Period Check
    results.append("## Double Period Check")
    if kwargs['double_period_valid']:
        results.append("✅ No double periods found.\n")
    else:
        results.append("❌ Sentences found with double periods:")
        for sentence in kwargs['incorrect_sentences']:
            results.append(f"- {sentence}")
    results.append("")

    # Spacing Check
    results.append("## Spacing Check")
    if kwargs['spacing_valid']:
        results.append("✅ All spacing is correct.\n")
    else:
        results.append("❌ Incorrect spacing found in:")
        for spacing in kwargs['incorrect_spacing']:
            results.append(f"- {spacing}")
    results.append("")

    # Date Format Consistency
    results.append("## Date Format Consistency")
    if not kwargs['date_issues']:
        results.append("✅ All dates are in the correct format.\n")
    else:
        results.append("❌ Date Format Issues:")
        for date, paragraph in kwargs['date_issues']:
            results.append(f"- Incorrect date format '{date}' in: {paragraph}")
    results.append("")

    # Placeholder Check
    results.append("## Placeholder Check")
    if not kwargs['placeholder_issues']:
        results.append("✅ No future references or placeholders found.\n")
    else:
        results.append("❌ Placeholders Found:")
        for phrase, paragraph in kwargs['placeholder_issues']:
            results.append(f"- Placeholder '{phrase}' in: {paragraph}")
    
    return "\n".join(results)

def process_file(file_obj, doc_type, template_type):
    """Process the uploaded file and return results with error handling."""
    if file_obj is None:
        return "Please upload a document first."
    
    try:
        # Convert bytes to BytesIO object
        doc_bytes = io.BytesIO(file_obj) if isinstance(file_obj, bytes) else io.BytesIO(file_obj.read())
        
        # Process the document
        results = process_document(doc_bytes, doc_type, template_type)
        return results
        
    except Exception as e:
        error_message = f"""An error occurred while processing the document:
        
Error: {str(e)}
Please ensure:
1. The file is a valid Word document (.docx)
2. The file is not corrupted
3. The file is not password protected
Technical details: {str(e)}"""
        print(f"Error processing file: {str(e)}")
        return error_message

# Create the Gradio interface
demo = gr.Blocks(theme='JohnSmith9982/small_and_pretty')

with demo:
    gr.Markdown("# Document Checker Tool")
    gr.Markdown("Upload a Word (docx) document to check for compliance with U.S. federal documentation standards.")
    gr.Markdown("*This tool is still in development and you might get false positives in your results*")
    gr.Markdown("Contact Eric Putnam if you have questions and comments.")
    gr.Markdown("""
    1. Upload a clean (no track changes or comments) Word file.
    2. Choose **Check Document**.""")
    
    document_types = [
        "Advisory Circular", "Airworthiness Criteria", "Deviation Memo", "Exemption", 
        "Federal Register Notice", "Handbook/Manual", "Order", "Policy Statement", 
        "Rule", "Special Condition", "Technical Standard Order", "Other"
    ]
    
    template_types = ["Short AC template AC", "Long AC template AC"]
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload Word Document (.docx)",
                file_types=[".docx"],
                type="binary"
            )
            doc_type = gr.Dropdown(
                choices=document_types,
                label="Document Type",
                value="Advisory Circular"
            )
            template_type = gr.Radio(
                choices=template_types,
                label="Template Type (Only for Advisory Circular)",
                visible=True,
                value="Short AC template AC"
            )
            submit_btn = gr.Button("Check Document", variant="primary")
        
        with gr.Column(scale=2):
            output = gr.Markdown(
                label="Check Results",
                value="Results will appear here after processing..."
            )
    
    # Update template type visibility based on document type
    def update_template_visibility(doc_type):
        return gr.update(visible=doc_type == "Advisory Circular")
    
    doc_type.change(
        fn=update_template_visibility,
        inputs=[doc_type],
        outputs=[template_type]
    )
    
    # Process file when submit button is clicked
    submit_btn.click(
        fn=process_file,
        inputs=[file_input, doc_type, template_type],
        outputs=[output]
    )

# Launch the demo
demo.launch()
