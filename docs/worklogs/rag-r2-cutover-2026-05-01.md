# RAG R2 Production Cutover - 2026-05-01

Objective: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`

## Decision

The original Phase 1 cutover gates failed, but the user explicitly approved
Option C risky cutover on 2026-05-01:

- corpus expansion is expected to make the Lance stack more valuable;
- root cause is assumed to be outside the embedding model itself;
- retrieval quality can be improved after the system is cut over and stable.

This worklog records the executed cutover and the safeguards retained for
rollback.

## Failed Local Attempt

The preserved R2 artifact from commit `6eb3764` was first extracted and
promoted, but its manifest carried corpus hash
`904a974f74ec661cb0f29f274e507408f93587c0ad7668d4d2be19972cbe8179`.
Current `knowledge/cs` hash is
`5e0eb308e60102df545a8f8c8f3ab326fb3d270b29080ba4d8072dcb7047d794`,
so `bin/rag-ask` correctly returned `rag_ready=false`, reason
`corpus_changed`.

A local Lance incremental rebuild attempted to update the 144 changed chunks,
but failed after encoding with:

```text
'pyarrow.lib.DataType' object has no attribute 'value_field'
```

That stale attempt was moved aside at:

```text
state/cs_rag_lance_stale_20260501T061201Z
```

Legacy v2 was restored before the remote build so learner-facing RAG did not
remain in a stale/no-hit state.

## Remote Rebuild

RunPod A5000, A6000, and 4090 community placement attempts failed due capacity.
The successful build used L40S community:

- run id: `r2-181d7b9-2026-05-01T0618`
- pod id: `pgtgev20qbfue2`
- artifact path:
  `artifacts/rag-full-build/r2-181d7b9-2026-05-01T0618/cs_rag_index_root.tar.zst`
- artifact sha256:
  `a1f61d6c8b891eb5a254461eb501f82ec14e47f0d3595e590b074321985533b3`
- estimated cost: `$0.1287`
- pod terminated: yes

Artifact manifest:

```json
{
  "index_version": 3,
  "row_count": 27157,
  "corpus_hash": "5e0eb308e60102df545a8f8c8f3ab326fb3d270b29080ba4d8072dcb7047d794",
  "encoder": {
    "model_id": "BAAI/bge-m3",
    "model_version": "BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181",
    "max_length": 512,
    "batch_size": 64
  },
  "modalities": ["fts", "dense", "sparse"],
  "ivf": {
    "num_partitions": 256,
    "num_sub_vectors": 64
  }
}
```

Remote holdout report copied to:

```text
reports/rag_eval/r2_181d7b9_remote_holdout_20260501T0618.json
```

Key measured values for `fts,dense,sparse`:

- category macro primary nDCG: `0.9416028732066558`
- language macro primary nDCG: `0.9278471316207187`
- micro primary nDCG: `0.9134837574964645`
- Korean primary nDCG: `0.8666666666666667`
- forbidden rate: `0.0`
- hard regression failures: `10`
- warm P95 in eval: `1107.5207106769085 ms`

## Production Swap

The remote artifact was extracted to:

```text
state/cs_rag_next_20260501T063445Z
```

Manifest validation passed for:

- `index_version == 3`
- `encoder.model_id == "BAAI/bge-m3"`
- `row_count == 27157`
- current corpus hash `5e0eb308e60102df545a8f8c8f3ab326fb3d270b29080ba4d8072dcb7047d794`
- modalities `fts,dense,sparse`
- IVF `256/64`

Atomic swap result:

```text
state/cs_rag                         # Lance R2 production
state/cs_rag_archive/v2_20260501T063445Z
```

`indexer.is_ready("state/cs_rag", corpus_root="knowledge/cs")` returns:

```text
state=ready reason=ready
```

## Smoke

`bin/rag-ask` and `bin/coach-run` were updated to prefer `.venv/bin/python`,
matching `bin/cs-index-build` and `bin/rag-eval`. Without that wrapper fix,
system `python3` lacked `lancedb` and Lance search degraded to
`search_error`.

Offline smoke results after the wrapper fix:

| Prompt | Tier | Backend | Ready | Hits |
|---|---:|---|---|---:|
| `트랜잭션 격리수준이란` | 2 | `lance` | `true` | 5 |
| `Spring Bean이 뭐야` | 2 | `lance` | `true` | 5 |
| `RAG로 깊게 What is dependency injection` | 2 | `lance` | `true` | 5 |

The English DI smoke uses an explicit RAG override because the plain English
prompt routes to tier 0.

## Rollback

Rollback runbook verified:

```text
docs/runbooks/rag-rollback.md
```

Use `state/cs_rag_archive/v2_20260501T063445Z` as the preserved legacy v2
source if the Lance production runtime must be reverted.

## Follow-Up

- Monitor local CPU latency. First warm full-mode Lance smoke took roughly
  6-10 seconds locally.
- Investigate the 14-query failure taxonomy and cross-category mis-retrieval.
- Evaluate `bge-reranker-v2-m3` as the next reranker candidate.
- Continue Phase 4 Korean/context improvements independently of the cutover.
