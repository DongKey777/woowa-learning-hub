# R3 Cutover Packet - 2026-05-02

> **🔴 DEPRECATED — historical record only**
>
> This packet was authored while the R3 system was running with the *circular
> qrel validation leak* active: corpus v2 `expected_queries` were appended into
> chunk indexing channels (`lexical_sidecar:aliases`, `chunk.body`,
> Tantivy FTS, `sidecar:body`). The 208q backend-compare gate that this
> packet cites as "all metrics 1.0" therefore measures *alias indexing
> regression*, not *retrieval quality*. The structural fix landed in commit
> `054a1a3 fix(rag-corpus): drop expected_queries from chunk indexing channels`
> and the underlying baseline reports moved to
> `reports/rag_eval/archive/2026-05-02-circular-leak-baseline/` (see that
> folder's README for the leak mechanism).
>
> Do not treat this packet as a production go-live record. The real cutover
> packet will be authored after Phase 4-6 (corpus v3 contract + Real qrel
> suite + Pilot 50 docs measurement) per
> `docs/worklogs/rag-r3-system-spec-v1.md` (forthcoming) and the matching
> `docs/worklogs/rag-r3-corpus-v3-contract.md`. Until then,
> `config/rag_models.json` keeps `selected_artifact / backend / runtime_policy`
> as `null` and learners continue to be served by the legacy v2 archive
> (`state/cs_rag_archive/v2_current_20260502T1101Z`).
>
> Plan reference: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
> Section 0 (Principle Correction) and Section 9 (immediate execution).

Decision: cut over the CS RAG runtime to R3 local serving over the verified
remote-built LanceDB artifact `r3-61216f2-2026-05-02T0937`, with current runtime
commit `788ee99e67b7131e647684592d53bd268eef93f0`.

## Selected Runtime

```text
remote-built LanceDB v3 index
+ BGE-M3 dense first-stage retrieval
+ BGE-M3 sparse first-stage sidecar
+ metadata lexical sidecar
+ signal retriever
+ fusion v2 runtime
+ sidecar-first auto rerank policy
```

Selected index artifact:

- archive: `artifacts/rag-full-build/r3-61216f2-2026-05-02T0937/cs_rag_index_root.tar.zst`
- artifact sha256: `5eab5b0fb9def8c0c58370eb64abbbbf6fb195c95bc6d4376832c654c3a78e0d`
- build commit: `61216f25cc219bae945cbc49d7c06bb7d2f9d5be`
- runtime commit: `788ee99e67b7131e647684592d53bd268eef93f0`
- row count: `27158`
- corpus hash: `c002a92b2b97033d5ff3f0a9c94d3c952586107337e3a07cd66e9c943643cacb`

## Evidence

| Gate | Evidence | Result |
|---|---|---|
| Strict remote artifact import | `.venv/bin/python -m scripts.remote.artifact_contract artifacts/rag-full-build/r3-61216f2-2026-05-02T0937 --strict-r3 --verify-import` | passed |
| 208q production qrel gate | `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T1052Z.summary.json` | all candidate/final primary/relevant metrics at 5/20/50/100 are `1.0`; Korean and mixed cohorts are `1.0`; forbidden hits `0` |
| Local R3 smoke | `reports/rag_eval/r3_61216f2_runtime_788ee99_local_smoke_20260502T1059Z.json` | cheap/full/direct Korean-mixed/daemon/forced reranker paths execute |
| Warm local daemon | same smoke report | second daemon full request `latency_ms=1020`, first hit `contents/network/latency-bandwidth-throughput-basics.md` |
| Forced BGE reranker | same smoke report | `BAAI/bge-reranker-v2-m3` loaded and reranked 20 pairs |
| Rollback current corpus | `reports/rag_eval/r3_legacy_rollback_current_corpus_smoke_20260502T1104Z.json` | legacy v2 archive is `ready` and searchable |
| RunPod cleanup | direct API check after failed latest-HEAD attempts | pod count `0`, active pod count `0` |

## Root-Cause Closure

Two non-cosmetic retrieval defects were closed before this packet:

- Dense pollution: Corpus v2 retrieval anchors were appended into chunk bodies
  and therefore embedded into dense vectors. The loader now preserves anchors
  for FTS/sidecar/reranking while using original chunk text as `embedding_body`.
- Alias under-weighting: exact Corpus v2 aliases/expected queries could appear
  at rank 1 in the lexical sidecar yet lose during fusion. Fusion v2 raises the
  alias sidecar weight so curated retrieval-contract anchors win without
  changing the dense index.

The final 208q gate and local service-locator smoke verify the repaired path.

## Rollback

Actual rollback index:

```text
state/cs_rag_archive/v2_current_20260502T1101Z
```

This archive was rebuilt against the current corpus and smoke-tested as
`ready`. The older `state/cs_rag_archive/v2_20260501T063445Z` remains preserved
but is stale against the expanded corpus.

Rollback runbook: `docs/runbooks/rag-rollback.md`.

## Risk Notes

- Latest-HEAD remote rebuilds after `61216f2` were blocked by RunPod pod
  disappearance, not by index code failure. The selected artifact is still a
  remote-built production index; the latest runtime was verified against it.
- The next index-affecting rebuild should use a stable/dedicated GPU provider
  or a persistent transfer path before replacing the selected artifact.
- `BAAI/bge-reranker-v2-m3` is the target quality reranker, but local default
  policy remains `auto` because the sidecar-first gate is green and warm daemon
  latency is interactive.

## Operator Commands

Production verify:

```bash
HF_HUB_OFFLINE=1 WOOWA_RAG_R3_RERANK_POLICY=auto \
  .venv/bin/python -m scripts.learning.rag.r3.eval.backend_compare \
  --qrels reports/rag_eval/r3_corpus_v2_qrels_20260502T0757Z.json \
  --out reports/rag_eval/r3_backend_compare_208q_production_r3_auto_<timestamp>.json \
  --index-root state/cs_rag \
  --backend production-r3:r3 \
  --top-k 100 \
  --window 5 --window 20 --window 50 --window 100 \
  --forbidden-window 5 \
  --no-reranker
```

Local serving smoke:

```bash
HF_HUB_OFFLINE=1 WOOWA_RAG_R3_RERANK_POLICY=auto \
  bin/rag-ask "RAG로 깊게 latency가 뭐야?" --via-daemon
```

Forced quality reranker smoke:

```bash
HF_HUB_OFFLINE=1 WOOWA_RAG_R3_RERANK_POLICY=always \
  bin/rag-ask "RAG로 깊게 latency가 뭐야?"
```
