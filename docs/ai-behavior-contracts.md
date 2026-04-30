# AI Behavior Contracts

Catalog of AI session in-turn components. Each contract pairs a deterministic
shell wrapper (creates input artifact + expected output path) with a Skill
file (instructs the AI on how to fill the output) and a schema regression
test (validates output shape only — content quality is tracked via learner
feedback).

This document is the canonical registry. Adding a new contract means landing
all five elements in lock-step:

1. **Input/Output JSON Schema** — recorded here under the contract section
2. **Skill file** — `skills/woowa-<task>/SKILL.md`
3. **Trigger wrapper** — `bin/<task>-prepare` (creates artifacts; never
   calls the AI directly)
4. **Storage layout** — disk path for input/output JSON
5. **Schema regression test** — `tests/unit/test_<contract>_contract.py`

Plan reference: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md`
§9 ("AI Behavior Contract 패턴 정의").

---

## Contract registry

| Contract id | Phase | Wrapper | Skill | Storage | Fallback |
|-------------|-------|---------|-------|---------|----------|
| `query-rewrite-v1` | P4.2 | `bin/rag-rewrite-prepare` | `skills/woowa-rag-rewrite/SKILL.md` | `state/cs_rag/query_rewrites/<key>.{input,output}.json` | PRF / RM3 (P4.3) |
| `router-fallback-v1` | P4.4 | `bin/rag-route-fallback` | `skills/woowa-rag-route/SKILL.md` | `state/repos/<repo>/logs/routing_ai_decisions.jsonl` | heuristic raw decision (P5.2 logs `ai_unavailable=true`) |
| `drill-grade-v1` | P7.3 | `bin/drill-grade-prepare` | `skills/woowa-drill-grade/SKILL.md` | `state/repos/<repo>/memory/drill-history.jsonl` | rule baseline (`scripts/learning/scoring.py`) |

Naming convention: `<task>-v1`. Bump the suffix only on backward-incompatible
schema changes; additive-optional fields can stay on the same version.

---

## Contract 1 — `query-rewrite-v1`

**Purpose**: AI session re-writes a learner query for retrieval, e.g. HyDE
(hypothesised answer), decomposition (compound → sub-queries), or
normalisation (콜로키얼/조사 제거 → 정형). Output drives an additional
retrieval pass alongside the original query.

**Trigger flow** (plan §9 element 3):
1. AI receives a learner question inside a coaching turn
2. AI invokes `bin/rag-rewrite-prepare <prompt_hash>` with the prompt
   payload (a CLI wrapper, so the AI calls it from its own turn — no
   external API hop)
3. Wrapper writes the *input artifact* and prints the *expected output
   path* to stdout
4. AI reads the input artifact, follows `skills/woowa-rag-rewrite/SKILL.md`
   to produce JSON, writes to the expected output path
5. `searcher.search()` (or a downstream caller) reads the output JSON and
   uses the rewrites; if the file is missing, falls back to PRF (P4.3)

**Input schema** (`<key>.input.json`):
```json
{
  "schema_id": "query-rewrite-v1.input",
  "prompt_hash": "sha1 hex",
  "prompt": "원본 학습자 질문",
  "learner_context": {
    "experience_level": "beginner|intermediate|advanced|null",
    "mastered_concepts": ["concept_id", ...],
    "uncertain_concepts": ["concept_id", ...],
    "recent_topics": ["..."]
  },
  "mode": "hyde|decompose|normalize",
  "produced_at": "ISO 8601"
}
```

**Output schema** (`<key>.output.json`):
```json
{
  "schema_id": "query-rewrite-v1.output",
  "prompt_hash": "sha1 hex (matches input)",
  "rewrites": [
    {"text": "재작성된 query 또는 hypothesised answer", "rationale": "왜 이렇게 재작성했는지 한 줄"},
    ...
  ],
  "confidence": 0.0,
  "scored_by": "ai_session",
  "produced_at": "ISO 8601"
}
```

**Validation rules**:
- `prompt_hash` in output MUST equal input `prompt_hash`
- `rewrites` non-empty array; each entry has `text` (non-empty string) +
  `rationale` (non-empty string)
- `confidence` in [0.0, 1.0]
- `scored_by` is the literal `"ai_session"`

**Storage location**:
- Input: `state/cs_rag/query_rewrites/<prompt_hash>.input.json`
- Output: `state/cs_rag/query_rewrites/<prompt_hash>.output.json`
- TTL: 30 days (caller cleans up; sidecar is gitignored under `state/`)

**Schema regression test**: `tests/unit/test_query_rewrite_contract.py`

**Fallback** (when AI session unavailable, e.g. cron job or stale cache):
- `scripts/learning/rag/prf.py` (P4.3) — Pseudo-Relevance Feedback /
  RM3, deterministic. searcher reads `state/cs_rag/query_rewrites/`
  first; on miss, runs PRF.

---

## Contract 2 — `router-fallback-v1`

**Purpose**: When the heuristic Tier router (`interactive_rag_router.py`)
returns low confidence, defer to AI session classification. Used only for
the modal 10% of ambiguous prompts; the deterministic 90% never round-trips
through the AI.

**Trigger flow**:
1. `classify()` computes a tier + confidence from token rules
2. If `confidence < threshold` AND AI session is in-turn, AI invokes
   `bin/rag-route-fallback <prompt_hash>` (wrapper writes input artifact)
3. AI reads, runs Skill, writes output JSON
4. `classify()` reads back, uses `tier` + `mode` + `rationale`
5. Decision (and `ai_unavailable` flag if no AI) appended to
   `state/repos/<repo>/logs/routing_ai_decisions.jsonl`

**Input schema** (`<key>.input.json`):
```json
{
  "schema_id": "router-fallback-v1.input",
  "prompt_hash": "sha1 hex",
  "prompt": "학습자 질문",
  "history_summary": "최근 turn 토픽 요약 (옵션)",
  "candidate_tiers": [0, 1, 2, 3],
  "heuristic_decision": {
    "tier": 1,
    "confidence": 0.42,
    "matched_tokens": ["..."]
  },
  "produced_at": "ISO 8601"
}
```

**Output schema** (`<key>.output.json`):
```json
{
  "schema_id": "router-fallback-v1.output",
  "prompt_hash": "sha1 hex (matches input)",
  "tier": 0,
  "mode": "skip|cheap|full|coach",
  "confidence": 0.0,
  "rationale": "왜 이 tier를 골랐는지 한국어 한 줄",
  "scored_by": "ai_session",
  "produced_at": "ISO 8601"
}
```

**Validation rules**:
- `tier` ∈ candidate_tiers
- `mode` ∈ {"skip", "cheap", "full", "coach"}
- `confidence` ∈ [0.0, 1.0]
- `rationale` non-empty

**Storage**: append-only `state/repos/<repo>/logs/routing_ai_decisions.jsonl`.
Each entry one full output object. Wrapper supports re-reading by
prompt_hash for cache hits.

**Schema regression test**: `tests/unit/test_router_fallback_contract.py`

**Fallback**: heuristic raw decision (no AI). Log entry includes
`ai_unavailable=true` so post-hoc analysis can distinguish AI-influenced
classifications from pure-heuristic.

---

## Contract 3 — `drill-grade-v1`

**Purpose**: AI session grades a learner's drill answer on the 4-dimension
rubric (accuracy / depth / practicality / completeness) and emits scores +
rationale. Replaces the keyword-counting baseline in
`scripts/learning/scoring.py` for the LLM-as-judge path; the rule baseline
remains as fallback.

**Trigger flow**:
1. Learner submits a drill answer
2. `bin/drill-grade-prepare <drill_session_id>` writes input artifact
3. AI reads, follows Skill rubric, writes output JSON
4. Scoring code reads output, validates schema, appends to
   `drill-history.jsonl`. Difference from `scripts/learning/scoring.py`
   ≥ 3 points → flag for review

**Input schema** (`<key>.input.json`):
```json
{
  "schema_id": "drill-grade-v1.input",
  "drill_session_id": "uuid or stable id",
  "question": "drill 질문 본문",
  "answer": "학습자 답안",
  "expected_terms": ["기대 키워드/개념"],
  "learning_point": "concept_id",
  "source_doc": "knowledge/cs/contents/.../doc.md (옵션)",
  "produced_at": "ISO 8601"
}
```

**Output schema** (`<key>.output.json`):
```json
{
  "schema_id": "drill-grade-v1.output",
  "drill_session_id": "matches input",
  "scores": {
    "accuracy": 0,
    "depth": 0,
    "practicality": 0,
    "completeness": 0
  },
  "total": 0,
  "level": "L1|L2|L3|L4|L5",
  "weak_dimensions": ["accuracy" | "depth" | "practicality" | "completeness", ...],
  "rationale": {
    "accuracy": "한국어 한 줄",
    "depth": "한국어 한 줄",
    "practicality": "한국어 한 줄",
    "completeness": "한국어 한 줄"
  },
  "improvement_notes": "다음 학습 권장 (옵션)",
  "scored_by": "ai_session",
  "produced_at": "ISO 8601"
}
```

**Validation rules** (form only — content via learner feedback):
- `accuracy` ∈ [0, 4]
- `depth` ∈ [0, 3]
- `practicality` ∈ [0, 2]
- `completeness` ∈ [0, 1]
- `total` == sum(scores) (verified)
- `level` ∈ {L1..L5}, mapped from total
- All four `rationale` keys present

**Level mapping** (from `scripts/learning/scoring.py:LEVEL_TABLE`):
- 0-2 → L1
- 3-4 → L2
- 5-6 → L3
- 7-8 → L4
- 9-10 → L5

**Storage**: append-only `state/repos/<repo>/memory/drill-history.jsonl`.

**Schema regression test**: `tests/unit/test_drill_grade_contract.py`

**Fallback**: rule baseline (`scripts/learning/scoring.py:score_answer`) —
deterministic 4-dimension keyword count + structural signals. Always
runs in parallel; if AI ↔ rule scores diverge ≥ 3 points, the case is
auto-surfaced for rubric or rule refinement.

---

## Lifecycle invariants (apply to every contract)

1. **Wrapper never calls AI**. Wrappers are deterministic shell scripts
   that write input artifacts and print expected output paths. AI session
   is the *caller*, wrapper is a *placeholder factory*.
2. **Output schema validation runs at I/O boundary**. The downstream
   consumer (`searcher`, `classify`, `scoring`) MUST validate before
   trusting. Validation failures fall back to the deterministic path
   AND log a contract violation.
3. **Round-trip determinism**: the same input artifact + the same
   AI session SHOULD yield comparable outputs (within natural-language
   variance). Tests assert *form*, not *content*.
4. **No external LLM API**. Plan `feedback_no_paid_llm_api.md` —
   contracts execute inside the learner's already-running Claude Code /
   Codex session; no SDK calls.
5. **Append-only logs / overwriteable caches**. JSONL logs are
   append-only with `ai_unavailable` flag for analysis;
   per-prompt_hash caches can be invalidated by deleting the file.

## Adding a new contract — checklist

- [ ] Append a section above with input/output schema + validation rules
- [ ] Land `skills/woowa-<task>/SKILL.md` describing the AI's procedure
- [ ] Add `bin/<task>-prepare` wrapper (deterministic; creates artifacts)
- [ ] Define storage path under `state/cs_rag/` or
      `state/repos/<repo>/...`
- [ ] Add `tests/unit/test_<contract>_contract.py` validating form only
- [ ] Document fallback path (deterministic alternative when AI absent)
- [ ] Update the registry table at the top
