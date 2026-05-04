# Master Plan Progress

> Single-page status of where the R3 RAG initiative actually stands,
> mapped against the master plan
> (`/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`,
> 2026-05-02).
>
> When this drifts out of date, fix it before working on plan items —
> a stale progress doc is worse than no progress doc.
>
> Last updated: 2026-05-05 (Phase 9 closed loops + Phase 8 fleet built).

## Headline

**Pilot baseline locked at OVERALL 95.5%** on 200q × 6 cohort, 200q
real qrel suite, three of six cohorts at 100%. Retrieval is locally
production-runnable (state/cs_rag/), distribution to other learners
is wired through GitHub Releases, query reformulation + forbidden
filter run end-to-end through `bin/rag-ask`, daemon mode is the
default so warm latency holds at ~1.3s.

The original Pilot target was 0.85.

## Phase-by-Phase

| Phase | Title (master plan) | Status | Evidence |
|---|---|---|---|
| 0 | Step 0 안전망 (untracked commit / archive cleanup / fix branch merge) | ✅ done | early commits in May 02-04 cycle |
| 1 | System spec — corpus-agnostic | ✅ done | `docs/worklogs/rag-r3-system-spec-v1.md` |
| 2 | Corpus v3 contract spec | ✅ done | `docs/worklogs/rag-r3-corpus-v3-contract.md`, `tests/fixtures/r3_corpus_v3_schema.json` |
| 3 | Real qrel suite (200q × 6 cohort) | ✅ done | `tests/fixtures/r3_qrels_real_v1.json`, 180/200 with reformulated_query field |
| 4 | Pilot 50 docs migration | ✅ done | 41 docs with v3 contextual_chunk_prefix + 4 new v3 frontmatter docs (`docs/worklogs/rag-r3-pilot-50-docs-selection.md`) |
| 5 | System implementation alignment | ✅ done | corpus_loader v3 + indexer + R3 retrievers (lexical / dense / sparse / signal / mission_bridge / symptom_router) + post-rerank forbidden_filter |
| 6 | Pilot baseline measurement | ✅ done | `reports/rag_eval/r3_phase4_6_closing_report.md` — OVERALL 95.5% |
| 7 | Frontier model A/B (Qwen3 / gte-multilingual) | ⏳ deferred | user-flagged as "do this last after everything else"; load-bearing only if Phase 8 corpus expansion reveals encoder-bound limits |
| 8 | Whole-corpus wave migration (51 → ~500 docs) | 🟡 fleet built, unstarted | 30-worker `migration_v3` fleet + Pilot lock + corpus_lint --strict-v3 gate shipped (commits `e29ec9e`, `df7304f`, `c4c1639`). Fleet execution gated on token budget. Real corpus scale = 2,286 docs (2,217 unfrontmattered) — see Phase 8 plan in `~/.claude/plans/abundant-humming-lovelace.md`. |
| 9 | Multi-turn / personalization / safety | ✅ closed | 4-loop closure: 9.4 citation block (`2a79548`), 9.3 refusal-as-tier-downgrade (`9c8dc33`, `52e0155`, `9199c06`), 9.1 anaphora in production R3 (`d2c6471`), 9.2 personalization-aware ranking default-off (`39b95de`). 62 new unit tests added; full regression 2395 pass. |
| 10 | Production hardening + cutover | ✅ done | this cycle's Phase A items below |

## Phase A — production transfer hardening (this cycle)

| Step | Goal | Status | Commit |
|---|---|---|---|
| A1 | Index distribution via GitHub Releases | ✅ done | `d9827bf` `feat(rag-r3): index distribution via GitHub Releases — learners skip local build` |
| A2 | `bin/rag-ask --reformulated-query` end-to-end forwarding | ✅ done | `1f726fd` `feat(rag-r3): bin/rag-ask end-to-end accepts --reformulated-query` |
| A3 | wrapper-side R3 env defaults (silent degradation killer) | ✅ done | `e192f4a` (wrapper code) + `aabdc64` (AGENTS / CLAUDE / GEMINI docs) |
| A4 | daemon warm service activated by default | ✅ done | `e192f4a` (wrapper) — measured cold 25s → warm 1.3s |
| A5 | unit + release-fetch test coverage | ✅ done | `85c8e98` `test(rag-r3): cover daemon reformulation forwarding + release fetch` |
| A6 | user memory entry on local-build infeasibility | ✅ done | `memory/project_index_distribution.md` |
| A7 | this progress doc | ✅ done | (this commit) |

## Phase 9 — closed-loop wiring (this cycle)

| Step | Goal | Status | Commit |
|---|---|---|---|
| 9.4 | pre-rendered `참고:` citation block in augment + rag-ask | ✅ done | `2a79548` `feat(rag-9.4): pre-rendered 참고: citation block in augment + rag-ask` |
| 9.3-A | R3Config.refusal_threshold + cross-encoder confidence sentinel | ✅ done | `9c8dc33` `feat(rag-9.3): R3Config.refusal_threshold + cross-encoder confidence sentinel` |
| 9.3-CD | augment detects sentinel + rag-ask forces tier 0 | ✅ done | `52e0155` `feat(rag-9.3): tier_downgrade contract — augment detects sentinel + rag-ask forces tier 0` |
| 9.3-EF | cohort_eval reform + calibration script + agent docs | ✅ done | `9199c06` `feat(rag-9.3): cohort_eval reform (tier_downgraded vs silent_failure) + calibration script + agent docs` |
| 9.1 | production R3 anaphora — reformulation primary, regex fallback | ✅ done | `d2c6471` `feat(rag-9.1): production R3 anaphora — reformulation primary, regex fallback` |
| 9.2 | personalization-aware fusion-stage ranking (default off) | ✅ done | `39b95de` `feat(rag-9.2): personalization-aware fusion-stage ranking (default off)` |

Activation knobs (default off — ship safe, opt in):
- `WOOWA_RAG_REFUSAL_THRESHOLD=<float>` — calibrate first via `python -m scripts.learning.rag.r3.eval.calibrate_refusal_threshold`
- `WOOWA_RAG_PERSONALIZATION_ENABLED=1` — flip on after Phase 8 corpus migration brings v3 concept_id coverage above ~30%

## Phase 8 — migration fleet (built, unstarted, this cycle)

| Step | Goal | Status | Commit |
|---|---|---|---|
| 8-tools | locked_pilot_paths.json + create_v3_frontmatter + synthesize_chunk_prefix | ✅ done | `e29ec9e` `feat(rag-r3): Phase 8 v3 migration tools — lock + frontmatter synth + prefix authoring helper` |
| 8-fleet | 30-worker `migration_v3` fleet + Pilot lock gate + corpus_lint --strict-v3 branch | ✅ done | `df7304f` `feat(rag-r3): Phase 8 v3 migration worker fleet + Pilot lock gate` |
| 8-tests | regression coverage (40 cases) | ✅ done | `c4c1639` `test(rag-r3): Phase 8 v3 migration regression coverage` |

Fleet is callable via `bin/orchestrator fleet-start --profile migration_v3` but **must not run** until token budget allows. Phase 9.2 personalization activation is gated on this fleet's execution.

## What's locked in

- **Production index** (`state/cs_rag/`) — 27,238 chunks, FTS + dense
  + sparse, BGE-M3 1024-dim, built from corpus@`029ec00`. Released as
  `index-v1.0.0-corpus@029ec00` on GitHub Releases (sha256
  `fce0d36685fd0d1b08d1bc991aaca29a4a41a3f21b6478cd3a812927e5256c51`,
  129 MB).
- **Runtime config** — `WOOWA_RAG_R3_ENABLED=1`,
  `WOOWA_RAG_R3_RERANK_POLICY=always`,
  `WOOWA_RAG_R3_FORBIDDEN_FILTER=1`, `HF_HUB_OFFLINE=1` enforced by
  `bin/_rag_env.sh` sourced from every wrapper.
- **Query side lever** — `reformulated_query` flows through
  `bin/rag-ask` → `cli.py` → `integration.augment` → `searcher.search`
  → `r3.search.search`. Daemon path forwards it via the HTTP payload.
- **Forbidden filter** — post-rerank stage in `r3.search.search`,
  reads `concepts.v3.json` for top-1's forbidden_neighbors and drops
  matching candidates from rank 2..N.
- **Cohort eval gate** — `python -m scripts.learning.rag.r3.eval.cohort_eval`
  with `--use-reformulated-query` is the canonical regression check.
  Re-run before any corpus or runtime config change.

## Open levers (deferred — none of them are load-bearing on 95.5%)

| Lever | Expected delta | Why deferred |
|---|---|---|
| chunk-level Anthropic contextual retrieval | +1-3pp on long-doc paraphrase | Bundled with Phase 8 — most of the long-doc payoff is on docs that don't exist yet |
| fusion weight tuning per cohort | Recover the confusable -2.5pp regression | Marginal at the 95.5% level; risk of new neighbor-cohort regression for 1q gain |
| Qwen3-Embedding / Qwen3-Reranker / gte-multilingual A/B | Unknown; published numbers slightly higher than BGE-M3 | Better measured against an expanded Phase 8 corpus where encoder differences amplify |
| Phase 8 corpus wave (51 → ~500 docs) | Breadth: covers more learner queries that are presently `corpus_gap` correctly-refused | User-flagged as "after everything else" |
| reranker batching / model swap | p95 700ms (plan §1.5) | Current warm 1.3s is acceptable for the learner UX; latency budget is a Phase 10 polish item |

## Next actions (when the user asks for them)

The closing report's "Next" pointer was *"Phase 7 frontier model A/B
and chunk-level Anthropic contextual context generation are now
optional ceilings"*. That still holds. For practical purposes the
next chunk of work the user has flagged is "fix anything else
non-Phase-7-or-8 that's still rough". Currently all of the Phase A
items are done.

When Phase 7 / 8 are unfrozen, the path is:

1. Ship Phase 8 corpus wave commits in batches of 50 docs, re-run
   cohort_eval after each batch, never more than 1pp regression in
   any cohort.
2. After the corpus wave plateaus, run the encoder A/B from Phase 7
   on the expanded corpus (the encoder differences will be more
   visible on the wider distribution).
3. If chunk-level Anthropic contextual retrieval is in scope by
   then, run it as Phase 8.5 — long-doc bias means it pairs naturally
   with the wave migration that adds long deep-dive docs.

## How to verify in 60 seconds

```bash
# 1. cohort_eval baseline replay
python -m scripts.learning.rag.r3.eval.cohort_eval \
  --qrels tests/fixtures/r3_qrels_real_v1.json \
  --out /tmp/replay.json \
  --index-root state/cs_rag \
  --catalog-root knowledge/cs/catalog \
  --top-k 5 --mode full \
  --use-reformulated-query
# Expected: OVERALL 0.955

# 2. End-to-end production path
bin/rag-daemon stop
bin/rag-ask "Spring Bean이 뭐야?" --reformulated-query "Spring Bean 기초 primer"
# Expected: top-1 contents/spring/spring-bean-di-basics.md, ~25s cold

bin/rag-ask "MVCC가 뭐야?" --reformulated-query "MVCC consistent read"
# Expected: top-1 contents/database/mvcc-... , ~1.3s warm

# 3. Release fetch path (after deleting state/cs_rag/)
mv state/cs_rag /tmp/cs_rag_backup
HF_HUB_OFFLINE=1 bin/cs-index-build
# Expected: "release_fetch=fetched — skipping local build" + state/cs_rag/ restored in ~30s
```

If any of these three checks fails, the Pilot baseline is broken
somewhere — start with the closing report and the failing check's
trace.
