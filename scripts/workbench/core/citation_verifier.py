"""Artifact-bounded citation invariant checks.

The verifier only inspects structured artifacts already produced by the
pipeline. It does not parse learner-facing response text.
"""

from __future__ import annotations

from typing import Any


def _path_values(items: list[Any]) -> list[str]:
    paths: list[str] = []
    for item in items:
        if isinstance(item, dict):
            value = item.get("path")
        else:
            value = item
        if value:
            paths.append(str(value))
    return paths


def _dedupe_preserving_order(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        out.append(path)
    return out


def verify_citation_invariants(
    cs_block: dict[str, Any],
    verifier_hits: list[dict[str, Any]],
    citation_paths: list[str],
) -> dict[str, Any]:
    """Check that cs_block sources are grounded by retrieval artifacts."""
    hit_paths = _path_values([hit for hit in verifier_hits if isinstance(hit, dict)])
    allowed = set(hit_paths) | {str(path) for path in citation_paths if path}
    sources = _path_values(cs_block.get("sources") or [])
    ungrounded = _dedupe_preserving_order([
        path for path in sources if path and path not in allowed
    ])
    return {
        "ok": not ungrounded,
        "ungrounded_paths": ungrounded,
        "severity": "ok" if not ungrounded else "warn",
    }
