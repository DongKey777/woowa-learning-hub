# woowa-drill-grade

AI session in-turn drill grader. Replaces the keyword-counting baseline
in `scripts/learning/scoring.py` for the LLM-as-judge path; the rule
baseline remains as fallback. Schema and storage layout are
canonicalised in
[`docs/ai-behavior-contracts.md`](../../docs/ai-behavior-contracts.md)
under the **`drill-grade-v1`** contract.

The wrapper `bin/drill-grade-prepare` writes the input artifact to
disk and prints the expected output path. The AI reads the input,
applies the rubric below, and writes a schema-conformant JSON. The
caller appends the validated output as one row to
`state/repos/<repo>/memory/drill-history.jsonl` and updates
`profile.json.cs_view`.

## When to invoke

After the learner submits a drill answer that the system has on record
(`memory/drill-pending.json` is consumed). The rule baseline runs in
parallel; if AI ↔ rule scores diverge ≥ 3 points, the case is
auto-surfaced for rubric or rule refinement.

If the AI session is unavailable, the caller falls back to
`scripts/learning/scoring.py:score_answer` and continues — drill
history is never blocked on AI presence.

## The 4-dimension rubric

Each dimension has a fixed score ceiling. Total = sum of four; clamp
to [0, 10].

### accuracy ∈ [0, 4]
*"Are the technical claims correct?"*

- **0** — major misconception (e.g. "스프링 빈은 매 요청마다 새로
  생성된다"). Answer is wrong on the central concept.
- **1** — vague but not contradictory ("뭔가 컨테이너가 관리하는
  거…"). No false claims, but no real ground.
- **2** — central concept is right but one or two factual slips
  ("싱글톤이 default라고 했지만 prototype scope 언급 없음").
- **3** — central concept right, supporting facts also right, minor
  imprecision tolerable ("DI를 통해 주입한다고 했고, 생성자/세터/필드
  중 생성자 권장이라고 함").
- **4** — every claim accurate; uses precise vocabulary
  (`@Component`/`@Bean` 차이, scope, lifecycle 등 도메인 정확).

If `expected_terms` is provided, weight coverage but don't mechanically
count tokens — a learner who paraphrases a term still earns the
points.

### depth ∈ [0, 3]
*"Did the answer go below surface definition?"*

- **0** — definition only ("Bean은 컨테이너가 관리하는 객체").
- **1** — definition + one mechanism ("싱글톤 scope이라 한 번 생성
  후 재사용").
- **2** — mechanism + reason ("싱글톤이 default인 이유는 stateless
  서비스가 대다수라 메모리·생성비용을 아끼려는 것").
- **3** — mechanism + reason + trade-off ("싱글톤이 stateful일 때 race
  condition 발생, 그래서 prototype 또는 ThreadLocal 검토").

### practicality ∈ [0, 2]
*"Can the learner apply this in code?"*

- **0** — no code, no concrete situation, all theory.
- **1** — references a code construct (`@Component`, `BeanFactory`,
  `applicationContext.xml`) or a concrete situation.
- **2** — gives a concrete usage rule ("도메인 객체는 Bean으로 등록하지
  않고 new로 생성한다, 서비스 레이어만 Bean으로") or shows what to
  avoid in practice.

### completeness ∈ [0, 1]
*"Does the answer hold together?"*

- **0** — fragmented, off-topic, or stops mid-sentence.
- **1** — beginning–middle–end. The answer reads as a coherent reply
  to the question.

### total + level

Compute `total = accuracy + depth + practicality + completeness`. Map
to `level`:

| total | level |
|-------|-------|
| 0–2   | L1    |
| 3–4   | L2    |
| 5–6   | L3    |
| 7–8   | L4    |
| 9–10  | L5    |

## Procedure

1. Run `bin/drill-grade-prepare <drill_session_id> ...` from your
   turn. Wrapper writes the input artifact and prints the expected
   output path.
2. Read the input. Inspect `question`, `answer`, `expected_terms`,
   `learning_point`, `source_doc` (optional).
3. Score each dimension by the rubric above. **Don't normalise or
   round — use the exact ceilings**.
4. Compute `total` (verified `total == sum(scores)`).
5. Compute `level` from the table.
6. List `weak_dimensions`: dimensions where the score is < 50% of
   ceiling (accuracy < 2, depth < 2, practicality < 1, completeness < 1).
   This drives the next-drill recommendation.
7. Write a one-Korean-sentence `rationale` for **every** dimension —
   even strong ones — naming the *evidence* you used. Examples:
   - accuracy: "DI 정의 정확하고 생성자 주입 권장 사유까지 맞음"
   - depth: "정의만 있고 메커니즘·이유가 없음"
   - practicality: "@Component 언급은 있으나 사용 시점/회피 사례 없음"
   - completeness: "결론에서 다시 한 번 정리해 흐름이 닫힘"
8. (Optional) `improvement_notes`: one Korean sentence on the next
   recommended drill or topic. Example: "다음에는 prototype scope의
   동시성 함정을 다루는 drill을 권장."
9. Write the output JSON to the path the wrapper printed:

```json
{
  "schema_id": "drill-grade-v1.output",
  "drill_session_id": "<copy from input>",
  "scores": {"accuracy": 3, "depth": 2, "practicality": 1, "completeness": 1},
  "total": 7,
  "level": "L4",
  "weak_dimensions": ["practicality"],
  "rationale": {
    "accuracy": "...",
    "depth": "...",
    "practicality": "...",
    "completeness": "..."
  },
  "improvement_notes": "...",
  "scored_by": "ai_session",
  "produced_at": "<ISO 8601 now>"
}
```

10. Validate before exiting:
    - `drill_session_id` matches input
    - `accuracy` ∈ [0, 4], `depth` ∈ [0, 3], `practicality` ∈ [0, 2],
      `completeness` ∈ [0, 1]
    - `total` == sum(scores)
    - `level` ∈ {L1..L5} matches the table
    - `weak_dimensions` ⊆ {accuracy, depth, practicality, completeness}
    - all four `rationale` keys present and non-empty
    - `scored_by` is exactly `"ai_session"`

The schema regression test
(`tests/unit/test_drill_grade_contract.py`) validates form. The rule
baseline (`scripts/learning/scoring.py`) runs in parallel; if your
total differs from rule baseline by ≥ 3 points, the case is flagged
for review — that's expected and useful, not a failure.

## Anti-patterns

- **Don't** inflate scores to encourage the learner. The rubric exists
  to feed `cs_view.weak_dimensions` accurately; soft scoring breaks
  the personalization loop.
- **Don't** punish the learner for terminology choice. If they
  paraphrase `@Component` as "이 클래스는 Bean으로 등록되는 표시"
  that's still accurate — count it.
- **Don't** copy the question into the rationale. Rationales should
  point to evidence in the *answer*.
- **Don't** skip a dimension's rationale to save tokens. Every key is
  required; missing one fails the schema test.

## Fallback

`scripts/learning/scoring.py:score_answer` runs deterministically on
the same input. When `scored_by` is `"rule_baseline"` the entry is
appended to `drill-history.jsonl` exactly the same shape; downstream
consumers (profile aggregation, weak-tag surfacing) treat both
sources identically. Auto-surface (≥ 3 point divergence) only fires
when both are present in the same turn.

## References

- Contract spec: `docs/ai-behavior-contracts.md` § drill-grade-v1
- Plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
  §P7.3 (Drill 채점 AI Behavior Contract) + §9 (AI Behavior Contract
  pattern)
- Wrapper: `bin/drill-grade-prepare`
- Storage: `state/repos/<repo>/memory/drill-history.jsonl`
- Rule baseline: `scripts/learning/scoring.py:score_answer`
- Level table: `LEVEL_TABLE` in `scripts/learning/scoring.py`
  (matches the table above)
