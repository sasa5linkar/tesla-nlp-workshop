"""Anonymous downloads, data-only spaCy loading, and one resident model."""
import gc
import hashlib
import json
import os
import shutil
import threading
import zipfile
from pathlib import Path, PurePosixPath

# Set before importing Hugging Face libraries. Explicit token=False is also passed.
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .registry import EMOTION_LABELS, PRESETS


def cache_root() -> Path:
    # Outside checkout by default, including when installed from a ZIP.
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".cache"))
    root = base / "tesla-nlp-workshop" / "models"
    root.mkdir(parents=True, exist_ok=True)
    return root


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_spacy_data(archive: Path, target: Path) -> Path:
    """Extract only the model-data subfolder, never package Python or entrypoints."""
    with zipfile.ZipFile(archive) as wheel:
        configs = [name for name in wheel.namelist() if name.endswith("/config.cfg")]
        if len(configs) != 1:
            raise ValueError("Unexpected spaCy package layout")
        prefix = configs[0].removesuffix("config.cfg")
        for entry in wheel.infolist():
            if any(ord(char) == 92 for char in entry.orig_filename):
                raise ValueError("Unsafe archive path separator")
            if not entry.filename.startswith(prefix) or entry.is_dir():
                continue
            relative = PurePosixPath(entry.filename[len(prefix):])
            if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative) or ":" in str(relative):
                raise ValueError("Unsafe archive path")
            if relative.suffix.lower() in {".py", ".pyc", ".pyd", ".dll", ".exe", ".pth"}:
                raise ValueError("Executable content inside model data")
            dest = target.joinpath(*relative.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with wheel.open(entry) as source, dest.open("wb") as output:
                shutil.copyfileobj(source, output)
    return target


def download_snapshot(preset, progress):
    from huggingface_hub import snapshot_download
    progress(0.12, desc=f"Preuzimanje javnog modela ({preset.download_gb:.2f} GB), prvi put može potrajati…")
    return Path(snapshot_download(
        preset.repo, revision=preset.revision, token=False,
        cache_dir=str(cache_root() / "hub"),
        allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"],
        ignore_patterns=["*.py", "*.bin", "*.msgpack", "*.h5", "*.onnx"],
        max_workers=2,
    ))


class ModelManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.current = None
        self.loaded = None

    def unload(self):
        self.loaded = None
        self.current = None
        gc.collect()

    def load(self, preset_id, progress):
        if self.current == preset_id:
            return self.loaded
        self.unload()  # Release references before allocating the next model.
        import torch
        torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
        preset = PRESETS[preset_id]
        if preset.kind == "spacy":
            from huggingface_hub import hf_hub_download
            import spacy
            import spacy_transformers  # noqa: F401 - official component registration
            progress(0.12, desc="Preuzimanje JuDig modela (2,13 GB), bez instaliranja koda iz paketa…")
            archive = Path(hf_hub_download(
                preset.repo, preset.filename, revision=preset.revision, token=False,
                cache_dir=str(cache_root() / "hub"),
            ))
            model_dir = cache_root() / ("judig-" + preset.revision)
            marker = model_dir / ".complete"
            if not marker.exists():
                progress(0.35, desc="Provera SHA-256 i izdvajanje podataka…")
                if file_hash(archive) != preset.sha256:
                    raise ValueError("Model checksum mismatch")
                extract_spacy_data(archive, model_dir)
                marker.write_text(preset.sha256, encoding="ascii")
            progress(0.50, desc="Učitavanje JuDig modela u CPU memoriju…")
            spacy.require_cpu()
            # Use the official inference implementation and published KB/weights.
            # The model package's custom training/evaluation Python is not executed.
            options = {"config": {"components": {"entity_linker": {
                "scorer": {"@scorers": "spacy.entity_linker_scorer.v1"},
            }}}} if preset.full_linker else {"exclude": ["entity_linker"]}
            model = spacy.load(model_dir, **options)
            loaded = {"model": model}
        else:
            from transformers import AutoModelForSequenceClassification, AutoModelForSeq2SeqLM, AutoTokenizer
            folder = download_snapshot(preset, progress)
            progress(0.50, desc="Učitavanje modela u CPU memoriju…")
            tokenizer = AutoTokenizer.from_pretrained(folder, local_files_only=True, trust_remote_code=False)
            cls = AutoModelForSequenceClassification if preset.kind == "emotion" else AutoModelForSeq2SeqLM
            model = cls.from_pretrained(folder, local_files_only=True, trust_remote_code=False, use_safetensors=True).to("cpu").eval()
            loaded = {"model": model, "tokenizer": tokenizer}
            if preset.kind == "emotion":
                labels = tuple(model.config.id2label[i] for i in range(model.config.num_labels))
                if labels != EMOTION_LABELS or model.config.problem_type != "multi_label_classification":
                    raise ValueError("Unexpected emotion label contract")
                thresholds = json.loads((folder / "thresholds.json").read_text(encoding="utf-8"))
                values = thresholds["thresholds"]
                if len(values) != len(labels) or not all(0 <= float(v) <= 1 for v in values):
                    raise ValueError("Invalid published thresholds")
                loaded["thresholds"] = values
        self.loaded, self.current = loaded, preset_id
        return loaded


MANAGER = ModelManager()
