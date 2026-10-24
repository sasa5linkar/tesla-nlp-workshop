"""Default workshop UI; optional network requests require a separate action."""
import gradio as gr

from .adapters import EXPLANATIONS, analyze
from .coordinates import location_qids, lookup_coordinates
from .inputs import InputError
from .registry import PRESETS
from .workshop_exports import export_workshop, render_coordinate_map

WORKSHOP_EXAMPLES = [
    "Nikola Tesla je posetio Beograd. Novi Sad se nalazi u Srbiji.",
    "Никола Тесла је посетио Београд. Нови Сад се налази у Србији.",
]


def _table(rows, columns):
    return gr.update(value=[[row.get(key, "") for key in columns] for row in rows],
                     headers=columns, column_count=(len(columns), "dynamic"))


def workshop_cleared(status="Spremno za analizu radionice."):
    return (None, _table([], ["Token"]), _table([], ["Entitet"]), _table([], ["Rečenica"]),
            "", status, None, None, None, None)


def compute_workshop(text, preset_id, progress=gr.Progress(track_tqdm=True)):
    completed = {"source": (text, preset_id)}
    try:
        completed["result"] = analyze("workshop", preset_id, text, progress)
    except InputError as exc:
        completed["error"] = f"Provera ulaza: {exc}"
    except Exception as exc:
        completed["error"] = (
            f"Analiza nije završena ({type(exc).__name__}). Proverite RAM, disk i vezu pri prvom preuzimanju. "
            "Pokušajte kraćim tekstom ili režimom bez NEL. Za podršku navedite tip greške, bez privatnog teksta."
        )
    return completed


def compute_coordinates(published, text, preset_id, consent):
    if not published or published.get("source") != (text, preset_id) or "result" not in published:
        return {"source": (text, preset_id), "error": "Najpre analizirajte trenutni tekst."}
    completed = {**published, "result": {**published["result"]}}
    if not consent:
        lookup = {"points": [], "error": "Za upit koordinata označite saglasnost. Nijedan zahtev nije poslat."}
    else:
        try:
            lookup = lookup_coordinates(location_qids(completed["result"]))
        except Exception as exc:
            lookup = {"points": [], "error": f"Koordinate nisu dostupne ({type(exc).__name__}). Analiza je sačuvana; možete ponoviti samo upit koordinata."}
    completed["result"]["coordinate_lookup"] = lookup
    return completed


def publish_workshop(completed, text, preset_id):
    if not completed or completed.get("source") != (text, preset_id):
        return workshop_cleared("Ulaz je promenjen tokom obrade. Pokrenite analizu za trenutni tekst.")
    if "error" in completed:
        return workshop_cleared(completed["error"])
    result = completed["result"]
    try:
        json_path, tsv_path, html_path = export_workshop(result)
        highlighted = {"text": text, "entities": [
            {"start": ent["start"], "end": ent["end"], "entity": ent["label"]} for ent in result["entities"]
        ]}
        status = (
            f"Završeno: {result['input_tokens']} tokena, {len(result['sentences'])} rečenica, "
            f"{len(result['entities'])} entiteta. NEL: {'uključen' if result['nel_enabled'] else 'isključen'}. "
            f"CPU analiza {result['timing']['inference_seconds']:.2f} s; RSS {result['process_rss_mb']:.0f} MB "
            "(trenutna, ne vršna memorija). Proverite oznake i QID veze ručno."
        )
        lookup = result.get("coordinate_lookup", {})
        if lookup:
            status += f" Koordinate: {len(lookup.get('points', []))}; bez koordinata: {len(lookup.get('without_coordinates', []))}; preko granice upita: {lookup.get('omitted_count', 0)}. {lookup.get('error', '')}"
        return (
            highlighted,
            _table(result["rows"], ["sentence_id", "token_id", "form", "lemma", "pos", "ner_iob", "ner", "kb_id", "qid"]),
            _table(result["entities"], ["entity_id", "text", "label", "start", "end", "kb_id", "qid"]),
            _table(result["sentences"], ["sentence_id", "start", "end", "text"]),
            render_coordinate_map(result), status, json_path, tsv_path, html_path, completed,
        )
    except Exception as exc:
        return workshop_cleared(f"Izvoz nije završen ({type(exc).__name__}). Pokušajte ponovo kraćim tekstom.")


def build_workshop_tab(load_upload):
    with gr.Tab("Radionica · JuDig NER/NEL, POS, leme i rečenice"):
        gr.Markdown(EXPLANATIONS["workshop"])
        gr.Markdown(
            "**Puni NEL učitava veliku bazu znanja i troši više RAM-a.** Planirajte najmanje 16 GB RAM-a; "
            "to nije garantovana granica. Ako nema dovoljno memorije, izaberite režim bez NEL. "
            "Učitava se samo jedan model, tek kada kliknete na analizu. CNN i četvoroklasni modeli nisu u ovoj lokalnoj instalaciji."
        )
        preset = gr.Radio(choices=[
            ("Puni JuDig: NER + NEL/Wikidata + POS + leme + rečenice", "judig_full"),
            ("JuDig bez NEL/KB: NER + POS + leme + rečenice", "judig"),
        ], value="judig_full", label="Izabrani režim modela")
        gr.Markdown(f"Model: `{PRESETS['judig'].repo}` · revizija `{PRESETS['judig'].revision}`. Granica: 12.000 znakova, 3.000 spaCy tokena i 512 podrečničkih tokena u prozoru; nema neprimetnog odsecanja.")
        source = gr.Textbox(label="Kratak tekst za radionicu", lines=5, placeholder="Unesite tekst latinicom ili ćirilicom.")
        upload = gr.File(label="Ili učitajte UTF-8 TXT (do 48 KB)", file_types=[".txt"], type="filepath")
        gr.Examples([[text] for text in WORKSHOP_EXAMPLES], inputs=source, label="Izmišljeni primeri · latinica i ćirilica")
        run = gr.Button("Analiziraj · učitaj izabrani model", variant="primary")
        status = gr.Markdown("Model još nije učitan.")
        highlighted = gr.HighlightedText(label="NER u izvornom tekstu", show_legend=True)
        tokens = gr.Dataframe(label="Tokeni · originalna predviđanja", headers=["Token"], column_count=(1, "dynamic"), interactive=False, wrap=True)
        entities = gr.Dataframe(label="Entiteti i KB/QID · NIL nije veza", headers=["Entitet"], column_count=(1, "dynamic"), interactive=False, wrap=True)
        sentences = gr.Dataframe(label="Rečenice i pomaci", headers=["Rečenica"], column_count=(1, "dynamic"), interactive=False, wrap=True)
        gr.Markdown("**Karta, opcioni internet upit:** šalju se samo do 20 predviđenih LOC QID-ova na Wikidata, bez izvornog teksta. Upit otkriva mrežne podatke i te QID-ove. Koordinate se čuvaju u memoriji do 24 sata (do 256 QID-ova). Nema automatskog upita ni ponavljanja. Predviđena veza može biti pogrešna i kada QID i koordinate postoje.")
        consent = gr.Checkbox(value=False, label="Dozvoljavam slanje samo QID-ova na Wikidata radi koordinata")
        lookup_button = gr.Button("Preuzmi koordinate sa Wikidata · internet")
        map_view = gr.HTML()
        gr.Markdown("HTML i karta koordinata rade bez spoljnih skripti ili pločica. Mreža je potrebna samo za izričit upit koordinata i klik na spoljne Wikidata/OpenStreetMap veze. TSV: red po tokenu, prazne corrected_* kolone za ispravke u Excelu; pomaci su Unicode znakovi od nule. Izvorni tekst je u JSON-u i source_text prvog TSV reda. Zaštitni apostrof sprečava Excel formule; excel_escaped_fields navodi sva izmenjena polja za tačno vraćanje originala.")
        with gr.Row():
            json_file = gr.File(label="JSON · tačan izvor i metapodaci", interactive=False)
            tsv_file = gr.File(label="TSV · ispravke u Excelu", interactive=False)
            html_file = gr.File(label="HTML · anotirani tekst, QID veze i karta", interactive=False)
        completed, published = gr.State(), gr.State()
        outputs = [highlighted, tokens, entities, sentences, map_view, status, json_file, tsv_file, html_file, published]
        run.click(compute_workshop, [source, preset], completed, concurrency_id="one-model", concurrency_limit=1, trigger_mode="once", api_name=False).then(
            publish_workshop, [completed, source, preset], outputs, queue=False, api_name=False,
        )
        lookup_button.click(compute_coordinates, [published, source, preset, consent], completed, concurrency_id="one-model", concurrency_limit=1, trigger_mode="once", api_name=False).then(
            publish_workshop, [completed, source, preset], outputs, queue=False, api_name=False,
        )
        upload.upload(load_upload, upload, source, api_name=False)
        source.change(workshop_cleared, inputs=None, outputs=outputs, queue=False, api_name=False)
        preset.change(workshop_cleared, inputs=None, outputs=outputs, queue=False, api_name=False)
