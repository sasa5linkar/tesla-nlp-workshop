import time

from .inputs import InputError, validate_text
from .models import MANAGER
from .registry import EMOTION_LABELS, PRESETS, TASK_PRESETS

EXPLANATIONS = {
    "ner": "NER označava pretpostavljene raspone i klase. spaCy ovde ne daje kalibrisanu verovatnoću po entitetu; zato nema izmišljenog procenta. NEL nije uključen. PERS=osoba, ROLE=uloga/zanimanje, LOC=mesto, ORG=organizacija, DEMO=grupa/demonim, WORK=delo, EVENT=događaj, PRODUCT=proizvod, IDEO=ideologija.",
    "pos": "UPOS je vrsta reči, lema je pretpostavljeni osnovni oblik. Model ne predviđa bogate morfološke osobine; prazna polja nisu sigurna oznaka. Nema kalibrisane pouzdanosti po tokenu. Pogrešan razmak ili tokenizacija mogu uticati na rezultat.",
    "emotion": "Osam nezavisnih sigmoid skorova, uz izvorne pragove iz thresholds.json. Skorovi nisu kalibrisane verovatnoće niti zbir od 100%. Više emocija može preći prag; nijedna izabrana oznaka ne znači neutralno. Model je za društvene mreže i nepouzdan je kao detektor neutralnosti. Koristimo izvorni tekst, bez reprodukcije celog trening postupka čišćenja.",
    "summary": "Generisani sažetak može izostaviti ili izmisliti činjenice. Proverite ga uz izvornik. Izlaz može promeniti pismo; ulaz i izvoz izvornog teksta ostaju sačuvani. Ovo nije mera tačnosti niti pouzdanosti.",
}


def no_progress(*args, **kwargs):
    pass


def check_token_limit(tokenizer, text, limit):
    encoded = tokenizer(text, return_tensors="pt", truncation=False)
    count = encoded["input_ids"].shape[1]
    if count > limit:
        raise InputError(f"Ulaz ima {count} modelskih tokena, a granica je {limit} (sa specijalnim tokenima). Skratite tekst; ništa nije odsečeno.")
    return encoded, count


def analyze(task, preset_id, text, progress=no_progress):
    validate_text(text)
    if task not in TASK_PRESETS or preset_id not in TASK_PRESETS[task]:
        raise InputError("Izaberite podržani model za ovaj zadatak.")
    preset = PRESETS[preset_id]
    # Gradio serializes all task events; this also protects CLI/API callers.
    with MANAGER.lock:
        started = time.perf_counter()
        progress(0.05, desc="Provera ulaza i priprema modela…")
        loaded = MANAGER.load(preset_id, progress)
        load_seconds = time.perf_counter() - started
        progress(0.75, desc="CPU analiza teksta…")
        infer_start = time.perf_counter()
        result = {
            "task": task, "model": preset.repo, "revision": preset.revision,
            "model_license": preset.license, "text": text, "rows": [], "entities": [],
            "summary": "", "explanation": EXPLANATIONS[task], "device": "cpu",
        }
        if preset.kind == "spacy":
            nlp = loaded["model"]
            probe = nlp.make_doc(text)
            if len(probe) > preset.limit:
                raise InputError(f"Ulaz ima {len(probe)} spaCy tokena; granica je {preset.limit}. Podelite tekst na odlomke.")
            # Validate every transformer span in advance; no wordpieces silently disappear.
            transformer = nlp.get_pipe("transformer").model
            tokenizer = transformer.tokenizer
            for start in range(0, len(probe), 96):
                chunk = probe[start:start + 128].text
                count = len(tokenizer(chunk, truncation=False)["input_ids"])
                if count > 512:
                    raise InputError("Jedan prozor teksta prelazi 512 podrečničkih tokena. Skratite dugačke reči ili odlomak; tekst nije odsečen.")
            doc = nlp(text)
            result["input_tokens"] = len(doc)
            result["rows"] = [
                {"token": token.text, "start": token.idx, "end": token.idx + len(token),
                 "lemma": token.lemma_, "upos": token.pos_, "tag": token.tag_,
                 "entity": token.ent_type_, "sentence_start": bool(token.is_sent_start)}
                for token in doc
            ]
            if task == "ner":
                result["entities"] = [
                    {"text": ent.text, "start": ent.start_char, "end": ent.end_char,
                     "label": ent.label_, "score": None}
                    for ent in doc.ents
                ]
        else:
            import torch
            encoded, count = check_token_limit(loaded["tokenizer"], text, preset.limit)
            result["input_tokens"] = count
            with torch.inference_mode():
                if task == "emotion":
                    scores = torch.sigmoid(loaded["model"](**encoded).logits[0]).tolist()
                    result["rows"] = [
                        {"label": label, "sigmoid_score": float(score), "threshold": float(threshold),
                         "selected": bool(score >= threshold)}
                        for label, score, threshold in zip(EMOTION_LABELS, scores, loaded["thresholds"], strict=True)
                    ]
                else:
                    generated = loaded["model"].generate(
                        **encoded, max_new_tokens=80, do_sample=False, num_beams=2,
                        no_repeat_ngram_size=3, early_stopping=True,
                    )
                    result["summary"] = loaded["tokenizer"].decode(generated[0], skip_special_tokens=True)
                    result["rows"] = [{"summary": result["summary"]}]
        result["timing"] = {
            "load_or_cache_seconds": round(load_seconds, 3),
            "inference_seconds": round(time.perf_counter() - infer_start, 3),
            "total_seconds": round(time.perf_counter() - started, 3),
        }
        import psutil
        result["process_rss_mb"] = round(psutil.Process().memory_info().rss / 1024**2, 1)
        progress(1, desc="Analiza je završena.")
        return result
