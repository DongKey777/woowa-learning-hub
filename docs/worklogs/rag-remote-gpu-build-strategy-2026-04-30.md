# RAG Remote GPU Build Strategy Handoff — 2026-04-30

## Purpose

다음 AI가 `woowa-learning-hub`의 CS RAG SOTA 전환 작업을 이어받을 때 읽는 실행 문서다.

중요한 전제 변경:

- 사용자는 원격 GPU 비용이 **체크포인트당 몇 달러 수준의 1회성 비용**이라면 허용한다.
- 따라서 로컬 MPS/16GB 한계 때문에 `bge-m3` full-corpus build를 포기하지 않는다.
- 앞으로 병목은 로컬 성능이 아니라 **평가 설계, artifact 재현성, 비용 누수 방지**다.

이 문서는 기존 계획서 `~/.claude/plans/abundant-humming-lovelace.md`와
`docs/worklogs/rag-sota-handoff-2026-04-30.md` 이후의 운영 방향을 정리한다.

## Current State

Branch state at this handoff:

- Branch: `main`
- Remote: `origin/main`
- Local ahead: `31` commits
- Working tree: clean before this document commit
- Production default: still legacy RAG path. LanceDB/bge-m3 is implemented as evaluation/candidate path, not cut over.

Recent relevant commits:

```text
d24a188 feat(rag-search): make LanceDB modality policy data-driven
09382fe feat(rag-search): gate LanceDB dense defaults by sampled evidence
1083d9f docs(rag): record core sampled dense sweep
a9c747d fix(rag-index): keep sampled LanceDB builds on exact scan
5f8f562 docs(rag): record sampled dense ablation result
b9fede7 docs(rag): record sampled ablation handoff
d283ba0 feat(rag-eval): add sampled LanceDB ablation mode
90989d3 fix(rag-index): skip bge-m3 load for FTS-only LanceDB builds
450d4ee feat(rag-eval): materialize sampled corpus for low-cost ablation
```

Implemented capabilities:

- LanceDB v3 index writer and search path.
- bge-m3 wrapper with dense/sparse/ColBERT modality output.
- `bin/cs-index-build --backend lance`.
- LanceDB device/precision/max length/batch/ETA controls.
- Modal ablation CLI: `bin/rag-eval --ablate`.
- Sampled corpus materialisation: `scripts/learning/rag/eval/sampled_ablation.py`.
- Sampled ablation CLI: `bin/rag-eval --sampled-ablate`.
- FTS-only LanceDB builds do not load bge-m3.
- Small sampled LanceDB indexes use exact scan instead of ANN k-means.
- LanceDB default modality policy is data-driven:
  `scripts/learning/rag/lance_modalities_policy.json`.

Latest focused verification:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_lance_index_builder.py \
  tests/unit/test_lance_search_path.py \
  tests/unit/test_rag_eval_cli.py \
  tests/unit/test_rag_eval_sampled_ablation.py \
  tests/unit/test_rag_eval_ab_retriever.py \
  tests/unit/test_rag_eval_ablation.py \
  tests/unit/test_bge_m3_encoder.py \
  -q
```

Result:

```text
83 passed in 2.49s
```

## What We Learned

Local full build is not a good loop:

- Full corpus is about `27K` chunks.
- Local bge-m3 `fts,dense` MPS/imported attempt observed ETA around `194m-253m`.
- Direct MPS path still hits a `FlagEmbedding` macOS-version error.
- CPU works but is too slow for repeated full-corpus experiments.

Sampled ablation is useful but not final:

| Category | Queries | Docs | Best | FTS nDCG / p95 / failures | FTS+dense nDCG / p95 / failures |
| --- | ---: | ---: | --- | --- | --- |
| spring | 72 | 17 | fts | 0.8886 / 38.2ms / 14 | 0.8248 / 157.7ms / 23 |
| database | 48 | 25 | fts+dense | 0.7825 / 114.2ms / 14 | 0.8968 / 478.7ms / 8 |
| network | 10 | 8 | fts+dense | 0.7655 / 44.8ms / 5 | 0.9262 / 134.4ms / 1 |
| operating-system | 7 | 7 | fts+dense | 0.7517 / 28.0ms / 1 | 0.9473 / 152.4ms / 1 |
| software-engineering | 16 | 10 | fts | 1.0000 / 40.1ms / 0 | 1.0000 / 165.2ms / 0 |
| data-structure | 2 | 3 | fts | 1.0000 / 21.0ms / 0 | 1.0000 / 138.5ms / 0 |

Implication:

- Dense is not globally safe.
- Dense looks useful for some categories, but final policy needs holdout/full-corpus confirmation.
- Small-query categories need more graded queries before firm decisions.

Current temporary policy:

```json
{
  "full_default_modalities": ["fts"],
  "dense_default_modalities": ["fts", "dense"],
  "dense_default_categories": ["database", "network", "operating-system"]
}
```

This is intentionally configurable because the corpus will keep growing.

## New Operating Model

Use two loops.

### Local Loop — Always Free

Use locally for daily corpus work:

- CS content expansion.
- QA/lint.
- graded query authoring.
- sampled ablation.
- policy draft updates.
- unit tests.

Local commands:

```bash
.venv/bin/python -m pytest tests/unit/test_rag_eval_sampled_ablation.py -q

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python scripts/learning/cli_rag_eval.py \
  --sampled-ablate \
  --sample-categories spring \
  --ablation-modalities fts \
  --ablation-modalities fts,dense \
  --ablation-split full \
  --device cpu
```

Do not run full-corpus bge-m3 locally unless explicitly testing ETA gates.

### Remote GPU Loop — Checkpoints Only

Use remote GPU when:

- Several hundred docs or major content changes accumulated.
- A final candidate stack needs full-corpus verification.
- Production cutover artifact is being prepared.
- A bigger embedding/reranker candidate is worth real evaluation.

Expected cost:

- Normal checkpoint: about `$2-$7`.
- Safe budget: `$10`.
- Avoid leaving pods running.

## Recommended Remote Service

Primary recommendation: **RunPod**.

Why RunPod:

- API key based CLI automation is realistic.
- GPU Pod can be created, used, artifact-copied, then deleted.
- SSH key can be generated by the AI session and registered through CLI/API.
- Fits this repo's need: full build job + result artifact download.

Alternative:

- Modal is clean for serverless jobs, but requires token id/secret and more app scaffolding.
- Vast.ai can be cheaper, but reliability/reproducibility are weaker.

Secrets rule:

- Never commit API keys.
- Store temporary credentials in environment variables or local ignored files only.
- Clear shell history/logs if a key is accidentally echoed.

## Remote Build Target Architecture

Add a small remote build harness rather than manually SSH-ing every time.

Recommended new files:

```text
scripts/remote/runpod_rag_full_build.py
scripts/remote/package_rag_artifact.py
docs/runbooks/rag-remote-gpu-build.md
```

The harness should:

1. Verify local tree is clean or record current commit SHA.
2. Verify current branch has been pushed, or create a patch bundle.
3. Create/launch RunPod GPU Pod from API key.
4. Register an ephemeral SSH key.
5. Clone repo at exact commit SHA.
6. Install dependencies.
7. Warm HuggingFace model cache.
8. Run full build matrix.
9. Run evaluation.
10. Package artifacts.
11. Download artifacts locally.
12. Delete Pod even on failure.

Minimum artifact shape:

```text
artifacts/rag-full-build/<run_id>/
  manifest.json
  run.log
  environment.json
  repo.diff_or_commit.txt
  cs_rag_lance.tar.zst
  eval/
    ablation_report.json
    holdout_report.json
```

Remote run metadata should include:

- repo commit SHA
- corpus hash
- fixture hash
- Python version
- GPU model
- CUDA version
- dependency versions
- model id and revision
- modalities
- index manifest
- wall-clock time
- estimated cost

## First Remote Build Matrix

Do not start with every candidate. First prove the remote path end to end.

### R0 — Infrastructure Smoke

Goal: prove RunPod automation and artifact return.

Build:

```text
backend=lance
modalities=fts
corpus=knowledge/cs
```

Expected:

- No bge-m3 load.
- Fast.
- Artifact returns and opens locally.

### R1 — bge-m3 Dense Full Build

Goal: first real full-corpus vector index.

Build:

```text
backend=lance
modalities=fts,dense
encoder=BAAI/bge-m3
max_length=512 or 1024
```

Evaluate:

```bash
bin/rag-eval --ablate \
  --embedding-index-root <downloaded_index> \
  --ablation-modalities fts \
  --ablation-modalities fts,dense \
  --ablation-split holdout
```

Decision:

- If holdout quality gain is weak or latency too high, keep production baseline.
- If category-specific gains hold, update `lance_modalities_policy.json`.

### R2 — Sparse Rescore

Build:

```text
modalities=fts,dense,sparse
```

Evaluate:

- `fts`
- `fts,dense`
- `fts,dense,sparse`

Decision:

- Sparse should recover code/identifier or ambiguous concept failures.
- If it only adds latency/noise, keep disabled.

### R3 — ColBERT / Multi-vector

Build:

```text
modalities=fts,dense,sparse,colbert
```

Evaluate:

- exact vs indexed if code supports both
- p95 latency
- disk footprint
- nDCG and hard-regression failures

Decision:

- ColBERT is only worth enabling if it improves hard failures or difficult buckets enough to justify latency/disk.

### R4 — Reranker A/B

After embedding modality stack is chosen:

- current reranker
- `bge-reranker-v2-m3`

Decision:

- Do not change reranker until embedding stack is stable.

## Candidate Scope With Remote GPU

The new condition widens candidates, but do not explode the matrix too early.

Reasonable candidates:

- Current legacy MiniLM stack: control.
- `BAAI/bge-m3`: primary hybrid candidate.
- `Qwen/Qwen3-Embedding-0.6B`: dense-only comparison if time permits.
- multilingual-e5-base/large: optional if bge-m3 disappoints.

Do not test giant models first:

- Qwen3-Embedding-8B and similar models may be technically possible on larger GPUs, but cost/time/eval complexity is not justified until bge-m3 full results are known.

## Production Cutover Rules

Do not cut over just because remote full build succeeds.

Cutover requires:

- full-corpus index artifact exists and is reproducible
- holdout eval passes
- no hard-regression increase beyond agreed gate
- p95 latency within target
- disk footprint acceptable
- rollback artifact exists
- `HF_HUB_OFFLINE=1` smoke works locally from downloaded artifact

If gate fails:

- keep legacy production path
- preserve remote artifact under `state/cs_rag_eval` or external storage
- document why the candidate failed

## Next AI Task List

1. Push the current 31 local commits so remote build can clone exact state.
2. Add `docs/runbooks/rag-remote-gpu-build.md`.
3. Add `scripts/remote/runpod_rag_full_build.py` with dry-run mode.
4. Add a command that packages local/remote index artifacts into `tar.zst`.
5. Implement RunPod lifecycle:
   - configure API key
   - create Pod
   - upload/register SSH key
   - clone repo
   - execute build
   - download artifact
   - delete Pod
6. Run R0 `fts` remote smoke.
7. Run R1 `fts,dense` remote full build.
8. Download artifact and run holdout ablation.
9. Update `lance_modalities_policy.json` only from holdout/full evidence.

## Do Not Do

- Do not run another old Qwen CPU sweep.
- Do not run full bge-m3 build locally as the main path.
- Do not enable dense globally from sampled results.
- Do not commit API keys, SSH private keys, or downloaded model cache.
- Do not cut over production before holdout gate.

## Definition Of Done For Remote GPU Phase

The remote GPU phase is complete when:

- RunPod automation can create a pod and always tear it down.
- At least one full-corpus LanceDB `fts,dense` bge-m3 artifact is downloaded.
- The artifact can be opened locally by `indexer.read_manifest_v3` and `searcher.search(..., backend="lance")`.
- Holdout eval report is generated.
- A clear decision is committed:
  - keep baseline, or
  - update policy for category-specific dense, or
  - prepare H10 cutover.

