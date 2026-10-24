"""Actual pinned full-NEL CPU execution and filesystem exports; fictional text only."""
import argparse
import csv
import json
import platform
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workshop.adapters import analyze
from workshop.coordinates import location_qids, lookup_coordinates
from workshop.models import MANAGER
from workshop.workshop_exports import export_workshop
from workshop.workshop_ui import WORKSHOP_EXAMPLES

parser = argparse.ArgumentParser()
parser.add_argument("--coordinates", action="store_true", help="Explicitly query only predicted location QIDs on Wikidata")
args = parser.parse_args()


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_source = False
        self.text = ""
        self.map_qids = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "pre" and attributes.get("id") == "source":
            self.in_source = True
        if tag == "g" and "data-qid" in attributes:
            self.map_qids.append(attributes["data-qid"])

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_source = False

    def handle_data(self, data):
        if self.in_source:
            self.text += data


result = analyze("workshop", "judig_full", WORKSHOP_EXAMPLES[0])
assert result["nel_enabled"] and result["sentences"] and result["entities"]
assert all(result["text"][row["start"]:row["end"]] == row["form"] for row in result["rows"])
assert "".join(row["form"] + row["whitespace"] for row in result["rows"]) == result["text"]
if args.coordinates:
    result["coordinate_lookup"] = lookup_coordinates(location_qids(result))
    assert result["coordinate_lookup"]["points"], "No live coordinates returned"
with tempfile.TemporaryDirectory(prefix="tesla-workshop-smoke-") as temporary:
    json_path, tsv_path, html_path = export_workshop(result, temporary)
    assert json.loads(Path(json_path).read_text(encoding="utf-8")) == result
    with open(tsv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(rows) == len(result["rows"])
    assert rows[0]["source_text"] == result["text"]
    parsed = SourceParser()
    parsed.feed(Path(html_path).read_text(encoding="utf-8"))
    assert parsed.text == result["text"]
    assert set(parsed.map_qids) == {point["qid"] for point in result.get("coordinate_lookup", {}).get("points", [])}
report = {
    "platform": platform.platform(), "python": platform.python_version(),
    "passed": True, "checks": ["actual full NEL", "token/source offsets", "sentence segmentation", "JSON/TSV/HTML filesystem exports", "parsed HTML source correspondence", "map/source QID correspondence"],
    "coordinates_requested": args.coordinates, "result": result,
}
path = Path(__file__).resolve().parents[1] / "docs" / "workshop-runtime-results.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"passed": True, "entities": result["entities"], "timing": result["timing"], "process_rss_mb": result["process_rss_mb"], "coordinate_points": len(result.get("coordinate_lookup", {}).get("points", []))}, ensure_ascii=True), flush=True)
MANAGER.unload()
