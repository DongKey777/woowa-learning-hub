"""Frontmatter migration: extract YAML frontmatter from existing CS doc
inline markers (plan §P5.3).

Deterministic regex extraction — **no LLM calls**. Run once over the
corpus to lift the in-body markers (`# H1`, `**난이도: 🟢 Beginner**`,
`> 한 줄 요약: ...`, `retrieval-anchor-keywords: ...`, `관련 문서: ...`)
into a YAML frontmatter block at the top of each file.

## Output frontmatter shape

```yaml
---
title: "Spring Bean and DI Basics"
concept_id: spring/bean-di-basics      # derived from path
difficulty: beginner | intermediate | advanced | unknown
summary: "한 줄 요약 본문..."           # may be null
retrieval_anchor_keywords: ["a", "b"]
related_docs:                           # extracted relative paths
  - "./bean-lifecycle.md"
audience: []                            # human curation slot
prereqs: []                             # human curation slot
learning_points: []                     # human curation slot
superseded_by: null                     # human curation slot
migrated_at: "2026-04-30T..."
migration_source: "auto_v1"
---
```

The four "human curation" slots are intentionally left empty so a
later pass (or learner-feedback-driven script) can populate them
without conflicting with this migration.

## Idempotency

Files that already contain a YAML frontmatter (lines start with
``---`` / ``---``) are **skipped**. Re-running the script on a
mostly-migrated corpus only touches new files. The ``--force`` flag
overrides existing frontmatter — useful only for full re-migrations
when the schema bumps.

## Modes

- ``--dry-run`` (default): print what would be written, no file
  changes.
- ``--apply``: rewrite files in place. Each rewrite is atomic
  (write to ``.tmp`` → rename) so a crash mid-migration leaves no
  half-written file.

## Tested in

``tests/unit/test_migrate_frontmatter.py``.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

DIFFICULTY_EMOJI_MAP = {
    "🟢": "beginner",
    "🟡": "intermediate",
    "🔴": "advanced",
}

# `**난이도: 🟢 Beginner**` or `**난이도: 🔴 Advanced**`
_DIFFICULTY_RE = re.compile(r"\*\*난이도:\s*([🟢🟡🔴])[^*]*\*\*")

# `# Title` (very first H1)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

# `> 한 줄 요약: 본문` (blockquote one-line summary)
_SUMMARY_RE = re.compile(r"^>\s*(?:\*\*)?한 줄 요약(?:\*\*)?[:：]\s*(.+?)\s*$", re.MULTILINE)

# `retrieval-anchor-keywords: a, b, c`
_ANCHOR_RE = re.compile(r"^retrieval-anchor-keywords:\s*(.+?)\s*$", re.MULTILINE)

# `관련 문서: [Title](./path.md), [...](./other.md)` or with bullet list
_RELATED_RE = re.compile(r"^\s*-?\s*관련 문서:\s*(.+?)\s*$", re.MULTILINE)
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

# Existing YAML frontmatter (open + close)
_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?\n)---\s*\n", re.DOTALL
)


def parse_difficulty(text: str) -> str:
    m = _DIFFICULTY_RE.search(text)
    if not m:
        return "unknown"
    return DIFFICULTY_EMOJI_MAP.get(m.group(1), "unknown")


def parse_title(text: str) -> str | None:
    m = _H1_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def parse_summary(text: str) -> str | None:
    m = _SUMMARY_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def parse_anchor_keywords(text: str) -> list[str]:
    m = _ANCHOR_RE.search(text)
    if not m:
        return []
    raw = m.group(1)
    return [k.strip() for k in raw.split(",") if k.strip()]


def parse_related_docs(text: str) -> list[str]:
    """Extract relative paths from 관련 문서 markdown links.

    Returns paths in the order they appear, de-duped while preserving
    first occurrence.
    """
    seen: set[str] = set()
    out: list[str] = []
    for m in _RELATED_RE.finditer(text):
        for link in _LINK_RE.finditer(m.group(1)):
            href = link.group(1).strip()
            if href and href not in seen:
                seen.add(href)
                out.append(href)
    return out


def has_frontmatter(text: str) -> bool:
    return bool(_FRONTMATTER_RE.match(text))


def derive_concept_id(path: Path, corpus_root: Path) -> str:
    """``knowledge/cs/contents/database/xa-2pc.md`` →
    ``database/xa-2pc``."""
    rel = path.relative_to(corpus_root)
    parts = list(rel.with_suffix("").parts)
    # drop a leading "contents" segment if present
    if parts and parts[0] == "contents":
        parts = parts[1:]
    return "/".join(parts)


# ---------------------------------------------------------------------------
# YAML emitter (no PyYAML dependency — keep deterministic)
# ---------------------------------------------------------------------------

def _yaml_escape_scalar(value: str) -> str:
    """Quote a string value for safe YAML emission.

    Use double quotes; escape ``"``, ``\\``, control chars. Korean
    characters pass through unchanged. Strings with newlines are
    flattened — frontmatter values are single-line by contract.
    """
    if value is None:
        return "null"
    s = str(value).replace("\n", " ")
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _yaml_string_list(items: Iterable[str]) -> str:
    """Render ``["a", "b"]`` as a YAML flow sequence."""
    parts = [_yaml_escape_scalar(x) for x in items]
    return "[" + ", ".join(parts) + "]"


def render_frontmatter(meta: dict) -> str:
    """Render ``meta`` as a YAML frontmatter block (with ``---``
    delimiters and trailing newline). Field order is fixed for
    deterministic diffs."""
    lines = ["---"]
    for key in (
        "title", "concept_id", "difficulty", "summary",
        "retrieval_anchor_keywords", "related_docs",
        "audience", "prereqs", "learning_points", "superseded_by",
        "migrated_at", "migration_source",
    ):
        if key not in meta:
            continue
        v = meta[key]
        if isinstance(v, list):
            lines.append(f"{key}: {_yaml_string_list(v)}")
        elif v is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {_yaml_escape_scalar(v)}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Migration plan + apply
# ---------------------------------------------------------------------------

def build_meta(
    *,
    text: str,
    path: Path,
    corpus_root: Path,
    now: datetime | None = None,
) -> dict:
    return {
        "title": parse_title(text),
        "concept_id": derive_concept_id(path, corpus_root),
        "difficulty": parse_difficulty(text),
        "summary": parse_summary(text),
        "retrieval_anchor_keywords": parse_anchor_keywords(text),
        "related_docs": parse_related_docs(text),
        "audience": [],
        "prereqs": [],
        "learning_points": [],
        "superseded_by": None,
        "migrated_at": (now or datetime.now(timezone.utc)).isoformat(),
        "migration_source": "auto_v1",
    }


def migrate_text(
    text: str,
    *,
    path: Path,
    corpus_root: Path,
    force: bool = False,
    now: datetime | None = None,
) -> tuple[str | None, str]:
    """Return ``(new_text, action)``.

    ``action`` ∈ ``{"skipped_existing", "migrated", "no_signals"}``.
    ``new_text`` is None when nothing changes.
    """
    if has_frontmatter(text) and not force:
        return None, "skipped_existing"

    meta = build_meta(text=text, path=path, corpus_root=corpus_root, now=now)
    body = text
    if has_frontmatter(text) and force:
        # Strip existing frontmatter before prepending the new one.
        m = _FRONTMATTER_RE.match(text)
        if m:
            body = text[m.end():]

    fm = render_frontmatter(meta)
    return fm + body, "migrated"


def find_markdown_files(corpus_root: Path) -> list[Path]:
    """Return all ``*.md`` files under ``corpus_root`` sorted for
    deterministic iteration."""
    return sorted(corpus_root.rglob("*.md"))


def atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically (tmp file → rename)."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(
        description="Migrate CS doc inline markers into YAML frontmatter."
    )
    parser.add_argument(
        "--corpus",
        default=str(repo_root / "knowledge" / "cs" / "contents"),
        help="Corpus content root.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files in place (default: dry-run).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing frontmatter (re-migration).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after N files (useful when previewing).",
    )
    args = parser.parse_args(argv)

    corpus_root = Path(args.corpus)
    if not corpus_root.exists():
        print(f"[migrate-frontmatter] corpus not found: {corpus_root}", file=sys.stderr)
        return 2

    files = find_markdown_files(corpus_root)
    if args.limit:
        files = files[: args.limit]

    counts = {"migrated": 0, "skipped_existing": 0, "no_signals": 0}
    for path in files:
        text = path.read_text(encoding="utf-8")
        new_text, action = migrate_text(
            text, path=path, corpus_root=corpus_root, force=args.force
        )
        counts[action] = counts.get(action, 0) + 1
        if action == "migrated" and new_text is not None:
            if args.apply:
                atomic_write(path, new_text)
                print(f"[migrate-frontmatter] migrated {path.relative_to(corpus_root)}")
            else:
                print(f"[migrate-frontmatter] would migrate {path.relative_to(corpus_root)}")

    print(
        "[migrate-frontmatter] summary "
        f"migrated={counts['migrated']} "
        f"skipped_existing={counts['skipped_existing']} "
        f"no_signals={counts.get('no_signals', 0)} "
        f"total={len(files)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
