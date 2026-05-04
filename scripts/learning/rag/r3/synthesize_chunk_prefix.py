"""Author the v3 ``contextual_chunk_prefix`` for a single doc.

Companion to ``create_v3_frontmatter.py``. ``contextual_chunk_prefix``
in v3 is a **doc-level** YAML scalar (verified against
``scripts/learning/rag/corpus_loader.py:110,482``); the corpus loader
attaches it to every chunk emitted from the doc, and the indexer
prepends it to the embedded text. There is no separate per-chunk
prefix in this implementation.

The prefix is 50-100 tokens of Korean prose and serves two purposes:

  1. orient the dense encoder — explicit doc intent + audience signal
     that lets BGE-M3 latch onto the topic even when the body is
     terse;

  2. bridge learner paraphrase to canonical vocabulary — listing 4-6
     surface phrases (e.g. "동시 변경 충돌 방지", "락이 뭐야") that
     learners would actually type but that don't appear verbatim in
     the body.

Sample (from ``knowledge/cs/contents/database/lock-basics.md``)::

    contextual_chunk_prefix: |
      이 문서는 데이터베이스 학습자가 여러 사용자가 같은 데이터를
      동시에 바꾸려 할 때 충돌을 어떻게 막는지, 동시성 제어 메커니즘
      으로서 lock이 무엇이고 왜 필요한지 처음 잡는 primer다. 동시
      변경 충돌 방지, 동시성 충돌, 같은 데이터 동시에 수정, 락이
      뭐야 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.

This module is a **pure helper** — it never invokes any LLM. It
exposes:

  * ``build_authoring_prompt(file_path)`` — returns the Korean prompt
    that a codex worker (or a manual AI session) must run to author
    the prefix. The prompt is deterministic given the file content.

  * ``embed_prefix(file_path, prefix_text)`` — writes the authored
    prefix into the doc's existing v3 frontmatter, preserving field
    order via the canonical ``V3_FIELD_ORDER`` from
    ``migrate_frontmatter_v3``.

  * CLI mode that runs both: prints the prompt for one or more docs
    and, with ``--prefix-file path``, embeds an already-authored
    prefix.

The orchestrator's migration_v3 fleet uses this module:
  - ``migration-v3-<category>-prefix`` workers run codex-exec against
    the authoring prompt and pipe the output through ``embed_prefix``.
  - Pilot v3 docs are skipped via the
    ``config/migration_v3/locked_pilot_paths.json`` lock.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required for synthesize_chunk_prefix"
    ) from exc

from scripts.learning.rag.r3.migrate_frontmatter_v3 import (
    V3_FIELD_ORDER,
    serialize_v3_frontmatter,
)


# ---------------------------------------------------------------------------
# Doc parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_BLOCK_RE = re.compile(
    r"\A(---\s*\n)(.*?)(\n---\s*\n)", re.DOTALL
)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_ONE_LINE_SUMMARY_RE = re.compile(
    r"^>\s*한\s*줄\s*요약\s*:\s*(.+?)\s*$", re.MULTILINE
)
_H2_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class DocContext:
    """Structured doc context used to compose the authoring prompt."""

    file_path: Path
    title: str
    one_line_summary: str
    doc_role: str
    level: str
    category: str
    aliases: list[str]
    h2_headings: list[str]
    body_excerpt: str  # first ~600 chars of body

    def to_prompt_block(self) -> str:
        bullet_aliases = ", ".join(self.aliases) if self.aliases else "(none)"
        h2_block = "\n".join(f"- {h}" for h in self.h2_headings) or "(none)"
        return (
            f"파일: {self.file_path.as_posix()}\n"
            f"제목: {self.title}\n"
            f"카테고리: {self.category}\n"
            f"doc_role: {self.doc_role}\n"
            f"level: {self.level}\n"
            f"한 줄 요약: {self.one_line_summary}\n"
            f"aliases: {bullet_aliases}\n"
            f"본문 H2 섹션:\n{h2_block}\n"
            f"본문 도입 발췌:\n{self.body_excerpt}\n"
        )


def parse_doc(file_path: Path) -> DocContext:
    text = file_path.read_text(encoding="utf-8")
    fm: dict = {}
    body = text
    block = _FRONTMATTER_BLOCK_RE.match(text)
    if block:
        fm = yaml.safe_load(block.group(2)) or {}
        body = text[block.end():]

    title_match = _H1_RE.search(body)
    title = (title_match.group(1).strip() if title_match
             else fm.get("title") or file_path.stem)

    summary_match = _ONE_LINE_SUMMARY_RE.search(body)
    one_line = (
        summary_match.group(1).strip() if summary_match else ""
    )

    h2 = [h.strip() for h in _H2_HEADING_RE.findall(body)]

    aliases = fm.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = []

    body_excerpt = body.strip()
    # Drop the H1 line + summary block from the excerpt so the prompt
    # gets *body* signal, not header repetition.
    if title_match:
        body_excerpt = body_excerpt[title_match.end():].lstrip()
    if summary_match:
        body_excerpt = body_excerpt.replace(summary_match.group(0), "", 1)
    body_excerpt = body_excerpt.strip()[:600]

    return DocContext(
        file_path=file_path,
        title=str(title),
        one_line_summary=one_line,
        doc_role=str(fm.get("doc_role") or "primer"),
        level=str(fm.get("level") or "intermediate"),
        category=str(fm.get("category")
                     or file_path.parent.name),
        aliases=[str(a) for a in aliases],
        h2_headings=h2,
        body_excerpt=body_excerpt,
    )


# ---------------------------------------------------------------------------
# Authoring prompt
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """\
다음 문서의 v3 contextual_chunk_prefix를 작성해라. 이 prefix는
indexer가 모든 chunk에 prepend해서 BGE-M3 dense embedding이 사용한다.

## 작성 규칙
1. 한국어로 작성. 영어 단어는 corpus 어휘일 때만 (예: lock, primary,
   read-after-write 같은 기술 용어는 영어 OK).
2. 50-100 토큰 (한국어 약 30-60글자 X 2~3 문장).
3. 첫 문장: 이 문서가 누구에게 / 무엇을 / 왜 필요한가를 doc_role 톤
   에 맞춰 한 문장으로. (primer = "처음 잡는다", deep_dive =
   "깊이 잡는다", playbook = "전략으로 막는다", chooser = "결정한다",
   bridge = "연결한다", drill = "확인 질문으로 굳힌다",
   symptom_router = "증상 → 원인으로 이어진다",
   mission_bridge = "Woowa 미션 ↔ CS concept를 잇는다")
4. 둘째 문장: 학습자가 자연어로 검색할 때 칠 paraphrase 표현 4-6개를
   "..., ..., ... 같은 자연어 paraphrase가 본 문서의 X에 매핑된다"
   형식으로 명시. paraphrase는 alias와 다른 표현이어야 한다 (alias는
   별도 indexed; prefix는 dense semantic anchor).
5. 본문에 없는 사실 추가 금지. 추측 금지.

## 출력 형식
프리픽스 본문 텍스트 ONE_STRING_ONLY. 따옴표나 마크다운 ❌. 코드 펜스
❌. 헤더 ❌. 줄바꿈은 자연스러운 문장 경계에서만.

## 문서 컨텍스트
{doc_block}
"""


def build_authoring_prompt(file_path: Path) -> str:
    """Return the Korean codex-exec prompt for authoring this doc's prefix."""
    ctx = parse_doc(file_path)
    return PROMPT_TEMPLATE.format(doc_block=ctx.to_prompt_block())


# ---------------------------------------------------------------------------
# Embedding the authored prefix back into frontmatter
# ---------------------------------------------------------------------------

class PrefixEmbedError(RuntimeError):
    """Raised when embedding fails (no frontmatter, invalid YAML, etc.)."""


def embed_prefix(file_path: Path, prefix_text: str) -> None:
    """Write ``prefix_text`` into the doc's frontmatter at
    ``contextual_chunk_prefix``.

    Preconditions:
      - file has a v3 frontmatter block (raises otherwise)
      - prefix_text is non-empty after stripping (raises otherwise)

    The frontmatter is re-rendered in canonical V3_FIELD_ORDER so
    diffs are reviewable.
    """
    cleaned = prefix_text.strip()
    if not cleaned:
        raise PrefixEmbedError("prefix_text is empty after stripping")

    text = file_path.read_text(encoding="utf-8")
    block = _FRONTMATTER_BLOCK_RE.match(text)
    if not block:
        raise PrefixEmbedError(
            f"{file_path}: no frontmatter — run create_v3_frontmatter first"
        )
    open_marker, body_yaml, close_marker = block.groups()
    rest = text[block.end():]
    fm = yaml.safe_load(body_yaml) or {}
    if not isinstance(fm, dict):
        raise PrefixEmbedError(
            f"{file_path}: frontmatter is not a mapping ({type(fm).__name__})"
        )
    if str(fm.get("schema_version")) != "3":
        raise PrefixEmbedError(
            f"{file_path}: schema_version != 3; refusing to write prefix"
        )

    fm["contextual_chunk_prefix"] = cleaned
    new_yaml = serialize_v3_frontmatter(fm).rstrip("\n")
    new_text = f"{open_marker}{new_yaml}{close_marker}{rest}"
    file_path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _discover(roots: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".md":
            out.append(root)
        elif root.is_dir():
            out.extend(sorted(root.rglob("*.md")))
    seen: set[Path] = set()
    deduped: list[Path] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="synthesize_chunk_prefix",
        description="Build the codex-exec prompt for a doc's "
                    "contextual_chunk_prefix, or embed an authored "
                    "prefix back into the doc's frontmatter.",
    )
    parser.add_argument(
        "--paths", nargs="+", required=True, type=Path,
        help="One or more .md files or directories to process.",
    )
    parser.add_argument(
        "--mode", choices=("prompt", "embed"), default="prompt",
        help="`prompt` prints the codex authoring prompt for each "
             "doc; `embed` writes a previously authored prefix back "
             "into the doc (paired with --prefix-file).",
    )
    parser.add_argument(
        "--prefix-file", type=Path,
        help="Path to a JSON file mapping {doc_path: prefix_text}, "
             "consumed in --mode=embed. Doc paths are repo-relative.",
    )
    parser.add_argument(
        "--lock-file",
        type=Path,
        default=Path("config/migration_v3/locked_pilot_paths.json"),
        help="Lock file listing v3 docs that must not be touched.",
    )
    args = parser.parse_args(argv)

    locked: set[str] = set()
    if args.lock_file.exists():
        payload = json.loads(args.lock_file.read_text(encoding="utf-8"))
        locked = {str(p) for p in payload.get("locked_paths", [])}

    files = _discover(args.paths)
    if not files:
        print("no markdown files found", file=sys.stderr)
        return 1

    if args.mode == "prompt":
        for f in files:
            if f.as_posix() in locked:
                print(f"# [lock] {f.as_posix()} — Pilot v3 (skip)\n")
                continue
            try:
                prompt = build_authoring_prompt(f)
            except Exception as exc:  # noqa: BLE001
                print(f"# [error] {f}: {exc}\n", file=sys.stderr)
                continue
            print(f"# === {f.as_posix()} ===")
            print(prompt)
            print()
        return 0

    # embed mode
    if not args.prefix_file or not args.prefix_file.exists():
        print("--mode=embed requires --prefix-file pointing to a "
              "{doc_path: prefix_text} json", file=sys.stderr)
        return 2
    mapping = json.loads(args.prefix_file.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        print("--prefix-file must contain a JSON object", file=sys.stderr)
        return 2

    failures = 0
    for f in files:
        rel = f.as_posix()
        if rel in locked:
            print(f"  [lock] {rel} — Pilot v3 (skip)")
            continue
        prefix = mapping.get(rel)
        if not prefix:
            print(f"  [skip] {rel}: no prefix in mapping")
            continue
        try:
            embed_prefix(f, prefix)
            print(f"  [embed] {rel}")
        except PrefixEmbedError as exc:
            print(f"  [fail] {rel}: {exc}", file=sys.stderr)
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
