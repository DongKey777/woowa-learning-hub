"""Phase 9.1 — multi-turn anaphora detection for production R3.

The legacy `_search_lance` path used a simple regex anaphora detector
(`scripts/learning/rag/follow_up.py:is_follow_up`) plus prior-turn
context fold-in (`scripts/learning/rag/searcher.py:_follow_up_context_for_prompt`).
That path is unreachable in production because every wrapper sources
`bin/_rag_env.sh` which exports `WOOWA_RAG_R3_ENABLED=1`. R3
production therefore had no anaphora handling at all.

This module ports the multi-turn primitives to R3 with two signal
sources, in priority order:

  1. **AI-session reformulation (primary)** — when an AI session
     emits ``reformulated_query``, the regulation in
     ``docs/agent-query-reformulation-contract.md`` says it has
     already folded prior-turn context. We use it verbatim as the
     semantic query and suppress the regex fallback entirely (so we
     never double-fold the same context).

  2. **Regex + learner_context (fallback)** — short anaphoric prompts
     ('그럼 IoC는?', 'then?') matched by the legacy ``is_follow_up``
     regex are augmented with up to 2 prior topics from
     ``learner_context.recent_rag_ask_context`` or
     ``learner_context.recent_topics``. The augmented semantic query
     becomes::

         이전 맥락: <topic1>, <topic2>
         현재 질문: <prompt>

     If the regex matched but no prior topics are available, the raw
     prompt is returned unchanged — this kills false-positives like
     '그럼 안녕' that would otherwise pollute retrieval.

The output of ``detect_follow_up`` is consumed by
``scripts/learning/rag/r3/search.py:search`` at the line where
``semantic_query`` is decided (just before
``encode_runtime_query``). Trace metadata records ``detected_via``
and ``prior_topics`` for telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.learning.rag.follow_up import is_follow_up as is_follow_up_regex


@dataclass(frozen=True)
class FollowUpDecision:
    """Output of ``detect_follow_up`` consumed by R3 search.

    * ``is_follow_up`` — True only when the regex fallback fired
      (and even then, the augmented query may equal the raw prompt
      if no prior topics were available). When the AI session
      reformulation handled it, this is **False** because R3 should
      not run a second fold-in.

    * ``detected_via`` — one of ``reformulated_query`` /
      ``regex`` / ``none``. Logged for trace; tests pin shape.

    * ``prior_topics`` — the up-to-2 strings folded into the
      augmented query. Empty for reformulation / none paths.

    * ``augmented_semantic_query`` — the string passed to dense
      embed + rerank. The lexical retriever continues to use the
      raw prompt in r3.search.
    """

    is_follow_up: bool
    detected_via: str
    prior_topics: list[str] = field(default_factory=list)
    augmented_semantic_query: str = ""


_PRIOR_TOPIC_KEYS = ("recent_rag_ask_context", "recent_topics")
_MAX_PRIOR_TOPICS = 2


def _extract_prior_topics(learner_context: Any) -> list[str]:
    """Pull up to 2 prior topic strings from learner_context.

    Tolerates None, missing keys, non-list values, and blank strings.
    """
    if not isinstance(learner_context, dict):
        return []
    for key in _PRIOR_TOPIC_KEYS:
        raw = learner_context.get(key)
        if not isinstance(raw, list):
            continue
        topics: list[str] = []
        for item in raw:
            value = str(item).strip()
            if not value:
                continue
            topics.append(value)
            if len(topics) >= _MAX_PRIOR_TOPICS:
                break
        if topics:
            return topics
    return []


def _augmented_query(prompt: str, prior_topics: list[str]) -> str:
    """Build the dense-embed-friendly augmented query.

    Format mirrors the legacy ``multi_query.build_query_candidates``
    follow_up bucket so the cross-encoder reranker sees a familiar
    shape across legacy and R3 paths::

        이전 맥락: spring/bean, spring/di
        현재 질문: 그럼 IoC는?
    """
    if not prior_topics:
        return prompt
    joined = ", ".join(prior_topics)
    return f"이전 맥락: {joined}\n현재 질문: {prompt}"


def detect_follow_up(
    *,
    prompt: str,
    reformulated_query: str | None,
    learner_context: Any,
) -> FollowUpDecision:
    """Decide the semantic query for the current R3 search turn.

    See module docstring for the priority and fallback semantics.
    """
    # 1. AI-session reformulation wins — regex suppressed to avoid
    #    double-fold.
    if reformulated_query is not None:
        cleaned = reformulated_query.strip()
        if cleaned:
            return FollowUpDecision(
                is_follow_up=False,
                detected_via="reformulated_query",
                prior_topics=[],
                augmented_semantic_query=cleaned,
            )

    # 2. Regex fallback. Match on the original prompt so the legacy
    #    is_follow_up regex shape is preserved.
    if not is_follow_up_regex(prompt):
        return FollowUpDecision(
            is_follow_up=False,
            detected_via="none",
            prior_topics=[],
            augmented_semantic_query=prompt,
        )

    prior_topics = _extract_prior_topics(learner_context)
    return FollowUpDecision(
        is_follow_up=True,
        detected_via="regex",
        prior_topics=prior_topics,
        augmented_semantic_query=_augmented_query(prompt, prior_topics),
    )
