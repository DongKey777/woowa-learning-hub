from __future__ import annotations

import json

from scripts.learning.rag.r3.corpus_catalog import (
    build_concept_catalog_v2,
    write_concept_catalog_v2,
)


def test_build_concept_catalog_v2_groups_schema_v2_frontmatter(tmp_path):
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    spring = corpus / "spring"
    spring.mkdir(parents=True)
    (spring / "di.md").write_text(
        "---\n"
        "schema_version: 2\n"
        'title: "Dependency Injection"\n'
        "concept_id: spring/di\n"
        "difficulty: beginner\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases:\n"
        "  - DI\n"
        "  - 의존성 주입\n"
        "expected_queries:\n"
        "  - DI가 뭐야?\n"
        "  - dependency injection이 뭐야?\n"
        "forbidden_neighbors:\n"
        "  - contents/design-pattern/service-locator.md\n"
        "---\n\nbody\n",
        encoding="utf-8",
    )
    (spring / "di-deep.md").write_text(
        "---\n"
        "schema_version: 2\n"
        'title: "DI Deep Dive"\n'
        "concept_id: spring/di\n"
        "difficulty: intermediate\n"
        "doc_role: deep_dive\n"
        "level: intermediate\n"
        "aliases:\n"
        "  - constructor injection\n"
        "expected_queries:\n"
        "  - 생성자 주입은 왜 좋아?\n"
        "---\n\nbody\n",
        encoding="utf-8",
    )
    (spring / "legacy.md").write_text("# no frontmatter\n", encoding="utf-8")

    catalog = build_concept_catalog_v2(corpus)

    assert catalog.concept_count == 1
    assert catalog.query_seed_count == 3
    entry = catalog.concepts["spring/di"]
    assert entry.paths == ("spring/di-deep.md", "spring/di.md")
    assert entry.doc_roles == ("deep_dive", "primer")
    assert entry.levels == ("beginner", "intermediate")
    assert "DI" in entry.aliases
    assert entry.expected_queries == (
        "생성자 주입은 왜 좋아?",
        "DI가 뭐야?",
        "dependency injection이 뭐야?",
    )
    assert entry.forbidden_neighbors == (
        "contents/design-pattern/service-locator.md",
    )


def test_write_concept_catalog_v2_outputs_json(tmp_path):
    corpus = tmp_path / "contents"
    corpus.mkdir()
    (corpus / "latency.md").write_text(
        "---\n"
        "schema_version: 2\n"
        'title: "Latency"\n'
        "concept_id: network/latency\n"
        "difficulty: beginner\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases: [latency, 지연 시간]\n"
        "expected_queries: [latency가 뭐야?]\n"
        "---\n\nbody\n",
        encoding="utf-8",
    )
    out = tmp_path / "catalog" / "concepts.v2.json"

    write_concept_catalog_v2(build_concept_catalog_v2(corpus), out)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2"
    assert payload["concepts"]["network/latency"]["paths"] == ["latency.md"]
