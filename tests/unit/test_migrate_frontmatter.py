"""Tests for the frontmatter migration script (plan §P5.3).

Validates pure regex extraction (no LLM calls), idempotent behavior
(skip files with existing frontmatter unless --force), and atomic
in-place rewrite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning.rag import migrate_frontmatter as M


SAMPLE_DOC = """\
# Spring Bean과 DI 기초

> 한 줄 요약: Spring Bean은 컨테이너가 관리하는 객체이고 DI는 그 의존성을 주입하는 패턴이다.

**난이도: 🟢 Beginner**

관련 문서: [Bean Lifecycle](./bean-lifecycle.md), [Component Scan](./component-scan.md)
retrieval-anchor-keywords: spring bean, di, dependency injection, ioc, 컨테이너

## 핵심 개념

본문 시작.
"""

ADVANCED_DOC = """\
# 쿼리 튜닝 체크리스트

**난이도: 🔴 Advanced**

> 쿼리 튜닝은 감으로 하는 작업이 아니라, 확인 순서가 있는 검증 작업이다.

관련 문서: [인덱스와 실행 계획](./index-and-explain.md)
retrieval-anchor-keywords: query tuning checklist, explain triage

본문.
"""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def test_parse_difficulty_emoji_to_label():
    assert M.parse_difficulty("**난이도: 🟢 Beginner**") == "beginner"
    assert M.parse_difficulty("**난이도: 🟡 Intermediate**") == "intermediate"
    assert M.parse_difficulty("**난이도: 🔴 Advanced**") == "advanced"


def test_parse_difficulty_unknown_when_missing():
    assert M.parse_difficulty("no marker at all") == "unknown"


def test_parse_title_returns_first_h1():
    assert M.parse_title("# Spring Bean과 DI 기초\n\n# Other") == "Spring Bean과 DI 기초"


def test_parse_title_none_when_no_h1():
    assert M.parse_title("not a heading\n## subheading") is None


def test_parse_summary_extracts_blockquote():
    txt = "> 한 줄 요약: 핵심 한 줄"
    assert M.parse_summary(txt) == "핵심 한 줄"


def test_parse_summary_none_when_missing():
    assert M.parse_summary("no summary line") is None


def test_parse_anchor_keywords_splits_csv():
    assert M.parse_anchor_keywords(SAMPLE_DOC) == [
        "spring bean", "di", "dependency injection", "ioc", "컨테이너"
    ]


def test_parse_anchor_keywords_empty_when_missing():
    assert M.parse_anchor_keywords("no anchors here") == []


def test_parse_related_docs_extracts_relative_paths():
    assert M.parse_related_docs(SAMPLE_DOC) == [
        "./bean-lifecycle.md", "./component-scan.md"
    ]


def test_parse_related_docs_dedupes():
    txt = "관련 문서: [A](./a.md), [A again](./a.md), [B](./b.md)"
    assert M.parse_related_docs(txt) == ["./a.md", "./b.md"]


# ---------------------------------------------------------------------------
# concept_id derivation
# ---------------------------------------------------------------------------

def test_derive_concept_id_drops_contents_prefix(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    path = corpus / "spring" / "bean-di-basics.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    assert M.derive_concept_id(path, corpus) == "spring/bean-di-basics"


# ---------------------------------------------------------------------------
# Frontmatter detection + render
# ---------------------------------------------------------------------------

def test_has_frontmatter_detects_yaml_block():
    assert M.has_frontmatter("---\ntitle: X\n---\n\nbody") is True


def test_has_frontmatter_false_when_missing():
    assert M.has_frontmatter("# Title\nbody") is False


def test_render_frontmatter_field_order_deterministic():
    meta = {
        "title": "X",
        "concept_id": "a/b",
        "difficulty": "beginner",
        "summary": None,
        "retrieval_anchor_keywords": ["k1"],
        "related_docs": [],
        "audience": [],
        "prereqs": [],
        "learning_points": [],
        "superseded_by": None,
        "migrated_at": "2026-01-01T00:00:00+00:00",
        "migration_source": "auto_v1",
    }
    out = M.render_frontmatter(meta)
    assert out.startswith("---\n")
    assert out.rstrip().endswith("---")
    # Title before concept_id before difficulty
    assert out.find("title:") < out.find("concept_id:") < out.find("difficulty:")
    # Strings double-quoted
    assert 'title: "X"' in out
    assert 'concept_id: "a/b"' in out
    # null surfaces as YAML null, not "None"
    assert "summary: null" in out
    assert "superseded_by: null" in out
    # Empty lists rendered as flow
    assert "audience: []" in out


def test_render_frontmatter_escapes_quotes_in_summary():
    meta = {
        "title": 'has "quote" inside',
        "concept_id": "x",
        "difficulty": "advanced",
        "summary": None,
        "retrieval_anchor_keywords": [],
        "related_docs": [],
        "audience": [], "prereqs": [], "learning_points": [],
        "superseded_by": None,
        "migrated_at": "now",
        "migration_source": "auto_v1",
    }
    out = M.render_frontmatter(meta)
    assert 'title: "has \\"quote\\" inside"' in out


# ---------------------------------------------------------------------------
# build_meta + migrate_text
# ---------------------------------------------------------------------------

def test_build_meta_extracts_full_signal_set(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    path = corpus / "spring" / "bean-di-basics.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    meta = M.build_meta(
        text=SAMPLE_DOC, path=path, corpus_root=corpus,
        now=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert meta["title"] == "Spring Bean과 DI 기초"
    assert meta["concept_id"] == "spring/bean-di-basics"
    assert meta["difficulty"] == "beginner"
    assert meta["summary"].startswith("Spring Bean은 컨테이너")
    assert meta["retrieval_anchor_keywords"] == [
        "spring bean", "di", "dependency injection", "ioc", "컨테이너"
    ]
    assert meta["related_docs"] == ["./bean-lifecycle.md", "./component-scan.md"]
    # Reserved human-curation slots
    assert meta["audience"] == []
    assert meta["prereqs"] == []
    assert meta["learning_points"] == []
    assert meta["superseded_by"] is None
    assert meta["migrated_at"] == "2026-04-30T12:00:00+00:00"
    assert meta["migration_source"] == "auto_v1"


def test_migrate_text_emits_frontmatter(tmp_path):
    corpus = tmp_path / "corpus"
    path = corpus / "x.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    new_text, action = M.migrate_text(
        SAMPLE_DOC, path=path, corpus_root=corpus,
        now=datetime(2026, 4, 30, tzinfo=timezone.utc),
    )
    assert action == "migrated"
    assert new_text is not None
    assert new_text.startswith("---\n")
    assert "difficulty: \"beginner\"" in new_text
    assert "# Spring Bean과 DI 기초" in new_text  # body preserved


def test_migrate_text_skips_when_frontmatter_present(tmp_path):
    corpus = tmp_path / "corpus"
    path = corpus / "x.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = "---\ntitle: existing\n---\n\n# Body\n"
    new_text, action = M.migrate_text(
        existing, path=path, corpus_root=corpus,
    )
    assert new_text is None
    assert action == "skipped_existing"


def test_migrate_text_force_replaces_existing(tmp_path):
    corpus = tmp_path / "corpus"
    path = corpus / "x.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = "---\ntitle: old\n---\n\n# New Title\n\n**난이도: 🔴 Advanced**\n"
    new_text, action = M.migrate_text(
        existing, path=path, corpus_root=corpus, force=True,
        now=datetime(2026, 4, 30, tzinfo=timezone.utc),
    )
    assert action == "migrated"
    assert new_text is not None
    # The old frontmatter is replaced, not nested
    assert new_text.count("---\n") >= 2
    assert "title: \"old\"" not in new_text  # replaced
    assert "title: \"New Title\"" in new_text
    assert "difficulty: \"advanced\"" in new_text


# ---------------------------------------------------------------------------
# Atomic write + CLI
# ---------------------------------------------------------------------------

def test_atomic_write_creates_parent(tmp_path):
    target = tmp_path / "deep" / "nest" / "file.md"
    M.atomic_write(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def test_main_dry_run_does_not_modify_files(tmp_path, capsys):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    spring = corpus / "spring"
    spring.mkdir(parents=True, exist_ok=True)
    p = spring / "bean.md"
    p.write_text(SAMPLE_DOC, encoding="utf-8")

    rc = M.main(["--corpus", str(corpus)])
    assert rc == 0
    assert p.read_text(encoding="utf-8") == SAMPLE_DOC  # untouched


def test_main_apply_rewrites_files(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    spring = corpus / "spring"
    spring.mkdir(parents=True, exist_ok=True)
    p = spring / "bean.md"
    p.write_text(SAMPLE_DOC, encoding="utf-8")

    rc = M.main(["--corpus", str(corpus), "--apply"])
    assert rc == 0
    new = p.read_text(encoding="utf-8")
    assert new.startswith("---\n")
    assert "concept_id: \"spring/bean\"" in new


def test_main_apply_idempotent_second_run(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    spring = corpus / "spring"
    spring.mkdir(parents=True, exist_ok=True)
    p = spring / "bean.md"
    p.write_text(SAMPLE_DOC, encoding="utf-8")

    M.main(["--corpus", str(corpus), "--apply"])
    after_first = p.read_text(encoding="utf-8")
    M.main(["--corpus", str(corpus), "--apply"])
    after_second = p.read_text(encoding="utf-8")
    assert after_first == after_second


def test_main_handles_advanced_marker(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    db = corpus / "database"
    db.mkdir(parents=True, exist_ok=True)
    (db / "tuning.md").write_text(ADVANCED_DOC, encoding="utf-8")
    rc = M.main(["--corpus", str(corpus), "--apply"])
    assert rc == 0
    out = (db / "tuning.md").read_text(encoding="utf-8")
    assert "difficulty: \"advanced\"" in out
