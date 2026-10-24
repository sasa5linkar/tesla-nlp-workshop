import csv
import json
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pytest

from workshop.adapters import analyze, check_token_limit
from workshop.exports import export_result
from workshop.inputs import InputError, MAX_CHARS, read_txt, validate_text
from workshop.models import MANAGER, extract_spacy_data


@pytest.mark.parametrize("text", ["", " \n\t", "x" * (MAX_CHARS + 1), "abc\x00def"])
def test_reject_input_without_model_download(text, monkeypatch):
    monkeypatch.setattr(MANAGER, "load", lambda *args: pytest.fail("must validate before downloading"))
    with pytest.raises(InputError):
        analyze("ner", "judig", text)


def test_unicode_upload_and_exports(tmp_path):
    text = "Ana Krstić, Štrbac, čćđšž ČĆĐŠŽ — Београд\nDrugi red."
    txt = tmp_path / "primer.txt"
    txt.write_text(text, encoding="utf-8-sig", newline="")
    assert read_txt(txt) == text == validate_text(text)
    result = {"text": text, "rows": [{"token": "=1+2"}, {"token": text}]}
    json_path, tsv_path = export_result(result, tmp_path / "export")
    assert json.loads(open(json_path, encoding="utf-8").read()) == result
    with open(tsv_path, encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert rows[0]["token"] == "'=1+2"
    assert rows[1]["token"] == text


def test_invalid_txt(tmp_path):
    path = tmp_path / "input.txt"
    path.write_bytes(b"\xff\xfeinvalid")
    with pytest.raises(InputError, match="UTF-8"):
        read_txt(path)
    path.write_bytes(b"a" * 48_001)
    with pytest.raises(InputError, match="48 KB"):
        read_txt(path)


def test_data_only_extraction(tmp_path):
    wheel = tmp_path / "fake.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("package/__init__.py", "raise RuntimeError('must never execute')")
        archive.writestr("package/model/config.cfg", "[nlp]")
        archive.writestr("package/model/vocab/strings.json", "[]")
    result = extract_spacy_data(wheel, tmp_path / "model")
    assert (result / "config.cfg").exists()
    assert not list(result.rglob("*.py"))


@pytest.mark.parametrize("unsafe", ["../escape", "nested/../../escape", "evil.py", "x\\escape", "C:escape"])
def test_unsafe_archive_rejected(tmp_path, unsafe):
    wheel = tmp_path / "unsafe.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("package/model/config.cfg", "[nlp]")
        info = zipfile.ZipInfo("package/model/placeholder")
        info.filename = "package/model/" + unsafe
        archive.writestr(info, "bad")
    with pytest.raises(ValueError):
        extract_spacy_data(wheel, tmp_path / "model")


def test_token_limit_never_truncates():
    import torch
    def tokenizer(text, **kwargs):
        assert kwargs["truncation"] is False
        return {"input_ids": torch.ones((1, len(text)), dtype=torch.long)}
    assert check_token_limit(tokenizer, "abc", 3)[1] == 3
    with pytest.raises(InputError, match="ništa nije odsečeno"):
        check_token_limit(tokenizer, "abcd", 3)


def test_errors_clear_old_exports_and_do_not_leak_text(monkeypatch):
    from workshop import ui
    secret = "PRIVATE_SENTINEL"
    def fail(*args, **kwargs):
        raise RuntimeError(secret)
    monkeypatch.setattr(ui, "analyze", fail)
    outputs = ui.run_task("ner", secret, "judig")
    assert secret not in str(outputs)
    assert outputs[-2:] == (None, None)
    assert "RuntimeError" in outputs[3]


def test_network_failure_is_visible_and_retryable(monkeypatch):
    from workshop import ui
    monkeypatch.setattr(ui, "analyze", lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError("private text")))
    outputs = ui.run_task("emotion", "Primer", "emotion")
    assert "ConnectionError" in outputs[3] and "private text" not in outputs[3]
    assert outputs[-1] is None


def test_ui_builds_without_loading_models(monkeypatch):
    from workshop.ui import build_app
    monkeypatch.setattr(MANAGER, "load", lambda *args: pytest.fail("eager model load"))
    app = build_app()
    assert sum(component.get("type") == "tabitem" for component in app.config["components"]) == 4
    assert app.enable_queue


def test_empty_result_dataframe_update_is_valid():
    import gradio as gr
    from workshop.ui import cleared
    update = cleared()[1]
    frame = gr.Dataframe(**{key: value for key, value in update.items() if key != "__type__"})
    assert frame.headers == ["Rezultat"]
