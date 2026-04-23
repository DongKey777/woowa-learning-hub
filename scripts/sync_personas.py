#!/usr/bin/env python3
"""Render persona body + per-host header → Claude / Codex / Gemini files.

Source of truth lives in ``docs/agent-personas/<persona>.body.md`` plus
per-host header fragments ``<persona>.header.{claude,codex,gemini}``. This
script concatenates ``header + body + GENERATED marker`` and writes each
host's expected file path. Run with ``--check`` in CI to fail on drift,
``--write`` to regenerate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "docs" / "agent-personas"

GENERATED_MARKER = "<!-- GENERATED — DO NOT EDIT BY HAND. Source: docs/agent-personas/. Run scripts/sync_personas.py --write -->\n\n"

# (persona-name, {host: relative_output_path})
PERSONAS: list[tuple[str, dict[str, str]]] = [
    (
        "mission-coach",
        {
            "claude": ".claude/agents/mission-coach.md",
            "codex": "skills/woowa-coach-run/SKILL.md",
            "gemini": "gemini-skills/mission-coach.md",
        },
    ),
    (
        "peer-pr-analyst",
        {
            "claude": ".claude/agents/peer-pr-analyst.md",
            "codex": "skills/woowa-peer-analysis/SKILL.md",
            "gemini": "gemini-skills/peer-analysis.md",
        },
    ),
    (
        "learning-memory-analyst",
        {
            "claude": ".claude/agents/learning-memory-analyst.md",
            "codex": "skills/woowa-learning-memory/SKILL.md",
            "gemini": "gemini-skills/learning-memory.md",
        },
    ),
]


def render(persona: str, host: str) -> str:
    body = (SOURCE_DIR / f"{persona}.body.md").read_text(encoding="utf-8")
    header = (SOURCE_DIR / f"{persona}.header.{host}").read_text(encoding="utf-8")
    return header + GENERATED_MARKER + body


def iter_targets() -> list[tuple[str, str, Path, str]]:
    out: list[tuple[str, str, Path, str]] = []
    for persona, hosts in PERSONAS:
        for host, rel in hosts.items():
            out.append((persona, host, ROOT / rel, render(persona, host)))
    return out


def cmd_check() -> int:
    drift: list[str] = []
    for persona, host, path, expected in iter_targets():
        if not path.exists():
            drift.append(f"missing: {path.relative_to(ROOT)} ({persona}/{host})")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            drift.append(f"drift: {path.relative_to(ROOT)} ({persona}/{host})")
    if drift:
        sys.stderr.write("persona sync drift detected:\n")
        for line in drift:
            sys.stderr.write(f"  - {line}\n")
        sys.stderr.write("Run: python3 scripts/sync_personas.py --write\n")
        return 1
    return 0


def cmd_write() -> int:
    for persona, host, path, expected in iter_targets():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({persona}/{host})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        return cmd_write()
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
