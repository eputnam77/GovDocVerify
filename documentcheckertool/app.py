import gradio as gr
import argparse
import sys
from pathlib import Path
from document_checker import FAADocumentChecker
from interfaces.gradio_ui import create_interface
from utils.formatting import format_results_to_html
import logging

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = [
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

def process_document(file_path: str, doc_type: str) -> str:
    """Process a document and return formatted results."""
    checker = FAADocumentChecker()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        results = checker.run_all_document_checks(content, doc_type)
        return format_results_to_html(results)
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return f"Error processing document: {str(e)}"

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='FAA Document Checker')
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('--file', type=str, help='Path to document file')
    parser.add_argument('--type', type=str, choices=DOCUMENT_TYPES,
                      help='Document type')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=7860, help='Server port')
    
    args = parser.parse_args()
    
    if args.cli:
        if not args.file or not args.type:
            print("Error: --file and --type are required in CLI mode")
            sys.exit(1)
        
        results = process_document(args.file, args.type)
        print(results)
    else:
        interface = create_interface()
        interface.launch(
            debug=args.debug,
            server_name=args.host,
            server_port=args.port,
            show_error=True,
            share=False
        )

if __name__ == "__main__":
    main()
