"""Markdown corpus loader for knowledge/cs/.

Walks the corpus root, parses each markdown file into section chunks, and
yields dicts suitable for the indexer. Stdlib only — no ML deps here so
the loader is safe to import from CLI tools and tests.

Chunk strategy
--------------
- Split on level-2 (`##`) headings (most notes use these as top-level sections).
- If a level-2 section exceeds ``max_chars`` characters, further split on
  level-3 (`###`). If still too long, fall back to hard splits at paragraph
  boundaries every ``max_chars``.
- Skip empty sections and navigation-only blocks (ToC, `<details>`, etc.).
- Each chunk carries the file path, document title (first H1), category
  (path prefix under ``contents/``), section heading path, and body text.

Category detection
------------------
The CS corpus layout is::

    knowledge/cs/contents/<category>/...
    knowledge/cs/master-notes/...
    knowledge/cs/rag/...

Files under ``contents/<category>/...`` get that category. Other top-level
folders are labeled with the folder name itself (``master-notes``, ``rag``,
``JUNIOR-BACKEND-ROADMAP`` → ``_root``).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

DEFAULT_CORPUS_ROOT = Path("knowledge/cs")
CONTENTS_DIR = "contents"

MAX_CHARS_PER_CHUNK = 1600       # ≈ 400 tokens
MIN_CHARS_PER_CHUNK = 60         # below this we skip (pure nav fragments)

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
DETAILS_RE = re.compile(r"<details>.*?</details>", re.DOTALL | re.IGNORECASE)


@dataclass
class CorpusChunk:
    """One indexable unit of CS content."""

    doc_id: str             # sha1(path)[:16]
    chunk_id: str           # f"{doc_id}#{chunk_index}"
    path: str               # repo-relative, POSIX
    title: str              # document H1 (fallback: file stem)
    category: str           # e.g. "database"
    section_title: str      # e.g. "실전 시나리오"
    section_path: list[str] # ["H1 title", "H2 title", "H3 title"]
    body: str               # raw markdown body of the chunk
    char_len: int = 0
    anchors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "path": self.path,
            "title": self.title,
            "category": self.category,
            "section_title": self.section_title,
            "section_path": list(self.section_path),
            "body": self.body,
            "char_len": self.char_len,
            "anchors": list(self.anchors),
        }


def _category_for(relpath: Path) -> str:
    parts = relpath.parts
    if len(parts) >= 2 and parts[0] == CONTENTS_DIR:
        return parts[1]
    # File directly under corpus root (README, roadmaps, etc.) → _root.
    if len(parts) == 1:
        return "_root"
    if parts:
        return parts[0]
    return "_root"


def _doc_title(text: str, fallback: str) -> str:
    m = H1_RE.search(text)
    if m:
        return m.group(1).strip()
    return fallback


def _strip_navigation(text: str) -> str:
    return DETAILS_RE.sub("", text)


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text on H2 headings.

    Returns a list of (heading, body) tuples. Content before the first H2
    becomes ("", preamble) if non-empty.
    """
    matches = list(H2_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    first_start = matches[0].start()
    preamble = text[:first_start].strip()
    if preamble:
        sections.append(("", preamble))

    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _split_h3(body: str) -> list[tuple[str, str]]:
    matches = list(H3_RE.finditer(body))
    if not matches:
        return [("", body)]
    out: list[tuple[str, str]] = []
    preamble = body[: matches[0].start()].strip()
    if preamble:
        out.append(("", preamble))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        if chunk:
            out.append((heading, chunk))
    return out


def _hard_split(body: str, limit: int) -> list[str]:
    """Last-resort paragraph-boundary split when a section is too long."""
    if len(body) <= limit:
        return [body]
    paragraphs = re.split(r"\n\s*\n", body)
    out: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        if buf_len + len(p) + 2 > limit and buf:
            out.append("\n\n".join(buf))
            buf = [p]
            buf_len = len(p)
        else:
            buf.append(p)
            buf_len += len(p) + 2
    if buf:
        out.append("\n\n".join(buf))
    return out or [body[:limit]]


def _extract_anchors(body: str) -> list[str]:
    """Pick up well-known Woowa-style anchor headings inside a chunk."""
    anchors = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("## "):
            anchors.append(stripped.lstrip("#").strip())
        if len(anchors) >= 5:
            break
    return anchors


def _emit_chunks(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    sections: list[tuple[str, str]],
) -> Iterator[CorpusChunk]:
    counter = 0
    for h2, body in sections:
        pieces: list[tuple[list[str], str]] = []
        if len(body) <= MAX_CHARS_PER_CHUNK:
            pieces.append(([title] + ([h2] if h2 else []), body))
        else:
            for h3, sub in _split_h3(body):
                if len(sub) <= MAX_CHARS_PER_CHUNK:
                    sp = [title] + ([h2] if h2 else []) + ([h3] if h3 else [])
                    pieces.append((sp, sub))
                else:
                    for slab in _hard_split(sub, MAX_CHARS_PER_CHUNK):
                        sp = [title] + ([h2] if h2 else []) + ([h3] if h3 else [])
                        pieces.append((sp, slab))

        for section_path, chunk_body in pieces:
            chunk_body = chunk_body.strip()
            if len(chunk_body) < MIN_CHARS_PER_CHUNK:
                continue
            section_title = section_path[-1] if len(section_path) > 1 else ""
            yield CorpusChunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}#{counter}",
                path=path,
                title=title,
                category=category,
                section_title=section_title,
                section_path=section_path,
                body=chunk_body,
                char_len=len(chunk_body),
                anchors=_extract_anchors(chunk_body),
            )
            counter += 1


def iter_corpus(corpus_root: Path | str = DEFAULT_CORPUS_ROOT) -> Iterator[CorpusChunk]:
    """Walk the corpus root and yield CorpusChunk objects."""
    root = Path(corpus_root)
    if not root.exists():
        return
    for md_path in sorted(root.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        text = _strip_navigation(text)
        if not text.strip():
            continue
        relpath = md_path.relative_to(root)
        category = _category_for(relpath)
        title = _doc_title(text, md_path.stem.replace("-", " "))
        doc_id = hashlib.sha1(str(relpath.as_posix()).encode("utf-8")).hexdigest()[:16]
        sections = _split_sections(text)
        yield from _emit_chunks(
            doc_id=doc_id,
            path=relpath.as_posix(),
            title=title,
            category=category,
            sections=sections,
        )


def load_corpus(corpus_root: Path | str = DEFAULT_CORPUS_ROOT) -> list[CorpusChunk]:
    return list(iter_corpus(corpus_root))


def corpus_hash(corpus_root: Path | str = DEFAULT_CORPUS_ROOT) -> str:
    """Stable hash of the corpus — used by indexer manifest to detect staleness.

    Hashes (relative path, content sha1) pairs, not file mtimes, so rebuilds
    on different machines yield the same hash.
    """
    root = Path(corpus_root)
    h = hashlib.sha256()
    if not root.exists():
        return h.hexdigest()
    for md_path in sorted(root.rglob("*.md")):
        try:
            data = md_path.read_bytes()
        except OSError:
            continue
        rel = md_path.relative_to(root).as_posix().encode("utf-8")
        h.update(rel)
        h.update(b"\x00")
        h.update(hashlib.sha1(data).digest())
        h.update(b"\x00")
    return h.hexdigest()
