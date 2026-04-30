# woowa-rag-rewrite

AI session in-turn query rewriter for the CS RAG retrieval pipeline. This
skill instructs the AI on how to fill the output artifact created by the
`bin/rag-rewrite-prepare` wrapper. Schema and storage layout are canonicalised
in [`docs/ai-behavior-contracts.md`](../../docs/ai-behavior-contracts.md)
under the **`query-rewrite-v1`** contract.

The AI is the *caller* of `bin/rag-rewrite-prepare`. The wrapper writes the
input artifact to disk and prints the expected output path. The AI then
reads the input, follows the procedure here, and writes a schema-conformant
JSON to the output path. Downstream `searcher.search()` reads the output
when present, or falls back to PRF (P4.3) when missing.

## When to invoke

Inside a coaching turn, when the learner's prompt is ambiguous, colloquial,
or so compound that a single dense retrieval underperforms. Concretely:

- learner uses 조사/구어체 ("스프링 빈 뭐야?") — `mode=normalize`
- learner asks a multi-part question ("DI랑 IoC 차이가 뭐고 언제 써야 해?") —
  `mode=decompose`
- learner asks a factual question with no obvious tokens ("MVCC가
  격리수준이랑 무슨 관계야?") — `mode=hyde`

If the prompt is already concrete and dense-friendly, do NOT invoke this
skill — the deterministic path handles it.

## Procedure

1. Run `bin/rag-rewrite-prepare <prompt_text>` from your turn. The wrapper
   prints the input path and the expected output path. Read the input
   path with the Read tool.

2. Inspect the input fields:
   - `prompt`: the original learner question.
   - `mode`: one of `hyde`, `decompose`, `normalize`. Defaults to whatever
     the wrapper inferred; you MAY override by writing the output with a
     different rationale that matches a different mode.
   - `learner_context`: experience level + mastered/uncertain concepts.
     Use this to calibrate vocabulary (e.g. don't introduce
     `concept_id=spring/bean` jargon if it's listed in `uncertain_concepts`).

3. Produce 1–3 rewrites following the mode:
   - **hyde**: write a one- to two-sentence *hypothesised answer* in the
     learner's domain language. The retriever embeds this string and
     searches dense; the answer doesn't need to be correct, only
     domain-shaped.
   - **decompose**: emit 2–3 sub-queries, each a self-contained question.
     Each sub-query is rewritten in the learner's language (Korean if the
     prompt is Korean).
   - **normalize**: produce one rewritten query that strips 조사 / 구어체
     / interjections while preserving intent. Example: "스프링 빈 뭐야"
     → "스프링 빈의 정의".

4. For each rewrite include `text` (the rewritten string) and `rationale`
   (one Korean sentence explaining why this form helps retrieval).

5. Write the output JSON to the path the wrapper printed. The schema is:

```json
{
  "schema_id": "query-rewrite-v1.output",
  "prompt_hash": "<copy from input>",
  "rewrites": [
    {"text": "...", "rationale": "..."},
    ...
  ],
  "confidence": 0.0,
  "scored_by": "ai_session",
  "produced_at": "<ISO 8601 now>"
}
```

6. Validate before exiting the turn:
   - `prompt_hash` matches input
   - 1 ≤ `len(rewrites)` ≤ 3
   - every entry has non-empty `text` AND non-empty `rationale`
   - `confidence` in [0.0, 1.0]
   - `scored_by` is exactly `"ai_session"`

7. The schema regression test
   (`tests/unit/test_query_rewrite_contract.py`) validates form only.
   *Content* quality is tracked through learner feedback (P7.1) — write
   honest rewrites; the system learns from `feedback.jsonl` over time.

## Anti-patterns

- **Don't** invent terms the learner hasn't met. If
  `uncertain_concepts` contains `concept_id=database/mvcc`, don't
  rewrite "MVCC 뭐야?" → "Multi-Version Concurrency Control의 read view
  메커니즘" — that pushes the retrieval toward advanced docs the learner
  isn't ready for.
- **Don't** translate Korean prompts to English unless `learner_context.
  experience_level == "advanced"` AND the mode is `hyde`. Default
  retrieval works on Korean queries.
- **Don't** emit more than 3 rewrites. Diminishing returns; the
  retriever fuses results so a 4th rewrite mostly adds noise.
- **Don't** skip the wrapper. The wrapper records `produced_at` and the
  input artifact for reproducibility; calling the AI without the
  wrapper leaves no audit trail.

## Fallback

When the AI session is not available (e.g. cron job, batch retrieval,
or the wrapper times out), `searcher.search()` falls back to PRF/RM3
(P4.3, `scripts/learning/rag/prf.py`). The PRF path is deterministic —
it runs an initial retrieval, extracts top tokens, and runs a second
expanded retrieval. Less precise than HyDE, but always available.

The retriever picks the AI rewrites when present
(`state/cs_rag/query_rewrites/<prompt_hash>.output.json` exists and
validates) and PRF otherwise.

## References

- Contract spec: `docs/ai-behavior-contracts.md` § query-rewrite-v1
- Plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
  §P4.2 (AI session in-turn query 재작성) + §9 (AI Behavior Contract
  pattern)
- Wrapper: `bin/rag-rewrite-prepare`
- Storage: `state/cs_rag/query_rewrites/<prompt_hash>.{input,output}.json`
- Fallback: `scripts/learning/rag/prf.py` (P4.3)
