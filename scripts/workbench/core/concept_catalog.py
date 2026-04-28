"""Canonical concept catalog for the learner profile (v3).

Maps surface forms ("Bean", "spring bean", "@Component bean", "스프링 빈") to a
single canonical `concept_id` like `concept:spring/bean`. The catalog is a
committed JSON file (`knowledge/cs/concept-catalog.json`), so concept_id
extraction is deterministic — no ML inference at call time.

Auto-generation enriches the file from JUNIOR-BACKEND-ROADMAP.md and
retrieval-anchor metadata; manual curation lives alongside.

This module intentionally has no dependency on the per-PR
LEARNING_POINT_RULES catalog. The two scopes are separate by design — see
plan v3 §Concept Catalog. Cross-mapping happens via the
`learning_point_aliases` field of the catalog.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from .paths import ROOT


CATALOG_PATH = ROOT / "knowledge" / "cs" / "concept-catalog.json"
OVERRIDES_PATH = ROOT / "knowledge" / "cs" / "concept-catalog.overrides.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Read the canonical concept catalog.

    Returns an empty skeleton when the file is missing so callers
    can degrade gracefully (concept_ids will be []).
    """
    if not CATALOG_PATH.exists():
        return {
            "schema_version": "v1",
            "concepts": {},
            "stages": {},
            "learning_point_aliases": {},
        }
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if OVERRIDES_PATH.exists():
        overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        for concept_id, payload in (overrides.get("concepts") or {}).items():
            catalog.setdefault("concepts", {})[concept_id] = payload
        for stage_id, payload in (overrides.get("stages") or {}).items():
            catalog.setdefault("stages", {})[stage_id] = payload
        for lp_id, concept_id in (overrides.get("learning_point_aliases") or {}).items():
            catalog.setdefault("learning_point_aliases", {})[lp_id] = concept_id
    return catalog


def reset_cache() -> None:
    """Test hook — drop the lru_cache so a freshly written catalog is reread."""
    load_catalog.cache_clear()


def _ascii_pattern(token: str) -> re.Pattern:
    """Compile an ASCII-only word-boundary pattern. Same trick as the RAG
    router: Python `\\b` is unicode-aware so it matches inside Korean —
    we want explicit `[A-Za-z0-9_]` boundaries so `bean` matches `Bean이`
    via the trailing Korean particle but not inside `urban`."""
    return re.compile(
        rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])",
        re.IGNORECASE,
    )


def _alias_matches(prompt: str, alias: str) -> bool:
    if not alias:
        return False
    if all(ord(c) < 128 for c in alias):
        return bool(_ascii_pattern(alias).search(prompt))
    return alias.casefold() in prompt.casefold()


def extract_concept_ids(text: str | None, catalog: dict) -> list[str]:
    """Static alias matching only — deterministic, no ML.

    Scans `catalog["concepts"][*]["aliases"]` for hits and returns the
    canonical `concept_id` for each match. Result is sorted+deduped to keep
    event payloads stable across runs.
    """
    if not text:
        return []
    hits: set[str] = set()
    concepts = catalog.get("concepts") or {}
    for concept_id, entry in concepts.items():
        if any(_alias_matches(text, alias) for alias in (entry.get("aliases") or [])):
            hits.add(concept_id)
        if _alias_matches(text, entry.get("name") or ""):
            hits.add(concept_id)
        if _alias_matches(text, entry.get("korean") or ""):
            hits.add(concept_id)
    return sorted(hits)


_MODULE_RE = re.compile(r"(spring-[a-z\-]+?-\d+)")


def infer_module_from_path(path: str | None) -> str | None:
    """Pull the module dir from a file path under spring-learning-test.

    e.g. `missions/spring-learning-test/spring-core-1/initial/...` → `spring-core-1`.
    """
    if not path:
        return None
    match = _MODULE_RE.search(path)
    return match.group(1) if match else None


def infer_stage_from_module(module: str | None, catalog: dict) -> str | None:
    """Walk catalog.stages to find which stage owns the given module."""
    if not module:
        return None
    for stage_id, stage in (catalog.get("stages") or {}).items():
        if module in (stage.get("modules") or []):
            return stage_id
    return None


def concept_module_hint(concept_id: str, catalog: dict) -> str | None:
    """Return the catalog's module_hint for a concept (e.g. 'spring-core-1')."""
    entry = (catalog.get("concepts") or {}).get(concept_id) or {}
    return entry.get("module_hint")


def concept_stage(concept_id: str, catalog: dict) -> str | None:
    entry = (catalog.get("concepts") or {}).get(concept_id) or {}
    return entry.get("stage")


def lp_to_concept_id(learning_point_id: str | None, catalog: dict) -> str | None:
    """Cross-map a per-PR learning_point_id to a catalog concept_id."""
    if not learning_point_id:
        return None
    return (catalog.get("learning_point_aliases") or {}).get(learning_point_id)


def infer_concepts_from_test(
    test_class: str,
    test_method: str,
    module: str | None,
    catalog: dict,
) -> tuple[list[str], str]:
    """Best-effort concept attribution for a JUnit test result.

    Returns ``(concept_ids, source)`` where ``source`` is one of:
      - ``"strict"`` — direct alias hit on ``test_class.test_method``
      - ``"fallback"`` — no alias hit, matched via ``module_hint``
      - ``"none"`` — no alias hit and no module to fall back to
    """
    text_hits = extract_concept_ids(f"{test_class}.{test_method}", catalog)
    if text_hits:
        return text_hits, "strict"
    if not module:
        return [], "none"
    matches = [
        cid
        for cid, entry in (catalog.get("concepts") or {}).items()
        if entry.get("module_hint") == module
    ]
    return sorted(matches), ("fallback" if matches else "none")


def infer_concepts_from_path(
    file_path: str,
    module: str | None,
    catalog: dict,
) -> list[str]:
    """Best-effort concept attribution for a code file change.

    Strategy:
      1. Alias match against the file path's basename (catches things like
         `SpringBeanTest.java` → bean).
      2. Fall back to module-hint match.
    """
    basename = file_path.rsplit("/", 1)[-1] if file_path else ""
    text_hits = extract_concept_ids(basename, catalog)
    if text_hits:
        return text_hits
    if not module:
        return []
    matches = [
        cid
        for cid, entry in (catalog.get("concepts") or {}).items()
        if entry.get("module_hint") == module
    ]
    return sorted(matches)


def next_stage(catalog: dict, current_stage: str | None) -> str | None:
    """Return the next stage by `order`, or None if at the end."""
    stages = catalog.get("stages") or {}
    if not current_stage or current_stage not in stages:
        return None
    current_order = stages[current_stage].get("order", 0)
    candidates: Iterable[tuple[str, dict]] = stages.items()
    later = [
        (sid, payload) for sid, payload in candidates
        if (payload.get("order") or 0) > current_order
    ]
    if not later:
        return None
    later.sort(key=lambda pair: pair[1].get("order") or 0)
    return later[0][0]


def stage_first_module(catalog: dict, stage_id: str) -> str | None:
    """Return the first module of a stage in declared order."""
    stage = (catalog.get("stages") or {}).get(stage_id)
    if not stage:
        return None
    modules = stage.get("modules") or []
    return modules[0] if modules else None
