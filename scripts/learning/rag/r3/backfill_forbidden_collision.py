"""Backfill cycle-1 forbidden_neighbors ↔ confusable_with collisions.

Cycle 1 cohort_eval (commit 5c64362) regressed -7.5pp on confusable_pairs
because fleet workers populated forbidden_neighbors with the canonical
primer they themselves named in confusable_with. corpus_lint --strict-v3
(commit ca8ddf8) catches the collision via slug containment.

This module removes the colliding entries from each affected file's
forbidden_neighbors list — direct text manipulation on the frontmatter
block, avoiding YAML round-trip drift. The body bytes are not touched.

Usage::

    python -m scripts.learning.rag.r3.backfill_forbidden_collision \\
        --report reports/rag_eval/cycle1_collision_dry_run.json \\
        --include safe unknown_target \\
        --dry-run

    python -m scripts.learning.rag.r3.backfill_forbidden_collision \\
        --report reports/rag_eval/cycle1_collision_dry_run.json \\
        --include safe unknown_target \\
        --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _split_frontmatter(text: str) -> tuple[str, str, str] | None:
    """Return (leading_marker, frontmatter_block, body_with_trailing_marker_and_after).

    Layout we expect::

        ---\\n
        <yaml fields>\\n
        ---\\n
        <body>

    The body half includes the trailing ``---`` marker and everything
    after, so the caller can reassemble the file by simple
    concatenation (frontmatter edits stay isolated).
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    return ("---\n", text[4:end], text[end:])


def remove_forbidden_entry(file_text: str, entry_to_remove: str) -> tuple[str, bool]:
    """Remove a single ``forbidden_neighbors`` list item from the
    frontmatter block.

    Returns ``(new_text, removed)`` where ``removed`` is True iff a
    matching line was found and dropped. We do *not* touch any other
    field, indentation, ordering, or whitespace — only the matching
    list-item line is dropped.

    The list-item line shape we expect (matching what the v3 prompts
    write today)::

        forbidden_neighbors:
          - contents/category/slug.md
          - contents/category/slug2.md

    or::

        forbidden_neighbors:
        - contents/category/slug.md

    Both indent variants are accepted.
    """
    parts = _split_frontmatter(file_text)
    if parts is None:
        return file_text, False
    leading, fm, body = parts

    lines = fm.split("\n")
    out_lines: list[str] = []
    in_forbidden = False
    removed = False
    for line in lines:
        # Detect entry into forbidden_neighbors block
        stripped = line.strip()
        if line.startswith("forbidden_neighbors:"):
            in_forbidden = True
            out_lines.append(line)
            continue
        # Detect exit: a non-indented line (next field) that is not a list item
        if in_forbidden:
            if not (line.startswith(" ") or line.startswith("\t") or line.startswith("-")):
                in_forbidden = False
            else:
                # Inside the forbidden_neighbors list. Match list items.
                # Strip leading "- " or "  - "
                for prefix in ("- ", "  - ", "    - "):
                    if line.startswith(prefix):
                        candidate = line[len(prefix):].strip().strip("'\"")
                        if candidate == entry_to_remove:
                            removed = True
                            break
                else:
                    candidate = None
                if removed and candidate is not None:
                    # Skip this line (drop it from output)
                    continue
        out_lines.append(line)
    if not removed:
        return file_text, False
    new_fm = "\n".join(out_lines)
    return f"{leading}{new_fm}{body}", True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--report", type=Path, required=True,
        help="dry-run JSON from cycle1 collision analysis",
    )
    parser.add_argument(
        "--include", nargs="+",
        choices=["safe", "ambiguous", "unknown_target"],
        default=["safe", "unknown_target"],
        help="Which collision categories to fix.",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually mutate files. Default is dry-run.",
    )
    parser.add_argument(
        "--repo-root", type=Path,
        default=Path(__file__).resolve().parents[4],
    )
    args = parser.parse_args(argv)

    report = json.loads(args.report.read_text(encoding="utf-8"))
    bucket_map = {
        "safe": report.get("safe_cases", []),
        "ambiguous": report.get("ambiguous_cases", []),
        "unknown_target": report.get("unknown_target_cases", []),
    }
    cases: list[dict] = []
    for name in args.include:
        cases.extend(bucket_map.get(name, []))

    print(f"[backfill] {'APPLY' if args.apply else 'DRY-RUN'} mode")
    print(f"[backfill] include buckets: {args.include}")
    print(f"[backfill] cases to process: {len(cases)}")

    by_file: dict[Path, list[str]] = defaultdict(list)
    for c in cases:
        full = args.repo_root / c["src_path"]
        by_file[full].append(c["forbidden_target_path"])
    print(f"[backfill] unique files affected: {len(by_file)}")

    n_files_changed = 0
    n_entries_removed = 0
    n_entries_missed = 0
    for path, entries in sorted(by_file.items()):
        if not path.exists():
            print(f"  [missing] {path}")
            continue
        text = _read_file(path)
        original = text
        local_removed = 0
        local_missed = 0
        for entry in entries:
            text, removed = remove_forbidden_entry(text, entry)
            if removed:
                local_removed += 1
            else:
                local_missed += 1
        if local_removed:
            n_files_changed += 1
            n_entries_removed += local_removed
            n_entries_missed += local_missed
            rel = path.relative_to(args.repo_root)
            print(f"  [{'WRITE' if args.apply else 'DIFF '}] {rel}: -{local_removed} entries"
                  + (f" ({local_missed} not found)" if local_missed else ""))
            if args.apply:
                _write_file(path, text)
        elif local_missed:
            n_entries_missed += local_missed

    print(f"\n[backfill] files changed:    {n_files_changed}")
    print(f"[backfill] entries removed:  {n_entries_removed}")
    print(f"[backfill] entries not found: {n_entries_missed}")
    if not args.apply:
        print(f"[backfill] DRY-RUN — no files written. Re-run with --apply.")
    return 0 if n_entries_missed == 0 else (0 if args.apply else 0)


if __name__ == "__main__":
    sys.exit(main())
