# Verification status

First runnable version, 2026-10-24. Windows CPU verification is in progress; completed checks below are actual results.

Python 3.11.14, uv 0.9.7, torch 2.7.1+cpu, spaCy 3.8.11, spacy-transformers 1.3.9, Transformers 4.49.0, Gradio 6.9.0. `uv sync --locked` completed in a fresh .venv. The complete local suite passes **17 tests**. `detect-secrets 1.5.0` found **zero flagged files** in staged source/docs (uv.lock excluded from entropy scanning; its URLs/hashes are package metadata).

| Real CPU check | Latin | Cyrillic | Inference seconds | Observed RSS MB |
|---|---|---|---|---|
| JuDig NER | PASS | PASS | 0.181 / 0.167 | ~4967 |
| JuDig POS/lemma | PASS | PASS | 0.161 / 0.161 | ~4967 |
| TeslaXLM emotion | PASS | PASS | 0.310 / 0.139 | ~1815 |
| PiloT5 summary | PASS | PASS | 2.777 / 2.463 | 1237–1311 |
| Return from summary to JuDig | PASS | — | 0.162; cached reload 13.872 | ~4956 |

First download/preparation times were 118.027 s JuDig, 79.975 s emotion, 29.337 s summarization. These mix download, import and load time and are not pure inference benchmarks. Machine reported about 127.7 GB RAM; these results do not benchmark a 16 GB laptop. RSS is a point-in-time process measurement, not peak memory. `runtime-results.json` contains model revisions, exact built-in example text, actual predictions and measurements. No personal inputs are included.

Both emotion and summary reject oversized token sequences without running inference. Emotion loaded successfully on Transformers 4.49 despite its config recording a 5.12.1 save version. Exact config label order, multilabel task, published thresholds and token limit 128 were checked. No compatibility claim relies on mocked model output.

Chrome opened the real UI. Empty input now returns a Serbian validation message. Browser testing found and repaired a Gradio dataframe header/column-count mismatch; a regression test now constructs the actual component update. The server listener was verified as 127.0.0.1:7860. Further UI/export/clean-install/Unicode-path checks continue after the first public checkpoint.

Mac/Linux are not locally tested. NEL is intentionally excluded. Download-failure handling is tested with a controlled ConnectionError, not a live service outage. Windows temp handling required an explicit workspace `--basetemp`; tests were executed with authorized full environment access after sandboxed imports stalled. A connection outage interrupted the first smoke run; persisted results were inspected and only unfinished cases resumed.
