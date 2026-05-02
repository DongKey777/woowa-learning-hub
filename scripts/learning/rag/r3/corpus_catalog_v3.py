"""Corpus v3 concept catalog generation + cross-doc reference resolver.

The v3 catalog is the authoritative concept_id ↔ doc index used by the
R3 retrieval fabric. It is built from frontmatter under
``knowledge/cs/contents/**/*.md`` and emitted as a single JSON file at
``knowledge/cs/catalog/concepts.v3.json`` (default).

Companion reverse indexes (separate files for retriever channel access):

* ``mission_ids_to_concepts.json``  — mission_bridge retriever
* ``confusable_neighbors.json``     — fusion-stage negative routing
* ``aliases_to_concept.json``       — alias-based lexical channel
* ``symptom_to_concepts.json``      — symptom_router retriever
* ``unresolved_refs.json``          — diagnostic — every dangling
  ``confusable_with`` / ``prerequisites`` / ``next_docs`` / ``mission_ids``
  reference. Lint pattern check is per-doc; resolver is global.

Pre-v2 docs (no frontmatter) are emitted as ``stub`` records keyed by
``concept_id_inferred = "<category>/<filename-without-ext>"`` so cross-doc
references that point at unmigrated docs do *not* show up as dangling
during Wave A migration. Stubs lose their stub flag once migrated.

Companion to:
- ``docs/worklogs/rag-r3-corpus-v3-contract.md``
- ``scripts/learning/rag/corpus_lint.py``
- ``scripts/learning/rag/r3/corpus_catalog.py`` (v2 builder, unchanged)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.learning.rag.corpus_lint import parse_frontmatter


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConceptCatalogEntryV3:
    concept_id: str
    doc_path: str           # repo-relative
    has_frontmatter: bool   # False for pre-v2 stubs
    canonical: bool = False
    category: str | None = None
    doc_role: str | None = None
    level: str | None = None
    language: str | None = None
    source_priority: int | None = None
    aliases: tuple[str, ...] = ()
    expected_queries: tuple[str, ...] = ()
    symptoms: tuple[str, ...] = ()
    intents: tuple[str, ...] = ()
    mission_ids: tuple[str, ...] = ()
    review_feedback_tags: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    next_docs: tuple[str, ...] = ()
    confusable_with: tuple[str, ...] = ()
    forbidden_neighbors: tuple[str, ...] = ()
    linked_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        blob = asdict(self)
        for key in (
            "aliases",
            "expected_queries",
            "symptoms",
            "intents",
            "mission_ids",
            "review_feedback_tags",
            "prerequisites",
            "next_docs",
            "confusable_with",
            "forbidden_neighbors",
            "linked_paths",
        ):
            blob[key] = list(blob[key])
        return blob


@dataclass
class ConceptCatalogV3:
    schema_version: str
    corpus_root: str
    concept_count: int
    stub_count: int
    concepts: dict[str, ConceptCatalogEntryV3]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "corpus_root": self.corpus_root,
            "concept_count": self.concept_count,
            "stub_count": self.stub_count,
            "concepts": {
                concept_id: entry.to_dict()
                for concept_id, entry in sorted(self.concepts.items())
            },
        }


@dataclass
class ReverseIndexes:
    mission_ids_to_concepts: dict[str, list[str]] = field(default_factory=dict)
    confusable_neighbors: dict[str, list[str]] = field(default_factory=dict)
    aliases_to_concept: dict[str, list[str]] = field(default_factory=dict)
    symptom_to_concepts: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class UnresolvedRefs:
    """Cross-doc references that name a concept_id not present in the
    catalog (neither as a v3 entry nor a stub)."""
    confusable_with: list[dict[str, str]] = field(default_factory=list)
    prerequisites: list[dict[str, str]] = field(default_factory=list)
    next_docs: list[dict[str, str]] = field(default_factory=list)
    mission_ids: list[dict[str, str]] = field(default_factory=list)

    def total(self) -> int:
        return sum(len(getattr(self, f.name)) for f in self.__dataclass_fields__.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total(),
            "confusable_with": list(self.confusable_with),
            "prerequisites": list(self.prerequisites),
            "next_docs": list(self.next_docs),
            "mission_ids": list(self.mission_ids),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _coerce_int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _relative_path(path: Path, corpus_root: Path) -> str:
    try:
        return str(path.relative_to(corpus_root))
    except ValueError:
        return str(path)


def _infer_stub_concept_id(path: Path, corpus_root: Path) -> str | None:
    """Pre-v2 docs without frontmatter — derive a placeholder concept_id
    from ``<category>/<slug>`` so cross-doc references can still resolve.
    Returns None if the path is not under ``contents/<category>/<slug>.md``.
    """
    try:
        rel = path.relative_to(corpus_root)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2:
        return None
    category = parts[0]
    slug = path.stem
    return f"{category}/{slug}"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_concept_catalog_v3(corpus_root: Path) -> ConceptCatalogV3:
    """Walk the corpus and emit a v3 catalog. v3 docs become full entries;
    pre-v2 docs become stubs (``has_frontmatter=False``)."""
    concepts: dict[str, ConceptCatalogEntryV3] = {}
    stub_count = 0

    for path in sorted(corpus_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        rel_path = _relative_path(path, corpus_root)

        if fm and str(fm.get("schema_version")) == "3":
            concept_id = str(fm.get("concept_id") or "").strip()
            if not concept_id:
                continue
            entry = ConceptCatalogEntryV3(
                concept_id=concept_id,
                doc_path=rel_path,
                has_frontmatter=True,
                canonical=bool(fm.get("canonical", False)),
                category=fm.get("category") if isinstance(fm.get("category"), str) else None,
                doc_role=fm.get("doc_role") if isinstance(fm.get("doc_role"), str) else None,
                level=fm.get("level") if isinstance(fm.get("level"), str) else None,
                language=fm.get("language") if isinstance(fm.get("language"), str) else None,
                source_priority=_coerce_int_or_none(fm.get("source_priority")),
                aliases=_as_string_list(fm.get("aliases")),
                expected_queries=_as_string_list(fm.get("expected_queries")),
                symptoms=_as_string_list(fm.get("symptoms")),
                intents=_as_string_list(fm.get("intents")),
                mission_ids=_as_string_list(fm.get("mission_ids")),
                review_feedback_tags=_as_string_list(fm.get("review_feedback_tags")),
                prerequisites=_as_string_list(fm.get("prerequisites")),
                next_docs=_as_string_list(fm.get("next_docs")),
                confusable_with=_as_string_list(fm.get("confusable_with")),
                forbidden_neighbors=_as_string_list(fm.get("forbidden_neighbors")),
                linked_paths=_as_string_list(fm.get("linked_paths")),
            )
            # Last v3 doc wins on collision (lint already enforces uniqueness).
            concepts[concept_id] = entry
        else:
            # Stub for pre-v2 / no-frontmatter / v2 docs (so that v3
            # confusable_with refs that point at unmigrated docs don't
            # show as dangling). v2 docs ALSO get stubs because the v2
            # builder owns its own catalog format; v3 just needs presence.
            stub_id = _infer_stub_concept_id(path, corpus_root)
            if stub_id is None:
                continue
            # Don't overwrite a real v3 entry with a stub.
            if stub_id in concepts and concepts[stub_id].has_frontmatter:
                continue
            concepts[stub_id] = ConceptCatalogEntryV3(
                concept_id=stub_id,
                doc_path=rel_path,
                has_frontmatter=False,
            )
            stub_count += 1

    return ConceptCatalogV3(
        schema_version="3",
        corpus_root=str(corpus_root),
        concept_count=sum(1 for e in concepts.values() if e.has_frontmatter),
        stub_count=stub_count,
        concepts=concepts,
    )


# ---------------------------------------------------------------------------
# Reverse index emitter
# ---------------------------------------------------------------------------

def build_reverse_indexes(catalog: ConceptCatalogV3) -> ReverseIndexes:
    """Build the four reverse indexes the R3 retrievers consume.

    Stub entries (``has_frontmatter=False``) contribute no aliases / symptoms /
    mission_ids — they only act as targets for cross-doc reference resolution.
    """
    rev = ReverseIndexes()
    for concept_id, entry in catalog.concepts.items():
        if not entry.has_frontmatter:
            continue
        for mid in entry.mission_ids:
            rev.mission_ids_to_concepts.setdefault(mid, []).append(concept_id)
        for cw in entry.confusable_with:
            # Reverse: cw is named as a confusable BY this concept. So the
            # neighbor view at cw includes concept_id.
            rev.confusable_neighbors.setdefault(cw, []).append(concept_id)
        for alias in entry.aliases:
            normalized = alias.strip().casefold()
            if normalized:
                rev.aliases_to_concept.setdefault(normalized, []).append(concept_id)
        for symptom in entry.symptoms:
            normalized = symptom.strip().casefold()
            if normalized:
                rev.symptom_to_concepts.setdefault(normalized, []).append(concept_id)

    # Sort every list deterministically for stable JSON output.
    for index in (
        rev.mission_ids_to_concepts,
        rev.confusable_neighbors,
        rev.aliases_to_concept,
        rev.symptom_to_concepts,
    ):
        for key, values in index.items():
            index[key] = sorted(set(values))
    return rev


# ---------------------------------------------------------------------------
# Cross-doc reference resolver
# ---------------------------------------------------------------------------

def resolve_cross_refs(catalog: ConceptCatalogV3) -> UnresolvedRefs:
    """Validate that every cross-doc concept_id reference points at an
    entry (or stub) actually present in the catalog. mission_ids point at
    a mission_id, not a concept_id — they have their own existence rule
    (mission_ids are *expected* to be opaque labels referenced by multiple
    docs, so cross-validation here only checks that *at least one*
    concept claims the mission_id).
    """
    unresolved = UnresolvedRefs()
    known_concepts = set(catalog.concepts.keys())
    known_missions: set[str] = set()
    for entry in catalog.concepts.values():
        for mid in entry.mission_ids:
            known_missions.add(mid)

    for concept_id, entry in catalog.concepts.items():
        if not entry.has_frontmatter:
            continue
        # confusable_with / prerequisites / next_docs all reference concept_ids
        for ref in entry.confusable_with:
            if ref not in known_concepts:
                unresolved.confusable_with.append(
                    {"source": concept_id, "ref": ref, "doc_path": entry.doc_path}
                )
        for ref in entry.prerequisites:
            if ref not in known_concepts:
                unresolved.prerequisites.append(
                    {"source": concept_id, "ref": ref, "doc_path": entry.doc_path}
                )
        for ref in entry.next_docs:
            if ref not in known_concepts:
                unresolved.next_docs.append(
                    {"source": concept_id, "ref": ref, "doc_path": entry.doc_path}
                )
    # mission_ids: each is its own namespace; we treat all referenced
    # mission_ids as known (they're defined-by-use during Pilot phase).
    # This will tighten in Phase 4.6 when the missions catalog ships.
    return unresolved


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_concept_catalog_v3(
    catalog: ConceptCatalogV3,
    out_dir: Path,
    *,
    reverse_indexes: ReverseIndexes | None = None,
    unresolved: UnresolvedRefs | None = None,
) -> dict[str, Path]:
    """Write the catalog + reverse indexes + unresolved diagnostic.

    Returns a dict ``{name: path}`` so callers can verify outputs.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    catalog_path = out_dir / "concepts.v3.json"
    catalog_path.write_text(
        json.dumps(catalog.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    written["catalog"] = catalog_path

    if reverse_indexes is not None:
        for name, payload in (
            ("mission_ids_to_concepts", reverse_indexes.mission_ids_to_concepts),
            ("confusable_neighbors", reverse_indexes.confusable_neighbors),
            ("aliases_to_concept", reverse_indexes.aliases_to_concept),
            ("symptom_to_concepts", reverse_indexes.symptom_to_concepts),
        ):
            target = out_dir / f"{name}.json"
            target.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            written[name] = target

    if unresolved is not None:
        target = out_dir / "unresolved_refs.json"
        target.write_text(
            json.dumps(unresolved.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        written["unresolved_refs"] = target

    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Catalog output directory (e.g. knowledge/cs/catalog).",
    )
    parser.add_argument(
        "--no-reverse",
        action="store_true",
        help="Skip reverse index emission (catalog only).",
    )
    parser.add_argument(
        "--no-resolve",
        action="store_true",
        help="Skip cross-doc reference resolution.",
    )
    parser.add_argument(
        "--strict-refs",
        action="store_true",
        help="Exit non-zero when unresolved cross-doc references are found.",
    )
    args = parser.parse_args(argv)

    catalog = build_concept_catalog_v3(args.corpus_root)
    reverse = None if args.no_reverse else build_reverse_indexes(catalog)
    unresolved = None if args.no_resolve else resolve_cross_refs(catalog)
    written = write_concept_catalog_v3(
        catalog, args.out_dir,
        reverse_indexes=reverse, unresolved=unresolved,
    )

    print(
        f"[concept-catalog-v3] {catalog.concept_count} v3 concepts, "
        f"{catalog.stub_count} pre-v2 stubs"
    )
    if reverse is not None:
        print(
            f"  reverse indexes: "
            f"missions={len(reverse.mission_ids_to_concepts)} | "
            f"confusables={len(reverse.confusable_neighbors)} | "
            f"aliases={len(reverse.aliases_to_concept)} | "
            f"symptoms={len(reverse.symptom_to_concepts)}"
        )
    if unresolved is not None:
        total = unresolved.total()
        print(f"  unresolved cross-refs: {total}")
        if total > 0:
            print(
                f"    confusable_with={len(unresolved.confusable_with)} | "
                f"prerequisites={len(unresolved.prerequisites)} | "
                f"next_docs={len(unresolved.next_docs)} | "
                f"mission_ids={len(unresolved.mission_ids)}"
            )
    for name, path in written.items():
        print(f"  -> {name}: {path}")
    if args.strict_refs and unresolved is not None and unresolved.total() > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
