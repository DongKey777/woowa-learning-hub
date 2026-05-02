"""Unit tests for the CS corpus loader retrieval-anchor contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.learning.rag import corpus_loader


class RetrievalAnchorParsingTest(unittest.TestCase):
    def test_extract_retrieval_anchors_supports_active_styles(self) -> None:
        cases = {
            "section_heading": (
                """# Title

## Concepts

### Retrieval Anchors

- `repository boundary`
- aggregate persistence

## More
""",
                ["repository boundary", "aggregate persistence"],
            ),
            "keyword_metadata": (
                """# Title

retrieval-anchor-keywords: transaction boundary, optimistic lock, write skew
""",
                ["transaction boundary", "optimistic lock", "write skew"],
            ),
            "blockquote_keyword_metadata": (
                """# Title

> retrieval-anchor-keywords: replica freshness, read-after-write, primary fallback
""",
                ["replica freshness", "read-after-write", "primary fallback"],
            ),
            "inline_retrieval_anchors": (
                """# Title

Retrieval anchors: `ghost read`, `mixed routing`, stale route
""",
                ["ghost read", "mixed routing", "stale route"],
            ),
            "numbered_section_heading": (
                """# Title

## Deep Dive

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `history list length`
- purge lag
- undo debt
""",
                ["history list length", "purge lag", "undo debt"],
            ),
            "multiline_inline_list": (
                """# Title

Retrieval anchors:

- `failover recovery`
- split brain
""",
                ["failover recovery", "split brain"],
            ),
        }

        for name, (text, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(
                    corpus_loader._extract_retrieval_anchors(text),
                    expected,
                )

    def test_extract_retrieval_anchors_merges_mixed_styles_in_document_order(self) -> None:
        text = """# Mixed Anchors

retrieval-anchor-keywords: Alpha, `Beta`, gamma

## Concepts

### Retrieval Anchors

- beta
- Delta

Retrieval anchors: `gamma`, epsilon, ALPHA
"""

        self.assertEqual(
            corpus_loader._extract_retrieval_anchors(text),
            ["Alpha", "Beta", "gamma", "Delta", "epsilon"],
        )

    def test_iter_corpus_appends_merged_retrieval_anchors_to_every_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc = root / "contents" / "database" / "anchor-contract.md"
            doc.parent.mkdir(parents=True)
            doc.write_text(
                """# Anchor Contract

retrieval-anchor-keywords: alpha, beta

## First Chunk

This section is intentionally long enough to survive the minimum chunk size.
It explains a retrieval case where chunk-local text is not enough by itself.

### Retrieval Anchors

- beta
- gamma

## Second Chunk

This section is also intentionally long enough to become its own chunk.
Retrieval anchors should still be appended here even though the section body
does not repeat every keyword in plain text.

Retrieval anchors: `gamma`, delta
""",
                encoding="utf-8",
            )

            chunks = list(corpus_loader.iter_corpus(root))

        self.assertEqual(len(chunks), 2)
        suffix = "[retrieval anchors] alpha | beta | gamma | delta"
        for chunk in chunks:
            self.assertIn(suffix, chunk.body)

    def test_iter_corpus_promotes_v2_frontmatter_into_chunk_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc = root / "contents" / "spring" / "di-basics.md"
            doc.parent.mkdir(parents=True)
            doc.write_text(
                """---
schema_version: 2
title: "DI Basics"
concept_id: "spring/di-basics"
difficulty: beginner
doc_role: primer
level: beginner
aliases:
  - DI
  - dependency injection
  - 의존성 주입
expected_queries:
  - DI가 뭐야?
---

# DI Basics

retrieval-anchor-keywords: new 대신 주입, 객체 조립

## Primer

This section is intentionally long enough to survive chunking and explain
why dependency injection makes object construction explicit in beginner code.
""",
                encoding="utf-8",
            )

            chunks = list(corpus_loader.iter_corpus(root))

        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertNotIn("schema_version", chunk.body)
        self.assertEqual(chunk.concept_id, "spring/di-basics")
        self.assertEqual(chunk.doc_role, "primer")
        self.assertEqual(chunk.level, "beginner")
        self.assertEqual(chunk.difficulty, "beginner")
        self.assertEqual(
            chunk.anchors,
            ["DI", "dependency injection", "의존성 주입", "new 대신 주입", "객체 조립"],
        )


if __name__ == "__main__":
    unittest.main()
