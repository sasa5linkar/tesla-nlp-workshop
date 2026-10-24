"""Input coverage, backend selection, SOCKS imports and result-source binding."""
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from workshop.adapters import analyze
from workshop.inputs import InputError
from workshop.models import MANAGER


@pytest.mark.parametrize("text", ["Градска библиотека.", "Latinica pa ћирилица.", "αβγ"])
def test_summary_rejects_other_scripts_before_loading(text, monkeypatch):
    monkeypatch.setattr(MANAGER, "load", lambda *args: pytest.fail("no model download"))
    with pytest.raises(InputError, match="latin"):
        analyze("summary", "summary", text)


def summary_stub(monkeypatch, ids):
    import torch

    class Tokenizer:
        unk_token_id = 0

        def __call__(self, text, **kwargs):
            assert kwargs["truncation"] is False
            return {"input_ids": torch.tensor([ids])}

        def decode(self, *args, **kwargs):
            return "Probni sažetak."

    def generate(**kwargs):
        assert 0 not in kwargs["input_ids"]
        return [[2, 1]]

    loaded = {"tokenizer": Tokenizer(), "model": SimpleNamespace(generate=generate)}
    monkeypatch.setattr(MANAGER, "load", lambda *args: loaded)


def test_summary_rejects_unknown_token_before_generation(monkeypatch):
    summary_stub(monkeypatch, [2, 0, 1])
    with pytest.raises(InputError, match="nepoznat token"):
        analyze("summary", "summary", "Biblioteka 🧪.")


def test_latin_summary_preserves_source_and_requires_review_in_exports(monkeypatch, tmp_path):
    from workshop.exports import export_result

    summary_stub(monkeypatch, [2, 3, 1])
    text = "Čitaonica radi. Članovi dolaze subotom."
    result = analyze("summary", "summary", text)
    assert result["text"] == text
    assert result["manual_review_required"] is True
    assert result["rows"][0]["manual_review_required"] is True
    assert "izmisliti" in result["explanation"]
    json_path, tsv_path = export_result(result, tmp_path)
    assert json.loads(open(json_path, encoding="utf-8").read())["manual_review_required"] is True
    assert "manual_review_required" in open(tsv_path, encoding="utf-8-sig").read()


@pytest.mark.parametrize("current", [
    ("summary", "Novi tekst", "summary"),
    ("emotion", "Izvorni tekst", "emotion"),
    ("summary", "Izvorni tekst", "other"),
])
def test_edit_during_inference_cannot_restore_stale_exports(monkeypatch, current):
    from workshop import ui

    old_outputs = (None, {}, "Old summary", "Done", "old.json", "old.tsv")
    monkeypatch.setattr(ui, "run_task", lambda *args: old_outputs)
    completed = ui.compute_task("summary", "Izvorni tekst", "summary")
    assert ui.publish_task(completed, "summary", "Izvorni tekst", "summary") == old_outputs
    outputs = ui.publish_task(completed, *current)
    assert outputs[2] == "" and outputs[-2:] == (None, None)
    assert "promenjen" in outputs[3]


def test_summary_examples_are_latin_only():
    from workshop.inputs import validate_summary_text
    from workshop.ui import SUMMARY_EXAMPLES

    assert SUMMARY_EXAMPLES
    for text in SUMMARY_EXAMPLES:
        validate_summary_text(text)


def test_backend_flags_precede_third_party_imports():
    env = {**os.environ, "USE_TF": "1", "USE_FLAX": "1", "USE_TORCH": "0"}
    code = """
import workshop
import sys
assert not any(name in sys.modules for name in ('transformers', 'spacy', 'gradio'))
from transformers.utils import is_tf_available, is_flax_available, is_torch_available
assert not is_tf_available() and not is_flax_available() and is_torch_available()
assert 'tensorflow' not in sys.modules and 'flax' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=60)


def test_gradio_import_supports_configured_socks_proxy():
    # Constructor/import only: this test does not connect to the proxy or alter
    # the parent process's network configuration.
    env = {**os.environ, "ALL_PROXY": "socks5://127.0.0.1:9"}
    code = """
import workshop
import socks
import socksio
import httpx
import gradio
with httpx.Client(proxy='socks5://127.0.0.1:9'):
    pass
"""
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=60)
