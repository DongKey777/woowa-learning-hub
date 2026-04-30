"""Sampled corpus materialisation for low-cost H8 candidate checks.

The full CS corpus is large enough that local bge-m3 re-encoding is not
practical on the current machine.  This module builds a small, explicit
subset from evaluated queries:

1. keep only queries in target categories;
2. copy every qrel/forbidden document those queries judge;
3. optionally add a small number of beginner/intermediate decoys per category;
4. dump a matching graded fixture.

The resulting corpus keeps the normal ``knowledge/cs`` layout under
``contents/<category>/...`` so the existing corpus loader and LanceDB indexer
can consume it unchanged.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .dataset import GradedQuery, dump_graded_fixture

DEFAULT_CORE_CATEGORIES = (
    "spring",
    "database",
    "network",
    "operating-system",
    "data-structure",
    "algorithm",
    "software-engineering",
)

PREFERRED_EXTRA_DIFFICULTIES = ("beginner", "intermediate", "unknown", "advanced")


@dataclass(frozen=True)
class SampledCorpusResult:
    corpus_root: Path
    fixture_path: Path
    categories: tuple[str, ...]
    queries: tuple[GradedQuery, ...]
    required_doc_paths: tuple[str, ...]
    extra_doc_paths: tuple[str, ...]

    @property
    def doc_count(self) -> int:
        return len(set(self.required_doc_paths) | set(self.extra_doc_paths))

    def to_summary(self) -> dict:
        return {
            "corpus_root": str(self.corpus_root),
            "fixture_path": str(self.fixture_path),
            "categories": list(self.categories),
            "query_count": len(self.queries),
            "required_doc_count": len(self.required_doc_paths),
            "extra_doc_count": len(self.extra_doc_paths),
            "doc_count": self.doc_count,
        }


def parse_categories(raw: str | Sequence[str] | None) -> tuple[str, ...]:
    """Parse comma-separated or sequence category input into a stable tuple."""
    if raw is None:
        return DEFAULT_CORE_CATEGORIES
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        parts = [str(part).strip() for part in raw if str(part).strip()]
    if not parts:
        raise ValueError("at least one category is required")
    return tuple(dict.fromkeys(parts))


def filter_queries_by_category(
    queries: Sequence[GradedQuery],
    categories: Sequence[str],
) -> tuple[GradedQuery, ...]:
    allowed = set(categories)
    return tuple(q for q in queries if q.bucket.category in allowed)


def _category_from_path(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] == "contents":
        return parts[1]
    return None


def collect_judged_paths(
    queries: Sequence[GradedQuery],
    *,
    include_forbidden: bool = True,
) -> tuple[str, ...]:
    paths: list[str] = []
    seen: set[str] = set()
    for query in queries:
        for qrel in query.qrels:
            if qrel.path not in seen:
                paths.append(qrel.path)
                seen.add(qrel.path)
        if include_forbidden:
            for path in query.forbidden_paths:
                if path not in seen:
                    paths.append(path)
                    seen.add(path)
    return tuple(paths)


def _difficulty_rank(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return PREFERRED_EXTRA_DIFFICULTIES.index("unknown")
    lowered = text.lower()
    for idx, label in enumerate(PREFERRED_EXTRA_DIFFICULTIES):
        if label != "unknown" and label in lowered:
            return idx
    return PREFERRED_EXTRA_DIFFICULTIES.index("unknown")


def select_extra_docs(
    source_corpus_root: Path | str,
    *,
    categories: Sequence[str],
    required_doc_paths: Sequence[str],
    per_category: int,
) -> tuple[str, ...]:
    """Select deterministic category decoys not already required by qrels."""
    if per_category <= 0:
        return ()

    root = Path(source_corpus_root)
    required = set(required_doc_paths)
    out: list[str] = []
    for category in categories:
        category_dir = root / "contents" / category
        if not category_dir.exists():
            continue
        candidates: list[tuple[int, str]] = []
        for md in category_dir.rglob("*.md"):
            rel = md.relative_to(root).as_posix()
            if rel in required:
                continue
            candidates.append((_difficulty_rank(md), rel))
        candidates.sort(key=lambda item: (item[0], item[1]))
        out.extend(rel for _rank, rel in candidates[:per_category])
    return tuple(dict.fromkeys(out))


def _copy_docs(
    *,
    source_corpus_root: Path,
    target_corpus_root: Path,
    paths: Iterable[str],
) -> None:
    for rel in paths:
        src = source_corpus_root / rel
        if not src.exists():
            continue
        dst = target_corpus_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def materialize_sampled_corpus(
    *,
    source_corpus_root: Path | str,
    target_root: Path | str,
    queries: Sequence[GradedQuery],
    categories: Sequence[str] = DEFAULT_CORE_CATEGORIES,
    extra_docs_per_category: int = 10,
    include_forbidden: bool = True,
    clean: bool = True,
) -> SampledCorpusResult:
    """Create a sampled corpus + fixture under ``target_root``."""
    source = Path(source_corpus_root)
    target = Path(target_root)
    corpus_root = target / "corpus"
    fixture_path = target / "fixture.json"
    categories_tuple = parse_categories(categories)
    selected_queries = filter_queries_by_category(queries, categories_tuple)
    if not selected_queries:
        raise ValueError(f"no queries matched categories: {categories_tuple!r}")

    required_paths = tuple(
        path
        for path in collect_judged_paths(
            selected_queries,
            include_forbidden=include_forbidden,
        )
        if _category_from_path(path) in set(categories_tuple)
    )
    if not required_paths:
        raise ValueError("selected queries had no judged docs in sampled categories")

    extra_paths = select_extra_docs(
        source,
        categories=categories_tuple,
        required_doc_paths=required_paths,
        per_category=extra_docs_per_category,
    )

    if clean:
        # Keep sibling build artifacts (notably ``target/index``) intact so
        # repeated sampled ablation can reuse a still-compatible LanceDB index.
        # Staleness is guarded by the index manifest corpus_hash in the CLI.
        if corpus_root.exists():
            shutil.rmtree(corpus_root)
        if fixture_path.exists():
            fixture_path.unlink()
    corpus_root.mkdir(parents=True, exist_ok=True)
    _copy_docs(
        source_corpus_root=source,
        target_corpus_root=corpus_root,
        paths=[*required_paths, *extra_paths],
    )
    dump_graded_fixture(selected_queries, fixture_path)

    return SampledCorpusResult(
        corpus_root=corpus_root,
        fixture_path=fixture_path,
        categories=categories_tuple,
        queries=selected_queries,
        required_doc_paths=required_paths,
        extra_doc_paths=extra_paths,
    )
