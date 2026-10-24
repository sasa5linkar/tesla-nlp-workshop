import csv
import json
from html.parser import HTMLParser

import httpx
import pytest

from workshop import coordinates
from workshop.workshop_exports import collect_annotations, export_workshop, render_coordinate_map, render_document

REAL_HTTPX_CLIENT = httpx.Client


@pytest.fixture
def result():
    import spacy
    from spacy.tokens import Span

    nlp = spacy.blank("sr")
    nlp.add_pipe("sentencizer")
    doc = nlp('=SUM(1)\tBeograd <script>alert("x")</script>.\nJoš jedan red. ')
    start = next(token.i for token in doc if token.text == "Beograd")
    doc.ents = [Span(doc, start, start + 1, label="LOC", kb_id="Q3711")]
    for token in doc:
        token.lemma_ = token.text
        token.pos_ = "X"
    data = {"text": doc.text, "model": "public/example", "revision": "abc123", "model_license": "MIT", "task": "workshop"}
    collect_annotations(doc, data, nel_enabled=True)
    return data


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.source = ""
        self.links = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == "pre" and attrs.get("id") == "source":
            self.inside = True
        if tag == "a":
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "pre":
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.source += data


def test_exports_preserve_source_offsets_and_reversible_excel_forms(result, tmp_path):
    json_path, tsv_path, html_path = export_workshop(result, tmp_path)
    assert json.loads(open(json_path, encoding="utf-8").read()) == result
    with open(tsv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert any(row["excel_escaped_fields"] for row in rows)
    for row, original in zip(rows, result["rows"], strict=True):
        for key in filter(None, row["excel_escaped_fields"].split("|")):
            assert row[key].startswith("'")
            row[key] = row[key][1:]
        assert row["form"] == original["form"]
        assert row["source_text"] == original["source_text"]
        assert result["text"][int(row["start"]):int(row["end"])] == row["form"]
        assert row["document_id"] == result["document_id"]
        assert all(row[key] == "" for key in ["corrected_lemma", "corrected_pos", "corrected_ner", "corrected_qid"])
    assert "".join(row["form"] + row["whitespace"] for row in rows) == result["text"]
    assert rows[0]["source_text"] == result["text"]
    parser = SourceParser()
    parser.feed(open(html_path, encoding="utf-8").read())
    assert parser.source == result["text"]
    assert "script" not in parser.tags
    assert "https://www.wikidata.org/wiki/Q3711" in parser.links
    for sentence in result["sentences"]:
        assert result["text"][sentence["start"]:sentence["end"]] == sentence["text"]


@pytest.mark.parametrize("qid", ["NIL", "", "Q0", "Q01", "Q-1", "Q3711\" onclick=\"bad", "https://evil.test", "Q٣"])
def test_invalid_qids_are_never_linked(result, qid):
    result["entities"][0]["kb_id"] = qid
    result["entities"][0]["qid"] = qid
    parser = SourceParser()
    parser.feed(render_document(result))
    assert not parser.links
    assert coordinates.location_qids(result) == []


def test_no_entities_and_no_coordinates(result, tmp_path):
    result["entities"] = []
    assert "Nema potvrđenih koordinata" in render_coordinate_map(result)
    assert export_workshop(result, tmp_path)
    parser = SourceParser()
    parser.feed(render_document(result))
    assert parser.source == result["text"] and not parser.links


def test_annotation_offsets_fail_closed(result):
    result["entities"][0]["end"] += 1
    with pytest.raises(ValueError, match="offsets"):
        render_document(result)


def wd_entity(qid="Q3711", latitude=44.8, longitude=20.47, globe="http://www.wikidata.org/entity/Q2"):
    return {"id": qid, "claims": {"P625": [{"rank": "normal", "mainsnak": {
        "snaktype": "value", "datavalue": {"value": {"latitude": latitude, "longitude": longitude, "globe": globe}},
    }}]}}


def mock_wikidata(monkeypatch, handler):
    coordinates._CACHE.clear()
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: REAL_HTTPX_CLIENT(transport=httpx.MockTransport(handler), **kwargs))


def test_coordinate_lookup_sends_only_bounded_qids_and_caches(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.host == "www.wikidata.org"
        assert set(request.url.params) == {"action", "ids", "props", "format"}
        ids = request.url.params["ids"].split("|")
        assert len(ids) <= 20 and all(coordinates.valid_qid(qid) for qid in ids)
        return httpx.Response(200, json={"entities": {qid: wd_entity(qid) for qid in ids}})

    mock_wikidata(monkeypatch, handler)
    data = coordinates.lookup_coordinates([f"Q{i}" for i in range(1, 30)] + ["NIL", "private input"])
    assert len(data["points"]) == 20 and data["omitted_count"] == 9
    coordinates.lookup_coordinates(data["requested_qids"])
    assert len(requests) == 1
    assert all(point["source"].startswith("https://www.wikidata.org/wiki/Q") for point in data["points"])


@pytest.mark.parametrize("changes", [{"latitude": 91}, {"longitude": 181}, {"globe": "http://www.wikidata.org/entity/Q405"}])
def test_rejects_invalid_or_non_earth_coordinates(monkeypatch, changes):
    mock_wikidata(monkeypatch, lambda request: httpx.Response(200, json={"entities": {"Q3711": wd_entity(**changes)}}))
    assert coordinates.lookup_coordinates(["Q3711"])["points"] == []


def test_missing_coordinates_and_http_failure(monkeypatch):
    mock_wikidata(monkeypatch, lambda request: httpx.Response(200, json={"entities": {"Q3711": {"id": "Q3711", "missing": ""}}}))
    assert coordinates.lookup_coordinates(["Q3711"])["without_coordinates"] == ["Q3711"]
    coordinates._CACHE.clear()
    mock_wikidata(monkeypatch, lambda request: httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        coordinates.lookup_coordinates(["Q3711"])


def test_coordinate_response_size_and_cache_bounds(monkeypatch):
    mock_wikidata(monkeypatch, lambda request: httpx.Response(200, json={"entities": {"Q3711": wd_entity()}}))
    monkeypatch.setattr(coordinates, "MAX_RESPONSE_BYTES", 10)
    with pytest.raises(ValueError, match="limits"):
        coordinates.lookup_coordinates(["Q3711"])
    assert not coordinates._CACHE


def test_coordinate_cache_expires_and_has_fixed_capacity(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"entities": {qid: wd_entity(qid) for qid in request.url.params["ids"].split("|")}})

    mock_wikidata(monkeypatch, handler)
    monkeypatch.setattr(coordinates, "CACHE_SIZE", 2)
    coordinates.lookup_coordinates(["Q1", "Q2", "Q3"])
    assert len(coordinates._CACHE) == 2
    coordinates._CACHE["Q3"] = (-coordinates.CACHE_TTL, coordinates._CACHE["Q3"][1])
    coordinates.lookup_coordinates(["Q3"])
    assert len(calls) == 2


def test_nonfinite_coordinates_are_rejected():
    assert coordinates._earth_point(wd_entity(latitude=float("nan"))) is None
    assert coordinates._earth_point(wd_entity(longitude=float("inf"))) is None


def test_map_uses_only_returned_location_coordinates(result):
    result["coordinate_lookup"] = {"points": [
        {"qid": "Q3711", "latitude": 44.8, "longitude": 20.47, "retrieved_at": "2026-10-24"},
        {"qid": "Q9036", "latitude": 0, "longitude": 0},
    ]}
    markup = render_coordinate_map(result)
    assert 'data-qid="Q3711" data-latitude="44.8" data-longitude="20.47"' in markup
    assert 'data-qid="Q9036"' not in markup
    assert "Wikidata P625 (CC0)" in markup and "OpenStreetMap (internet)" in markup
    assert "<script" not in markup and "<iframe" not in markup


def test_coordinate_action_requires_consent_and_matching_source(result, monkeypatch):
    from workshop import workshop_ui
    published = {"source": (result["text"], "judig_full"), "result": result}
    monkeypatch.setattr(workshop_ui, "lookup_coordinates", lambda *args: pytest.fail("no request without consent"))
    denied = workshop_ui.compute_coordinates(published, result["text"], "judig_full", False)
    assert denied["result"]["text"] == result["text"]
    assert "Nijedan zahtev" in denied["result"]["coordinate_lookup"]["error"]
    stale = workshop_ui.publish_workshop(published, "changed", "judig_full")
    assert stale[6:9] == (None, None, None) and stale[-1] is None
    assert "error" in workshop_ui.compute_coordinates(published, "changed", "judig_full", True)


def test_default_ui_omits_experiments_and_optional_ui_retains_them(monkeypatch):
    from workshop.models import MANAGER
    from workshop.ui import build_app
    monkeypatch.setattr(MANAGER, "load", lambda *args: pytest.fail("no eager models"))
    for experiments, expected in [(False, 1), (True, 5)]:
        app = build_app(experiments=experiments)
        tabs = [component["props"]["label"] for component in app.config["components"] if component["type"] == "tabitem"]
        assert len(tabs) == expected
        assert "Radionica" in tabs[0]
        assert any("Sažetak" in tab for tab in tabs) is experiments
