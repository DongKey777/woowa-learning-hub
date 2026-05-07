# Agent Query Reformulation Contract

> Audience: any AI session (Claude Code, Codex, Gemini) that calls
> `bin/rag-ask` or `r3.search.search()` on behalf of a learner.
>
> Purpose: explain the runtime behaviour the AI session must perform
> so that the corpus side baseline (90.5% OVERALL, see
> `reports/rag_eval/r3_phase4_6_closing_report.md`) and the query side
> baseline (94.5% OVERALL, same report) hold in production for real
> learners — not just on the static qrel suite.

## Why this exists

The R3 retrieval system has two complementary axes for bridging the
gap between learner natural language and corpus vocabulary:

1. **Corpus side** — `contextual_chunk_prefix` in v3 frontmatter,
   prepended to every chunk's embed text. Authored offline. Static.
2. **Query side** — `reformulated_query` argument to
   `r3.search.search()`. Generated at runtime by the AI session. Per
   query.

The qrel suite stores a `reformulated_query` field for measurement —
but in production, **the AI session itself must emit the reformulation
before calling `bin/rag-ask`**. Otherwise the system runs as if every
production query is "raw query only," and we lose the +4pp OVERALL
(and +16.7pp on symptom_to_cause) that the closing report measured.

This document is the contract.

## Scope

This contract applies only to **interactive learning RAG turns** — the
turns described in CLAUDE.md / AGENTS.md *Interactive Learning RAG
Routing*. Specifically:

- the AI session is in a learning conversation with the learner
- the learner asks a CS / theory question that triggers `bin/rag-ask`
- the question is in natural language (Korean, English, or mixed)

It does **not** apply to:

- mission coaching turns (`bin/coach-run`) — those use a different
  evidence path
- non-learning developer turns
- direct CLI invocations by the learner themselves

## What the AI session must do

Before calling `bin/rag-ask`, the AI session computes a reformulated
query string from the learner's raw prompt + recent conversation
context, then passes both:

```
bin/rag-ask "<learner raw prompt>" --reformulated-query "<reformulation>"
```

Or in Python:

```python
from scripts.learning.rag.r3.search import search

results = search(
    prompt="<learner raw prompt>",
    reformulated_query="<reformulation>",
    top_k=5,
    mode="full",
    index_root=...,
    catalog_root=...,
    use_reranker=True,
)
```

The R3 search routing keeps the lexical FTS channel on the **raw
prompt** (so the learner's natural-language tokens still surface) and
sends the **reformulated query** to dense BGE-M3 + cross-encoder
rerank.

The interactive Tier router also receives the reformulated query. User
overrides (`그냥 답해`, `RAG로 깊게`, `코치 모드`) and tool-only guards are still
decided from the raw prompt, but domain/depth/definition/study-intent
detection uses `raw + reformulated`. The router also consults corpus-owned
vocabulary as a domain bridge: first `signal_rules`, then cached frontmatter
phrases from `title`, `concept_id`, `aliases`, `symptoms`, `expected_queries`,
and `review_feedback_tags`. Specific terms that are not hand-listed in
`lexicon.py` can still pass the first gate when the learner expresses a study
intent. This lets a corpus-friendly reformulation rescue a learner prompt that
would otherwise look too vague and fall to Tier 0.

## How to write a reformulation

A good reformulation:

1. **Preserves the learner's intent** — paraphrase, comparison,
   symptom triage, mission concept lookup, etc.
2. **Adds the corpus's technical vocabulary** — Spring Bean lifecycle,
   MVCC consistent read, lock wait timeout, cookie three-way splitter,
   etc. Use the vocabulary the corpus body actually uses, not generic
   synonyms.
3. **Folds in conversation context** — if the learner has been talking
   about DB topics for the last 2-3 turns and now asks "락 걸어 읽는
   거랑 차이는?", the reformulation should say "MVCC vs lock-based
   read 비교" not "MVCC vs lock 비교 (어떤 도메인일 수 있음)".
4. **Stays short** — 10-30 tokens. The reformulation goes through the
   same dense encoder as the raw prompt; long reformulations dilute
   the embedding.
5. **Uses the cohort's natural framing**:
   - paraphrase → straight technical phrase
   - comparison ("X vs Y") → keep "vs" structure
   - symptom → router/playbook keyword
   - mission → mission name + linked CS concept
   - primer / "처음 배우는데" → keep the primer cue so deep-dive
     forbidden neighbors stay demoted

## Examples (pulled from `tests/fixtures/r3_qrels_real_v1.json`)

| Learner raw | Reformulation |
|---|---|
| 객체를 직접 만들지 않고 외부에서 받는 게 뭐야? | Spring 의존성 주입 DI 의 정의 — 객체를 직접 new로 만들지 않고 외부에서 받는 wiring 방식 |
| 스프링이 객체를 어떻게 만들어주는지 큰 그림이 궁금해 | Spring Bean 라이프사이클 큰 그림 — 컨테이너가 객체를 언제 만들고 초기화하고 소멸시키는지 |
| 갑자기 트랜잭션이 다 lock timeout으로 떨어지고 있어 | 갑자기 트랜잭션이 다 lock timeout — blocker 먼저 보는 mini card, lock wait 진단 |
| 쿠키는 있는데 자꾸 로그인 페이지로 튀겨 | cookie failure three-way splitter (blocked / stored not sent / sent but anonymous) chooser |
| roomescape 미션에서 DAO 패턴 쓰라는데 그게 뭔 의미야? | roomescape 미션 DAO 패턴 — repository-dao-entity bridge, 미션에서 DAO 의미 |
| Connection pool이 뭐야? | Connection pool 기초 primer — DB 연결 풀 자원 관리 입문 |

The pattern: **learner phrasing kept** (so the AI session preserves
intent for the answer), **technical phrase appended or substituted**
(so dense encoding lands on corpus chunks).

## When NOT to reformulate

1. **The query is already in corpus vocabulary** — e.g. "MVCC read
   view consistent read 내부 구조가 어떻게 돼?" Pass `prompt` only;
   the reformulation would be redundant.
2. **The learner is asking about a topic the corpus does not cover
   (corpus_gap intent)** — reformulating to corpus vocabulary defeats
   the refusal. The system's `corpus_gap_probe` cohort is at 100%
   precisely because we did not reformulate it.
3. **The learner explicitly types raw English / technical terms** —
   "@Transactional self-invocation 함정" already lands well on dense
   embedding. No reformulation needed.

When in doubt, omit `reformulated_query`. The system falls back to
raw prompt for all channels.

## Conversation context handling

The AI session has access to recent turn history (`memory/history.jsonl`
in coach-run; in-context for shorter sessions). Use it.

Example:

- Turn N-1 learner: "MVCC가 뭐야?"
- Turn N-1 AI: explains MVCC
- Turn N learner: "그럼 락 걸어 읽는 거랑 차이는?"

Turn N raw prompt is ambiguous in isolation ("락 걸어 읽기" could be
filesystem locking, git locking, etc.). Reformulation must inject the
DB context:

```
prompt = "그럼 락 걸어 읽는 거랑 차이는?"
reformulated = "MVCC snapshot read vs locking read 비교 — DB 동시 트랜잭션의 두 읽기 방식"
```

This is the second user-identified lever: *"이전 대화에서 DB 얘기를
했으니 학습자는 DB 생략하고 묻는다 → AI session이 그 컨텍스트를
reformulation에 채워서 retrieval 정확도 유지"*.

## Adaptive Response interaction

If `bin/rag-ask` returns `learner_context.response_hints`, the AI
session continues to follow the existing v3 closed loop contract
(`must_skip_explanations_of`, `must_include_phrases`, etc.). The
reformulation is upstream of `bin/rag-ask` — it does not change the
adaptive response contract.

Headers stay as-is:

```
[RAG: tier-N — <reason>]
```

The reformulation does **not** appear in the header, because it's an
internal retrieval implementation detail. The learner sees their own
phrasing reflected in the AI's answer.

## Failure mode (what happens if AI session forgets)

If the AI session calls `bin/rag-ask` with raw prompt only:

- Retrieval falls back to v21 raw baseline (90.5% OVERALL on the qrel
  suite)
- paraphrase / symptom / mission / forbidden cohorts each lose 3-17pp
  vs the reformulated baseline
- Answers can still be coherent; they are just less precisely
  grounded for paraphrase-heavy queries

It is graceful degradation, not breakage. But the contract is to
emit the reformulation; we measured 94.5% OVERALL with it.

## Audit / regression

The R3 trace records both `reformulated_query` and `semantic_query`
in `metadata` so analysts can verify per-call which form was used:

```python
debug = {}
results = search(prompt=raw, reformulated_query=ref, debug=debug)
assert debug["r3_reformulated_query"] == ref  # or None if omitted
assert debug["r3_semantic_query"] == ref or raw
```

The cohort_eval harness (`scripts/learning/rag/r3/eval/cohort_eval.py`)
takes a `--use-reformulated-query` CLI flag for offline A/B against
the qrel's stored reformulations.

## Versioning

This contract is at v1. Future changes that affect the runtime
behaviour (e.g. extending to lexical FTS, adding multi-query rewriting,
chunk-level Anthropic contextual retrieval) should bump the version
in this header and update the closing report's measurement column.
