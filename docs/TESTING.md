# Verification status

## Current workshop mode, 2026-10-24

The newly authorized workshop adds full JuDig NEL/KB to sentence segmentation, POS, lemmas and NER, with exact-source HTML/JSON and participant-correction TSV. The default UI has one workshop tab; emotion and Latin-summary experiments require `--experiments`. This task changed no Colab, email or sharing settings. No dependencies were added for the workshop; the existing lock was retained.

`uv 0.9.7 sync --locked` succeeded in another fresh, separate Windows environment, Python 3.11.14. All **50 tests pass** in 17.97 seconds. The suite covers reversible Excel formula protection, original form/whitespace/offset/source recovery, sentence/token IDs, exact source after HTML parsing, escaped hostile text, NIL/malformed-ID suppression, missing entities/coordinates, real callback source binding and coordinate consent. Mock HTTP checks verify QID-only batches (20 maximum), size limits, missing/invalid/non-Earth/nonfinite coordinates, HTTP failure, cache capacity and expiration. Ruff and whitespace/UTF-8 checks pass.

The real locked-environment JuDig run loaded all seven published components, including the linker and KB, without executing model-package Python. The only override is the official spaCy evaluation scorer in place of the unavailable custom scorer; published inference weights and labels are unchanged. A short fictional Latin example produced two sentences, 13 tokens and four entities: `Nikola Tesla/PERS → NIL`, `Beograd/LOC → Q3711`, `Novi Sad/LOC → Q55630`, `Srbiji/LOC → Q403`. These are actual predictions: NIL and imperfect POS/lemma output are retained, not relabeled as accurate.

The explicit live coordinate test sent only those three location QIDs to Wikidata and received Earth P625 coordinates for all three. The HTML map uses those returned values, with source URLs/timestamps, and makes no tile/script requests. A coordinate is verified against the returned entity record, not proof that the model linked the source mention correctly. JSON/TSV were parsed from generated files and checked against the exact source; the HTML parser verifies source and map/QID correspondence. Evidence is [workshop-runtime-results.json](workshop-runtime-results.json). Input and model downloads used the existing pinned public cache offline; the coordinate request was the separately enabled network action.

The first new full run took 13.320 seconds to load/prepare and 0.185 seconds for inference, with 4978.2 MB process RSS after inference. RSS is not peak RAM. This Windows host has about 127.7 GB RAM, so these numbers do not establish a 16 GB laptop or free-Colab memory guarantee. The parent handles Linux/Colab verification separately. Independently reported Colab large-model full-NEL success after disabling TF/Flax is a separate environment; no Colab was edited here. An additional fresh-environment execution is recorded in the JSON evidence.

The actual default UI page and `/config` returned HTTP 200 on this checkout's separate `127.0.0.1:7861` server; configuration exposed only the workshop tab. That server was then closed. No browser tab or browser file download was used. The original task's port-7860 approval/tabs/process/checkout were untouched. Browser file-download interaction, real Excel GUI import, Mac execution and the parent's new Linux/Colab retest remain unverified here; filesystem export validation is complete.

## Historical scoped fixes (`e9bcea5`), 2026-10-24

A new, independent Windows checkout was created from remote main `68c86e30970d8d2734d46dc01dccb8dd7466a67c`. `uv 0.9.7 sync --locked` succeeded in a fresh `.venv` using the existing package cache, with Python 3.11.14. The updated lock adds `httpx[socks]`/socksio 1.0.0 and PySocks 1.7.1; existing package versions remain unchanged. Proxy settings and certificate verification were not changed.

The complete suite passes **28 tests** in 11.14 seconds with normal local import access. New regressions cover Cyrillic/mixed/other-script rejection before model loading, unknown-token rejection before generation, exact Latin source preservation, manual-review metadata in JSON/TSV, changed text/task/model suppressing stale results and exports, Latin-only examples, backend flags before third-party imports, and actual Gradio/HTTPX import/construction with a SOCKS proxy configured (without connecting to it). Ruff 0.14.2 passes on `workshop tests scripts`; `git diff --check` and UTF-8 Serbian sentinel checks pass. A sandboxed suite stalled after 26 cases; the complete reported run used normal local import access.

`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ... python scripts/smoke.py --small` exercised only the already cached public models at the exact revisions in `registry.py`. It did not download model weights. All four checks passed: actual CPU emotion inference, actual CPU Latin-summary inference, and both oversized-input rejection checks. Evidence is in [runtime-small-results.json](runtime-small-results.json), including exact built-in inputs, predictions and revisions.

| New real CPU execution check | Revision | Inference seconds | Observed RSS MB |
|---|---|---:|---:|
| Latin emotion | `3be268fae557df0a258150207813d993dc9551a2` | 0.325 | 1762.9 |
| Latin experimental summary | `c9bac5bb79ecdd585a763ed5fe64abd9800bceea` | 2.822 | 1332.4 |

These are execution checks, not quality or factual-accuracy benchmarks. The new summary copied the full example rather than shortening it; other independently tested Latin results had omissions/hallucinations. The pinned tokenizer loses Cyrillic words as unknown tokens. Cyrillic is now rejected without transliteration, unknown tokens prevent generation, and all summary outputs require manual factual review. The earlier Cyrillic summary "PASS" below meant only that generation ran; it was not valid language support.

At that checkpoint the package forced `USE_TF=0`, `USE_FLAX=0`, `USE_TORCH=1` before relevant imports. An independent Colab report found that avoiding unused frameworks changed full-NEL large-model execution from a RAM crash around 12.67 GB to success. That was a different environment and did not establish this app's peak RAM requirement. The local app at that checkpoint excluded `entity_linker`; NEL had not yet been enabled. No heavy JuDig run, browser download/export, Colab edit or Mac test was repeated for those fixes. A Linux retest was delegated separately.

## Historical first checkpoint (`68c86e3`)

The original Windows CPU results below are retained as historical evidence.

Python 3.11.14, uv 0.9.7, torch 2.7.1+cpu, spaCy 3.8.11, spacy-transformers 1.3.9, Transformers 4.49.0, Gradio 6.9.0. `uv sync --locked` completed in a fresh .venv. The complete local suite passes **17 tests**. `detect-secrets 1.5.0` found **zero flagged files** in staged source/docs (uv.lock excluded from entropy scanning; its URLs/hashes are package metadata).

| Real CPU check | Latin | Cyrillic | Inference seconds | Observed RSS MB |
|---|---|---|---|---|
| JuDig NER | PASS | PASS | 0.181 / 0.167 | ~4967 |
| JuDig POS/lemma | PASS | PASS | 0.161 / 0.161 | ~4967 |
| TeslaXLM emotion | PASS | PASS | 0.310 / 0.139 | ~1815 |
| PiloT5 summary | Executed; manual review required | Executed but unsupported; now rejected | 2.777 / 2.463 | 1237-1311 |
| Return from summary to JuDig | PASS | — | 0.162; cached reload 13.872 | ~4956 |

First download/preparation times were 118.027 s JuDig, 79.975 s emotion, 29.337 s summarization. These mix download, import and load time and are not pure inference benchmarks. Machine reported about 127.7 GB RAM; these results do not benchmark a 16 GB laptop. RSS is a point-in-time process measurement, not peak memory. `runtime-results.json` contains model revisions, exact built-in example text, actual predictions and measurements. No personal inputs are included.

Both emotion and summary reject oversized token sequences without running inference. Emotion loaded successfully on Transformers 4.49 despite its config recording a 5.12.1 save version. Exact config label order, multilabel task, published thresholds and token limit 128 were checked. No compatibility claim relies on mocked model output.

Chrome opened the real UI. Empty input now returns a Serbian validation message. Browser testing found and repaired a Gradio dataframe header/column-count mismatch; a regression test now constructs the actual component update. The server listener was verified as 127.0.0.1:7860. Further UI/export/clean-install/Unicode-path checks continue after the first public checkpoint.

At that checkpoint Mac/Linux were not locally tested. NEL is intentionally excluded. Download-failure handling is tested with a controlled ConnectionError, not a live service outage. Windows temp handling required an explicit workspace `--basetemp`; tests were executed with authorized full environment access after sandboxed imports stalled. A connection outage interrupted the first smoke run; persisted results were inspected and only unfinished cases resumed.
