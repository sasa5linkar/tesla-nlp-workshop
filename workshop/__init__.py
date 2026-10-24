"""Local Serbian NLP workshop. Importing this package does not load a model."""
import os

# Precede Gradio, spaCy and Transformers imports, including direct UI imports.
# This application runs only PyTorch; avoid initializing unused TF/Flax runtimes.
os.environ["USE_TF"] = "0"
os.environ["USE_FLAX"] = "0"
os.environ["USE_TORCH"] = "1"
