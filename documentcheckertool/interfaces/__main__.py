import argparse

from gradio_ui import create_interface

from documentcheckertool.logging_config import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Document Checker Gradio UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Set up logging based on debug flag
    setup_logging(debug=args.debug)

    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
