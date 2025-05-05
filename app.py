import gradio as gr
from documentcheckertool.interfaces.gradio_ui import create_interface
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create and launch the interface
demo = create_interface()

if __name__ == "__main__":
    demo.launch(
        show_error=True,
        server_name="0.0.0.0",
        server_port=7860
    )
