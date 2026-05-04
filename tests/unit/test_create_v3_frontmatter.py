"""Unit tests for scripts.learning.rag.r3.create_v3_frontmatter.

Verifies the deterministic v3 baseline synthesis for docs that have
no frontmatter at all (the Phase 8 Wave A target — 2,200+ docs).

Covers:
  * H1 / 한 줄 요약 / 난이도 / retrieval-anchor-keywords / 관련 문서
    extraction
  * concept_id, category, language inference
  * doc_role heuristic by filename suffix
  * canonical=true for primer (matches migrate_frontmatter_v3 §6)
  * authorial fields stay empty (mission_ids, symptoms, etc.)
  * skip when frontmatter already exists (idempotent re-run)
  * lock list short-circuit
"""

from __future__ import annotations

import json
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3 import create_v3_frontmatter as M


def _make_doc(tmp: Path, category: str, filename: str, body: str) -> Path:
    target = tmp / "knowledge" / "cs" / "contents" / category / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body).strip(), encoding="utf-8")
    return target


SAMPLE_BEGINNER_PRIMER = """
# 트랜잭션 기초

> 한 줄 요약: 트랜잭션 단위와 안전 보장의 네 글자 약속을 설명한다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords: 트랜잭션 기초, 트랜잭션 단위, 커밋, 롤백, 원자성, 일관성, 격리성, 지속성

관련 문서:

- [JDBC 기초](./jdbc-basics.md)
- [Lock Basics](./lock-basics.md)
- [database 카테고리 인덱스](./README.md)

## 핵심 개념

트랜잭션은 커밋과 롤백으로 묶인 작업 단위이다. 트랜잭션 단위가 안전 보장 약속과 어떻게 맞물리는지가 핵심이다. 입문자에게 트랜잭션이 무엇인지 처음 잡아주는 역할을 한다.

본문이 충분한 한국어를 담아 언어 판정이 한국어로 나와야 한다. 학습자가 처음 다가갈 때 알아야 할 핵심 개념을 정리한다. 격리, 원자성, 지속성, 일관성을 어떻게 묶어 보장하는지 짧게 살펴본다.
"""


class DeterministicBaselineTest(unittest.TestCase):
    """Smoke test on a realistic legacy primer."""

    def test_synthesizes_complete_baseline_for_legacy_primer(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _make_doc(tmp, "database", "transaction-basics.md", SAMPLE_BEGINNER_PRIMER)
            result = M.synthesize_file(doc)

        fm = result.new_frontmatter
        self.assertIsNotNone(fm)
        assert fm is not None

        # Required v3 fields present
        self.assertEqual(fm["schema_version"], 3)
        self.assertEqual(fm["concept_id"], "database/transaction-basics")
        self.assertEqual(fm["category"], "database")
        self.assertEqual(fm["doc_role"], "primer")  # filename ends with -basics
        self.assertEqual(fm["level"], "beginner")
        self.assertEqual(fm["difficulty"], "beginner")
        self.assertEqual(fm["language"], "ko")  # body majority Korean
        self.assertEqual(fm["source_priority"], 90)  # primer default
        self.assertTrue(fm["canonical"])  # primer → canonical=true

        # Lifted from body
        self.assertIn("트랜잭션 기초", fm["aliases"])
        self.assertIn("롤백", fm["aliases"])
        # All aliases lowercased (no-op for Korean but enforced for ASCII)
        for alias in fm["aliases"]:
            self.assertEqual(alias, alias.lower())

        # 관련 문서 lifted
        self.assertTrue(any("jdbc-basics.md" in p for p in fm["linked_paths"]))
        self.assertTrue(any("lock-basics.md" in p for p in fm["linked_paths"]))
        # README excluded — navigator, not retrieval candidate
        self.assertFalse(any("README" in p for p in fm["linked_paths"]))

        # Authorial fields are present-but-empty
        self.assertEqual(fm["mission_ids"], [])
        self.assertEqual(fm["review_feedback_tags"], [])
        self.assertEqual(fm["symptoms"], [])
        self.assertEqual(fm["prerequisites"], [])
        self.assertEqual(fm["next_docs"], [])
        self.assertEqual(fm["confusable_with"], [])
        self.assertEqual(fm["forbidden_neighbors"], [])
        self.assertEqual(fm["expected_queries"], [])
        self.assertEqual(fm["contextual_chunk_prefix"], "")

        # intents default by role
        self.assertEqual(fm["intents"], ["definition"])

        # The text emitted starts with --- frontmatter block
        self.assertTrue((result.new_text or "").startswith("---\n"))


class DocRoleHeuristicTest(unittest.TestCase):
    """Filename-suffix → doc_role mapping (deterministic, no LLM)."""

    cases = [
        ("login-loop-symptom-router.md", "symptom_router"),
        ("deadlock-case-study.md", "playbook"),
        ("isolation-cheat-sheet.md", "drill"),
        ("strategy-mini-card.md", "drill"),
        ("strategy-vs-template-method.md", "chooser"),
        ("dao-vs-repository-bridge.md", "bridge"),
        ("read-view-internals.md", "deep_dive"),
        ("transaction-basics.md", "primer"),
        ("connection-pool-foundations.md", "primer"),
        ("roomescape-mission-bridge.md", "mission_bridge"),
        # Default fallback
        ("some-generic-name.md", "primer"),
    ]

    def test_filename_to_doc_role(self):
        for filename, expected in self.cases:
            with self.subTest(filename=filename):
                self.assertEqual(M._doc_role_for_stem(Path(filename).stem), expected)


class IdempotencySkipTest(unittest.TestCase):
    """Doc with existing frontmatter is skipped (must use migrate_v2_to_v3 instead)."""

    def test_skips_doc_with_existing_frontmatter(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _make_doc(tmp, "spring", "x.md", """
---
schema_version: 3
concept_id: spring/x
---
# X
body
""")
            result = M.synthesize_file(doc)
        self.assertTrue(result.skipped)
        self.assertIn("frontmatter", result.skipped_reason or "")


class LockListShortCircuitTest(unittest.TestCase):
    """When --lock-file lists a path, that path is not synthesized."""

    def test_lock_file_paths_skipped_in_main(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _make_doc(tmp, "spring", "locked.md", "# Locked\n\nbody.\n")
            other = _make_doc(tmp, "spring", "unlocked.md", "# Unlocked\n\nbody.\n")
            lock_file = tmp / "lock.json"
            lock_file.write_text(json.dumps({
                "locked_paths": [
                    # The CLI compares as_posix() of the file path. Use full path.
                    doc.as_posix(),
                ],
            }), encoding="utf-8")

            rc = M.main([
                "--paths", str(doc), str(other),
                "--lock-file", str(lock_file),
            ])
        self.assertEqual(rc, 0)


class ConceptIdSafetyTest(unittest.TestCase):
    """concept_id pattern '^[a-z][a-z0-9-]*\\/[a-z][a-z0-9-]+$'."""

    def test_concept_id_is_kebab_lowercase(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _make_doc(tmp, "design-pattern", "Strategy_VS_State.md", "# X\n")
            result = M.synthesize_file(doc)
        fm = result.new_frontmatter
        assert fm is not None
        self.assertRegex(fm["concept_id"], r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]+$")


if __name__ == "__main__":
    unittest.main()
