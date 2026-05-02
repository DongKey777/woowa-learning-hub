"""Symptom-router retriever — surface playbook / symptom_router docs
when the learner describes a symptom in natural language.

The R3 spec calls for a dedicated retrieval channel that routes
symptom-shaped queries (e.g. "@Transactional이 안 먹어요",
"connection pool이 고갈됐어요") to the doc whose ``symptoms`` frontmatter
list contains a sufficiently overlapping phrasing. Without this channel
the retriever ends up boosting the canonical primer that *defines* the
underlying concept (e.g. ``@Transactional``) instead of the playbook
that *triages* the symptom — losing the symptom→cause routing intent.

Channel behaviour:
- At init, load ``symptom_to_concepts.json`` reverse index. For each
  symptom string, compute its content tokens (Korean morpheme + raw
  whitespace tokens, lowercased, length ≥ 2) and store as a tuple.
- At retrieval, tokenize the query the same way. Score each symptom by
  Jaccard-like overlap (|q∩s| / |s|) with a small floor so a single
  matching content word is still a candidate when the symptom is short.
- Emit one candidate per unique (path, chunk) pair, ranked by score.

Like ``mission_bridge``, this channel is corpus-agnostic — different
catalogs and document sets work the same way.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from ..candidate import Candidate, R3Document
from ..query_plan import QueryPlan
from ..tokenization import tokenize_text


# Words that match too generically to count as evidence on their own.
# Keep the list tight — every entry is a deliberate carve-out, not a
# blanket stoplist.
_GENERIC_TOKENS = frozenset({
    "안",       # 안 먹어요 / 안 돼요 — frequent but on its own carries no signal
    "왜",
    "뭐",
    "어떻게",
    "그",
    "이",
    "저",
    "게",
    "거",
    "것",
    "the",
    "a",
    "an",
    "is",
    "are",
    "what",
    "why",
    "how",
})


def _content_tokens(text: str) -> tuple[str, ...]:
    """Tokenize for symptom matching — Korean morpheme + raw whitespace
    + length ≥ 2 + drop generic markers."""
    morphs = tuple(t.casefold() for t in tokenize_text(text))
    raw = tuple(
        t.casefold()
        for t in re.findall(r"[\w@/.-]+", text)
        if len(t) >= 2
    )
    seen: set[str] = set()
    out: list[str] = []
    for tok in morphs + raw:
        if len(tok) < 2 or tok in _GENERIC_TOKENS or tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return tuple(out)


class SymptomRouterRetriever:
    """Routes symptom-shaped queries to symptom_router / playbook docs."""

    retriever_name = "symptom_router"

    def __init__(
        self,
        *,
        catalog: dict,
        symptom_to_concepts: dict[str, list[str]],
        documents: Iterable[R3Document],
        limit: int = 10,
        min_overlap: int = 1,
        min_score: float = 0.34,
    ) -> None:
        self.catalog = catalog
        self.documents = tuple(documents)
        self.limit = limit
        self.min_overlap = min_overlap
        self.min_score = min_score
        self._docs_by_concept = self._index_documents_by_concept()
        self._symptom_index = self._build_symptom_index(symptom_to_concepts)

    # ------------------------------------------------------------------
    @classmethod
    def from_catalog_dir(
        cls,
        catalog_dir: Path,
        documents: Iterable[R3Document],
        *,
        limit: int = 10,
    ) -> "SymptomRouterRetriever":
        with (catalog_dir / "concepts.v3.json").open(encoding="utf-8") as fh:
            catalog = json.load(fh)
        with (catalog_dir / "symptom_to_concepts.json").open(encoding="utf-8") as fh:
            symptom_index = json.load(fh)
        return cls(
            catalog=catalog,
            symptom_to_concepts=symptom_index,
            documents=documents,
            limit=limit,
        )

    # ------------------------------------------------------------------
    def _index_documents_by_concept(self) -> dict[str, list[R3Document]]:
        out: dict[str, list[R3Document]] = {}
        for doc in self.documents:
            cid = doc.metadata.get("concept_id")
            if isinstance(cid, str) and cid:
                out.setdefault(cid, []).append(doc)
        concepts_blob = self.catalog.get("concepts", {}) if isinstance(self.catalog, dict) else {}
        path_to_doc = {doc.path: doc for doc in self.documents}
        for cid, entry in concepts_blob.items():
            if cid in out:
                continue
            if not isinstance(entry, dict):
                continue
            doc_path = entry.get("doc_path")
            if isinstance(doc_path, str) and doc_path in path_to_doc:
                out[cid] = [path_to_doc[doc_path]]
        return out

    def _build_symptom_index(
        self, symptom_to_concepts: dict[str, list[str]],
    ) -> list[tuple[str, frozenset[str], list[str]]]:
        """Pre-tokenize each symptom string. Returns a list of
        (raw_symptom, token_set, concept_ids).
        """
        out: list[tuple[str, frozenset[str], list[str]]] = []
        for symptom, concept_ids in symptom_to_concepts.items():
            tokens = frozenset(_content_tokens(symptom))
            if not tokens or not concept_ids:
                continue
            out.append((symptom, tokens, list(concept_ids)))
        return out

    # ------------------------------------------------------------------
    def retrieve(self, query_plan: QueryPlan) -> list[Candidate]:
        if not self._symptom_index:
            return []
        query_tokens = frozenset(_content_tokens(query_plan.raw_query))
        if not query_tokens:
            return []

        # Score each symptom against the query.
        # score = overlap_count / len(symptom_tokens)
        # tie-break by overlap_count, then symptom string.
        scored: list[tuple[float, int, str, list[str], list[str]]] = []
        for symptom, sym_tokens, concept_ids in self._symptom_index:
            overlap = query_tokens & sym_tokens
            if len(overlap) < self.min_overlap:
                continue
            score = len(overlap) / max(len(sym_tokens), 1)
            if score < self.min_score:
                continue
            scored.append((
                score,
                len(overlap),
                symptom,
                sorted(overlap),
                concept_ids,
            ))
        scored.sort(key=lambda t: (-t[0], -t[1], t[2]))

        candidates: list[Candidate] = []
        seen: set[tuple[str, str | None]] = set()
        rank = 1
        for score, overlap_n, symptom, matched_tokens, concept_ids in scored:
            for cid in concept_ids:
                for doc in self._docs_by_concept.get(cid, []):
                    key = (doc.path, doc.chunk_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(Candidate(
                        path=doc.path,
                        chunk_id=doc.chunk_id,
                        retriever=self.retriever_name,
                        rank=rank,
                        score=float(score),
                        title=doc.title,
                        section_title=doc.section_title,
                        metadata={
                            "matched_symptom": symptom,
                            "matched_tokens": matched_tokens,
                            "overlap_count": overlap_n,
                            "concept_id": cid,
                            "document": dict(doc.metadata),
                        },
                    ))
                    rank += 1
                    if rank > self.limit:
                        return candidates
        return candidates
