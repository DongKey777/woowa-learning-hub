"""Augment `knowledge/cs/concept-catalog.json` with retrieval-anchor aliases.

Strategy (deterministic — committed output, no ML at runtime):
  1. Load the existing catalog as the base of truth.
  2. Walk `knowledge/cs/contents/spring/*.md` and harvest
     `retrieval-anchor-keywords:` lines.
  3. For each (anchor, concept) pair where the anchor casefold-substring
     matches the concept's name/korean/aliases, add the anchor to the
     concept's alias list (deduped, sorted). This keeps the file
     deterministic — re-running with the same corpus yields the same diff
     or no diff at all.
  4. Write back with sorted keys + a refreshed `generated_at`.

Run with `python3 scripts/learning/build_concept_catalog.py [--check]`.
The `--check` flag exits non-zero when running would change the file
(useful for CI). The aliases discovered here feed `extract_concept_ids`
during event recording.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "knowledge" / "cs" / "concept-catalog.json"
SPRING_DOCS_DIR = ROOT / "knowledge" / "cs" / "contents" / "spring"

ANCHOR_RE = re.compile(
    r"retrieval[-_]anchor[-_]keywords?\s*[:=]\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _collect_anchor_keywords(docs_dir: Path) -> list[str]:
    if not docs_dir.exists():
        return []
    found: set[str] = set()
    for path in sorted(docs_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in ANCHOR_RE.finditer(text):
            raw = match.group(1).strip().strip("[]")
            for piece in re.split(r"[,;\|]", raw):
                cleaned = piece.strip().strip("\"'")
                if 2 <= len(cleaned) <= 60:
                    found.add(cleaned)
    return sorted(found)


def _augment_aliases(catalog: dict, anchors: list[str]) -> dict:
    """Return a new catalog with anchor aliases merged into matching concepts.

    Matching is intentionally tight: an anchor is added iff it equals
    (casefold) the concept's name, korean translation, or one of its
    existing aliases. Loose substring matching produced thousands of noisy
    aliases and made the committed file unreadable. If you want fuzzy
    enrichment, add the anchor explicitly to the seed catalog instead.
    """
    out = json.loads(json.dumps(catalog, ensure_ascii=False))
    for concept_id, entry in (out.get("concepts") or {}).items():
        existing = list(entry.get("aliases") or [])
        existing_cf = {a.casefold() for a in existing}
        existing_cf.add((entry.get("name") or "").casefold())
        existing_cf.add((entry.get("korean") or "").casefold())
        existing_cf.discard("")
        for anchor in anchors:
            cf = anchor.casefold()
            if cf in existing_cf and not any(a.casefold() == cf for a in existing):
                existing.append(anchor)
                existing_cf.add(cf)
        seen_cf: set[str] = set()
        deduped: list[str] = []
        for alias in sorted(existing, key=str.casefold):
            cf = alias.casefold()
            if cf in seen_cf:
                continue
            seen_cf.add(cf)
            deduped.append(alias)
        entry["aliases"] = deduped
    out["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out["generator"] = "scripts/learning/build_concept_catalog.py"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild knowledge/cs/concept-catalog.json")
    parser.add_argument(
        "--check", action="store_true",
        help="Exit non-zero if running would change the file."
    )
    args = parser.parse_args()

    catalog = _load_catalog()
    anchors = _collect_anchor_keywords(SPRING_DOCS_DIR)
    augmented = _augment_aliases(catalog, anchors)

    # `generated_at` always changes — strip it for diff purposes.
    def _stable(payload: dict) -> str:
        copy = dict(payload)
        copy.pop("generated_at", None)
        copy.pop("generator", None)
        return json.dumps(copy, ensure_ascii=False, indent=2, sort_keys=True)

    same = _stable(catalog) == _stable(augmented)

    if args.check:
        if same:
            print("concept-catalog.json: up to date")
            return 0
        print("concept-catalog.json: would change", file=sys.stderr)
        return 1

    if same:
        print("concept-catalog.json: no changes (already up to date)")
        return 0
    CATALOG_PATH.write_text(
        json.dumps(augmented, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"concept-catalog.json: rewrote with {len(anchors)} anchor candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
