from __future__ import annotations

from pathlib import Path

from scripts.learning.rag import corpus_lint as L


def _write_v3_doc(
    path: Path,
    *,
    concept_id: str,
    confusable_with: list[str],
    forbidden_neighbors: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "schema_version: 3",
                f"title: {concept_id}",
                f"concept_id: {concept_id}",
                "canonical: true",
                "category: spring",
                "difficulty: beginner",
                "doc_role: chooser",
                "level: beginner",
                "language: mixed",
                "source_priority: 90",
                "mission_ids: []",
                "review_feedback_tags: []",
                "aliases:",
                "- bean chooser",
                "symptoms:",
                "- 같은 Bean 문서와 chooser가 헷갈려요",
                "intents:",
                "- comparison",
                "prerequisites: []",
                "next_docs: []",
                "linked_paths: []",
                "confusable_with:",
                *[f"- {item}" for item in confusable_with],
                "forbidden_neighbors:",
                *[f"- {item}" for item in forbidden_neighbors],
                "expected_queries:",
                "- Bean chooser가 뭐야",
                "contextual_chunk_prefix: spring chooser test fixture",
                "---",
                f"# {concept_id}",
                "",
                "body",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_changed_files_empty_keeps_legacy_strict_v3_warnings_non_blocking(tmp_path: Path) -> None:
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    legacy = corpus / "spring" / "legacy-collision.md"
    _write_v3_doc(
        legacy,
        concept_id="spring/legacy-collision",
        confusable_with=["spring/bean-di-basics", "spring/other"],
        forbidden_neighbors=["contents/spring/spring-bean-di-basics.md"],
    )

    assert L.main([
        "--corpus", str(corpus),
        "--strict", "--strict-v3",
        "--changed-files",
    ]) == 0


def test_changed_file_collision_is_strict_v3_blocker(tmp_path: Path) -> None:
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    changed = corpus / "spring" / "changed-collision.md"
    _write_v3_doc(
        changed,
        concept_id="spring/changed-collision",
        confusable_with=["spring/bean-di-basics", "spring/other"],
        forbidden_neighbors=["contents/spring/spring-bean-di-basics.md"],
    )

    assert L.main([
        "--corpus", str(corpus),
        "--strict", "--strict-v3",
        "--changed-files", str(changed),
    ]) == 1


def test_changed_clean_file_passes_while_legacy_collision_is_warning(tmp_path: Path) -> None:
    corpus = tmp_path / "knowledge" / "cs" / "contents"
    legacy = corpus / "spring" / "legacy-collision.md"
    changed = corpus / "spring" / "changed-clean.md"
    _write_v3_doc(
        legacy,
        concept_id="spring/legacy-collision",
        confusable_with=["spring/bean-di-basics", "spring/other"],
        forbidden_neighbors=["contents/spring/spring-bean-di-basics.md"],
    )
    _write_v3_doc(
        changed,
        concept_id="spring/changed-clean",
        confusable_with=["spring/clean-target", "spring/other"],
        forbidden_neighbors=["contents/spring/unrelated.md"],
    )

    assert L.main([
        "--corpus", str(corpus),
        "--strict", "--strict-v3",
        "--changed-files", str(changed),
    ]) == 0
