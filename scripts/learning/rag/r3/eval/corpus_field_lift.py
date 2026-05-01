"""Measure Corpus v2 retrieval lift from staged frontmatter fields."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

from scripts.learning.rag.corpus_lint import parse_frontmatter

from ..candidate import R3Document
from ..fusion import fuse_candidates
from ..index.lexical_store import LexicalStore
from ..query_plan import build_query_plan
from ..retrievers.lexical import LexicalRetriever
from .metrics import RetrievalEvaluationQuery, retrieval_summary
from .qrels import R3QueryJudgement, qrels_from_corpus


_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
DEFAULT_FIELD_RUNS = {
    "body_only": ("body",),
    "body_title": ("body", "title"),
    "body_aliases": ("body", "aliases"),
    "body_title_aliases": ("body", "title", "aliases"),
}


def _body_without_frontmatter(text: str) -> str:
    return _FRONTMATTER_BLOCK_RE.sub("", text, count=1)


def _as_string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _doc_path(path: Path, corpus_root: Path) -> str:
    try:
        relative = str(path.relative_to(corpus_root))
    except ValueError:
        relative = str(path)
    return relative if relative.startswith("contents/") else f"contents/{relative}"


def _category(path: str) -> str:
    parts = path.split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "contents" else "unknown"


def corpus_v2_documents(
    corpus_root: Path,
    *,
    fields: Iterable[str],
) -> list[R3Document]:
    """Build in-memory R3 docs with only selected retrieval fields enabled."""

    field_set = set(fields)
    documents: list[R3Document] = []
    for path in sorted(corpus_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm or str(fm.get("schema_version")) != "2":
            continue
        doc_path = _doc_path(path, corpus_root)
        body = _body_without_frontmatter(text) if "body" in field_set else ""
        title = str(fm.get("title") or "") if "title" in field_set else ""
        aliases = _as_string_list(fm.get("aliases")) if "aliases" in field_set else ()
        metadata = {
            "concept_id": fm.get("concept_id"),
            "doc_role": fm.get("doc_role"),
            "level": fm.get("level"),
            "category": _category(doc_path),
        }
        documents.append(
            R3Document(
                path=doc_path,
                title=title,
                body=body,
                aliases=aliases,
                signals=tuple(
                    str(metadata[key])
                    for key in ("doc_role", "level", "category")
                    if metadata.get(key)
                ),
                metadata=metadata,
            )
        )
    return documents


def _evaluate_field_run(
    documents: list[R3Document],
    qrels: list[R3QueryJudgement],
    *,
    windows: tuple[int, ...],
) -> dict[str, Any]:
    retriever = LexicalRetriever(LexicalStore.from_documents(documents), limit_per_field=max(windows))
    max_window = max(windows)
    evaluation: list[RetrievalEvaluationQuery] = []
    for query in qrels:
        plan = build_query_plan(query.prompt)
        candidates = retriever.retrieve(plan)
        fused = fuse_candidates(candidates, limit=max_window)
        final_paths = tuple(candidate.path for candidate in fused)
        evaluation.append(
            RetrievalEvaluationQuery(
                query_id=query.query_id,
                language=plan.language,
                level=_tag_value(query.tags, "level"),
                category=_tag_value(query.tags, "category"),
                primary_paths=tuple(sorted(query.primary_paths())),
                acceptable_paths=tuple(sorted(query.acceptable_paths())),
                forbidden_paths=query.forbidden_paths,
                candidate_paths=final_paths,
                final_paths=final_paths,
            )
        )
    return retrieval_summary(evaluation, windows=windows)


def _tag_value(tags: tuple[str, ...], prefix: str) -> str:
    needle = f"{prefix}:"
    for tag in tags:
        if tag.startswith(needle):
            return tag[len(needle) :]
    return "unknown"


def run_corpus_field_lift(
    corpus_root: Path,
    *,
    windows: tuple[int, ...] = (5, 20),
    field_runs: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Evaluate which Corpus v2 fields move lexical candidate recall."""

    qrels = qrels_from_corpus(corpus_root)
    runs = field_runs or DEFAULT_FIELD_RUNS
    report: dict[str, Any] = {
        "schema_version": 1,
        "corpus_root": str(corpus_root),
        "query_count": len(qrels),
        "windows": list(windows),
        "field_runs": {},
        "notes": [
            "concept_id and expected_queries are measured through qrel generation.",
            "doc_role and level are retained as metadata/routing fields; this lexical field-lift report does not claim standalone lift for them.",
        ],
    }
    for run_name, fields in runs.items():
        documents = corpus_v2_documents(corpus_root, fields=fields)
        report["field_runs"][run_name] = {
            "fields": list(fields),
            "document_count": len(documents),
            "summary": _evaluate_field_run(documents, qrels, windows=windows),
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--window", type=int, action="append", default=None)
    args = parser.parse_args(argv)

    report = run_corpus_field_lift(
        args.corpus_root,
        windows=tuple(args.window or [5, 20]),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        "wrote Corpus v2 field-lift report "
        f"({report['query_count']} qrels) to {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
