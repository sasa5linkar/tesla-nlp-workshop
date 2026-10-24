import csv
import json
import tempfile
from pathlib import Path


def spreadsheet_safe(value):
    # TSV is often opened by Excel. Prevent an input token becoming a formula.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_result(result, directory=None):
    root = Path(directory or tempfile.mkdtemp(prefix="tesla-nlp-export-"))
    root.mkdir(parents=True, exist_ok=True)
    json_path, tsv_path = root / "rezultat.json", root / "rezultat.tsv"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = result["rows"]
    columns = list(rows[0]) if rows else ["text", "model", "revision"]
    with tsv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: spreadsheet_safe(value) for key, value in row.items()})
    return str(json_path), str(tsv_path)
