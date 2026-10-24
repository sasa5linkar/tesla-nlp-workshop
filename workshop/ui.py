"""Small task-specific local interface. No model is loaded while building the UI."""
import gradio as gr

from .adapters import EXPLANATIONS, analyze
from .exports import export_result
from .inputs import InputError, read_txt
from .registry import PRESETS, TASK_PRESETS

EXAMPLES = [
    "Profesorka Ana Petrović radi na Univerzitetu u Beogradu. Marko putuje u Novi Sad.",
    "Професорка Ана Петровић ради на Универзитету у Београду. Марко путује у Нови Сад.",
]
EMOTION_EXAMPLES = [
    "Baš se radujem što ćemo ponovo biti zajedno! Hvala vam na pomoći.",
    "Баш се радујем што ћемо поново бити заједно! Хвала вам на помоћи.",
]
SUMMARY_EXAMPLES = [
    "Gradska biblioteka je otvorila novu čitaonicu. Prostor ima dvadeset mesta za rad i dostupan je svim članovima. Radionice čitanja održavaće se subotom. Prijave se primaju na pultu biblioteke.",
    "Градска библиотека је отворила нову читаоницу. Простор има двадесет места за рад и доступан је свим члановима. Радионице читања одржаваће се суботом. Пријаве се примају на пулту библиотеке.",
]


def cleared(status="Spremno za novu analizu."):
    return None, gr.update(value=[], headers=["Rezultat"], column_count=(1, "dynamic")), "", status, None, None


def run_task(task, text, preset_id, progress=gr.Progress(track_tqdm=True)):
    try:
        result = analyze(task, preset_id, text, progress)
        json_path, tsv_path = export_result(result)
        highlighted = {
            "text": text,
            "entities": [{"start": e["start"], "end": e["end"], "entity": e["label"]} for e in result["entities"]],
        }
        columns = list(result["rows"][0]) if result["rows"] else ["Rezultat"]
        values = [[row[key] for key in columns] for row in result["rows"]]
        timing = result["timing"]
        status = (
            f"Završeno · {result['input_tokens']} tokena · CPU · "
            f"priprema {timing['load_or_cache_seconds']:.2f} s · "
            f"analiza {timing['inference_seconds']:.2f} s · "
            f"memorija procesa {result['process_rss_mb']:.0f} MB. "
            f"Revizija: `{result['revision'][:12]}`."
        )
        return highlighted, gr.update(value=values, headers=columns, column_count=(len(columns), "dynamic")), result["summary"], status, json_path, tsv_path
    except InputError as exc:
        return cleared(f"**Provera ulaza:** {exc}")
    except Exception as exc:
        # Exceptions from libraries can contain tokenized user text or file paths.
        # Return the class only; do not print exceptions or raw inputs.
        return cleared(
            f"**Analiza nije završena ({type(exc).__name__}).** "
            "Proverite internet pri prvom preuzimanju, slobodan disk i RAM. "
            "Pokušajte ponovo kraćim primerom. Model i zavisnosti moraju biti iz zaključane instalacije. "
            "Za podršku navedite zadatak i tip greške, bez slanja privatnog teksta."
        )


def load_upload(path):
    if not path:
        return ""
    try:
        return read_txt(path)
    except (InputError, OSError) as exc:
        message = str(exc) if isinstance(exc, InputError) else "TXT nije moguće otvoriti. Izaberite datoteku ponovo."
        raise gr.Error(message) from None


def build_app():
    with gr.Blocks(title="Tesla · radionica srpskog NLP-a", analytics_enabled=False, delete_cache=(3600, 3600)) as app:
        gr.Markdown(
            "# Tesla · radionica srpskog NLP-a\n"
            "Nalepite kratak tekst, izaberite zadatak i pokrenite analizu. "
            "Radi na vašem CPU-u, na adresi **127.0.0.1**. Tekst se ne šalje modelskom servisu. "
            "Prvo korišćenje preuzima javne težine sa Hugging Face-a; zatim se koriste lokalno."
        )
        gr.Markdown(
            "**Priprema:** preporučeno 16 GB RAM-a i najmanje 15 GB slobodnog diska. "
            "U memoriji je jedan model. Promena zadatka može zahtevati ponovno učitavanje. "
            "Do 12.000 znakova po unosu; modeli imaju i niže granice tokena. "
            "Nema skraćivanja bez upozorenja. Zaustavite server sa Ctrl+C u terminalu."
        )
        for task, title in [("ner", "Imenovani entiteti · NER"), ("pos", "Vrste reči i leme"), ("emotion", "Emocije"), ("summary", "Kratak sažetak")]:
            with gr.Tab(title):
                gr.Markdown(EXPLANATIONS[task])
                preset = gr.Dropdown(
                    choices=[(PRESETS[key].title, key) for key in TASK_PRESETS[task]],
                    value=TASK_PRESETS[task][0], label="Model · provereni izbor",
                    allow_custom_value=False,
                )
                if task == "emotion":
                    gr.Markdown("Granica: **128 modelskih tokena**. Oznake: anger=ljutnja, anticipation=iščekivanje, disgust=gađenje, fear=strah, joy=radost, sadness=tuga, surprise=iznenađenje, trust=poverenje.")
                elif task == "summary":
                    gr.Markdown("Granica: **512 modelskih tokena**; do 80 novih tokena u sažetku. Koristi se tokenizator iz istog repozitorijuma kao model.")
                else:
                    gr.Markdown("Granica: **3.000 spaCy tokena**; svaki transformer prozor proverava se i prema granici od 512 podrečničkih tokena.")
                source = gr.Textbox(label="Tekst za analizu", lines=6, max_lines=12, placeholder="Unesite srpski tekst latinicom ili ćirilicom…")
                upload = gr.File(label="Ili učitajte UTF-8 TXT (do 48 KB)", file_types=[".txt"], type="filepath")
                examples = EMOTION_EXAMPLES if task == "emotion" else SUMMARY_EXAMPLES if task == "summary" else EXAMPLES
                gr.Examples([[text] for text in examples], inputs=source, label="Primeri · latinica i ćirilica")
                run = gr.Button("Analiziraj tekst", variant="primary")
                status = gr.Markdown("Model se učitava tek kada pokrenete analizu.")
                highlighted = gr.HighlightedText(label="Entiteti u izvornom tekstu", visible=task == "ner", show_legend=True)
                table = gr.Dataframe(label="Rezultati · originalne oznake modela", headers=["Rezultat"], column_count=(1, "dynamic"), interactive=False, wrap=True)
                summary = gr.Textbox(label="Generisani sažetak · proverite uz izvornik", interactive=False, visible=task == "summary")
                with gr.Row():
                    json_file = gr.File(label="Preuzmite JSON · izvorni tekst i metapodaci", interactive=False)
                    tsv_file = gr.File(label="Preuzmite TSV · tabela za Excel", interactive=False)
                outputs = [highlighted, table, summary, status, json_file, tsv_file]
                task_state = gr.State(task)
                run.click(
                    run_task, [task_state, source, preset], outputs,
                    concurrency_id="one-model", concurrency_limit=1,
                    trigger_mode="once", api_name=False,
                )
                upload.upload(load_upload, upload, source, api_name=False)
                source.change(lambda: cleared(), outputs=outputs, queue=False, api_name=False)
                preset.change(lambda: cleared(), outputs=outputs, queue=False, api_name=False)
        gr.Markdown(
            "Rezultati su predviđanja za učenje, uz moguću grešku. "
            "JSON čuva tačan ulaz i reviziju modela; TSV čuva tabelu u UTF-8 sa BOM-om. "
            "U TSV-u su potencijalne Excel formule zaštićene apostrofom; tačan sadržaj je u JSON-u. "
            "Preuzimanja i otpremljeni TXT fajlovi ostaju u privremenom lokalnom skladištu "
            "i mogu opstati nakon zatvaranja aplikacije. Ne unosite osetljive podatke na zajedničkom računaru. "
            "[Kod i uputstvo](https://github.com/sasa5linkar/tesla-nlp-workshop) · "
            "[JuDig model](https://huggingface.co/Tanor/sr_judig2026_teslaxlm) · "
            "[Emocije](https://huggingface.co/te-sla/serbian-emotion-teslaxlm) · "
            "[PiloT5](https://huggingface.co/te-sla/pilot5-sumarizacija)"
        )
    return app.queue(max_size=8, default_concurrency_limit=1)
