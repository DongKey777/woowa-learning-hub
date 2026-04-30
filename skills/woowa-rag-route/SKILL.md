# woowa-rag-route

AI session in-turn router fallback for the CS RAG Tier classifier. The
deterministic heuristic in `interactive_rag_router.classify()` handles
~90% of prompts; this Skill instructs the AI on what to do when the
heuristic returns low confidence and asks for a second opinion. Schema
and storage layout are canonicalised in
[`docs/ai-behavior-contracts.md`](../../docs/ai-behavior-contracts.md)
under the **`router-fallback-v1`** contract.

The wrapper `bin/rag-route-fallback` writes the input artifact to disk
and prints the expected output path. The AI reads the input, picks a
tier from `candidate_tiers`, and writes a schema-conformant JSON line
that the caller appends to
`state/repos/<repo>/logs/routing_ai_decisions.jsonl`.

## When to invoke

The Tier classifier delegates to AI only when:

- the heuristic decision's `confidence < threshold` (default 0.55), AND
- the learner is in an active coaching session (AI session is in-turn)

If the heuristic confidence is high, the deterministic path wins —
**do NOT invoke this Skill**. Round-tripping through AI for the easy
90% wastes Pro quota and adds latency.

## Procedure

1. Run `bin/rag-route-fallback <prompt> [--heuristic-tier N --heuristic-confidence X --matched-tokens "tok1,tok2"]`
   from your turn. The wrapper prints `{input_path, output_path}`.
   Read `input_path` with the Read tool.

2. Inspect:
   - `prompt`: original learner question.
   - `history_summary` (optional): last 1–2 turn topics so you can
     detect topic drift (e.g., learner asked Spring Bean DI for 3
     turns; this turn's "어떻게 잘 쪼개?" probably continues the same
     topic, not a fresh one).
   - `candidate_tiers`: the *allowed* tiers (often `[0,1,2,3]` but may
     exclude tier 3 when preconditions are missing — e.g. no PR open).
   - `heuristic_decision`: what the deterministic classifier wanted +
     why it's unsure. Treat as a strong prior; only override when the
     evidence is clear.

3. Pick a tier ∈ `candidate_tiers`:

   - **Tier 0** — *skip RAG*. Tool/build question, off-topic chat, or
     prompt is so vague no retrieval helps ("아 그럼 다음은?", "ㅇㅋ").
   - **Tier 1 (cheap)** — single concept definition. Cheap dense
     retrieval, top-3, no rerank: "스프링 빈이 뭐야?".
   - **Tier 2 (full)** — comparison, depth, "왜 필요해", "어떻게
     동작해". Full hybrid + rerank: "@Component vs @Repository 차이?",
     "MVCC가 격리수준이랑 어떤 관계?".
   - **Tier 3 (coach)** — learner is asking about *their own
     mission code or PR*. Round-trips to `bin/coach-run`. Pick this
     only when `coach-run` is in `candidate_tiers` AND the prompt
     references their PR/branch/file.

4. Pick a `mode` consistent with the tier:
   - tier 0 → `"skip"`
   - tier 1 → `"cheap"`
   - tier 2 → `"full"`
   - tier 3 → `"coach"`

5. Write a one-Korean-sentence `rationale` that names the *evidence*
   you used. Examples:
   - "도메인 토큰 없고 도구 질문이라 tier 0"
   - "정의 시그널만 있고 비교/깊이 없음 → tier 1"
   - "vs/차이 시그널 + 도메인 토큰 둘 다 있어 tier 2"
   - "PR open 상태 + 본인 코드 직접 가리킴 → tier 3 coach"

6. Set `confidence` to your own subjective certainty in [0, 1]. Lower
   values surface the case for human review during weekly
   `bin/routing-analyze`.

7. Write the output JSON to the path the wrapper printed:

```json
{
  "schema_id": "router-fallback-v1.output",
  "prompt_hash": "<copy from input>",
  "tier": 1,
  "mode": "cheap",
  "confidence": 0.7,
  "rationale": "정의 시그널만 있고 비교/깊이 없음 → tier 1",
  "scored_by": "ai_session",
  "produced_at": "<ISO 8601 now>"
}
```

8. Validate before exiting the turn:
   - `prompt_hash` matches input
   - `tier` ∈ `candidate_tiers`
   - `mode` ∈ {"skip", "cheap", "full", "coach"}
   - tier ↔ mode pairing matches the table in step 4
   - `confidence` in [0, 1]
   - `rationale` non-empty Korean sentence
   - `scored_by` is exactly `"ai_session"`

The schema regression test
(`tests/unit/test_router_fallback_contract.py`) validates form. The
caller (router) appends the validated output as one JSONL row to
`state/repos/<repo>/logs/routing_ai_decisions.jsonl` for post-hoc
analysis (P5.2 + P7.2).

## Anti-patterns

- **Don't** pick a tier outside `candidate_tiers`. The wrapper passes
  the allowed set so we don't surface a `tier=3 coach` decision when
  PR preconditions aren't met.
- **Don't** override the heuristic when both decisions agree but you
  *feel* differently. The heuristic asked you because it was unsure,
  not because it was wrong. Disagreement should be evidence-driven.
- **Don't** invent an experience-level promotion. Tier promotion based
  on learner profile is the heuristic's job (`promoted_by_profile`),
  not the AI's.
- **Don't** mix tier and mode (e.g. `tier=1, mode="full"`). Pairing is
  a hard contract.

## Fallback

When the AI session is unavailable (cron job, batch run, or AI
unreachable), the caller logs the heuristic raw decision with
`ai_unavailable=true` and proceeds. Less precise than AI fallback but
always available — the system never blocks on AI presence.

## References

- Contract spec: `docs/ai-behavior-contracts.md` § router-fallback-v1
- Plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
  §P4.4 (AI session in-turn router fallback) + §9 (AI Behavior
  Contract pattern)
- Wrapper: `bin/rag-route-fallback`
- Storage: `state/repos/<repo>/logs/routing_ai_decisions.jsonl`
- Heuristic source: `scripts/workbench/core/interactive_rag_router.py`
  (`classify()` + tier preconditions)
