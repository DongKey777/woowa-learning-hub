"""Unit tests for ``scripts/learning/rag/r3/retrievers/symptom_router.py``.

Coverage:
- Token overlap matching (Korean morpheme + raw)
- Generic stoplist tokens don't trigger false positives
- min_score threshold filters weak matches
- Multiple symptoms scored independently and ranked
- No-match returns empty
- Limit honored
- ``from_catalog_dir`` IO roundtrip
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.candidate import R3Document
from scripts.learning.rag.r3.query_plan import build_query_plan
from scripts.learning.rag.r3.retrievers.symptom_router import (
    SymptomRouterRetriever,
    _content_tokens,
)


def _doc(
    path: str,
    *,
    concept_id: str,
    title: str = "",
    body: str = "",
) -> R3Document:
    return R3Document(
        path=path,
        title=title,
        body=body,
        metadata={"concept_id": concept_id},
    )


def _catalog(concept_entries: dict) -> dict:
    return {
        "schema_version": "3",
        "concept_count": len(concept_entries),
        "stub_count": 0,
        "concepts": concept_entries,
    }


class ContentTokenTest(unittest.TestCase):
    def test_drops_generic_tokens(self):
        toks = set(_content_tokens("@Transactional이 안 먹어요"))
        # '안' is in the generic stoplist, must not appear
        self.assertNotIn("안", toks)
        # the actual concept word should appear (as raw match if not morphologically split)
        self.assertTrue(any("transactional" in t for t in toks))

    def test_korean_morpheme_split(self):
        toks = _content_tokens("프록시 우회 발생")
        # at least 2 distinct content tokens
        self.assertGreaterEqual(len(set(toks)), 2)


class OverlapMatchTest(unittest.TestCase):
    def _build(self) -> SymptomRouterRetriever:
        catalog = _catalog({
            "spring/self-invocation": {
                "concept_id": "spring/self-invocation",
                "doc_path": "spring/self-invocation.md",
                "doc_role": "playbook",
            },
            "database/connection-pool-starvation": {
                "concept_id": "database/connection-pool-starvation",
                "doc_path": "database/cp-starvation.md",
                "doc_role": "symptom_router",
            },
        })
        docs = [
            _doc("spring/self-invocation.md", concept_id="spring/self-invocation",
                 title="self invocation"),
            _doc("database/cp-starvation.md", concept_id="database/connection-pool-starvation",
                 title="connection pool starvation"),
        ]
        return SymptomRouterRetriever(
            catalog=catalog,
            symptom_to_concepts={
                "@Transactional이 안 먹어요 프록시 우회": ["spring/self-invocation"],
                "connection pool 고갈 timeout 발생": ["database/connection-pool-starvation"],
            },
            documents=docs,
        )

    def test_query_matches_proxy_bypass_symptom(self):
        r = self._build()
        plan = build_query_plan("프록시 우회로 @Transactional이 안 먹습니다")
        out = r.retrieve(plan)
        self.assertGreaterEqual(len(out), 1)
        self.assertEqual(out[0].path, "spring/self-invocation.md")
        self.assertEqual(out[0].retriever, "symptom_router")
        self.assertGreaterEqual(out[0].score, 0.34)

    def test_query_matches_pool_starvation_symptom(self):
        r = self._build()
        plan = build_query_plan("connection pool 고갈 timeout이 자꾸 발생해요")
        out = r.retrieve(plan)
        self.assertGreaterEqual(len(out), 1)
        self.assertEqual(out[0].path, "database/cp-starvation.md")

    def test_unrelated_query_no_match(self):
        r = self._build()
        plan = build_query_plan("OAuth2 토큰 만료 시 갱신 흐름")
        out = r.retrieve(plan)
        self.assertEqual(out, [])

    def test_generic_only_query_no_match(self):
        """A query with only stoplist tokens (안, 왜, 그) cannot trigger
        any symptom — even if the symptom string also has 안/왜."""
        r = self._build()
        plan = build_query_plan("안 왜 그게")
        out = r.retrieve(plan)
        self.assertEqual(out, [])


class RankingTest(unittest.TestCase):
    def test_higher_overlap_ratio_ranks_first(self):
        catalog = _catalog({
            "x/short": {
                "concept_id": "x/short",
                "doc_path": "x/short.md",
                "doc_role": "playbook",
            },
            "x/long": {
                "concept_id": "x/long",
                "doc_path": "x/long.md",
                "doc_role": "playbook",
            },
        })
        docs = [
            _doc("x/short.md", concept_id="x/short", title="short symptom"),
            _doc("x/long.md", concept_id="x/long", title="long symptom"),
        ]
        r = SymptomRouterRetriever(
            catalog=catalog,
            symptom_to_concepts={
                # short symptom — 100% overlap when query has both tokens
                "deadlock 발생": ["x/short"],
                # long symptom — partial overlap when query mentions just two of many
                "deadlock 발생 이후 재시도 정책 결정 어려움 latch 통합": ["x/long"],
            },
            documents=docs,
            min_score=0.0,  # let both match for the rank ordering test
        )
        plan = build_query_plan("deadlock 발생")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 2)
        # short symptom (100%) ranks before long symptom (~25%)
        self.assertEqual(out[0].path, "x/short.md")
        self.assertEqual(out[1].path, "x/long.md")
        self.assertGreater(out[0].score, out[1].score)


class LimitTest(unittest.TestCase):
    def test_limit_caps_output(self):
        catalog = _catalog({
            f"x/c{i}": {
                "concept_id": f"x/c{i}",
                "doc_path": f"x/c{i}.md",
                "doc_role": "playbook",
            }
            for i in range(8)
        })
        docs = [_doc(f"x/c{i}.md", concept_id=f"x/c{i}") for i in range(8)]
        r = SymptomRouterRetriever(
            catalog=catalog,
            symptom_to_concepts={
                f"deadlock 발생 케이스 {i}": [f"x/c{i}"] for i in range(8)
            },
            documents=docs,
            limit=3,
        )
        plan = build_query_plan("deadlock 발생")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 3)


class FromCatalogDirTest(unittest.TestCase):
    def test_loads_from_disk_files(self):
        with TemporaryDirectory() as td:
            cat_dir = Path(td)
            catalog_blob = _catalog({
                "spring/self-invocation": {
                    "concept_id": "spring/self-invocation",
                    "doc_path": "spring/si.md",
                    "doc_role": "playbook",
                },
            })
            (cat_dir / "concepts.v3.json").write_text(
                json.dumps(catalog_blob), encoding="utf-8",
            )
            (cat_dir / "symptom_to_concepts.json").write_text(
                json.dumps({"@Transactional 프록시 우회": ["spring/self-invocation"]}),
                encoding="utf-8",
            )
            docs = [_doc("spring/si.md", concept_id="spring/self-invocation")]
            r = SymptomRouterRetriever.from_catalog_dir(cat_dir, docs)
            plan = build_query_plan("@Transactional 프록시 우회 어떻게 해?")
            out = r.retrieve(plan)
            self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main()
