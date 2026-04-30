"""Corpus integrity lint (plan §P5.4).

Static checks over ``knowledge/cs/contents/**/*.md`` so coordination
mistakes (broken cross-doc links, missing required fields, duplicate
concept_ids) surface in CI rather than during retrieval debugging.

Three checks are deterministic and run by default:

1. **link_integrity** — every relative markdown link
   (``[text](./relative.md)`` or ``../sibling.md``) must resolve to a
   real file on disk. Anchored fragments (``./doc.md#section``) are
   accepted as-is — the part before ``#`` must exist.
2. **frontmatter_schema** — when a file has YAML frontmatter (P5.3
   migration output), the required fields are present and the
   difficulty enum is valid. Missing frontmatter is *not* an error
   yet; that becomes mandatory after P5.3 is applied to the full
   corpus.
3. **concept_id_uniqueness** — every ``concept_id`` from frontmatter
   must be unique across the corpus.

A fourth check (**dedupe_candidates** — cosine ≥ 0.92 between chunk
embeddings) is opt-in via ``--with-dedupe`` because it requires the
embedding index. It is delegated to a callable so this module stays
LLM-free and standalone-testable.

Output: a structured ``LintReport`` listing every violation with
``file_path`` + ``message``. CLI exits 0 only when ``violations`` is
empty.

Tested in ``tests/unit/test_corpus_lint.py``.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Frontmatter parsing (light — single-line scalars + flow lists only)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LINE_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
_FLOW_LIST_RE = re.compile(r"^\[(.*)\]$")
_QUOTED_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"$')

REQUIRED_FRONTMATTER_FIELDS = (
    "title",
    "concept_id",
    "difficulty",
)
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced", "unknown"}


def parse_frontmatter(text: str) -> dict | None:
    """Parse a minimal subset of YAML frontmatter — enough for
    migrate_frontmatter.py output. Returns None if no frontmatter
    block is present."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    body = m.group(1)
    out: dict = {}
    for line in body.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        kv = _LINE_KV_RE.match(line)
        if not kv:
            continue
        key, raw_value = kv.group(1), kv.group(2).strip()
        out[key] = _parse_yaml_scalar(raw_value)
    return out


def _parse_yaml_scalar(raw: str):
    if raw == "null" or raw == "":
        return None
    flow = _FLOW_LIST_RE.match(raw)
    if flow:
        inner = flow.group(1).strip()
        if not inner:
            return []
        return [_parse_yaml_scalar(p.strip()) for p in _split_flow_list(inner)]
    qm = _QUOTED_RE.match(raw)
    if qm:
        return qm.group(1).encode("utf-8").decode("unicode_escape")
    return raw


def _split_flow_list(inner: str) -> list[str]:
    """Split a flow-list inner string by ``, `` while respecting
    double quotes."""
    parts: list[str] = []
    buf: list[str] = []
    in_quote = False
    escaped = False
    for c in inner:
        if escaped:
            buf.append(c)
            escaped = False
            continue
        if c == "\\":
            buf.append(c)
            escaped = True
            continue
        if c == '"':
            in_quote = not in_quote
            buf.append(c)
            continue
        if c == "," and not in_quote:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(c)
    parts.append("".join(buf).strip())
    return parts


# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------

# Markdown link `[text](href)` — capture the href.
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def extract_relative_links(text: str) -> list[str]:
    """Return all relative markdown link hrefs in ``text``. Absolute
    URLs (http://, https://, mailto:) and bare anchors (#section) are
    skipped — only relative paths get checked."""
    out: list[str] = []
    for m in _MD_LINK_RE.finditer(text):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Drop fragment for resolution
        href_no_frag = href.split("#", 1)[0]
        if not href_no_frag:
            continue
        out.append(href_no_frag)
    return out


# ---------------------------------------------------------------------------
# Lint report
# ---------------------------------------------------------------------------

@dataclass
class LintViolation:
    check: str  # "link_integrity" | "frontmatter_schema" | "concept_id_uniqueness" | "dedupe_candidates"
    file_path: str
    message: str


@dataclass
class LintReport:
    files_scanned: int = 0
    violations: list[LintViolation] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.violations

    def by_check(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for v in self.violations:
            out[v.check] = out.get(v.check, 0) + 1
        return out


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_link_integrity(
    *,
    file_path: Path,
    text: str,
    corpus_root: Path,
    repo_root: Path | None = None,
) -> list[LintViolation]:
    """Flag relative markdown links whose target file does not exist.

    Links that resolve *outside* ``corpus_root`` but inside ``repo_root``
    (e.g. cross-domain references to ``../../JUNIOR-BACKEND-ROADMAP.md``)
    are accepted as long as the target file exists — those are
    legitimate inter-domain references, not retrieval-time concerns.
    Links that escape ``repo_root`` (when provided) are flagged.
    """
    out: list[LintViolation] = []
    corpus_resolved = corpus_root.resolve()
    repo_resolved = repo_root.resolve() if repo_root else None
    for href in extract_relative_links(text):
        target = (file_path.parent / href).resolve()

        # Outside the corpus subtree — only fail if escaping the repo
        # entirely (or the file simply does not exist).
        if not _is_within(target, corpus_resolved):
            if repo_resolved is not None and not _is_within(target, repo_resolved):
                out.append(LintViolation(
                    check="link_integrity",
                    file_path=str(file_path),
                    message=f"link '{href}' escapes repo root",
                ))
                continue
            # Within repo but outside corpus — accept if target exists.
            if not target.exists():
                out.append(LintViolation(
                    check="link_integrity",
                    file_path=str(file_path),
                    message=f"broken link (cross-domain): {href}",
                ))
            continue
        if not target.exists():
            out.append(LintViolation(
                check="link_integrity",
                file_path=str(file_path),
                message=f"broken link: {href}",
            ))
    return out


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def check_frontmatter_schema(
    *,
    file_path: Path,
    text: str,
) -> list[LintViolation]:
    """Frontmatter is optional during P5.3 rollout. Once present,
    required fields and difficulty enum are enforced."""
    out: list[LintViolation] = []
    fm = parse_frontmatter(text)
    if fm is None:
        return out  # pre-migration, not a violation yet
    for field_name in REQUIRED_FRONTMATTER_FIELDS:
        if field_name not in fm or fm[field_name] in (None, ""):
            out.append(LintViolation(
                check="frontmatter_schema",
                file_path=str(file_path),
                message=f"frontmatter missing required field: {field_name}",
            ))
    diff = fm.get("difficulty")
    if diff is not None and diff not in VALID_DIFFICULTIES:
        out.append(LintViolation(
            check="frontmatter_schema",
            file_path=str(file_path),
            message=f"frontmatter difficulty '{diff}' not in {sorted(VALID_DIFFICULTIES)}",
        ))
    return out


def check_concept_id_uniqueness(
    files: Iterable[tuple[Path, str]],
) -> list[LintViolation]:
    """``files`` is an iterable of ``(path, text)``. Concept IDs come
    from frontmatter; duplicates are reported on each colliding file."""
    seen: dict[str, list[Path]] = {}
    for path, text in files:
        fm = parse_frontmatter(text)
        if not fm:
            continue
        cid = fm.get("concept_id")
        if not isinstance(cid, str) or not cid:
            continue
        seen.setdefault(cid, []).append(path)

    out: list[LintViolation] = []
    for cid, paths in seen.items():
        if len(paths) <= 1:
            continue
        for p in paths:
            others = [str(o) for o in paths if o != p]
            out.append(LintViolation(
                check="concept_id_uniqueness",
                file_path=str(p),
                message=f"concept_id '{cid}' also used in: {others}",
            ))
    return out


def find_markdown_files(corpus_root: Path) -> list[Path]:
    return sorted(corpus_root.rglob("*.md"))


def lint_corpus(
    corpus_root: Path,
    *,
    repo_root: Path | None = None,
    dedupe_candidates_fn=None,  # optional callable -> list[LintViolation]
) -> LintReport:
    """Run all checks over ``corpus_root``. ``dedupe_candidates_fn``,
    when provided, is called with the list of (path, text) tuples and
    must return a list of LintViolation entries — keeps embedding
    dependencies out of this module.

    ``repo_root`` enables a softer link-integrity rule: cross-domain
    references that leave ``corpus_root`` but stay within the repo
    (e.g. ``knowledge/cs/contents/.../doc.md`` linking to
    ``knowledge/cs/JUNIOR-BACKEND-ROADMAP.md``) are accepted when the
    target exists.
    """
    report = LintReport()
    files_with_text: list[tuple[Path, str]] = []
    for path in find_markdown_files(corpus_root):
        text = path.read_text(encoding="utf-8")
        files_with_text.append((path, text))
        report.files_scanned += 1
        report.violations.extend(check_link_integrity(
            file_path=path, text=text, corpus_root=corpus_root,
            repo_root=repo_root,
        ))
        report.violations.extend(check_frontmatter_schema(
            file_path=path, text=text,
        ))
    report.violations.extend(check_concept_id_uniqueness(files_with_text))

    if dedupe_candidates_fn is not None:
        report.violations.extend(dedupe_candidates_fn(files_with_text))

    return report


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
    import argparse
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(description="CS corpus integrity lint (plan §P5.4).")
    parser.add_argument(
        "--corpus",
        default=str(repo_root / "knowledge" / "cs" / "contents"),
    )
    parser.add_argument(
        "--with-dedupe",
        action="store_true",
        help=(
            "Run embedding-cosine dedupe candidate check using "
            "state/cs_rag/dense.npz. Requires the production index "
            "to be built (bin/cs-index-build)."
        ),
    )
    parser.add_argument(
        "--dedupe-threshold",
        type=float,
        default=0.92,
        help="Cosine similarity threshold (default: 0.92, plan §P5.4).",
    )
    parser.add_argument(
        "--dedupe-cross-category",
        action="store_true",
        help=(
            "Allow cross-category dedupe pairs. Default scope is "
            "same-category only — cuts compute and avoids accidental "
            "false positives across unrelated domains."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero when violations are found (default: report-only). "
            "Flip this on after the P5.5 manual dedup/link-rot pass cleans "
            "the corpus so CI can gate on it."
        ),
    )
    args = parser.parse_args(argv)

    corpus_root = Path(args.corpus)
    if not corpus_root.exists():
        print(f"[corpus-lint] corpus not found: {corpus_root}", file=sys.stderr)
        return 2

    dedupe_fn = None
    if args.with_dedupe:
        # Lazy import keeps the lint module standalone-testable.
        from scripts.learning.rag.corpus_dedupe_runner import make_lint_callback  # noqa: WPS433
        index_root = repo_root / "state" / "cs_rag"
        dedupe_fn = make_lint_callback(
            index_root=index_root,
            threshold=args.dedupe_threshold,
            same_category_only=not args.dedupe_cross_category,
        )

    report = lint_corpus(corpus_root, repo_root=repo_root, dedupe_candidates_fn=dedupe_fn)
    print(f"[corpus-lint] scanned {report.files_scanned} files")
    by_check = report.by_check()
    if report.ok():
        print("[corpus-lint] OK — no violations")
        return 0
    for check, n in sorted(by_check.items()):
        print(f"[corpus-lint] {check}: {n} violations")
    for v in report.violations:
        print(f"  [{v.check}] {v.file_path}: {v.message}")
    if args.strict:
        return 1
    print("[corpus-lint] report-only mode (use --strict to fail on violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
