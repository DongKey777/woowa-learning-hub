"""Mission-bridge retriever — surface mission_bridge docs when a query
mentions a Woowa mission name.

The R3 spec calls for a dedicated retrieval channel that maps the
learner's mention of *mission context* (e.g. "roomescape", "lotto",
"룸이스케이프") to the bridge docs that link that mission to a CS
concept. Without this channel, dense + lexical alone tend to favour the
canonical CS primer over the mission_bridge doc, which loses the
mission framing the learner asked for.

Channel behaviour:
- At init, scan the catalog's mission_ids_to_concepts.json reverse index
  to build a ``{mission_id: detection_tokens}`` map, where detection_tokens
  are the case-folded mission slug + every alias token from any doc that
  declares that mission_id.
- At retrieval, scan the query for any detection token. If matched,
  emit one candidate per linked concept's primary doc (resolved via the
  catalog's concepts.v3.json plus the in-memory R3Document index).
- Score = number of mission tokens matched (1+); higher score for queries
  that name multiple distinct missions.

The class is corpus-agnostic — feed it a different catalog and a different
document set and it will work the same. Tests construct synthetic catalogs
to exercise the matching logic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from ..candidate import Candidate, R3Document
from ..query_plan import QueryPlan


_MISSION_SLUG_RE = re.compile(r"^missions/(?P<slug>[a-z][a-z0-9-]+)$")


def _slug_tokens(mission_id: str) -> set[str]:
    """``missions/spring-roomescape-admin`` → ``{spring-roomescape-admin,
    spring, roomescape, admin}``. The split tokens let queries match on
    the short form (\"roomescape\") even when the canonical slug is
    multi-segment.
    """
    m = _MISSION_SLUG_RE.match(mission_id)
    if not m:
        return set()
    slug = m.group("slug")
    parts = slug.split("-")
    out = {slug.casefold()}
    for p in parts:
        if len(p) >= 3:  # drop noise like "vs" / "pr"
            out.add(p.casefold())
    return out


def _alias_tokens_from_concepts(
    catalog: dict, concept_ids: Iterable[str],
) -> set[str]:
    """Collect every alias token (case-folded) from each concept entry.
    These are the *Korean / English / mission-aware* labels the doc
    author chose — perfect for query-side detection.
    """
    out: set[str] = set()
    concepts_blob = catalog.get("concepts", {}) if isinstance(catalog, dict) else {}
    for cid in concept_ids:
        entry = concepts_blob.get(cid)
        if not isinstance(entry, dict):
            continue
        for alias in entry.get("aliases", []) or []:
            if isinstance(alias, str) and alias.strip():
                out.add(alias.strip().casefold())
    return out


class MissionBridgeRetriever:
    """Retrieves mission_bridge / mission-relevant docs by detecting
    mission mentions in the query.

    Two construction paths:
      - ``from_catalog_dir(path, documents)``: load
        ``mission_ids_to_concepts.json`` + ``concepts.v3.json`` from disk
      - ``__init__(...)``: pass dicts directly (used by tests)
    """

    retriever_name = "mission_bridge"

    def __init__(
        self,
        *,
        catalog: dict,
        mission_ids_to_concepts: dict[str, list[str]],
        documents: Iterable[R3Document],
        limit: int = 10,
        extra_aliases: dict[str, set[str]] | None = None,
    ) -> None:
        self.catalog = catalog
        self.mission_ids_to_concepts = dict(mission_ids_to_concepts or {})
        self.documents = tuple(documents)
        self.limit = limit
        self._docs_by_concept = self._index_documents_by_concept()
        self._detection = self._build_detection_map(extra_aliases or {})

    # ------------------------------------------------------------------
    @classmethod
    def from_catalog_dir(
        cls,
        catalog_dir: Path,
        documents: Iterable[R3Document],
        *,
        limit: int = 10,
    ) -> "MissionBridgeRetriever":
        catalog_path = catalog_dir / "concepts.v3.json"
        rev_path = catalog_dir / "mission_ids_to_concepts.json"
        with catalog_path.open(encoding="utf-8") as fh:
            catalog = json.load(fh)
        with rev_path.open(encoding="utf-8") as fh:
            mission_index = json.load(fh)
        return cls(
            catalog=catalog,
            mission_ids_to_concepts=mission_index,
            documents=documents,
            limit=limit,
        )

    # ------------------------------------------------------------------
    def _index_documents_by_concept(self) -> dict[str, list[R3Document]]:
        """Match a doc to its concept_id via the doc's metadata.

        Each R3Document carries ``metadata['concept_id']`` (set by the
        corpus loader from frontmatter). We also fall back to
        ``catalog['concepts'][cid]['doc_path']`` matching when the doc
        metadata is missing (older test fixtures).
        """
        out: dict[str, list[R3Document]] = {}
        # Forward index: doc.metadata['concept_id'] → list[R3Document]
        for doc in self.documents:
            cid = doc.metadata.get("concept_id")
            if isinstance(cid, str) and cid:
                out.setdefault(cid, []).append(doc)
        # Fallback: catalog doc_path → R3Document via path match
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

    def _build_detection_map(
        self, extra_aliases: dict[str, set[str]],
    ) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for mission_id, concept_ids in self.mission_ids_to_concepts.items():
            tokens = _slug_tokens(mission_id)
            tokens |= _alias_tokens_from_concepts(self.catalog, concept_ids)
            tokens |= {t.casefold() for t in extra_aliases.get(mission_id, set())}
            # Drop tokens shorter than 3 chars unless they are a slug part —
            # keeps "DI" (an alias) accepted but filters single-letter noise.
            out[mission_id] = {t for t in tokens if len(t) >= 2}
        return out

    # ------------------------------------------------------------------
    def retrieve(self, query_plan: QueryPlan) -> list[Candidate]:
        if not self._detection:
            return []
        haystack = query_plan.normalized_query  # already case-folded + space-normalized

        matched_missions: dict[str, list[str]] = {}
        for mission_id, tokens in self._detection.items():
            hit_tokens = sorted(t for t in tokens if t in haystack)
            if hit_tokens:
                matched_missions[mission_id] = hit_tokens

        if not matched_missions:
            return []

        # Collect candidate concept_ids in priority order:
        # 1. concepts whose doc_role == 'mission_bridge' AND mission_ids hit
        # 2. other concepts linked from the matched mission_id
        candidates: list[Candidate] = []
        seen: set[tuple[str, str | None]] = set()
        rank = 1
        concepts_blob = self.catalog.get("concepts", {})

        # Phase 1 — bridge docs first (highest signal)
        for mission_id, hit_tokens in matched_missions.items():
            for cid in self.mission_ids_to_concepts.get(mission_id, []):
                entry = concepts_blob.get(cid) or {}
                if entry.get("doc_role") != "mission_bridge":
                    continue
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
                        score=float(len(hit_tokens) + 1),
                        title=doc.title,
                        section_title=doc.section_title,
                        metadata={
                            "matched_mission_id": mission_id,
                            "matched_tokens": hit_tokens,
                            "match_phase": "bridge",
                            "concept_id": cid,
                            "document": dict(doc.metadata),
                        },
                    ))
                    rank += 1
                    if rank > self.limit:
                        return candidates

        # Phase 2 — non-bridge linked concepts (still mission-relevant)
        for mission_id, hit_tokens in matched_missions.items():
            for cid in self.mission_ids_to_concepts.get(mission_id, []):
                entry = concepts_blob.get(cid) or {}
                if entry.get("doc_role") == "mission_bridge":
                    continue  # already covered in Phase 1
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
                        score=float(len(hit_tokens)),
                        title=doc.title,
                        section_title=doc.section_title,
                        metadata={
                            "matched_mission_id": mission_id,
                            "matched_tokens": hit_tokens,
                            "match_phase": "linked",
                            "concept_id": cid,
                            "document": dict(doc.metadata),
                        },
                    ))
                    rank += 1
                    if rank > self.limit:
                        return candidates

        return candidates
