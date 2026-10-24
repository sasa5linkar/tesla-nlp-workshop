from pathlib import Path
import unicodedata

MAX_CHARS = 12_000
MAX_FILE_BYTES = 48_000


class InputError(ValueError):
    """Safe user-facing validation error; never contains the input text."""


def validate_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise InputError("Unesite tekst za analizu.")
    if len(text) > MAX_CHARS:
        raise InputError(f"Tekst ima {len(text)} znakova; granica je {MAX_CHARS}. Podelite ga na kraće odlomke.")
    if "\x00" in text:
        raise InputError("Tekst sadrži nedozvoljeni NUL znak. Koristite običan UTF-8 TXT.")
    return text


def validate_summary_text(text: str) -> None:
    """Reject unsupported scripts without modifying the original input."""
    if any("CYRILLIC" in unicodedata.name(char, "") for char in text):
        raise InputError(
            "Eksperimentalni sažetak podržava samo latinicu. Ćirilica nije podržana; "
            "tekst nije preslovljen. Unesite zaseban latinični tekst."
        )
    if any(char.isalpha() and "LATIN" not in unicodedata.name(char, "") for char in text):
        raise InputError("Eksperimentalni sažetak podržava samo latinična slova. Tekst nije izmenjen.")


def read_txt(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() != ".txt":
        raise InputError("Izaberite TXT datoteku kodiranu kao UTF-8.")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise InputError("TXT je veći od 48 KB. Podelite tekst na kraće odlomke.")
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("TXT nije UTF-8. Sačuvajte ga kao UTF-8 pa pokušajte ponovo.") from None
    return validate_text(text)
