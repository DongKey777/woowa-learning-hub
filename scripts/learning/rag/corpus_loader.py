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

Scope
-----
Only files under ``knowledge/cs/contents/<category>/...`` are indexed.
Top-level docs (``README.md``, ``ADVANCED-BACKEND-ROADMAP.md``, ``LICENSE``,
etc.) and sibling trees like ``master-notes/`` / ``rag/`` are meta content
— they show up in retrieval as noise because they cover everything at a
high level. Rebuilding the index after this change is what enforces the
scope; callers that point ``iter_corpus`` at a subdirectory directly are
unaffected.

Retrieval anchors
-----------------
Woowa CS notes carry retrieval phrases in a few live markdown forms:
``### Retrieval Anchors`` sections, inline ``retrieval-anchor-keywords:``
metadata, and inline ``Retrieval anchors:`` metadata. We extract those
phrases once per document and append them to every chunk's persisted
``body`` so FTS, lexical sidecars, and reranker passages can pick up the
intent. The original section text is also kept as ``embedding_body`` so
dense/ColBERT embeddings are trained on substantive content, not on
qrel-like query strings. Corpus v2 ``expected_queries`` are treated as
retrieval-contract phrases, not passive documentation — e.g. a
"repository boundary" query hits every chunk of
``repository-pattern-vs-antipattern.md`` via the anchors even when the
chunk text itself is discussing a tangential subtopic. Dedupe-by-path
downstream ensures only one chunk per doc still reaches top-K.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from scripts.learning.rag.corpus_lint import parse_frontmatter

DEFAULT_CORPUS_ROOT = Path("knowledge/cs")
CONTENTS_DIR = "contents"

MAX_CHARS_PER_CHUNK = 1600       # ≈ 400 tokens
MIN_CHARS_PER_CHUNK = 60         # below this we skip (pure nav fragments)

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
DETAILS_RE = re.compile(r"<details>.*?</details>", re.DOTALL | re.IGNORECASE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
HEADING_START_RE = re.compile(r"^#{1,6}\s+", re.IGNORECASE)
RETRIEVAL_ANCHOR_SECTION_RE = re.compile(
    r"^###\s+(?:\d+\.\s*)?retrieval anchors\s*$",
    re.IGNORECASE,
)
RETRIEVAL_ANCHOR_INLINE_RE = re.compile(
    r"^(?:>\s*)?(?:retrieval-anchor-keywords|retrieval anchors):\s*(.*)$",
    re.IGNORECASE,
)
# Extracts `phrase` list items (backtick-quoted or plain bullets).
_ANCHOR_ITEM_RE = re.compile(r"^\s*(?:>\s*)?(?:[-*]|\d+\.)\s+(.+?)\s*$")

# Difficulty label — emitted by the metadata normalization sweep as
# ``**난이도: 🟢 Beginner**`` (or 🟡 Intermediate / 🔴 Advanced / 🔴 Expert).
# We extract the canonical English tier so the index can rank against
# learner experience_level without re-parsing the label at query time.
DIFFICULTY_RE = re.compile(r"\*\*난이도:\s*[^A-Za-z]*([A-Za-z]+)\s*\*\*")
DIFFICULTY_TIERS = {
    "beginner": "beginner",
    "basic": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
    "expert": "expert",
}


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
    embedding_body: str | None = None  # body used for semantic vectors
    char_len: int = 0
    anchors: list[str] = field(default_factory=list)
    difficulty: str | None = None  # "beginner"|"intermediate"|"advanced"|"expert"|None
    concept_id: str | None = None
    doc_role: str | None = None
    level: str | None = None

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
            "embedding_body": self.embedding_body,
            "char_len": self.char_len,
            "anchors": list(self.anchors),
            "difficulty": self.difficulty,
            "concept_id": self.concept_id,
            "doc_role": self.doc_role,
            "level": self.level,
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


def _strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def _frontmatter_string(frontmatter: dict | None, key: str) -> str | None:
    if not frontmatter:
        return None
    value = frontmatter.get(key)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _frontmatter_list(frontmatter: dict | None, key: str) -> list[str]:
    if not frontmatter:
        return []
    value = frontmatter.get(key)
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe_phrases(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for raw in group:
            phrase = re.sub(r"\s+", " ", raw.strip())
            if not phrase:
                continue
            key = phrase.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(phrase)
    return out


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


def _extract_retrieval_anchors(text: str) -> list[str]:
    """Pull canonical phrases from live retrieval-anchor metadata styles.

    Returns an ordered, de-duplicated list of phrases. Empty when the doc
    has no supported anchor metadata.
    """
    seen: set[str] = set()
    out: list[str] = []

    def add_phrase(raw: str) -> None:
        phrase = re.sub(r"\s+", " ", raw.strip().strip("`").strip("\"'"))
        if not phrase:
            return
        key = phrase.casefold()
        if key in seen:
            return
        seen.add(key)
        out.append(phrase)

    def add_inline_values(raw: str) -> None:
        buf: list[str] = []
        in_backticks = False
        for char in raw:
            if char == "`":
                in_backticks = not in_backticks
                buf.append(char)
                continue
            if not in_backticks and char in ",;|":
                add_phrase("".join(buf))
                buf = []
                continue
            buf.append(char)
        add_phrase("".join(buf))

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        if RETRIEVAL_ANCHOR_SECTION_RE.match(line):
            i += 1
            while i < len(lines) and not HEADING_START_RE.match(lines[i]):
                item = _ANCHOR_ITEM_RE.match(lines[i])
                if item:
                    add_phrase(item.group(1))
                else:
                    inline = RETRIEVAL_ANCHOR_INLINE_RE.match(lines[i])
                    if inline and inline.group(1).strip():
                        add_inline_values(inline.group(1).strip())
                i += 1
            continue

        inline = RETRIEVAL_ANCHOR_INLINE_RE.match(line)
        if inline:
            value = inline.group(1).strip()
            if value:
                add_inline_values(value)
                i += 1
                continue

            i += 1
            found_item = False
            while i < len(lines):
                if HEADING_START_RE.match(lines[i]):
                    break
                if not lines[i].strip():
                    if found_item:
                        break
                    i += 1
                    continue
                item = _ANCHOR_ITEM_RE.match(lines[i])
                if not item:
                    break
                add_phrase(item.group(1))
                found_item = True
                i += 1
            continue

        i += 1

    return out


def _extract_difficulty(text: str) -> str | None:
    """Return canonical tier (``beginner``|``intermediate``|``advanced``|``expert``).

    Reads the first ``**난이도: ...**`` label in the document. Returns
    ``None`` when the label is absent or the tier word is unrecognized.
    """
    m = DIFFICULTY_RE.search(text)
    if not m:
        return None
    word = m.group(1).strip().lower()
    return DIFFICULTY_TIERS.get(word)


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
    retrieval_anchors: list[str] | None = None,
    difficulty: str | None = None,
    concept_id: str | None = None,
    doc_role: str | None = None,
    level: str | None = None,
    frontmatter_aliases: list[str] | None = None,
    frontmatter_expected_queries: list[str] | None = None,
) -> Iterator[CorpusChunk]:
    document_retrieval_phrases = _dedupe_phrases(
        frontmatter_expected_queries or [],
        retrieval_anchors or [],
    )
    anchor_suffix = ""
    if document_retrieval_phrases:
        anchor_suffix = (
            "\n\n[retrieval anchors] "
            + " | ".join(document_retrieval_phrases)
        )
    document_aliases = _dedupe_phrases(
        frontmatter_aliases or [],
        document_retrieval_phrases,
    )
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
            final_body = chunk_body + anchor_suffix
            chunk_anchors = _dedupe_phrases(_extract_anchors(chunk_body), document_aliases)
            yield CorpusChunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}#{counter}",
                path=path,
                title=title,
                category=category,
                section_title=section_title,
                section_path=section_path,
                body=final_body,
                embedding_body=chunk_body,
                char_len=len(final_body),
                anchors=chunk_anchors,
                difficulty=difficulty,
                concept_id=concept_id,
                doc_role=doc_role,
                level=level,
            )
            counter += 1


def iter_corpus(corpus_root: Path | str = DEFAULT_CORPUS_ROOT) -> Iterator[CorpusChunk]:
    """Walk the corpus root and yield CorpusChunk objects.

    Only files under ``<root>/contents/<category>/...`` are yielded — root
    READMEs, roadmaps, and sibling trees like ``master-notes/`` / ``rag/``
    are skipped because they behave as retrieval noise.
    """
    root = Path(corpus_root)
    if not root.exists():
        return
    contents_root = root / CONTENTS_DIR
    if not contents_root.exists():
        return
    for md_path in sorted(contents_root.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        frontmatter = parse_frontmatter(text)
        text = _strip_frontmatter(text)
        text = _strip_navigation(text)
        if not text.strip():
            continue
        relpath = md_path.relative_to(root)
        category = _category_for(relpath)
        title = _doc_title(text, md_path.stem.replace("-", " "))
        doc_id = hashlib.sha1(str(relpath.as_posix()).encode("utf-8")).hexdigest()[:16]
        sections = _split_sections(text)
        retrieval_anchors = _extract_retrieval_anchors(text)
        difficulty = _frontmatter_string(frontmatter, "difficulty") or _extract_difficulty(text)
        yield from _emit_chunks(
            doc_id=doc_id,
            path=relpath.as_posix(),
            title=title,
            category=category,
            sections=sections,
            retrieval_anchors=retrieval_anchors,
            difficulty=difficulty,
            concept_id=_frontmatter_string(frontmatter, "concept_id"),
            doc_role=_frontmatter_string(frontmatter, "doc_role"),
            level=_frontmatter_string(frontmatter, "level"),
            frontmatter_aliases=_frontmatter_list(frontmatter, "aliases"),
            frontmatter_expected_queries=_frontmatter_list(
                frontmatter, "expected_queries"
            ),
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
