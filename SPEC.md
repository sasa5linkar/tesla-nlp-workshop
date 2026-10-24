# Serbian NLP workshop specification

## Objective and acceptance
A beginner-facing Serbian Gradio app with NER, POS/lemma, emotions and optional short summarization. Paste text or UTF-8 TXT, Latin/Cyrillic examples, entity highlighting, token tables, honest task-specific score explanations and JSON/TSV downloads. No private sources or generated personal outputs enter Git. Public publication on sasa5linkar is explicitly authorized.

## Assumptions
Windows CPU is the verified platform. Mac/Linux launch instructions will be provided without claims of testing there. First launch downloads public model weights; analysis stays on localhost. Unsupported or unsafe models are documented rather than executed. Defaults prioritize a useful supported vertical slice. Model presets are fixed and revision-pinned, not arbitrary code loaders.

## Stack, structure and commands
Python 3.11 (uv pinned), Gradio, PyTorch CPU, Transformers, Hugging Face Hub; spaCy only if its model/runtime is verified. Exact compatible versions recorded in pyproject.toml and uv.lock after the audit.

`uv sync --locked`; `uv run --locked python -m workshop`; `uv run --locked pytest`; CPU smoke tests in `scripts/`; `workshop/` for adapters, model registry and UI; `docs/` for model audit/results.

## Style
UTF-8 Python, explicit task adapters, structured results. Example: `raise InputError("Unesite tekst za analizu.")`. Inputs never silently truncated; unknown labels are not renamed into guessed labels. Errors contain useful next steps without echoing user text.

## Testing
Meaningful validation/export/concurrency tests; actual CPU smoke inference for each enabled preset; browser UI test, launch from spaces/Unicode, input boundaries and model switching; clean uv install. Record model revisions, load/inference timings and memory when available. Cross-platform portability is documented separately from tested Windows behavior.

## Boundaries
Always: explicit 127.0.0.1, share=False, one loaded large model, serialized inference, UTF-8 preservation, no raw-text logs, standard model implementations and safetensors where possible. Download only public weights with anonymous requests.
Never: arbitrary remote/custom code, trust_remote_code=True, LAN/public tunnel defaults, remote inference, credentials/corpora/weights in Git, edits to existing corpus/training repositories, organization transfer.
User has authorized dependency installation, testing, implementation and public GitHub publication. No additional approval gate is needed for those actions.

## Implementation plan
1. Inspect model metadata/cards/configuration and anonymous weight access.
2. Choose compatible presets; implement adapters, validation and exports.
3. Build Serbian tabs, progress/errors and launchers.
4. Lock/install, test real inference and browser workflows, repair failures.
5. Write honest results, scan tracked files, publish main and verify remote.
