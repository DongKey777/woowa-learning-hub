# RAG R1: bge-m3 fts+dense Full Build + Holdout Decision (2026-04-30)

## Outcome (Plan v5 §12 Definition of Done)

- ✅ **R0 RunPod automation smoke** ($0.06, 7m, FTS-only)
- ✅ **R1 full-corpus artifact** (commit `c352271`, 27,155 chunks, BGE-M3 fp16, 122 MB tar.zst, sha256 `87d79f46…`)
- ✅ **Holdout decision committed**: dense modality production-ready globally

## Headline result (`reports/rag_eval/r1_holdout_c352271.json`, 101-query holdout split)

| Modality | primary_nDCG@10 | P95 warm | hard-fail count |
|---|---|---|---|
| `fts` (lexical baseline) | 0.6862 | 85.5 ms | 54 |
| **`fts,dense`** | **0.7890** | 303.1 ms | **47** |

**Δ nDCG = +0.1028 (+15.0% relative)**, hard-fail recovery −7 (−13%), P95 well under the 500 ms gate, no `forbidden_rate` regression.

Plan v5 §3 R1 acceptance gate (`+0.005 absolute` global) cleared by **21×**. 

## Bucket-level breakdown (where dense earns its keep)

| Category (n) | fts | fts+dense | Δ |
|---|---|---|---|
| **database** (12) | 0.480 | **0.803** | **+0.323** |
| **network** (4) | 0.515 | **1.000** | **+0.485** |
| operating-system (3) | 0.833 | 0.877 | +0.044 |
| language (6) | 0.750 | 0.833 | +0.083 |
| security (6) | 1.000 | 1.000 | 0 (already perfect) |
| spring (26) | 0.743 | 0.742 | −0.001 (FTS already strong) |
| software-engineering (3) | 0.667 | 0.667 | 0 |
| system-design (2) | 1.000 | 1.000 | 0 |
| **design-pattern (39)** | **0.187** | **0.180** | **−0.007** ⚠️ |

| Language (n) | fts | fts+dense | Δ |
|---|---|---|---|
| en (14) | 0.670 | 0.778 | +0.108 |
| mixed (57) | 0.668 | 0.748 | +0.080 |
| **ko (30)** | **0.133** | **0.133** | **0** ⚠️ |

## Decision: global dense ON

`scripts/learning/rag/lance_modalities_policy.json` upgraded to `schema_version: 2`:

- `full_default_modalities = ["fts", "dense"]` (was `["fts"]`)
- `dense_default_categories` expanded from `{database, network, operating-system}` (sampled-era) to all 9 categories — holdout shows no material regression in any
- `holdout_required_before_global_dense = false` (the holdout we required is now in hand)
- Per-bucket numbers preserved as `category_holdout_results` / `language_holdout_results` for future audit

## Open weaknesses (carry into R3 / corpus work)

1. **`language.ko` stuck at 0.133**: BGE-M3 multilingual embedding does not lift Korean retrieval here. Dense adds nothing. This is the single biggest remaining problem — n=30 (largest single language bucket after `mixed`). Candidates: ColBERT MaxSim (R3), sparse term-weight (R2), or corpus boost (Korean docs underrepresented).
2. **`category.design-pattern` stuck at ~0.18**: largest bucket (n=39). Both FTS and dense fail. Queries are highly conceptual ("Strategy vs Template") and chunks don't carry that abstraction-level signal. Query rewriting or sparse term-emphasis may help; a corpus-level fix (more discriminative design-pattern docs) probably needed.

Both are pinned in `lance_modalities_policy.json.open_R3_candidates` for downstream R-phase planning.

## Cost ledger

| Run | GPU | Wall | Cost |
|---|---|---|---|
| R0 v1-v5 (smoke fixes) | A4000/A5000 | 27m total | $0.06 |
| R1 v1-v8 (8 fix iterations) | A4000 | ~70m total | ~$0.36 |
| **R1 v9 (success)** | A4000 | 19m 56s | **$0.166** |
| **R1 cumulative** | — | — | **~$0.55** |

Safety budget for the R-phase was $5 (Plan v5 §6); we used 11% of it.

## R1 v1-v9 fix iteration log (paramiko stderr-tail logger from R1 v8 made the last 4 fast)

| Iter | Failure | Root cause | Fix |
|---|---|---|---|
| R1 v1 | GPU 0%, 38 min CPU | created venv → cu130 wheel vs Pod 12.4 driver | use Pod's system Python with `--break-system-packages` |
| R1 v2/v3 | HF Hub fetch crashed at 60% | unauthenticated rate limit on RunPod community IPs | retry with HF cache reuse (later replaced by subprocess+timeout) |
| R1 v4 | child stalls at 100% download | torch.load hang on Pod overlayfs | subprocess + 900s wall-clock timeout in `_warm_bge_m3.py` |
| R1 v5 | model load `ValueError: torch < 2.6` | CVE-2025-32434 check in transformers 5.x | superseded by R1 v9 fix |
| R1 v6 | `ModuleNotFoundError: BloomPreTrainedModel` | transformers 5.7 refactored lazy imports | superseded by R1 v9 fix |
| R1 v7 | `operator torchvision::nms does not exist` | torch upgraded but vision/audio left on 2.4 ABI | superseded by R1 v9 fix |
| R1 v8 | `XLMRobertaModel got dtype kwarg` | FlagEmbedding 1.4.0 uses transformers 4.50+ kwarg | **R1 v9: pin FlagEmbedding 1.3.5 + transformers <4.50** (verified against upstream `setup.py` + `runner.py`) |
| **R1 v9** | — | — | success |

The R1 v8 logger fix (`stderr[-2000:]` instead of `[:500]`) was decisive — paramiko's truncated buffer had been hiding the actual `ErrorType: message` line in every prior round.

## Files committed

- `scripts/remote/runpod_rag_full_build.py` — final pin stack (commit `c352271`) + eval download (commit `6f90db0`)
- `scripts/remote/_warm_bge_m3.py` — subprocess + timeout retry helper
- `scripts/learning/rag/lance_modalities_policy.json` — schema_version 2
- `tests/unit/test_runpod_rag_full_build.py`, `test_warm_bge_m3.py`, `test_lance_search_path.py` — updated
- `artifacts/rag-full-build/r1-c352271-2026-04-30T1400/` — local artifact (not tracked; covered by .gitignore as artifacts/)
- `state/cs_rag_eval/r1/` — extracted index root for local eval (not tracked)
- `reports/rag_eval/r1_holdout_c352271.json` — eval output

## Next R-phase recommendations

- **R2 (sparse)**: Plan v5 §3. Worth running specifically because the two unsolved buckets (`ko`, `design-pattern`) are the kind of failures where learned-sparse term weighting can help — sparse can recover identifier matches and rare-term emphasis that dense smooths over. Estimated: A4000, ~20 min, ~$0.20.
- **R3 (ColBERT) — gated**: Plan v5 specifies user confirmation is required before launch ($8–12 worst case). Run only if R2 still leaves Korean significantly under-served.
- **R4 (reranker A/B)**: deferred until embedding stack is locked. Plan v5 rule.
- **Cutover regression measurement**: legacy v2 (SQLite + MiniLM) vs R1 LanceDB stack on the same fixture/corpus_hash. This is independent of R2/R3 progress and can run any time we want to lock production.

## Lessons captured

1. **Subprocess + wall-clock timeout** is necessary for any "import + load model" warm step on shared/community Pod filesystems. A pure-Python try/except can't break a syscall hang.
2. **paramiko buffers stderr**; `[:500]` shows the call site, never the exception text. Always log head + tail.
3. **For framework version-pinning, read upstream `setup.py` + the call site that's failing**. R1 v1–v7 all guessed at version bands; R1 v8's docs-grounded fix landed in one shot.
4. **Local M5 16 GB cannot run BGE-M3 on MPS** (FlagEmbedding macOS-version error); CPU is too slow for full encoding (3+ hours on 27K chunks). Remote build is the only viable path for hybrid encoders. The dual-loop model (sampled-local + full-remote) from Plan v5 is correct.
