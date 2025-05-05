import argparse
import logging
from gradio_ui import create_interface

def main():
    parser = argparse.ArgumentParser(description="Document Checker Gradio UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
