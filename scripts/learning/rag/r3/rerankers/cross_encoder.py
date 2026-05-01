"""Language-aware cross-encoder reranker adapter for R3."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..candidate import Candidate
from ..config import R3Config
from ..query_plan import Language


ModelFactory = Callable[[str], Any]
REMOTE_CODE_RERANKER_MODELS = {
    "Alibaba-NLP/gte-multilingual-reranker-base",
}
CPU_ONLY_RERANKER_MODELS = {
    "Alibaba-NLP/gte-multilingual-reranker-base",
}
_MODEL_CACHE: dict[str, Any] = {}


def reranker_chain_for_language(
    language: Language,
    config: R3Config | None = None,
) -> tuple[str, ...]:
    """Return safe model order for a query language bucket.

    Korean and mixed Korean/English CS queries must not fall back to the
    English-only mxbai candidate.
    """

    def _dedupe(models: tuple[str, ...]) -> tuple[str, ...]:
        out: list[str] = []
        for model in models:
            if model and model not in out:
                out.append(model)
        return tuple(out)

    cfg = config or R3Config.from_env()
    if language in {"ko", "mixed"}:
        return _dedupe((
            cfg.reranker_model,
            cfg.multilingual_fallback_model,
            cfg.compatibility_fallback_model,
        ))
    if language == "en":
        return _dedupe((
            cfg.reranker_model,
            cfg.english_only_experiment_model,
            cfg.compatibility_fallback_model,
        ))
    return _dedupe((
        cfg.reranker_model,
        cfg.multilingual_fallback_model,
        cfg.compatibility_fallback_model,
    ))


def default_model_factory(model_id: str) -> Any:
    cached = _MODEL_CACHE.get(model_id)
    if cached is not None:
        return cached
    from sentence_transformers import CrossEncoder  # type: ignore

    kwargs = {}
    if model_id in REMOTE_CODE_RERANKER_MODELS:
        kwargs["trust_remote_code"] = True
    if model_id in CPU_ONLY_RERANKER_MODELS:
        kwargs["device"] = "cpu"
    model = CrossEncoder(model_id, **kwargs)
    _MODEL_CACHE[model_id] = model
    return model


def _candidate_passage(candidate: Candidate) -> str:
    passage = candidate.metadata.get("passage") or candidate.metadata.get("body")
    if passage:
        return str(passage)
    parts = [candidate.title or "", candidate.section_title or ""]
    document = candidate.metadata.get("document") or {}
    if document.get("body"):
        parts.append(str(document["body"]))
    return "\n\n".join(part for part in parts if part)


@dataclass
class CrossEncoderReranker:
    """Small adapter that reranks R3 Candidate objects."""

    model_id: str
    model_factory: ModelFactory = default_model_factory
    max_pair_len: int = 512

    _model: Any | None = field(default=None, init=False, repr=False)

    @classmethod
    def for_language(
        cls,
        language: Language,
        *,
        config: R3Config | None = None,
        model_factory: ModelFactory = default_model_factory,
    ) -> "CrossEncoderReranker":
        return cls(
            model_id=reranker_chain_for_language(language, config)[0],
            model_factory=model_factory,
        )

    def _get_model(self) -> Any:
        if self._model is None:
            self._model = self.model_factory(self.model_id)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: Sequence[Candidate],
        *,
        top_n: int,
    ) -> list[Candidate]:
        if not candidates or top_n <= 0:
            return list(candidates)
        head = list(candidates[:top_n])
        tail = list(candidates[top_n:])
        pairs = [
            [query, _candidate_passage(candidate)[: self.max_pair_len]]
            for candidate in head
        ]
        scores = self._get_model().predict(pairs, show_progress_bar=False)
        reranked: list[Candidate] = []
        for candidate, score in zip(head, scores):
            metadata = dict(candidate.metadata)
            metadata.update(
                {
                    "reranker_model": self.model_id,
                    "pre_rerank_rank": candidate.rank,
                    "pre_rerank_score": candidate.score,
                }
            )
            reranked.append(
                Candidate(
                    path=candidate.path,
                    chunk_id=candidate.chunk_id,
                    retriever=f"reranker:{self.model_id}",
                    rank=candidate.rank,
                    score=float(score),
                    title=candidate.title,
                    section_title=candidate.section_title,
                    metadata=metadata,
                )
            )
        reranked.sort(key=lambda candidate: (-candidate.score, candidate.path))
        out: list[Candidate] = []
        for rank, candidate in enumerate([*reranked, *tail], start=1):
            out.append(
                Candidate(
                    path=candidate.path,
                    chunk_id=candidate.chunk_id,
                    retriever=candidate.retriever,
                    rank=rank,
                    score=candidate.score,
                    title=candidate.title,
                    section_title=candidate.section_title,
                    metadata=dict(candidate.metadata),
                )
            )
        return out
