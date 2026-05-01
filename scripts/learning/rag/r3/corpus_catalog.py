"""Corpus v2 concept catalog generation from staged frontmatter."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.learning.rag.corpus_lint import parse_frontmatter


@dataclass(frozen=True)
class ConceptCatalogEntryV2:
    concept_id: str
    paths: tuple[str, ...]
    doc_roles: tuple[str, ...]
    levels: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    expected_queries: tuple[str, ...] = ()
    forbidden_neighbors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        blob = asdict(self)
        for key in (
            "paths",
            "doc_roles",
            "levels",
            "aliases",
            "expected_queries",
            "forbidden_neighbors",
        ):
            blob[key] = list(blob[key])
        return blob


@dataclass(frozen=True)
class ConceptCatalogV2:
    schema_version: str
    corpus_root: str
    concept_count: int
    query_seed_count: int
    concepts: dict[str, ConceptCatalogEntryV2]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "corpus_root": self.corpus_root,
            "concept_count": self.concept_count,
            "query_seed_count": self.query_seed_count,
            "concepts": {
                concept_id: entry.to_dict()
                for concept_id, entry in sorted(self.concepts.items())
            },
        }


def _as_string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _relative_path(path: Path, corpus_root: Path) -> str:
    try:
        return str(path.relative_to(corpus_root))
    except ValueError:
        return str(path)


def build_concept_catalog_v2(corpus_root: Path) -> ConceptCatalogV2:
    grouped: dict[str, dict[str, Any]] = {}
    for path in sorted(corpus_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm or str(fm.get("schema_version")) != "2":
            continue
        concept_id = str(fm.get("concept_id") or "").strip()
        if not concept_id:
            continue
        entry = grouped.setdefault(
            concept_id,
            {
                "paths": [],
                "doc_roles": set(),
                "levels": set(),
                "aliases": set(),
                "expected_queries": [],
                "forbidden_neighbors": set(),
            },
        )
        entry["paths"].append(_relative_path(path, corpus_root))
        if fm.get("doc_role"):
            entry["doc_roles"].add(str(fm["doc_role"]))
        if fm.get("level"):
            entry["levels"].add(str(fm["level"]))
        entry["aliases"].update(_as_string_list(fm.get("aliases")))
        entry["expected_queries"].extend(_as_string_list(fm.get("expected_queries")))
        entry["forbidden_neighbors"].update(
            _as_string_list(fm.get("forbidden_neighbors"))
        )

    concepts = {
        concept_id: ConceptCatalogEntryV2(
            concept_id=concept_id,
            paths=tuple(sorted(blob["paths"])),
            doc_roles=tuple(sorted(blob["doc_roles"])),
            levels=tuple(sorted(blob["levels"])),
            aliases=tuple(sorted(blob["aliases"])),
            expected_queries=tuple(blob["expected_queries"]),
            forbidden_neighbors=tuple(sorted(blob["forbidden_neighbors"])),
        )
        for concept_id, blob in grouped.items()
    }
    return ConceptCatalogV2(
        schema_version="2",
        corpus_root=str(corpus_root),
        concept_count=len(concepts),
        query_seed_count=sum(len(entry.expected_queries) for entry in concepts.values()),
        concepts=concepts,
    )


def write_concept_catalog_v2(catalog: ConceptCatalogV2, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(catalog.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    catalog = build_concept_catalog_v2(args.corpus_root)
    write_concept_catalog_v2(catalog, args.out)
    print(
        "wrote Corpus v2 concept catalog "
        f"({catalog.concept_count} concepts, {catalog.query_seed_count} query seeds) "
        f"to {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
