from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    id: str
    title: str
    repo: str
    revision: str
    license: str
    kind: str
    limit: int
    download_gb: float
    filename: str = ""
    sha256: str = ""


PRESETS = {
    "judig": Preset(
        "judig", "JuDig2026 · NER, vrste reči i leme · 2,13 GB",
        "Tanor/sr_judig2026_teslaxlm", "259e37f6f9bec66baa51e28079cfdc777010d344",
        "CC-BY-SA-4.0", "spacy", 3000, 2.13,
        "sr_judig2026_teslaxlm-1.0.0-py3-none-any.whl",
        "769468d04013326ca820ed626cf04f8c89cd050d0faa9539eaa439921b389198",
    ),
    "emotion": Preset(
        "emotion", "TeslaXLM · osam emocija · 2,24 GB",
        "te-sla/serbian-emotion-teslaxlm", "3be268fae557df0a258150207813d993dc9551a2",
        "CC-BY-SA-4.0", "emotion", 128, 2.24,
    ),
    "summary": Preset(
        "summary", "PiloT5 · kratak sažetak · 0,99 GB",
        "te-sla/pilot5-sumarizacija", "c9bac5bb79ecdd585a763ed5fe64abd9800bceea",
        "CC-BY-4.0", "summary", 512, 0.99,
    ),
}
TASK_PRESETS = {"ner": ["judig"], "pos": ["judig"], "emotion": ["emotion"], "summary": ["summary"]}
EMOTION_LABELS = ("anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust")
