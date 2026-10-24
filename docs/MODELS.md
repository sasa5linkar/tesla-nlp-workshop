# Public model audit — 2026-10-24

All requests in the local audit used anonymous HTTPS, without an HF token. Hub API reported `private=false`, `gated=false` and weight HEAD requests followed redirects to HTTP 200. This is stronger evidence of anonymous download availability than the README visibility alone. The selected weights are downloaded and exercised by the CPU smoke suite; results are recorded separately. No private repositories, training corpora or cached personal models were read.

| Candidate and source card | Inspected revision | Public weight bytes | License from card | Decision |
|---|---|---:|---|---|
| [Tanor/sr_judig2026_teslaxlm](https://huggingface.co/Tanor/sr_judig2026_teslaxlm) | `259e37f6f9bec66baa51e28079cfdc777010d344` | 2,128,066,238 | CC BY-SA 4.0 | Default workshop: sentences/POS/lemmas/NER and full NEL; optional KB-free mode; both scripts |
| [te-sla/sr_nerel_teslaxlm](https://huggingface.co/te-sla/sr_nerel_teslaxlm) | `90c21cfaf43c43289a9744ee91bd36dfe10520e0` | 2,133,602,294 | CC BY-SA 4.0 | Compatible stack, four NER labels; not bundled as a redundant second large download |
| [Tanor/sr_pln_tesla_j125](https://huggingface.co/Tanor/sr_pln_tesla_j125) | `e13fdfafda4e178e31a6e84422461a0ba08f4af2` | 296,174,546 | CC BY-SA 4.0 | spaCy >=3.7.2,<3.8 requirement; not an automatic fallback in this environment |
| [te-sla/serbian-emotion-teslaxlm](https://huggingface.co/te-sla/serbian-emotion-teslaxlm) | `3be268fae557df0a258150207813d993dc9551a2` | 2,239,643,272 | CC BY-SA 4.0 | Selected; eight true labels and published thresholds |
| [procesaur/Emo355](https://huggingface.co/procesaur/Emo355) | `488bfbd44daab5d5ecbbd96698bd5ad14ce30fbd` | 1,416,925,056 + 65,752 dense head | Apache 2.0 | 16-dimensional expressed/evoked regression; not a categorical replacement |
| [te-sla/pilot5-sumarizacija](https://huggingface.co/te-sla/pilot5-sumarizacija) | `c9bac5bb79ecdd585a763ed5fe64abd9800bceea` | 990,345,064 | CC BY 4.0 | Experimental Latin-only summary; manual factual review required |

## Coherent runtime and code boundary

JuDig card pins Python 3.11, spaCy 3.8.11, spacy-transformers 1.3.9, Transformers 4.49.0 and torch 2.7.1. This app follows that stack, using official CPU PyTorch wheels on Windows/Linux and the standard macOS package. Transformers 4.49 requires Hugging Face Hub <1; Gradio 6.30 requires Hub >=1.16 and is incompatible. Gradio 6.9.0 explicitly permits Hub 0.36.0, so that compatible version is pinned. `uv.lock` records transitive versions and hashes. This compatibility selection is not a claim that every package is the newest release.

The public JuDig wheel was downloaded as an archive and its Python initialization, runtime registrations, config and metadata were inspected. It includes custom training-reader and NEL-scoring registry entries. The app does not pip-install/import that wheel and does not execute any of its `.py` files. It extracts only the known data subfolder after verifying SHA-256 `769468d04013326ca820ed626cf04f8c89cd050d0faa9539eaa439921b389198` from the public release manifest. Python/native executable files and archive traversal paths are rejected. Full workshop mode loads the published linker, KB and weights through standard spaCy, overriding only the unavailable custom evaluation scorer with the official `spacy.entity_linker_scorer.v1`. Inference weights and class labels remain intact; no evaluation accuracy is claimed. The optional lighter mode excludes `entity_linker`. NIL and malformed IDs are preserved as raw KB output but never linked.

JuDig's nine NER classes are PERS, ROLE, LOC, ORG, DEMO, WORK, EVENT, PRODUCT and IDEO. UPOS and lemmas are learned predictions. Raw-text performance is not implied by the card's evaluation on pretokenized documents. Its entity-linking metric uses known gold links and a KB with train/dev/test coverage; it should not be presented as general end-to-end accuracy. The workshop shows no fabricated confidence score for spaCy spans/tokens.

## Emotion contract

The selected checkpoint is public now; a private *source evidence repository* mentioned by its card is a separate resource and was not accessed. Its standard `XLMRobertaForSequenceClassification` architecture loads through Transformers with remote code disabled and safetensors only. Config gives the exact order `anger, anticipation, disgust, fear, joy, sadness, surprise, trust`, `problem_type=multi_label_classification`. The runtime checks this order and uses sigmoid independently for each logit, comparing with `thresholds.json` from the same pinned revision. No fixed 0.5 threshold and no neutral label are added.

The card's training maximum is 128 tokens; this app rejects longer inputs rather than using the card example's truncation. It preserves the raw input and does not claim exact reproduction of the training cleaner (NFC/Markdown/URL/mention/hashtag/punctuation processing). Skor interpretation and the weak neutral-abstention behavior are explained in the UI. This is a workshop demonstration on social-media emotion labels, not a psychological assessment.

## Summarization contract

The model repo itself includes tokenizer.json/spiece.model and tokenizer configuration with a 512-token maximum. We retain that same pinned snapshot. Independent tests found that its tokenizer maps Cyrillic words to `<unk>`; merely generating output on a Cyrillic sample did not establish support. This finding does not establish a tokenizer mismatch as the cause, and no alternate tokenizer has been substituted.

The task is experimental and Latin-only. Cyrillic and other non-Latin letters are rejected before loading a model, without silent transliteration. After tokenization, any unknown token rejects the input before generation. Input is also rejected above 512 tokens including specials. Deterministic generation uses two CPU beams and up to 80 new tokens; it is a lighter workshop setting than the card's six-beam example. Real Latin outputs have omissions and hallucinations, so successful execution and representable tokens do not establish factual reliability. The UI, JSON and TSV require manual factual review. The original input remains exact in JSON.

## Runtime resource boundary

The package sets `USE_TF=0`, `USE_FLAX=0`, `USE_TORCH=1` before any Gradio, spaCy or Transformers import. Only PyTorch is needed. Independently reported Colab testing of the full NEL large-model setup changed from a RAM crash around 12.67 GB to success with these flags. That is evidence for avoiding unused runtimes, not a measured memory guarantee for this local application. Full workshop mode now enables the linker explicitly with a RAM warning; NER/POS experimental tabs and the lighter workshop option still exclude it. See the testing report for the environments and limits actually exercised here.

## Attribution

Model data stays in a local cache, outside Git. Follow the linked authors' model cards and licenses; no corpus redistribution rights are inferred. No code was copied from nel_viewer, It-Sr-NER or private training repositories. The app is an independent implementation, with separate MIT code licensing.
