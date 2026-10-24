# Serbian NLP workshop specification

## Objective and acceptance
A beginner-facing Serbian Gradio workshop with the new pinned JuDig model: sentence segmentation, POS, lemmas, NER and full NEL/Wikidata linking. Short pasted text and UTF-8 TXT; original labels and offsets; downloadable HTML, correction TSV and exact JSON. Full NEL is explicitly selected with a RAM warning; a lighter JuDig mode may exclude its KB. Exactly one model is resident. Emotions and Latin-only experimental summaries are available only through a separate `--experiments` launch option, outside workshop mode. No private sources or personal outputs enter Git. Public publication on sasa5linkar is explicitly authorized.

The map uses only predicted LOC spans with syntactically valid QIDs whose Earth coordinates are returned by Wikidata. Coordinate lookup requires an explicit checkbox and button; transmit QIDs only, never input text. At most 20 unique QIDs per action, bounded response size/time, bounded TTL cache, no automatic retries. Missing entities/coordinates and service failures retain the analysis and explain what is unavailable. HTML renders a self-contained coordinate map with source attribution; no external assets or tiles load automatically. Optional external map/entity links disclose internet use. Escape untrusted content and never link NIL or malformed IDs.

TSV includes traceable document, sentence and token IDs, original form/whitespace/offsets, actual lemma/POS/NER/KB predictions and blank participant-correction columns. Preserve original text in the first row and exact JSON. Formula-protect spreadsheet cells and identify every protected field so the original form can be recovered exactly. HTML annotated source must reproduce the original text when its annotation markup is stripped. Edited inputs cannot regain stale results/exports from in-flight analysis or coordinate lookup.

Only JuDig is installed locally; do not advertise unsupported POS/lemma capabilities for CNN/four-class models. The older CNN's spaCy 3.5.4 alternative stays in Colab, separate from this app's spaCy 3.8.11 lock. No Colab edits or email/sharing are part of this local task.

## Assumptions
Windows CPU is the verified platform. Mac/Linux launch instructions will be provided without claims of testing there. First launch downloads public model weights; analysis stays on localhost. Unsupported or unsafe models are documented rather than executed. Defaults prioritize a useful supported vertical slice. Model presets are fixed and revision-pinned, not arbitrary code loaders.

## Stack, structure and commands
Python 3.11 (uv pinned), Gradio, PyTorch CPU, Transformers, Hugging Face Hub; spaCy only if its model/runtime is verified. Exact compatible versions recorded in pyproject.toml and uv.lock after the audit.

`uv sync --locked`; `uv run --locked python -m workshop`; `uv run --locked pytest`; CPU smoke tests in `scripts/`; `workshop/` for adapters, model registry and UI; `docs/` for model audit/results.

Workshop verification: `uv run --locked python scripts/smoke_workshop.py`; optional coordinate test: add `--coordinates`. Optional experiments: `uv run --locked python -m workshop --experiments`. Lint: `ruff check workshop tests scripts`.

## Style
UTF-8 Python, explicit task adapters, structured results. Example: `raise InputError("Unesite tekst za analizu.")`. Inputs never silently truncated; unknown labels are not renamed into guessed labels. Errors contain useful next steps without echoing user text.

## Testing
Meaningful validation/export/concurrency tests; actual CPU smoke inference for each enabled preset; browser UI test, launch from spaces/Unicode, input boundaries and model switching; clean uv install. Record model revisions, load/inference timings and memory when available. Cross-platform portability is documented separately from tested Windows behavior.

## Boundaries
Always: explicit 127.0.0.1, share=False, one loaded large model, serialized inference, UTF-8 preservation, no raw-text logs, standard model implementations and safetensors where possible. Download only public weights with anonymous requests.
Never: arbitrary remote/custom code, trust_remote_code=True, LAN/public tunnel defaults, remote inference, credentials/corpora/weights in Git, edits to existing corpus/training repositories, organization transfer. Never touch the original app task's port-7860 browser download, tabs, processes or checkout.
User has authorized dependency installation, testing, implementation and public GitHub publication. No additional approval gate is needed for those actions.

## Implementation plan
1. Inspect full linker configuration; retain pinned weights/data-only loading and use an official inference scorer without executing model package Python. Verify full-NEL CPU inference.
2. Extract token/sentence/entity provenance; implement correction TSV and escaped annotated HTML. Verify exact source correspondence and formula recovery.
3. Add bounded consent-based Wikidata coordinates, offline coordinate map and attribution. Verify valid-QID and missing-coordinate paths.
4. Make workshop the default UI, hide experiments behind launch option, preserve current-input result binding and serialized model use. Verify UI configuration and filesystem exports without browser downloads.
5. Fresh locked install, regressions, actual full-NEL/map smoke, lint and secret scan; document actual limits, fetch/reconcile and publish main without force pushing.
