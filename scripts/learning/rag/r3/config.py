"""Configuration for the experimental R3 retrieval path."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_COMPATIBILITY_FALLBACK = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
DEFAULT_MULTILINGUAL_FALLBACK = DEFAULT_COMPATIBILITY_FALLBACK
DEFAULT_ENGLISH_ONLY_EXPERIMENT = "mixedbread-ai/mxbai-rerank-base-v1"
EXPERIMENTAL_GTE_MULTILINGUAL_RERANKER = "Alibaba-NLP/gte-multilingual-reranker-base"
RERANK_INPUT_WINDOW_ENV = "WOOWA_RAG_RERANK_INPUT_WINDOW"
RerankPolicy = Literal["auto", "always", "off"]


def _int_from_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 0)


def _bool_from_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _rerank_policy_from_env(name: str, default: RerankPolicy) -> RerankPolicy:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"auto", "always", "off"}:
        return value  # type: ignore[return-value]
    return default


def resolve_rerank_input_window(top_k: int, *, default: int | None = None) -> int:
    """Resolve the reranker pair window without hard-coding ``top_k * 2``.

    Existing production behavior stays the fallback default, while experiments
    can set ``WOOWA_RAG_RERANK_INPUT_WINDOW`` to values such as 10, 50, or 100
    and observe a real change in reranker input size.
    """

    fallback = default if default is not None else max(top_k * 2, 1)
    raw = os.environ.get(RERANK_INPUT_WINDOW_ENV)
    if raw is None:
        return fallback
    try:
        value = int(raw)
    except ValueError:
        return fallback
    if value <= 0:
        return fallback
    return value


@dataclass(frozen=True)
class R3Config:
    """Typed knobs for R3 experiments.

    The local default rerank window is deliberately smaller than offline
    evaluation.  The plan's hard runtime target is an M5 MacBook Air with 16GB
    unified memory, so broad top-100 reranking must be opt-in.  The 20-pair
    default is backed by the 2026-05-01 100q Corpus v2 gate: final relevant@5
    and lost_top20_rate matched the earlier 50-pair local profile.
    """

    enabled: bool = False
    reranker_model: str = DEFAULT_RERANKER_MODEL
    multilingual_fallback_model: str = DEFAULT_MULTILINGUAL_FALLBACK
    compatibility_fallback_model: str = DEFAULT_COMPATIBILITY_FALLBACK
    english_only_experiment_model: str = DEFAULT_ENGLISH_ONLY_EXPERIMENT
    local_rerank_input_window: int = 20
    offline_rerank_input_window: int = 100
    local_rerank_policy: RerankPolicy = "auto"
    runtime_lance_prefetch_limit: int = 100
    sparse_encoder_in_cheap_mode: bool = False
    lexical_sidecar_enabled: bool = True
    trace_dir: Path = Path("reports/rag_eval/r3_traces")

    @classmethod
    def from_env(cls) -> "R3Config":
        return cls(
            enabled=_bool_from_env("WOOWA_RAG_R3_ENABLED", False),
            reranker_model=os.environ.get(
                "WOOWA_RAG_R3_RERANKER_MODEL",
                DEFAULT_RERANKER_MODEL,
            ),
            multilingual_fallback_model=os.environ.get(
                "WOOWA_RAG_R3_MULTILINGUAL_FALLBACK",
                DEFAULT_MULTILINGUAL_FALLBACK,
            ),
            compatibility_fallback_model=os.environ.get(
                "WOOWA_RAG_R3_COMPATIBILITY_FALLBACK",
                DEFAULT_COMPATIBILITY_FALLBACK,
            ),
            english_only_experiment_model=os.environ.get(
                "WOOWA_RAG_R3_ENGLISH_ONLY_EXPERIMENT",
                DEFAULT_ENGLISH_ONLY_EXPERIMENT,
            ),
            local_rerank_input_window=_int_from_env(
                "WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW",
                20,
            ),
            offline_rerank_input_window=_int_from_env(
                "WOOWA_RAG_R3_OFFLINE_RERANK_INPUT_WINDOW",
                100,
            ),
            local_rerank_policy=_rerank_policy_from_env(
                "WOOWA_RAG_R3_RERANK_POLICY",
                "auto",
            ),
            runtime_lance_prefetch_limit=_int_from_env(
                "WOOWA_RAG_R3_LANCE_PREFETCH_LIMIT",
                100,
            ),
            sparse_encoder_in_cheap_mode=_bool_from_env(
                "WOOWA_RAG_R3_SPARSE_ENCODER_IN_CHEAP",
                False,
            ),
            lexical_sidecar_enabled=_bool_from_env(
                "WOOWA_RAG_R3_LEXICAL_SIDECAR",
                True,
            ),
            trace_dir=Path(
                os.environ.get("WOOWA_RAG_R3_TRACE_DIR", "reports/rag_eval/r3_traces")
            ),
        )

    def rerank_input_window(self, *, offline: bool = False) -> int:
        return self.offline_rerank_input_window if offline else self.local_rerank_input_window
