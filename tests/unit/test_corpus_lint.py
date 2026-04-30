"""Tests for the corpus integrity lint (plan §P5.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.learning.rag import corpus_lint as L


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def test_parse_frontmatter_returns_none_when_absent():
    assert L.parse_frontmatter("# H\nbody") is None


def test_parse_frontmatter_handles_quoted_strings_and_lists():
    text = (
        '---\n'
        'title: "Hello"\n'
        'concept_id: "spring/bean"\n'
        'difficulty: "beginner"\n'
        'retrieval_anchor_keywords: ["a", "b"]\n'
        'audience: []\n'
        'superseded_by: null\n'
        '---\n\n'
        'body\n'
    )
    fm = L.parse_frontmatter(text)
    assert fm["title"] == "Hello"
    assert fm["concept_id"] == "spring/bean"
    assert fm["difficulty"] == "beginner"
    assert fm["retrieval_anchor_keywords"] == ["a", "b"]
    assert fm["audience"] == []
    assert fm["superseded_by"] is None


def test_parse_frontmatter_unescapes_quotes():
    text = '---\ntitle: "has \\"quote\\" inside"\n---\n\nbody'
    fm = L.parse_frontmatter(text)
    assert fm["title"] == 'has "quote" inside'


# ---------------------------------------------------------------------------
# extract_relative_links
# ---------------------------------------------------------------------------

def test_extract_relative_links_skips_absolute():
    text = "[A](https://x.com) [B](./local.md) [C](mailto:x@x) [D](#anchor)"
    assert L.extract_relative_links(text) == ["./local.md"]


def test_extract_relative_links_strips_fragment():
    text = "[A](./doc.md#section)"
    assert L.extract_relative_links(text) == ["./doc.md"]


def test_extract_relative_links_handles_dotdot():
    text = "[A](../sibling/doc.md)"
    assert L.extract_relative_links(text) == ["../sibling/doc.md"]


# ---------------------------------------------------------------------------
# check_link_integrity
# ---------------------------------------------------------------------------

def test_check_link_integrity_passes_when_target_exists(tmp_path):
    corpus = tmp_path / "corpus"
    spring = corpus / "spring"
    spring.mkdir(parents=True, exist_ok=True)
    target = spring / "bean.md"
    target.write_text("body", encoding="utf-8")
    src = spring / "intro.md"
    src.write_text("see [Bean](./bean.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(), corpus_root=corpus,
    )
    assert violations == []


def test_check_link_integrity_flags_broken_link(tmp_path):
    corpus = tmp_path / "corpus"
    spring = corpus / "spring"
    spring.mkdir(parents=True, exist_ok=True)
    src = spring / "intro.md"
    src.write_text("see [Missing](./missing.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(), corpus_root=corpus,
    )
    assert len(violations) == 1
    assert violations[0].check == "link_integrity"
    assert "missing.md" in violations[0].message


def test_check_link_integrity_accepts_cross_domain_link_when_target_exists(tmp_path):
    """Links that leave corpus but stay within repo + target exists →
    accepted (real-world cross-domain references like
    JUNIOR-BACKEND-ROADMAP.md sit one directory above corpus_root)."""
    repo = tmp_path / "repo"
    corpus = repo / "knowledge" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    (repo / "knowledge" / "cs" / "ROADMAP.md").write_text("roadmap", encoding="utf-8")
    src = corpus / "intro.md"
    src.write_text("see [Roadmap](../ROADMAP.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(),
        corpus_root=corpus, repo_root=repo,
    )
    assert violations == []


def test_check_link_integrity_flags_cross_domain_when_target_missing(tmp_path):
    repo = tmp_path / "repo"
    corpus = repo / "knowledge" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    src = corpus / "intro.md"
    src.write_text("see [Missing](../missing.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(),
        corpus_root=corpus, repo_root=repo,
    )
    assert any("cross-domain" in v.message for v in violations)


def test_check_link_integrity_flags_links_escaping_repo(tmp_path):
    repo = tmp_path / "repo"
    corpus = repo / "knowledge" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    src = corpus / "intro.md"
    # `../../../../../escape.md` escapes the repo entirely
    src.write_text("see [Escape](../../../../../escape.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(),
        corpus_root=corpus, repo_root=repo,
    )
    assert any("escapes repo root" in v.message for v in violations)


def test_check_link_integrity_outside_corpus_without_repo_root(tmp_path):
    """Without repo_root context, all out-of-corpus links must point
    at existing files — otherwise flagged as broken."""
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    src = corpus / "intro.md"
    src.write_text("see [Escape](../escape.md)", encoding="utf-8")

    violations = L.check_link_integrity(
        file_path=src, text=src.read_text(), corpus_root=corpus,
    )
    assert any("cross-domain" in v.message for v in violations)


# ---------------------------------------------------------------------------
# check_frontmatter_schema
# ---------------------------------------------------------------------------

def test_frontmatter_schema_no_violation_when_absent(tmp_path):
    src = tmp_path / "x.md"
    src.write_text("# H\nbody", encoding="utf-8")
    assert L.check_frontmatter_schema(file_path=src, text=src.read_text()) == []


def test_frontmatter_schema_requires_title_concept_difficulty(tmp_path):
    src = tmp_path / "x.md"
    src.write_text(
        '---\ntitle: "T"\n---\n\nbody',
        encoding="utf-8",
    )
    violations = L.check_frontmatter_schema(file_path=src, text=src.read_text())
    keys = {v.message for v in violations}
    assert any("concept_id" in m for m in keys)
    assert any("difficulty" in m for m in keys)


def test_frontmatter_schema_rejects_invalid_difficulty(tmp_path):
    src = tmp_path / "x.md"
    src.write_text(
        '---\ntitle: "T"\nconcept_id: "x"\ndifficulty: "expert"\n---\n\nbody',
        encoding="utf-8",
    )
    violations = L.check_frontmatter_schema(file_path=src, text=src.read_text())
    assert any("expert" in v.message for v in violations)


def test_frontmatter_schema_accepts_full_valid(tmp_path):
    src = tmp_path / "x.md"
    src.write_text(
        '---\ntitle: "T"\nconcept_id: "x"\ndifficulty: "beginner"\n---\n\nbody',
        encoding="utf-8",
    )
    assert L.check_frontmatter_schema(file_path=src, text=src.read_text()) == []


# ---------------------------------------------------------------------------
# concept_id uniqueness
# ---------------------------------------------------------------------------

def test_concept_id_uniqueness_passes_when_unique(tmp_path):
    a = tmp_path / "a.md"; b = tmp_path / "b.md"
    a.write_text('---\ntitle: "A"\nconcept_id: "x/a"\ndifficulty: "beginner"\n---\n\n', encoding="utf-8")
    b.write_text('---\ntitle: "B"\nconcept_id: "x/b"\ndifficulty: "beginner"\n---\n\n', encoding="utf-8")
    files = [(a, a.read_text()), (b, b.read_text())]
    assert L.check_concept_id_uniqueness(files) == []


def test_concept_id_uniqueness_flags_duplicates(tmp_path):
    a = tmp_path / "a.md"; b = tmp_path / "b.md"
    a.write_text('---\ntitle: "A"\nconcept_id: "x/dup"\ndifficulty: "beginner"\n---\n\n', encoding="utf-8")
    b.write_text('---\ntitle: "B"\nconcept_id: "x/dup"\ndifficulty: "beginner"\n---\n\n', encoding="utf-8")
    files = [(a, a.read_text()), (b, b.read_text())]
    violations = L.check_concept_id_uniqueness(files)
    assert len(violations) == 2
    for v in violations:
        assert v.check == "concept_id_uniqueness"
        assert "x/dup" in v.message


def test_concept_id_uniqueness_skips_files_without_frontmatter(tmp_path):
    a = tmp_path / "a.md"; b = tmp_path / "b.md"
    a.write_text("# H1\nbody", encoding="utf-8")  # no frontmatter
    b.write_text("# H2\nbody", encoding="utf-8")  # no frontmatter
    files = [(a, a.read_text()), (b, b.read_text())]
    assert L.check_concept_id_uniqueness(files) == []


# ---------------------------------------------------------------------------
# lint_corpus end-to-end
# ---------------------------------------------------------------------------

def test_lint_corpus_returns_clean_report(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "x.md").write_text("# clean\n", encoding="utf-8")
    report = L.lint_corpus(corpus)
    assert report.ok() is True
    assert report.files_scanned == 1


def test_lint_corpus_aggregates_violations(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "broken.md").write_text("see [X](./missing.md)", encoding="utf-8")
    (corpus / "bad-fm.md").write_text(
        '---\ntitle: "T"\nconcept_id: "y"\ndifficulty: "expert"\n---\n', encoding="utf-8",
    )
    report = L.lint_corpus(corpus)
    assert report.ok() is False
    by_check = report.by_check()
    assert by_check.get("link_integrity", 0) == 1
    assert by_check.get("frontmatter_schema", 0) == 1


def test_lint_corpus_passes_dedupe_callback(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "x.md").write_text("# clean\n", encoding="utf-8")
    captured = []

    def fake_dedupe(files):
        captured.append([str(p) for p, _ in files])
        return [L.LintViolation(check="dedupe_candidates", file_path="x.md", message="dup with y.md (cosine=0.95)")]

    report = L.lint_corpus(corpus, dedupe_candidates_fn=fake_dedupe)
    assert len(captured) == 1
    assert captured[0][0].endswith("x.md")
    assert any(v.check == "dedupe_candidates" for v in report.violations)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_main_clean_corpus_returns_zero(tmp_path, capsys):
    corpus = tmp_path / "k" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "x.md").write_text("# H1\nbody\n", encoding="utf-8")
    rc = L.main(["--corpus", str(corpus)])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_main_dirty_corpus_returns_zero_in_report_only(tmp_path, capsys):
    """Default mode is report-only — surfaces violations but exits 0
    so CI can gradually enforce."""
    corpus = tmp_path / "k" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "broken.md").write_text("see [X](./missing.md)", encoding="utf-8")
    rc = L.main(["--corpus", str(corpus)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "report-only mode" in out


def test_main_strict_dirty_corpus_returns_one(tmp_path, capsys):
    """--strict re-enables hard failure for CI once P5.5 cleanup
    finishes."""
    corpus = tmp_path / "k" / "cs" / "contents"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "broken.md").write_text("see [X](./missing.md)", encoding="utf-8")
    rc = L.main(["--corpus", str(corpus), "--strict"])
    assert rc == 1


def test_main_missing_corpus_returns_two(tmp_path, capsys):
    rc = L.main(["--corpus", str(tmp_path / "does-not-exist")])
    assert rc == 2
