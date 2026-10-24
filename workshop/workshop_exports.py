"""Correction-friendly exports with exact provenance and no external assets."""
import csv
import hashlib
import html
import json
import math
import tempfile
from pathlib import Path

from .coordinates import location_qids, valid_qid
from .exports import spreadsheet_safe


def document_id(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_annotations(doc, result, nel_enabled=False):
    """Extract actual JuDig annotations; offsets are Python Unicode code points."""
    text = result["text"]
    assert doc.text == text
    result["document_id"] = document_id(text)
    result["offset_unit"] = "Unicode code points; zero-based start, exclusive end"
    result["sentences"] = [
        {"sentence_id": index, "start": sent.start_char, "end": sent.end_char, "text": sent.text}
        for index, sent in enumerate(doc.sents, 1)
    ]
    result["entities"] = [
        {"entity_id": f"E{index}", "text": ent.text, "start": ent.start_char, "end": ent.end_char,
         "label": ent.label_, "kb_id": ent.kb_id_, "qid": valid_qid(ent.kb_id_), "score": None}
        for index, ent in enumerate(doc.ents, 1)
    ]
    entity_by_token = {token.i: entity for ent, entity in zip(doc.ents, result["entities"], strict=True) for token in ent}
    rows = []
    for sentence_id, sentence in enumerate(doc.sents, 1):
        for sentence_token_id, token in enumerate(sentence, 1):
            entity = entity_by_token.get(token.i, {})
            rows.append({
                "document_id": result["document_id"], "sentence_id": sentence_id,
                "token_id": token.i + 1, "sentence_token_id": sentence_token_id,
                "start": token.idx, "end": token.idx + len(token), "form": token.text,
                "whitespace": token.whitespace_, "lemma": token.lemma_, "pos": token.pos_, "tag": token.tag_,
                "ner_iob": token.ent_iob_, "ner": token.ent_type_, "entity_id": entity.get("entity_id", ""),
                "kb_id": entity.get("kb_id", ""), "qid": entity.get("qid", ""),
                "corrected_lemma": "", "corrected_pos": "", "corrected_ner": "", "corrected_qid": "", "notes": "",
                "model": result["model"], "revision": result["revision"],
                "source_text": text if not rows else "",
            })
    result["rows"] = rows
    result["nel_enabled"] = nel_enabled
    result["manual_review_required"] = True


def render_coordinate_map(result):
    """Self-contained equirectangular coordinate map; no tiles/scripts/guesses."""
    points = result.get("coordinate_lookup", {}).get("points", [])
    allowed = set(location_qids(result))
    points = [p for p in points if p.get("qid") in allowed
              and type(p.get("latitude")) in (int, float) and type(p.get("longitude")) in (int, float)
              and math.isfinite(p["latitude"]) and math.isfinite(p["longitude"])
              and -90 <= p["latitude"] <= 90 and -180 <= p["longitude"] <= 180]
    if not points:
        return "<p>Nema potvrđenih koordinata za prikaz. Analiza i izvozi ostaju dostupni.</p>"
    names = {}
    for entity in result["entities"]:
        names.setdefault(entity.get("qid"), entity["text"])
    minlon, maxlon = min(p["longitude"] for p in points), max(p["longitude"] for p in points)
    minlat, maxlat = min(p["latitude"] for p in points), max(p["latitude"] for p in points)
    padlon, padlat = max((maxlon - minlon) * .15, .1), max((maxlat - minlat) * .15, .1)
    west, east, south, north = minlon - padlon, maxlon + padlon, minlat - padlat, maxlat + padlat
    parts = ['<figure><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 400" role="img" aria-label="Karta koordinata WGS84" style="width:100%;max-width:900px;background:#edf5fa">']
    for step in range(5):
        x, y = 55 + step * 162.5, 30 + step * 77.5
        lon, lat = west + (east - west) * step / 4, north - (north - south) * step / 4
        parts.append(f'<path d="M{x} 30V340 M55 {y}H705" stroke="#bdcdd8" fill="none"/>')
        parts.append(f'<text x="{x}" y="365" font-size="12" text-anchor="middle">{lon:.3f}° E</text>')
        parts.append(f'<text x="5" y="{y + 4}" font-size="11">{lat:.3f}° N</text>')
    table = []
    for index, point in enumerate(points, 1):
        qid, lat, lon = point["qid"], point["latitude"], point["longitude"]
        x, y = 55 + (lon - west) / (east - west) * 650, 30 + (north - lat) / (north - south) * 310
        name = html.escape(names.get(qid, qid))
        title = html.escape(f"{names.get(qid, qid)} ({qid}): {lat}, {lon}")
        parts.append(f'<g data-qid="{qid}" data-latitude="{lat}" data-longitude="{lon}"><title>{title}</title><circle cx="{x}" cy="{y}" r="7" fill="#b73832"/><text x="{x + 10}" y="{y - 8}" font-size="14">{index}</text></g>')
        table.append(f'<li>{index}. {name} — <a href="https://www.wikidata.org/wiki/{qid}#P625" target="_blank" rel="noopener noreferrer">{qid}, Wikidata P625</a>: {lat:.6f}, {lon:.6f}; <a href="https://www.openstreetmap.org/?mlat={lat}&amp;mlon={lon}#map=12/{lat}/{lon}" target="_blank" rel="noopener noreferrer">OpenStreetMap (internet)</a>. Preuzeto: {html.escape(point.get("retrieved_at", ""))}</li>')
    parts.append('</svg><figcaption>Karta koordinata WGS84, ravna projekcija bez geografske podloge. Brojevi odgovaraju spisku; bliske tačke mogu se preklopiti. Izvor: Wikidata P625 (CC0). Veza modela sa QID-om zahteva ručnu proveru.</figcaption><ol>')
    parts.extend(table)
    parts.append('</ol><p>Nema spoljnih skripti, slika ni pločica karte; prikaz radi bez interneta. Klik na Wikidata ili OpenStreetMap otvara spoljni sajt i šalje tom sajtu uobičajene mrežne podatke.</p></figure>')
    return "".join(parts)


def annotated_source(result):
    text, cursor, parts = result["text"], 0, []
    for entity in sorted(result["entities"], key=lambda ent: ent["start"]):
        start, end = entity["start"], entity["end"]
        if not 0 <= cursor <= start < end <= len(text) or text[start:end] != entity["text"]:
            raise ValueError("Entity offsets do not match source")
        parts.append(html.escape(text[cursor:start]))
        value = html.escape(text[start:end])
        qid = valid_qid(entity.get("qid"))
        if qid:
            value = f'<a href="https://www.wikidata.org/wiki/{qid}" target="_blank" rel="noopener noreferrer">{value}</a>'
        parts.append(f'<mark data-start="{start}" data-end="{end}" data-entity-id="{html.escape(entity["entity_id"], quote=True)}" title="{html.escape(entity["label"], quote=True)}">{value}</mark>')
        cursor = end
    parts.append(html.escape(text[cursor:]))
    return "".join(parts)


def render_document(result):
    sentence_rows = "".join(f'<tr><td>{s["sentence_id"]}</td><td>{s["start"]}:{s["end"]}</td><td>{html.escape(s["text"])}</td></tr>' for s in result["sentences"])
    entity_rows = []
    for entity in result["entities"]:
        qid = valid_qid(entity.get("qid"))
        link = f'<a href="https://www.wikidata.org/wiki/{qid}" target="_blank" rel="noopener noreferrer">{qid}</a>' if qid else html.escape(entity.get("kb_id", ""))
        entity_rows.append(f'<tr><td>{html.escape(entity["entity_id"])}</td><td>{html.escape(entity["text"])}</td><td>{html.escape(entity["label"])}</td><td>{entity["start"]}:{entity["end"]}</td><td>{link}</td></tr>')
    lookup = result.get("coordinate_lookup", {})
    notice = html.escape(lookup.get("error", ""))
    return f'''<!doctype html><html lang="sr-Latn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Tesla · radionica</title><style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#183242}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}}mark{{background:#ffe8a6;border-radius:3px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cad4db;padding:.4rem;text-align:left}}a{{color:#125a90}}svg{{height:auto}}</style></head><body><h1>Tesla · rezultati radionice</h1><p>Predviđanja modela, obavezna ručna provera. NEL: {"uključen" if result["nel_enabled"] else "isključen"}. NIL i neispravni identifikatori nisu veze. Nema kalibrisanih procenata pouzdanosti.</p><p>Model: {html.escape(result["model"])} · revizija: {html.escape(result["revision"])} · licenca: {html.escape(result["model_license"])}</p><p>Dokument SHA-256: {result["document_id"]}. Pomaci: Unicode znakovi, od nule, završni pomak nije uključen.</p><h2>Izvorni tekst sa entitetima</h2><pre id="source">{annotated_source(result)}</pre><h2>Entiteti i veze</h2><table><thead><tr><th>ID</th><th>Tekst</th><th>Izvorna klasa</th><th>Pomaci</th><th>KB/QID</th></tr></thead><tbody>{"".join(entity_rows)}</tbody></table><h2>Rečenice</h2><table><thead><tr><th>ID</th><th>Pomaci</th><th>Tekst</th></tr></thead><tbody>{sentence_rows}</tbody></table><h2>Povezane lokacije</h2><p>{notice}</p>{render_coordinate_map(result)}<p>TSV sadrži red po tokenu i prazne kolone corrected_* za ispravke u Excelu. Original je u JSON-u i u source_text prvog TSV reda. Apostrof štiti ćelije od Excel formula; excel_escaped_fields navodi tačno zaštićena polja — uklonite samo jedan dodat apostrof u tim poljima da povratite original. Prazna ispravka znači da ispravka nije uneta.</p></body></html>'''


def export_workshop(result, directory=None):
    root = Path(directory or tempfile.mkdtemp(prefix="tesla-workshop-"))
    root.mkdir(parents=True, exist_ok=True)
    json_path, tsv_path, html_path = (root / name for name in ("radionica.json", "radionica.tsv", "radionica.html"))
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = result["rows"] or [{"document_id": result["document_id"], "source_text": result["text"]}]
    columns = [*rows[0], "excel_escaped_fields"]
    with tsv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            safe = {key: spreadsheet_safe(value) for key, value in row.items()}
            safe["excel_escaped_fields"] = "|".join(key for key in row if safe[key] != row[key])
            writer.writerow(safe)
    html_path.write_text(render_document(result), encoding="utf-8")
    return str(json_path), str(tsv_path), str(html_path)
