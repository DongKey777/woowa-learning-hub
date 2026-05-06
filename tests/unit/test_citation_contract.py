"""Phase 9.4 — Citation block contract.

Pre-renders a `참고:` markdown block in `bin/rag-ask` output so the AI
session can copy it verbatim instead of authoring citation by hand.

Contract:
  * `integration.augment()` return dict gains `response_hints`
    sub-dict with citation fields:
      - `citation_markdown`: paste-ready string for tier ≥ 1 with
        hits, else None
      - `citation_paths`: deduplicated list of hit paths used in
        citation_markdown (max 3)
      - `citation_trace`: per-path trace metadata so operators can
        explain which retrieval bucket and score backed the pasted
        `참고:` block
      - `tier_downgrade` / `fallback_disclaimer`: always-present
        downgrade keys so consumers can read a stable shape even when
        citation is absent
  * `bin/rag-ask` JSON output gains a top-level `response_hints`
    field surfaced from augment.

These tests guard the contract — if a refactor drops the field,
they fail. AGENTS.md / CLAUDE.md regulation switches from
"AI 세션이 `참고:` 인용" to "verbatim copy of
`response_hints.citation_markdown`".
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import indexer, searcher


class _ReadyReport:
    state = "ready"
    reason = "ready"
    corpus_hash = "fixture"
    index_manifest_hash = "fixture"
    next_command = None


def _write_manifest(index_root: Path) -> None:
    index_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "row_count": 1,
        "corpus_hash": "fixture",
        "corpus_root": "fixture",
        "encoder": {"model_id": "BAAI/bge-m3"},
        "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
        "modalities": ["fts", "dense", "sparse"],
    }
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _hit(path: str, score: float = 1.0) -> dict:
    return {
        "path": path,
        "title": Path(path).stem,
        "category": Path(path).parent.name,
        "section_title": "핵심 개념",
        "section_path": [Path(path).stem, "핵심 개념"],
        "score": score,
        "snippet_preview": "preview",
    }


def _refusal_sentinel() -> dict:
    return {
        "path": "<sentinel:no_confident_match>",
        "title": "",
        "category": "",
        "section_title": "",
        "section_path": [],
        "score": -1.5,
        "snippet_preview": "",
        "sentinel": "no_confident_match",
    }


def test_augment_emits_citation_markdown_when_hits_present(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.92),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.81),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert "response_hints" in result
    rh = result["response_hints"]

    assert rh["citation_markdown"] is not None
    assert rh["citation_markdown"].startswith("참고:\n"), \
        f"unexpected citation prefix: {rh['citation_markdown'][:40]!r}"

    # Every hit path appears in the markdown
    for path in (
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ):
        assert path in rh["citation_markdown"], \
            f"{path} missing from citation"

    # citation_paths reflects hits in order, deduplicated, max 3
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ]
    assert rh["tier_downgrade"] is None
    assert rh["fallback_disclaimer"] is None
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.92,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.81,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
    ]


def test_augment_caps_citation_at_three_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit(f"knowledge/cs/contents/spring/x{i}.md", 1.0 - i * 0.05)
            for i in range(7)
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert len(rh["citation_paths"]) == 3
    # Only the top three are in the markdown
    for i in range(3):
        assert f"x{i}.md" in rh["citation_markdown"]
    for i in range(3, 7):
        assert f"x{i}.md" not in rh["citation_markdown"]


def test_augment_dedupes_repeated_paths_in_citation(tmp_path, monkeypatch):
    """When the same path appears in by_learning_point AND by_fallback_key
    buckets, citation_paths should still list it once."""
    index_root = tmp_path / "index"
    _write_manifest(index_root)
    same_path = "knowledge/cs/contents/spring/spring-bean-di-basics.md"

    def fake_search(prompt, **kwargs):
        # augment dedupes by `seen_paths` so this naturally tests
        # citation_paths not duplicating.
        return [_hit(same_path, 0.92)]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"].count(same_path) == 1


def test_augment_citation_trace_keeps_best_bucket_per_path(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)
    same_path = "knowledge/cs/contents/spring/spring-bean-di-basics.md"

    def fake_search(prompt, **kwargs):
        learning_points = kwargs.get("learning_points") or []
        if learning_points == ["spring/di"]:
            return [_hit(same_path, 0.71)]
        if learning_points == ["spring/ioc"]:
            return [
                _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.85),
                _hit(same_path, 0.94),
            ]
        return []

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=["spring/di", "spring/ioc"],
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        same_path,
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ]
    assert rh["citation_trace"] == [
        {
            "path": same_path,
            "score": 0.94,
            "category": "spring",
            "bucket": "learning_point:spring/ioc",
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.85,
            "category": "spring",
            "bucket": "learning_point:spring/ioc",
        },
    ]


def test_augment_ignores_malformed_non_dict_hits_in_citation_trace(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            "junk-row",
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.92),
            ["nested-junk"],
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.81),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["meta"]["reason"] == "ready"
    assert result["response_hints"]["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ]
    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.92,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.81,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
    ]


def test_select_citation_hits_ignores_malformed_non_dict_rows():
    assert integration._select_citation_hits(
        [
            "junk-row",
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            123,
        ]
    ) == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        }
    ]


def test_select_citation_hits_prefers_cleaner_metadata_on_equal_score():
    same_path = "knowledge/cs/contents/spring/spring-bean-di-basics.md"

    assert integration._select_citation_hits(
        [
            {
                **_hit(same_path, 0.91),
                "_citation_bucket": "learning_point:spring/dirty\ntrace:leak",
            },
            {
                **_hit(same_path, 0.91),
                "_citation_bucket": "learning_point:spring/clean",
            },
        ]
    ) == [
        {
            "path": same_path,
            "score": 0.91,
            "category": "spring",
            "bucket": "learning_point:spring/clean",
        }
    ]


def test_select_citation_hits_prefers_learning_point_bucket_on_equal_score():
    same_path = "knowledge/cs/contents/spring/spring-bean-di-basics.md"

    assert integration._select_citation_hits(
        [
            {
                **_hit(same_path, 0.91),
                "_citation_bucket": "fallback:spring:spring_framework",
            },
            {
                **_hit(same_path, 0.91),
                "_citation_bucket": "learning_point:spring/di",
            },
        ]
    ) == [
        {
            "path": same_path,
            "score": 0.91,
            "category": "spring",
            "bucket": "learning_point:spring/di",
        }
    ]


def test_select_citation_hits_keeps_first_seen_order_on_equal_scores():
    assert integration._select_citation_hits(
        [
            {
                **_hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
                "_citation_bucket": "fallback:spring:spring_framework",
            },
            {
                **_hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.91),
                "_citation_bucket": "fallback:spring:spring_framework",
            },
            {
                **_hit("knowledge/cs/contents/spring/bean-scope.md", 0.91),
                "_citation_bucket": "fallback:spring:spring_framework",
            },
        ]
    ) == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
        {
            "path": "knowledge/cs/contents/spring/bean-scope.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
    ]


def test_augment_citation_trace_matches_pasted_paths_exactly(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.97),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.93),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.88),
            _hit("knowledge/cs/contents/spring/bean-scope.md", 0.84),
            _hit("knowledge/cs/contents/spring/extra-fourth.md", 0.79),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/ioc-di-container.md",
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/bean-scope.md",
    ]
    assert [entry["path"] for entry in rh["citation_trace"]] == rh["citation_paths"]
    assert all(
        entry["path"] != "knowledge/cs/contents/spring/extra-fourth.md"
        for entry in rh["citation_trace"]
    )


def test_augment_builds_citation_markdown_and_trace_from_one_selection_pass(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.97),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.93),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_select = integration._select_citation_hits
    select_calls = 0

    def wrapped_select(all_hits, *, max_n=3):
        nonlocal select_calls
        select_calls += 1
        selected = original_select(all_hits, max_n=max_n)
        if select_calls == 1:
            return selected
        return [
            {
                **selected[0],
                "path": "knowledge/cs/contents/spring/mismatched-second-pass.md",
            }
        ]

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert select_calls == 1
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/ioc-di-container.md",
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
    ]
    assert [entry["path"] for entry in rh["citation_trace"]] == rh["citation_paths"]
    assert "mismatched-second-pass.md" not in rh["citation_markdown"]


def test_augment_revalidates_selected_citation_trace_entries(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.97),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.93),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    def wrapped_select(all_hits, *, max_n=3):
        return [
            {
                "path": "knowledge/cs/contents/spring/ioc-di-container.md",
                "score": "NaN",
                "category": " totally-wrong ",
                "bucket": "manual_override:spring",
            },
            {
                "path": "knowledge/cs/contents/spring/ioc-di-container.md",
                "score": 0.88,
                "category": "spring",
                "bucket": "fallback:spring:spring_framework",
            },
            {
                "path": "knowledge/cs/contents/spring/bean-scope.md\n- leak.md",
                "score": 0.91,
                "category": "spring",
                "bucket": "fallback:spring:spring_framework",
            },
            {
                "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
                "score": 0.93,
                "category": "database",
                "bucket": "fallback:spring:spring_framework",
            },
        ]

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_paths"] == [
        "knowledge/cs/contents/spring/ioc-di-container.md",
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
    ]
    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": None,
            "category": "spring",
            "bucket": None,
        },
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.93,
            "category": "database",
            "bucket": "fallback:spring:spring_framework",
        },
    ]
    assert "bean-scope.md" not in result["response_hints"]["citation_markdown"]


def test_augment_empty_hits_returns_none_citation(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return []

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []
    assert rh["citation_trace"] == []
    assert rh["tier_downgrade"] is None
    assert rh["fallback_disclaimer"] is None


def test_augment_citation_trace_avoids_non_json_scores(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            {**_hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.0), "score": "NaN"},
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": None,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        },
    ]
    json.dumps(result["response_hints"], allow_nan=False)


def test_augment_citation_trace_ignores_whitespace_injected_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit(
                "knowledge/cs/contents/spring/ioc-di-container.md\n- leak.md",
                0.99,
            ),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert rh["citation_markdown"] == (
        "참고:\n- knowledge/cs/contents/spring/spring-bean-di-basics.md"
    )


def test_augment_citation_trace_ignores_non_corpus_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit("docs/internal-only.md", 0.99),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]


def test_augment_citation_trace_ignores_non_content_cs_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/README.md", 0.99),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert "knowledge/cs/README.md" not in rh["citation_markdown"]


def test_augment_citation_trace_ignores_fragment_and_query_decorated_paths(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md#section", 0.99),
            _hit("knowledge/cs/contents/spring/spring-aop-basics.md?lang=ko", 0.95),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert "ioc-di-container.md#section" not in rh["citation_markdown"]
    assert "spring-aop-basics.md?lang=ko" not in rh["citation_markdown"]


def test_augment_citation_trace_ignores_parent_traversal_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/../spring/escape.md", 0.99),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert "escape.md" not in rh["citation_markdown"]


def test_augment_citation_trace_ignores_dot_segment_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/./spring/dot-segment.md", 0.99),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert "dot-segment.md" not in rh["citation_markdown"]


def test_augment_citation_trace_ignores_duplicate_separator_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring//double-slash.md", 0.99),
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md"
    ]
    assert rh["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]
    assert "double-slash.md" not in rh["citation_markdown"]


def test_augment_citation_trace_derives_category_from_path_when_hit_metadata_is_dirty(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            {
                **_hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
                "category": " spring basics ",
            }
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:spring:spring_framework",
        }
    ]


def test_augment_citation_trace_keeps_valid_hit_category_when_it_differs_from_path(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            {
                **_hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
                "category": "database",
            }
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "database",
            "bucket": "fallback:spring:spring_framework",
        }
    ]


def test_augment_citation_trace_keeps_clean_hyphenated_cross_category_labels(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            {
                **_hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
                "category": "system-design",
            }
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "system-design",
            "bucket": "fallback:spring:spring_framework",
        }
    ]


def test_augment_citation_trace_nulls_dirty_bucket_metadata(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_extend = integration._select_citation_hits

    def wrapped_select(all_hits, *, max_n=3):
        dirty_hits = [
            {**hit, "_citation_bucket": "fallback:spring\ntrace:leak"}
            for hit in all_hits
        ]
        return original_extend(dirty_hits, max_n=max_n)

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        }
    ]


def test_augment_citation_trace_nulls_unknown_bucket_prefix(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_select = integration._select_citation_hits

    def wrapped_select(all_hits, *, max_n=3):
        dirty_hits = [{**hit, "_citation_bucket": "manual_override:spring"} for hit in all_hits]
        return original_select(dirty_hits, max_n=max_n)

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        }
    ]


def test_augment_citation_trace_nulls_empty_and_nested_bucket_aliases(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.88),
            _hit("knowledge/cs/contents/spring/spring-aop-basics.md", 0.87),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_select = integration._select_citation_hits

    def wrapped_select(all_hits, *, max_n=3):
        selected = original_select(all_hits, max_n=max_n)
        return [
            {**selected[0], "bucket": "fallback:"},
            {**selected[1], "bucket": "fallback:fallback:spring:spring_framework"},
            {**selected[2], "bucket": "learning_point:learning_point:spring/di"},
        ]

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.88,
            "category": "spring",
            "bucket": None,
        },
        {
            "path": "knowledge/cs/contents/spring/spring-aop-basics.md",
            "score": 0.87,
            "category": "spring",
            "bucket": None,
        },
    ]


def test_augment_citation_trace_nulls_overqualified_bucket_aliases(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.88),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_select = integration._select_citation_hits

    def wrapped_select(all_hits, *, max_n=3):
        selected = original_select(all_hits, max_n=max_n)
        return [
            {**selected[0], "bucket": "learning_point:spring/di:alias"},
            {**selected[1], "bucket": "fallback:spring:spring_framework:alias"},
        ]

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.88,
            "category": "spring",
            "bucket": None,
        },
    ]


def test_augment_citation_trace_nulls_punctuation_injected_bucket_aliases(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.88),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    original_select = integration._select_citation_hits

    def wrapped_select(all_hits, *, max_n=3):
        selected = original_select(all_hits, max_n=max_n)
        return [
            {**selected[0], "bucket": "learning_point:spring/di?topic=bean"},
            {**selected[1], "bucket": "fallback:spring:spring.framework"},
        ]

    monkeypatch.setattr(integration, "_select_citation_hits", wrapped_select)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": None,
        },
        {
            "path": "knowledge/cs/contents/spring/ioc-di-container.md",
            "score": 0.88,
            "category": "spring",
            "bucket": None,
        },
    ]


def test_augment_skip_mode_returns_none_response_hints():
    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="skip",
    )
    # Even in skip mode the response_hints field exists with None
    # citation — keeps the contract uniform.
    rh = result.get("response_hints")
    assert rh is not None
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []
    assert rh["citation_trace"] == []
    assert rh["tier_downgrade"] is None
    assert rh["fallback_disclaimer"] is None


def test_augment_general_fallback_trace_sanitizes_non_ascii_query_token(
    tmp_path, monkeypatch
):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.91),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)
    monkeypatch.setattr(integration.signal_rules, "detect_signals", lambda *_: [])

    result = integration.augment(
        prompt="스프링 빈이 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert result["response_hints"]["citation_trace"] == [
        {
            "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "score": 0.91,
            "category": "spring",
            "bucket": "fallback:general:unknown",
        }
    ]


def test_augment_refusal_sentinel_clears_citation_trace(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [_refusal_sentinel()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []
    assert rh["citation_trace"] == []
    assert rh["tier_downgrade"] == "corpus_gap_no_confident_match"
    assert rh["fallback_disclaimer"] is not None
    assert result["fallback_reason"] == "corpus_gap_no_confident_match"


def test_augment_refusal_sentinel_discards_earlier_bucket_hits(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        learning_points = kwargs.get("learning_points") or []
        if learning_points == ["spring/di"]:
            return [_hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.92)]
        return [_refusal_sentinel()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=["spring/di", "spring/ioc"],
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert result["by_learning_point"] == {}
    assert result["by_fallback_key"] == {}
    assert result["cs_categories_hit"] == []
    assert result["sidecar"] is None
    assert result["fallback_reason"] == "corpus_gap_no_confident_match"
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []
    assert rh["citation_trace"] == []
    assert rh["tier_downgrade"] == "corpus_gap_no_confident_match"


# ---------------------------------------------------------------------------
# `bin/rag-ask` surface — top-level response_hints contract
# ---------------------------------------------------------------------------

def _import_cli():
    import sys
    repo_root = Path(__file__).resolve().parents[2]
    for entry in (repo_root, repo_root / "scripts" / "workbench"):
        if str(entry) not in sys.path:
            sys.path.insert(0, str(entry))
    from scripts.workbench import cli  # noqa: WPS433
    return cli


def _patch_classify(monkeypatch, decision):
    """cli.build_rag_ask_output performs `from core.interactive_rag_router
    import classify` via sys.path entry — patch BOTH possible module
    aliases (`core.*` and `scripts.workbench.core.*`) so the local-scope
    rebind sees our fake."""
    cli_mod = _import_cli()  # ensures sys.path is set
    import importlib

    def fake_classify(prompt, **kwargs):
        return decision

    for module_name in (
        "core.interactive_rag_router",
        "scripts.workbench.core.interactive_rag_router",
    ):
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            continue
        monkeypatch.setattr(mod, "classify", fake_classify)


def test_rag_ask_output_has_response_hints_stub_for_tier_0(monkeypatch):
    """Tier 0 / blocked / tier 3 turns must still carry the
    `response_hints` key so downstream code can read a uniform shape."""
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision

    _patch_classify(monkeypatch, RouterDecision(
        tier=0, mode=None, reason="tool/build question, no CS domain",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    args = type("Args", (), {
        "prompt": "git log 어떻게 써?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    assert "response_hints" in out
    assert out["response_hints"]["citation_markdown"] is None
    assert out["response_hints"]["citation_paths"] == []
    assert out["response_hints"]["citation_trace"] == []
    assert out["response_hints"]["tier_downgrade"] is None
    assert out["response_hints"]["fallback_disclaimer"] is None


def test_rag_ask_output_surfaces_augment_response_hints(tmp_path, monkeypatch):
    """When tier ∈ {1,2}, build_rag_ask_output should mirror
    augment's response_hints to the top-level rag-ask payload."""
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision
    from scripts.learning import integration as integration_mod

    _patch_classify(monkeypatch, RouterDecision(
        tier=1, mode="cheap", reason="domain definition",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    captured_hints = {
        "citation_markdown":
            "참고:\n- knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "citation_paths":
            ["knowledge/cs/contents/spring/spring-bean-di-basics.md"],
        "citation_trace": [
            {
                "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
                "score": 0.92,
                "category": "spring",
                "bucket": "fallback:general:spring",
            }
        ],
        "tier_downgrade": None,
        "fallback_disclaimer": None,
    }

    def fake_augment(**kwargs):
        return {
            "by_learning_point": {},
            "by_fallback_key": {"definition": [
                {"path": "knowledge/cs/contents/spring/spring-bean-di-basics.md"}
            ]},
            "fallback_reason": None,
            "cs_categories_hit": ["spring"],
            "sidecar": None,
            "meta": {
                "latency_ms": 1, "rag_ready": True, "reason": "ready",
                "mode_used": "cheap", "backend": "r3",
                "category_filter_fallback": False,
            },
            "response_hints": captured_hints,
        }

    monkeypatch.setattr(integration_mod, "augment", fake_augment)

    args = type("Args", (), {
        "prompt": "Spring DI가 뭐야?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    assert out["decision"]["tier"] == 1
    assert out["response_hints"] == captured_hints
    # Citation markdown is paste-ready — exact string match guards the
    # AI session contract.
    assert out["response_hints"]["citation_markdown"].startswith("참고:\n- ")
