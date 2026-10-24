from . import models  # noqa: F401 - configure privacy before importing Gradio
from .ui import build_app


def main():
    app = build_app()
    app.launch(
        server_name="127.0.0.1", server_port=7860, share=False,
        inbrowser=False, show_error=False,
        max_file_size="48kb", quiet=True,
        enable_monitoring=False, footer_links=[],
    )


if __name__ == "__main__":
    main()
