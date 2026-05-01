"""Load current runtime indexes into R3 prototype document records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.learning.rag import indexer

from ..candidate import R3Document
from ..tokenization import tokenize_text

_DOCUMENT_CACHE: dict[tuple[str, str, str, str, str], list[R3Document]] = {}


def load_legacy_documents(index_root: Path | str) -> list[R3Document]:
    """Read the legacy SQLite chunks table as R3Document records."""

    conn = indexer.open_readonly(index_root)
    try:
        rows = conn.execute(
            """
            SELECT chunk_id, path, title, category, section_title, body,
                   anchors, difficulty
            FROM chunks
            ORDER BY id
            """
        ).fetchall()
    finally:
        conn.close()

    documents: list[R3Document] = []
    for chunk_id, path, title, category, section_title, body, anchors_json, difficulty in rows:
        try:
            anchors = tuple(json.loads(anchors_json or "[]"))
        except json.JSONDecodeError:
            anchors = ()
        documents.append(
            R3Document(
                path=str(path),
                chunk_id=str(chunk_id),
                title=str(title),
                section_title=str(section_title),
                body=str(body),
                aliases=tuple(str(anchor) for anchor in anchors),
                signals=(f"category:{category}",),
                metadata={
                    "category": category,
                    "difficulty": difficulty,
                    "index_backend": "legacy",
                },
            )
        )
    return documents


def _plain_list(value: Any) -> list:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return list(value.tolist())
    return list(value)


def _parse_json_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "[]")
        except json.JSONDecodeError:
            parsed = []
    else:
        parsed = _plain_list(value)
    return tuple(str(item) for item in parsed if str(item))


def _records_from_lance_table(
    table,
    *,
    query: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    columns = [
        "chunk_id",
        "path",
        "title",
        "category",
        "difficulty",
        "section_path",
        "body",
        "search_terms",
        "anchors",
    ]
    if query:
        search = table.search(query, query_type="fts")
        if limit is not None:
            search = search.limit(limit)
        return search.to_list()
    try:
        frame = table.to_pandas(columns=columns)
    except TypeError:
        frame = table.to_pandas()
    return frame.to_dict("records")


def load_lance_documents(
    index_root: Path | str,
    *,
    query: str | None = None,
    limit: int | None = None,
) -> list[R3Document]:
    """Read the production LanceDB v3 table as lightweight R3 documents."""

    root = Path(index_root)
    manifest = indexer.read_manifest_v3(root)
    table = indexer.open_lance_table(root)
    cache_key = (
        str(root.resolve()),
        str(manifest.get("corpus_hash")),
        str(getattr(table, "version", "unknown")),
        query or "",
        str(limit or ""),
    )
    cached = _DOCUMENT_CACHE.get(cache_key)
    if cached is not None:
        return cached

    documents: list[R3Document] = []
    for row in _records_from_lance_table(table, query=query, limit=limit):
        anchors = _parse_json_list(row.get("anchors"))
        section_path = _parse_json_list(row.get("section_path"))
        section_title = section_path[-1] if section_path else ""
        search_terms = str(row.get("search_terms") or "")
        sparse_terms = {term: 1.0 for term in tokenize_text(search_terms)}
        category = str(row.get("category") or "unknown")
        documents.append(
            R3Document(
                path=str(row.get("path") or ""),
                chunk_id=str(row.get("chunk_id") or ""),
                title=str(row.get("title") or ""),
                section_title=section_title,
                body=str(row.get("body") or ""),
                aliases=anchors,
                sparse_terms=sparse_terms,
                signals=(f"category:{category}",),
                metadata={
                    "category": category,
                    "difficulty": row.get("difficulty"),
                    "index_backend": "lance",
                },
            )
        )
    _DOCUMENT_CACHE.clear()
    _DOCUMENT_CACHE[cache_key] = documents
    return documents


def load_runtime_documents(
    index_root: Path | str,
    *,
    query: str | None = None,
    limit: int | None = None,
) -> list[R3Document]:
    """Load R3 documents from the current runtime index format."""

    try:
        manifest = indexer.load_manifest(index_root)
    except Exception:
        return load_legacy_documents(index_root)
    if manifest.get("index_version") == indexer.LANCE_INDEX_VERSION:
        return load_lance_documents(index_root, query=query, limit=limit)
    return load_legacy_documents(index_root)
