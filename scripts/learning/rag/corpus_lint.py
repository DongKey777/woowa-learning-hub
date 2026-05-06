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
# Match a YAML block sequence list item at any indentation, e.g.
# ``- DI``, ``  - DI``, ``    - DI``. Group 1 is the value after ``- ``.
_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.+)$")

REQUIRED_FRONTMATTER_FIELDS = (
    "title",
    "concept_id",
    "difficulty",
)
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced", "unknown"}
PILOT_V2_FIELDS = ("concept_id", "doc_role", "level", "aliases", "expected_queries")
VALID_DOC_ROLES = {
    "primer",
    "deep_dive",
    "chooser",
    "comparison",
    "playbook",
    "bridge",
    "drill",
}
VALID_LEVELS = {"beginner", "intermediate", "advanced"}

# ---------------------------------------------------------------------------
# Corpus v3 contract — see docs/worklogs/rag-r3-corpus-v3-contract.md
# Companion JSON Schema: tests/fixtures/r3_corpus_v3_schema.json
# ---------------------------------------------------------------------------
PILOT_V3_FIELDS = (
    "concept_id",
    "doc_role",
    "level",
    "language",
    "aliases",
    "expected_queries",
)
# v3 doc roles: 8 explicit values (primer/bridge/deep_dive/playbook/chooser/
# symptom_router/drill/mission_bridge). v2's "comparison" is dropped (use
# bridge or chooser); v3 adds symptom_router and mission_bridge.
VALID_DOC_ROLES_V3 = {
    "primer",
    "bridge",
    "deep_dive",
    "playbook",
    "chooser",
    "symptom_router",
    "drill",
    "mission_bridge",
}
VALID_LANGUAGES_V3 = {"ko", "en", "mixed"}
VALID_INTENTS_V3 = {
    "definition",
    "comparison",
    "symptom",
    "mission_bridge",
    "deep_dive",
    "drill",
    "design",
    "troubleshooting",
}
VALID_CATEGORIES_V3 = {
    "algorithm",
    "data-structure",
    "database",
    "design-pattern",
    "language",
    "network",
    "operating-system",
    "security",
    "software-engineering",
    "spring",
    "system-design",
}
_CONCEPT_ID_RE = re.compile(r"^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]+$")
_MISSION_ID_RE = re.compile(r"^missions\/[a-z][a-z0-9-]+$")
_CORPUS_PATH_RE = re.compile(r"^contents\/[a-z][a-z0-9-]*\/[a-z0-9_.\-/]+\.md$")


def parse_frontmatter(text: str) -> dict | None:
    """Parse a minimal subset of YAML frontmatter — enough for
    migrate_frontmatter.py output. Returns None if no frontmatter
    block is present."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    body = m.group(1)
    out: dict = {}
    pending_list_key: str | None = None
    pending_block_key: str | None = None
    pending_block_indent: int | None = None
    pending_block_lines: list[str] = []
    pending_block_chomp: str = ""

    def _flush_block() -> None:
        nonlocal pending_block_key, pending_block_indent, pending_block_lines, pending_block_chomp
        if pending_block_key is None:
            return
        text_block = "\n".join(pending_block_lines)
        if pending_block_chomp != "+":
            text_block = text_block.rstrip("\n")
        if pending_block_chomp == "":
            text_block = text_block.rstrip("\n") + "\n" if text_block else ""
        out[pending_block_key] = text_block
        pending_block_key = None
        pending_block_indent = None
        pending_block_lines = []
        pending_block_chomp = ""

    raw_lines = body.splitlines()
    for line in raw_lines:
        if pending_block_key is not None:
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            if line.strip() == "":
                pending_block_lines.append("")
                continue
            if pending_block_indent is None and indent > 0:
                pending_block_indent = indent
            if pending_block_indent is not None and indent >= pending_block_indent:
                pending_block_lines.append(line[pending_block_indent:])
                continue
            _flush_block()
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        list_item_match = _LIST_ITEM_RE.match(line)
        if pending_list_key and list_item_match:
            out[pending_list_key].append(_parse_yaml_scalar(list_item_match.group(1).strip()))
            continue
        kv = _LINE_KV_RE.match(line)
        if not kv:
            pending_list_key = None
            continue
        key, raw_value = kv.group(1), kv.group(2).strip()
        if raw_value in ("|", ">", "|-", ">-", "|+", ">+"):
            pending_list_key = None
            pending_block_key = key
            pending_block_indent = None
            pending_block_lines = []
            pending_block_chomp = raw_value[1:] if len(raw_value) > 1 else ""
            continue
        if raw_value == "":
            out[key] = []
            pending_list_key = key
            continue
        out[key] = _parse_yaml_scalar(raw_value)
        pending_list_key = None
    _flush_block()
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
    strict_v3: bool = False,
) -> list[LintViolation]:
    """Frontmatter is optional during P5.3 rollout. Once present,
    required fields and difficulty enum are enforced.

    ``strict_v3`` toggles the v3 lint between lenient (default — Wave A
    migration; role-conditional requirements emit warnings) and strict
    (CI / pre-cutover; role-conditional requirements block). See
    ``check_corpus_v3_pilot_frontmatter`` for the full mode contract.
    """
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
    if str(fm.get("schema_version")) == "2":
        out.extend(check_corpus_v2_pilot_frontmatter(file_path=file_path, frontmatter=fm))
    elif str(fm.get("schema_version")) == "3":
        out.extend(check_corpus_v3_pilot_frontmatter(
            file_path=file_path, frontmatter=fm, strict_mode=strict_v3,
        ))
    return out


def check_corpus_v2_pilot_frontmatter(
    *,
    file_path: Path,
    frontmatter: dict,
) -> list[LintViolation]:
    """Validate the staged Corpus v2 pilot fields."""
    out: list[LintViolation] = []
    for field_name in PILOT_V2_FIELDS:
        value = frontmatter.get(field_name)
        if value in (None, "", []):
            out.append(LintViolation(
                check="corpus_v2_frontmatter",
                file_path=str(file_path),
                message=f"corpus v2 missing pilot field: {field_name}",
            ))

    doc_role = frontmatter.get("doc_role")
    if doc_role not in (None, "") and doc_role not in VALID_DOC_ROLES:
        out.append(LintViolation(
            check="corpus_v2_frontmatter",
            file_path=str(file_path),
            message=f"doc_role '{doc_role}' not in {sorted(VALID_DOC_ROLES)}",
        ))

    level = frontmatter.get("level")
    if level not in (None, "") and level not in VALID_LEVELS:
        out.append(LintViolation(
            check="corpus_v2_frontmatter",
            file_path=str(file_path),
            message=f"level '{level}' not in {sorted(VALID_LEVELS)}",
        ))

    for list_field in ("aliases", "expected_queries"):
        value = frontmatter.get(list_field)
        if value in (None, ""):
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            out.append(LintViolation(
                check="corpus_v2_frontmatter",
                file_path=str(file_path),
                message=f"{list_field} must be a non-empty string list",
            ))
    return out


def _derive_category_from_path(file_path: Path) -> str | None:
    """Walk the path to find the parent directly under ``contents/``.

    Used to verify ``frontmatter.category`` matches folder placement.
    Returns None if the path is not under ``contents/<category>/...``.
    """
    parts = file_path.as_posix().split("/")
    if "contents" in parts:
        idx = parts.index("contents")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def _v3_violation(file_path: Path, message: str) -> LintViolation:
    return LintViolation(
        check="corpus_v3_frontmatter",
        file_path=str(file_path),
        message=message,
    )


def _is_non_empty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(isinstance(s, str) and s.strip() for s in value)
    )


def check_corpus_v3_pilot_frontmatter(
    *,
    file_path: Path,
    frontmatter: dict,
    strict_mode: bool = False,
) -> list[LintViolation]:
    """Validate the Corpus v3 pilot frontmatter (schema_version: 3).

    Two modes (per contract §2.1 + §6 lint design):

    * ``strict_mode=False`` (default — *lenient* / Wave A migration): only
      Pilot-required invariants block. Role-conditional Wave 2 fields
      (e.g. ``symptoms`` for symptom_router/playbook, ``confusable_with``
      for chooser, ``mission_ids`` for mission_bridge) emit *warnings*
      tagged as ``corpus_v3_frontmatter_wave2``. This lets Wave A
      migration ship without holding for content authoring.

    * ``strict_mode=True`` (CI / pre-cutover): every Pilot AND Wave 2
      conditional invariant blocks. All checks promoted to
      ``corpus_v3_frontmatter`` errors.

    Pilot-required invariants (always blockers):
      - PILOT_V3_FIELDS presence
      - doc_role, level, language enum
      - aliases / expected_queries shape
      - aliases ⊥ expected_queries (the circular-leak structural defense)
      - category matches folder placement (when category is set)
      - concept_id pattern
      - intents enum (when set)
      - mission_ids pattern (when set)
      - linked_paths / forbidden_neighbors path pattern (when set)
      - prerequisites / next_docs / confusable_with concept_id pattern
      - source_priority range

    Wave 2 conditional invariants (warnings in lenient, blockers in strict):
      - doc_role=symptom_router → symptoms ≥ 3
      - doc_role=playbook → symptoms ≥ 1
      - doc_role=mission_bridge → mission_ids ≥ 1
      - doc_role=chooser → confusable_with ≥ 2
    """
    out: list[LintViolation] = []

    # 1. PILOT_V3_FIELDS all present + non-empty
    for field_name in PILOT_V3_FIELDS:
        value = frontmatter.get(field_name)
        if value in (None, "", []):
            out.append(_v3_violation(
                file_path,
                f"corpus v3 missing pilot field: {field_name}",
            ))

    # 2. concept_id pattern
    concept_id = frontmatter.get("concept_id")
    if isinstance(concept_id, str) and concept_id and not _CONCEPT_ID_RE.match(concept_id):
        out.append(_v3_violation(
            file_path,
            f"concept_id '{concept_id}' does not match "
            f"'^[a-z][a-z0-9-]*\\/[a-z][a-z0-9-]+$'",
        ))

    # 3. doc_role enum
    doc_role = frontmatter.get("doc_role")
    if doc_role not in (None, "") and doc_role not in VALID_DOC_ROLES_V3:
        out.append(_v3_violation(
            file_path,
            f"doc_role '{doc_role}' not in {sorted(VALID_DOC_ROLES_V3)}",
        ))

    # 4. level enum
    level = frontmatter.get("level")
    if level not in (None, "") and level not in VALID_LEVELS:
        out.append(_v3_violation(
            file_path,
            f"level '{level}' not in {sorted(VALID_LEVELS)}",
        ))

    # 5. language enum
    language = frontmatter.get("language")
    if language not in (None, "") and language not in VALID_LANGUAGES_V3:
        out.append(_v3_violation(
            file_path,
            f"language '{language}' not in {sorted(VALID_LANGUAGES_V3)}",
        ))

    # 6. category enum + folder placement
    category = frontmatter.get("category")
    if category not in (None, "") and category not in VALID_CATEGORIES_V3:
        out.append(_v3_violation(
            file_path,
            f"category '{category}' not in {sorted(VALID_CATEGORIES_V3)}",
        ))
    expected_category = _derive_category_from_path(file_path)
    if (
        expected_category is not None
        and category not in (None, "")
        and category != expected_category
    ):
        out.append(_v3_violation(
            file_path,
            f"category '{category}' does not match folder placement "
            f"'{expected_category}' (path under contents/{expected_category}/)",
        ))

    # 7. aliases / expected_queries shape
    aliases = frontmatter.get("aliases")
    expected_queries = frontmatter.get("expected_queries")
    aliases_valid = _is_non_empty_string_list(aliases)
    eq_valid = _is_non_empty_string_list(expected_queries)
    if aliases is not None and not aliases_valid:
        out.append(_v3_violation(
            file_path,
            "aliases must be a non-empty list[str]",
        ))
    if expected_queries is not None and not eq_valid:
        out.append(_v3_violation(
            file_path,
            "expected_queries must be a non-empty list[str]",
        ))

    # 8. CRITICAL invariant: aliases ⊥ expected_queries (case-insensitive,
    # whitespace-normalized). This is the structural defense against the
    # circular-leak class of bug.
    if aliases_valid and eq_valid:
        norm_aliases = {re.sub(r"\s+", " ", a.strip().casefold()) for a in aliases}
        norm_eq = {re.sub(r"\s+", " ", q.strip().casefold()) for q in expected_queries}
        overlap = norm_aliases & norm_eq
        if overlap:
            out.append(_v3_violation(
                file_path,
                f"aliases ⊥ expected_queries violation (overlap: "
                f"{sorted(overlap)}). v3 contract requires structural "
                f"separation (aliases = lexical hint channel, "
                f"expected_queries = qrel seed only).",
            ))

    # 9. intents enum
    intents = frontmatter.get("intents")
    if intents is not None:
        if not isinstance(intents, list):
            out.append(_v3_violation(
                file_path,
                "intents must be a list[str]",
            ))
        else:
            for intent in intents:
                if intent not in VALID_INTENTS_V3:
                    out.append(_v3_violation(
                        file_path,
                        f"intent '{intent}' not in "
                        f"{sorted(VALID_INTENTS_V3)}",
                    ))

    # 10. mission_ids pattern
    mission_ids = frontmatter.get("mission_ids")
    if isinstance(mission_ids, list):
        for mid in mission_ids:
            if not (isinstance(mid, str) and _MISSION_ID_RE.match(mid)):
                out.append(_v3_violation(
                    file_path,
                    f"mission_id '{mid}' does not match "
                    f"'^missions\\/[a-z][a-z0-9-]+$'",
                ))

    # 11. linked_paths / forbidden_neighbors path pattern
    for path_field in ("linked_paths", "forbidden_neighbors"):
        value = frontmatter.get(path_field)
        if isinstance(value, list):
            for p in value:
                if not (isinstance(p, str) and _CORPUS_PATH_RE.match(p)):
                    out.append(_v3_violation(
                        file_path,
                        f"{path_field} entry '{p}' does not match "
                        f"corpus path pattern",
                    ))

    # 12. prerequisites / next_docs / confusable_with concept_id pattern
    for cid_field in ("prerequisites", "next_docs", "confusable_with"):
        value = frontmatter.get(cid_field)
        if isinstance(value, list):
            for c in value:
                if not (isinstance(c, str) and _CONCEPT_ID_RE.match(c)):
                    out.append(_v3_violation(
                        file_path,
                        f"{cid_field} entry '{c}' does not match "
                        f"concept_id pattern",
                    ))

    # 13. Role-conditional requirements (Wave 2 fields).
    #     In lenient mode (strict_mode=False), violations are tagged
    #     ``corpus_v3_frontmatter_wave2`` so consumers can filter them as
    #     warnings during Wave A migration. In strict mode they collapse
    #     into the normal ``corpus_v3_frontmatter`` error track.
    wave2_check = (
        "corpus_v3_frontmatter" if strict_mode else "corpus_v3_frontmatter_wave2"
    )

    def _wave2_violation(message: str) -> LintViolation:
        return LintViolation(
            check=wave2_check,
            file_path=str(file_path),
            message=message,
        )

    if doc_role == "symptom_router":
        symptoms = frontmatter.get("symptoms")
        if not (isinstance(symptoms, list) and len(symptoms) >= 3):
            out.append(_wave2_violation(
                "doc_role=symptom_router requires symptoms with at least "
                "3 entries (per contract §3.2 symptom_router)",
            ))
    if doc_role == "playbook":
        symptoms = frontmatter.get("symptoms")
        if not (isinstance(symptoms, list) and len(symptoms) >= 1):
            out.append(_wave2_violation(
                "doc_role=playbook requires symptoms with at least 1 entry",
            ))
    if doc_role == "mission_bridge":
        mids = frontmatter.get("mission_ids")
        if not (isinstance(mids, list) and len(mids) >= 1):
            out.append(_wave2_violation(
                "doc_role=mission_bridge requires mission_ids with at least "
                "1 entry",
            ))
    if doc_role == "chooser":
        cw = frontmatter.get("confusable_with")
        if not (isinstance(cw, list) and len(cw) >= 2):
            out.append(_wave2_violation(
                "doc_role=chooser requires confusable_with with at least 2 "
                "candidates (per contract §3.2 chooser)",
            ))

    # 13b. forbidden_neighbors discipline for chooser/bridge/symptom_router
    #
    # Cycle 1 cohort_eval (2026-05-06) showed that fleet workers were
    # populating forbidden_neighbors with the canonical primer of the
    # same area, treating "competing/learning-path neighbour" the same
    # as "wrong-bucket noise". The post-rerank forbidden_filter then
    # demoted the primer out of top-k whenever the chooser became top-1,
    # regressing confusable_pairs by -7.5pp.
    #
    # Wave 2 warning, not a hard error: legacy docs predate this rule
    # and the lint shouldn't block the migration. New writes that cite
    # a primer they themselves point at as canonical surface this issue.
    if doc_role in ("chooser", "bridge", "symptom_router"):
        forbidden = frontmatter.get("forbidden_neighbors")
        confusable = frontmatter.get("confusable_with")
        if isinstance(forbidden, list) and isinstance(confusable, list):
            # Same path appearing in both fields is the strongest signal
            # that the worker collapsed the two dimensions. confusable
            # entries are concept_ids; forbidden entries are paths. Match
            # the slug fragment so we catch the chooser→primer collision
            # without needing a full catalog lookup at lint time.
            # confusable_with entries are concept_ids
            # (`category/slug`). forbidden_neighbors entries are paths
            # (`contents/category/filename.md`). The filename slug is
            # often a longer form than the concept_id slug — e.g.
            # concept_id `spring/bean-di-basics` corresponds to path
            # `contents/spring/spring-bean-di-basics.md` (filename
            # carries a category prefix for in-directory uniqueness).
            # Substring containment is the cheap robust proxy that
            # catches both directions.
            confusable_slugs = {
                str(c).split("/")[-1].lower()
                for c in confusable
                if isinstance(c, str)
            }
            for fpath in forbidden:
                if not isinstance(fpath, str):
                    continue
                fslug = fpath.split("/")[-1].removesuffix(".md").lower()
                # Match if any confusable concept's slug appears as a
                # substring of the forbidden path's filename slug, or
                # vice versa. The strict form (cross-checking
                # canonical=true via catalog) needs whole-corpus access;
                # this lint runs per-file, so the substring signal is
                # the cheap proxy.
                hit = next(
                    (cs for cs in confusable_slugs if cs and (
                        cs in fslug or fslug.endswith(cs)
                    )),
                    None,
                )
                if hit is not None:
                    out.append(_wave2_violation(
                        f"doc_role={doc_role}: forbidden_neighbors entry "
                        f"{fpath!r} matches confusable_with slug {hit!r} — "
                        "these are different dimensions (forbidden=wrong-"
                        "bucket, confusable=learning-path neighbour). See "
                        "cycle 1 regression analysis 2026-05-06 — collapsing "
                        "the two demotes legitimate primary docs out of "
                        "top-k.",
                    ))

    # 14. source_priority range (when present)
    # parse_frontmatter is a minimal YAML parser — numeric scalars come back
    # as strings. Accept str digits and int alike.
    sp = frontmatter.get("source_priority")
    if sp is not None:
        sp_int: int | None = None
        if isinstance(sp, bool):
            # bool is a subclass of int in Python; reject it explicitly.
            pass
        elif isinstance(sp, int):
            sp_int = sp
        elif isinstance(sp, str) and sp.lstrip("-").isdigit():
            try:
                sp_int = int(sp)
            except ValueError:
                sp_int = None
        if sp_int is None or sp_int < 0 or sp_int > 100:
            out.append(_v3_violation(
                file_path,
                f"source_priority must be int in [0, 100], got {sp!r}",
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
    strict_v3: bool = False,
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

    ``strict_v3`` toggles the v3 lint mode (default lenient — Wave 2
    role-conditional requirements emit ``corpus_v3_frontmatter_wave2``
    warnings; strict mode promotes them to ``corpus_v3_frontmatter``
    blockers).
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
            file_path=path, text=text, strict_v3=strict_v3,
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
    parser.add_argument(
        "--strict-v3",
        action="store_true",
        help=(
            "Promote v3 Wave 2 role-conditional warnings (symptoms / "
            "confusable_with / mission_ids) to errors. Default is lenient "
            "(warnings only) so Wave A migration ships without holding "
            "for content authoring. Flip on for CI / pre-cutover gating."
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

    report = lint_corpus(
        corpus_root,
        repo_root=repo_root,
        dedupe_candidates_fn=dedupe_fn,
        strict_v3=args.strict_v3,
    )
    print(f"[corpus-lint] scanned {report.files_scanned} files")
    by_check = report.by_check()
    if report.ok():
        print("[corpus-lint] OK — no violations")
        return 0
    blocker_count = 0
    for check, n in sorted(by_check.items()):
        is_warning = check == "corpus_v3_frontmatter_wave2"
        label = "warnings" if is_warning else "violations"
        print(f"[corpus-lint] {check}: {n} {label}")
        if not is_warning:
            blocker_count += n
    for v in report.violations:
        prefix = "warn" if v.check == "corpus_v3_frontmatter_wave2" else v.check
        print(f"  [{prefix}] {v.file_path}: {v.message}")
    if args.strict:
        # Wave 2 warnings never block --strict in lenient v3 mode; only the
        # combined --strict + --strict-v3 promotes them. Blockers always
        # block in --strict mode.
        return 1 if blocker_count > 0 else 0
    print("[corpus-lint] report-only mode (use --strict to fail on violations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
