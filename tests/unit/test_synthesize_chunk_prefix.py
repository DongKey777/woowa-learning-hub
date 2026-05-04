"""Unit tests for scripts.learning.rag.r3.synthesize_chunk_prefix.

Verifies:
  * the codex authoring prompt embeds the doc context (title, role,
    aliases, H2 list, body excerpt) deterministically
  * embedding the authored prefix back into a v3 doc preserves the
    rest of the frontmatter and re-renders fields in canonical order
  * embed refuses to write into a doc with no v3 frontmatter
  * embed refuses to write a v2 doc (must migrate first)
  * embed refuses an empty prefix
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scripts.learning.rag.r3 import synthesize_chunk_prefix as M


def _write_doc(tmp: Path, body: str, *, category: str = "spring",
               filename: str = "x.md") -> Path:
    target = tmp / "knowledge" / "cs" / "contents" / category / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body).strip(), encoding="utf-8")
    return target


V3_DOC_TEMPLATE = """\
---
schema_version: 3
title: 락 기초
concept_id: database/lock-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
aliases:
- 락
- lock
- shared lock
- exclusive lock
intents:
- definition
expected_queries:
- 락이 뭐야?
contextual_chunk_prefix: ''
---

# 락 기초

> 한 줄 요약: 동시 변경 충돌을 막는 동시성 제어 메커니즘이다.

**난이도: 🟢 Beginner**

## 핵심 개념

본문 핵심 개념 정의.

## 한눈에 보기

표.

## 상세 분해

세부.
"""


class PromptBuildTest(unittest.TestCase):
    def test_prompt_embeds_doc_context(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _write_doc(tmp, V3_DOC_TEMPLATE,
                             category="database", filename="lock-basics.md")
            prompt = M.build_authoring_prompt(doc)

        # Title in prompt
        self.assertIn("락 기초", prompt)
        # doc_role in prompt
        self.assertIn("doc_role: primer", prompt)
        # H2 sections enumerated
        self.assertIn("핵심 개념", prompt)
        self.assertIn("한눈에 보기", prompt)
        # alias passthrough
        self.assertIn("shared lock", prompt)
        # rule banner present
        self.assertIn("contextual_chunk_prefix", prompt)
        self.assertIn("paraphrase", prompt)


class EmbedRoundtripTest(unittest.TestCase):
    def test_embed_writes_prefix_into_frontmatter(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _write_doc(tmp, V3_DOC_TEMPLATE,
                             category="database", filename="lock-basics.md")

            prefix = (
                "이 문서는 동시 변경 충돌을 막는 lock 메커니즘을 처음 잡는 "
                "primer다. 동시성 충돌 방지, 낙관적 비관적 락 비교 같은 "
                "자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다."
            )
            M.embed_prefix(doc, prefix)

            text = doc.read_text(encoding="utf-8")

        # Re-parse the frontmatter and confirm the field is set
        block_re = M._FRONTMATTER_BLOCK_RE
        match = block_re.match(text)
        self.assertIsNotNone(match)
        fm = yaml.safe_load(match.group(2))
        self.assertEqual(fm["contextual_chunk_prefix"], prefix)

        # Other fields preserved
        self.assertEqual(fm["concept_id"], "database/lock-basics")
        self.assertEqual(fm["doc_role"], "primer")
        self.assertEqual(fm["aliases"], ["락", "lock", "shared lock", "exclusive lock"])

        # Body preserved
        self.assertIn("# 락 기초", text)
        self.assertIn("## 핵심 개념", text)


class EmbedRefusalTest(unittest.TestCase):
    def test_refuses_doc_with_no_frontmatter(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _write_doc(tmp, "# X\n\nbody.\n",
                             category="spring", filename="bare.md")
            with self.assertRaises(M.PrefixEmbedError):
                M.embed_prefix(doc, "any prefix text long enough")

    def test_refuses_v2_doc(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _write_doc(tmp, """
---
schema_version: 2
concept_id: spring/x
---
# X
body.
""", category="spring", filename="legacy.md")
            with self.assertRaises(M.PrefixEmbedError):
                M.embed_prefix(doc, "prefix text")

    def test_refuses_empty_prefix(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            doc = _write_doc(tmp, V3_DOC_TEMPLATE,
                             category="database", filename="lock-basics.md")
            with self.assertRaises(M.PrefixEmbedError):
                M.embed_prefix(doc, "   \n   ")


if __name__ == "__main__":
    unittest.main()
