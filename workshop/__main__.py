import argparse

from . import models  # noqa: F401 - configure privacy before importing Gradio
from .ui import build_app


def main():
    parser = argparse.ArgumentParser(description="Lokalna Tesla NLP radionica")
    parser.add_argument("--experiments", action="store_true", help="Prikaži dodatne kartice, uključujući emocije i eksperimentalni sažetak")
    args = parser.parse_args()
    app = build_app(experiments=args.experiments)
    app.launch(
        server_name="127.0.0.1", server_port=7860, share=False,
        inbrowser=False, show_error=False,
        max_file_size="48kb", quiet=True,
        enable_monitoring=False, footer_links=[],
    )


if __name__ == "__main__":
    main()
