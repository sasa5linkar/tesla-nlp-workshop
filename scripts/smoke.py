"""Actual CPU model tests; only built-in fictional examples are written to the report."""
import json
import platform
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workshop.adapters import analyze
from workshop.inputs import InputError
from workshop.models import MANAGER
from workshop.ui import EMOTION_EXAMPLES, EXAMPLES, SUMMARY_EXAMPLES

reports = []
small = "--small" in sys.argv
report_path = Path(__file__).resolve().parents[1] / "docs" / ("runtime-small-results.json" if small else "runtime-results.json")
if "--resume" in sys.argv and report_path.exists():
    reports = json.loads(report_path.read_text(encoding="utf-8"))["results"]
completed = Counter(item.get("task") for item in reports if item["passed"] and "task" in item)
seen = Counter()


def save():
    dest = report_path
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps({"platform": platform.platform(), "python": platform.python_version(), "results": reports}, ensure_ascii=False, indent=2), encoding="utf-8")


cases = [("emotion", "emotion", EMOTION_EXAMPLES[:1]), ("summary", "summary", SUMMARY_EXAMPLES)] if small else [
    ("ner", "judig", EXAMPLES), ("pos", "judig", EXAMPLES),
    ("emotion", "emotion", EMOTION_EXAMPLES), ("summary", "summary", SUMMARY_EXAMPLES),
    ("ner", "judig", EXAMPLES[:1]),
]
for task, preset, examples in cases:
    for text in examples:
        seen[task] += 1
        if seen[task] <= completed[task]:
            print("ALREADY PASSED", task, seen[task], flush=True)
            continue
        print("RUN", task, preset, "cyrillic" if "Б" in text or "П" in text else "latin", flush=True)
        try:
            result = analyze(task, preset, text)
            assert result["text"] == text and result["rows"]
            if task == "summary":
                assert result["manual_review_required"] is True
            for entity in result["entities"]:
                assert text[entity["start"]:entity["end"]] == entity["text"]
            reports.append({"passed": True, **result})
            print("PASS", result["timing"], result["process_rss_mb"], flush=True)
        except Exception as exc:
            reports.append({"passed": False, "task": task, "error": type(exc).__name__, "detail": str(exc)})
            print("FAIL", task, type(exc).__name__, str(exc), flush=True)
        save()
    if task in {"emotion", "summary"}:
        if any(item.get("test") == task + "_oversized" and item["passed"] for item in reports):
            continue
        try:
            analyze(task, preset, "reč " * 1200)
            reports.append({"passed": False, "test": task + "_oversized", "error": "accepted oversized input"})
        except InputError:
            reports.append({"passed": True, "test": task + "_oversized"})
        save()

MANAGER.unload()
if any(not item["passed"] for item in reports):
    sys.exit(1)
