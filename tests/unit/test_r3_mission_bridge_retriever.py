"""Unit tests for ``scripts/learning/rag/r3/retrievers/mission_bridge.py``.

Coverage:
- Detection by canonical mission slug (``roomescape``, ``lotto``)
- Detection by alias the bridge doc carried in its frontmatter
- Detection by Korean alias when present
- Bridge docs prioritized over linked non-bridge docs
- Score reflects number of matched tokens
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
from scripts.learning.rag.r3.retrievers.mission_bridge import MissionBridgeRetriever


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


def _catalog_with(*, missions: dict[str, list[str]],
                  concept_entries: dict[str, dict]) -> dict:
    return {
        "schema_version": "3",
        "concept_count": len(concept_entries),
        "stub_count": 0,
        "concepts": concept_entries,
    }


class MissionDetectionTest(unittest.TestCase):
    def _build(self) -> MissionBridgeRetriever:
        catalog = _catalog_with(
            missions={"missions/roomescape": ["spring/roomescape-di-bridge"]},
            concept_entries={
                "spring/roomescape-di-bridge": {
                    "concept_id": "spring/roomescape-di-bridge",
                    "doc_path": "spring/roomescape-di-bridge.md",
                    "doc_role": "mission_bridge",
                    "aliases": ["roomescape DI", "룸이스케이프 의존성 주입"],
                },
            },
        )
        docs = [
            _doc("spring/roomescape-di-bridge.md", concept_id="spring/roomescape-di-bridge",
                 title="roomescape DI bridge"),
        ]
        return MissionBridgeRetriever(
            catalog=catalog,
            mission_ids_to_concepts={"missions/roomescape": ["spring/roomescape-di-bridge"]},
            documents=docs,
        )

    def test_canonical_mission_slug_matches(self):
        r = self._build()
        plan = build_query_plan("roomescape에서 DI는 어떻게 적용해?")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].retriever, "mission_bridge")
        self.assertEqual(out[0].path, "spring/roomescape-di-bridge.md")
        self.assertEqual(out[0].metadata["matched_mission_id"], "missions/roomescape")
        self.assertIn("roomescape", out[0].metadata["matched_tokens"])

    def test_alias_token_matches(self):
        """Without 'roomescape' in the query, the Korean alias still triggers."""
        r = self._build()
        plan = build_query_plan("룸이스케이프 의존성 주입이 뭐야?")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 1)
        self.assertIn("룸이스케이프 의존성 주입", out[0].metadata["matched_tokens"])

    def test_no_match_returns_empty(self):
        r = self._build()
        plan = build_query_plan("일반적인 DI는 뭐야?")
        out = r.retrieve(plan)
        self.assertEqual(out, [])


class BridgePriorityTest(unittest.TestCase):
    def test_bridge_doc_ranked_before_linked_concept(self):
        """When a mission_id maps to both a bridge doc and a non-bridge
        primer, the bridge doc must rank first because the channel's
        purpose is to surface mission-aware framing."""
        catalog = _catalog_with(
            missions={"missions/lotto": [
                "design-pattern/lotto-strategy-bridge",
                "design-pattern/strategy-pattern-basics",
            ]},
            concept_entries={
                "design-pattern/lotto-strategy-bridge": {
                    "concept_id": "design-pattern/lotto-strategy-bridge",
                    "doc_path": "design-pattern/lotto-strategy-bridge.md",
                    "doc_role": "mission_bridge",
                    "aliases": ["lotto strategy"],
                },
                "design-pattern/strategy-pattern-basics": {
                    "concept_id": "design-pattern/strategy-pattern-basics",
                    "doc_path": "design-pattern/strategy-pattern-basics.md",
                    "doc_role": "primer",
                    "aliases": ["strategy pattern"],
                },
            },
        )
        docs = [
            _doc("design-pattern/strategy-pattern-basics.md",
                 concept_id="design-pattern/strategy-pattern-basics",
                 title="Strategy primer"),
            _doc("design-pattern/lotto-strategy-bridge.md",
                 concept_id="design-pattern/lotto-strategy-bridge",
                 title="Lotto strategy bridge"),
        ]
        r = MissionBridgeRetriever(
            catalog=catalog,
            mission_ids_to_concepts={"missions/lotto": [
                "design-pattern/lotto-strategy-bridge",
                "design-pattern/strategy-pattern-basics",
            ]},
            documents=docs,
        )
        plan = build_query_plan("lotto에서 strategy 패턴이 어떻게 어울려?")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].path, "design-pattern/lotto-strategy-bridge.md")
        self.assertEqual(out[0].metadata["match_phase"], "bridge")
        self.assertEqual(out[1].path, "design-pattern/strategy-pattern-basics.md")
        self.assertEqual(out[1].metadata["match_phase"], "linked")
        # bridge score >= linked score (bridge gets +1 boost)
        self.assertGreaterEqual(out[0].score, out[1].score)


class LimitTest(unittest.TestCase):
    def test_limit_caps_output(self):
        catalog = _catalog_with(
            missions={"missions/roomescape": [f"x/c{i}" for i in range(10)]},
            concept_entries={
                f"x/c{i}": {
                    "concept_id": f"x/c{i}",
                    "doc_path": f"x/c{i}.md",
                    "doc_role": "primer",
                    "aliases": [],
                }
                for i in range(10)
            },
        )
        docs = [_doc(f"x/c{i}.md", concept_id=f"x/c{i}") for i in range(10)]
        r = MissionBridgeRetriever(
            catalog=catalog,
            mission_ids_to_concepts={"missions/roomescape": [f"x/c{i}" for i in range(10)]},
            documents=docs,
            limit=3,
        )
        plan = build_query_plan("roomescape 어떻게 시작해?")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 3)


class SlugTokenTest(unittest.TestCase):
    def test_multi_segment_slug_splits_into_short_form(self):
        """``missions/spring-roomescape-admin`` should detect on either
        the full slug or any 3+ char segment."""
        catalog = _catalog_with(
            missions={"missions/spring-roomescape-admin": ["spring/admin-bridge"]},
            concept_entries={
                "spring/admin-bridge": {
                    "concept_id": "spring/admin-bridge",
                    "doc_path": "spring/admin-bridge.md",
                    "doc_role": "mission_bridge",
                    "aliases": [],
                },
            },
        )
        docs = [_doc("spring/admin-bridge.md", concept_id="spring/admin-bridge")]
        r = MissionBridgeRetriever(
            catalog=catalog,
            mission_ids_to_concepts={
                "missions/spring-roomescape-admin": ["spring/admin-bridge"],
            },
            documents=docs,
        )
        # Just "roomescape" mentioned
        plan = build_query_plan("roomescape 미션의 admin 인증 어떻게 해?")
        out = r.retrieve(plan)
        self.assertEqual(len(out), 1)
        # "admin" + "roomescape" both should match (and "spring-roomescape-admin")
        matched = set(out[0].metadata["matched_tokens"])
        self.assertIn("roomescape", matched)


class FromCatalogDirTest(unittest.TestCase):
    def test_loads_from_disk_files(self):
        with TemporaryDirectory() as td:
            cat_dir = Path(td)
            catalog_blob = _catalog_with(
                missions={"missions/roomescape": ["spring/roomescape-bridge"]},
                concept_entries={
                    "spring/roomescape-bridge": {
                        "concept_id": "spring/roomescape-bridge",
                        "doc_path": "spring/roomescape-bridge.md",
                        "doc_role": "mission_bridge",
                        "aliases": ["roomescape DI"],
                    },
                },
            )
            (cat_dir / "concepts.v3.json").write_text(
                json.dumps(catalog_blob), encoding="utf-8",
            )
            (cat_dir / "mission_ids_to_concepts.json").write_text(
                json.dumps({"missions/roomescape": ["spring/roomescape-bridge"]}),
                encoding="utf-8",
            )
            docs = [
                _doc("spring/roomescape-bridge.md",
                     concept_id="spring/roomescape-bridge",
                     title="bridge"),
            ]
            r = MissionBridgeRetriever.from_catalog_dir(cat_dir, docs)
            plan = build_query_plan("roomescape에서 DI 어떻게?")
            out = r.retrieve(plan)
            self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main()
