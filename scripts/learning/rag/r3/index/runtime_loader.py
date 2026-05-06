"""Load current runtime indexes into R3 prototype document records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.learning.rag import indexer

from ..candidate import Candidate, R3Document
from ..query_plan import QUERY_PLAN_VERSION, normalize_query
from ..tokenization import tokenize_text

_DOCUMENT_CACHE: dict[tuple[str, str, str, str, str, str], list[R3Document]] = {}
_MAX_QUERY_DOCUMENT_CACHE_ENTRIES = 32
_SPARSE_QUERY_ENCODER_CACHE: dict[str, Any] = {}
_QUERY_ENCODING_CACHE: dict[
    tuple[str, str, str, tuple[str, ...], str, str],
    dict[str, Any],
] = {}
_MAX_QUERY_ENCODING_CACHE_ENTRIES = 256


def _normalize_optional_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = str(value)
    return "" if text.casefold() == "nan" else text


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
                    "body": body,
                    "aliases": tuple(str(anchor) for anchor in anchors),
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


def _parse_sparse_terms(row: dict[str, Any]) -> dict[str, float]:
    sparse_vec = row.get("sparse_vec") or {}
    indices = _plain_list(sparse_vec.get("indices") if isinstance(sparse_vec, dict) else [])
    values = _plain_list(sparse_vec.get("values") if isinstance(sparse_vec, dict) else [])
    terms: dict[str, float] = {}
    for token_id, weight in zip(indices, values):
        try:
            normalized_id = str(int(token_id))
            normalized_weight = float(weight)
        except (TypeError, ValueError):
            continue
        if normalized_weight > 0:
            terms[normalized_id] = normalized_weight
    if terms:
        return terms
    search_terms = str(row.get("search_terms") or "")
    return {term: 1.0 for term in tokenize_text(search_terms)}


def _dense_query_vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    try:
        if getattr(value, "ndim", 1) == 2:
            value = value[0]
    except Exception:
        pass
    if hasattr(value, "tolist"):
        value = value.tolist()
    try:
        return [float(item) for item in value]
    except TypeError:
        return None


def _lance_table_column_names(table) -> set[str] | None:
    try:
        schema = getattr(table, "schema", None)
        if callable(schema):
            schema = schema()
        names = getattr(schema, "names", None)
        if names is not None:
            return {str(name) for name in names}
    except Exception:
        return None
    return None


def _select_existing_columns(table, columns: list[str]) -> list[str]:
    names = _lance_table_column_names(table)
    if names is None:
        return columns
    return [column for column in columns if column in names]


def _records_from_lance_table(
    table,
    *,
    query: str | None = None,
    limit: int | None = None,
    sparse_sidecar: bool = False,
) -> list[dict]:
    columns = [
        "chunk_id",
        "path",
        "title",
        "category",
        "difficulty",
        "concept_id",
        "doc_role",
        "level",
        "section_path",
        "search_terms",
        "anchors",
        "sparse_vec",
    ]
    if not sparse_sidecar:
        columns.insert(columns.index("search_terms"), "body")
    if query:
        search = table.search(query, query_type="fts")
        if limit is not None:
            search = search.limit(limit)
        return search.to_list()
    selected_columns = _select_existing_columns(table, columns)
    try:
        frame = table.to_pandas(columns=selected_columns)
    except TypeError:
        frame = table.to_pandas()
    except Exception:
        legacy_columns = [
            column
            for column in columns
            if column not in {"concept_id", "doc_role", "level"}
        ]
        try:
            frame = table.to_pandas(columns=_select_existing_columns(table, legacy_columns))
        except TypeError:
            frame = table.to_pandas()
    return frame.to_dict("records")


def _lance_row_score(row: dict[str, Any], rank: int) -> float:
    if "_score" in row:
        return float(row["_score"])
    if "_distance" in row:
        return 1.0 / (1.0 + max(float(row["_distance"]), 0.0))
    return 1.0 / rank


def _cache_lance_documents(
    cache_key: tuple[str, str, str, str, str, str],
    documents: list[R3Document],
) -> None:
    _DOCUMENT_CACHE[cache_key] = documents
    query_keys = [
        key
        for key in _DOCUMENT_CACHE
        if key[-1] == "documents" and key[3]
    ]
    while len(query_keys) > _MAX_QUERY_DOCUMENT_CACHE_ENTRIES:
        oldest = query_keys.pop(0)
        _DOCUMENT_CACHE.pop(oldest, None)


def load_lance_documents(
    index_root: Path | str,
    *,
    query: str | None = None,
    limit: int | None = None,
    sparse_sidecar: bool = False,
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
        "sparse_sidecar" if sparse_sidecar else "documents",
    )
    cached = _DOCUMENT_CACHE.get(cache_key)
    if cached is not None:
        return cached

    documents: list[R3Document] = []
    for row in _records_from_lance_table(
        table,
        query=query,
        limit=limit,
        sparse_sidecar=sparse_sidecar,
    ):
        anchors = _parse_json_list(row.get("anchors"))
        section_path = _parse_json_list(row.get("section_path"))
        section_title = section_path[-1] if section_path else ""
        sparse_terms = _parse_sparse_terms(row)
        category = _normalize_optional_text(row.get("category")) or "unknown"
        concept_id = _normalize_optional_text(row.get("concept_id"))
        doc_role = _normalize_optional_text(row.get("doc_role"))
        level = _normalize_optional_text(row.get("level"))
        signals = [f"category:{category}"]
        if doc_role:
            signals.append(f"doc_role:{doc_role}")
        if level:
            signals.append(f"level:{level}")
        documents.append(
            R3Document(
                path=str(row.get("path") or ""),
                chunk_id=str(row.get("chunk_id") or ""),
                title=str(row.get("title") or ""),
                section_title=section_title,
                body=str(row.get("body") or ""),
                aliases=anchors,
                sparse_terms=sparse_terms,
                signals=tuple(signals),
                metadata={
                    "category": category,
                    "difficulty": row.get("difficulty"),
                    "concept_id": concept_id or None,
                    "doc_role": doc_role or None,
                    "level": level or None,
                    "index_backend": "lance",
                    "body": str(row.get("body") or ""),
                    "aliases": anchors,
                },
            )
        )
    _cache_lance_documents(cache_key, documents)
    return documents


def load_runtime_sparse_documents(index_root: Path | str) -> list[R3Document]:
    """Load the full sparse sidecar candidate set for first-stage retrieval."""

    try:
        manifest = indexer.load_manifest(index_root)
    except Exception:
        return load_legacy_documents(index_root)
    if manifest.get("index_version") == indexer.LANCE_INDEX_VERSION:
        return load_lance_documents(index_root, sparse_sidecar=True)
    return load_legacy_documents(index_root)


def encode_runtime_query(
    index_root: Path | str,
    query: str,
    *,
    modalities: tuple[str, ...] = ("dense", "sparse"),
    query_plan_version: str = QUERY_PLAN_VERSION,
) -> dict[str, Any]:
    """Encode a query with the index encoder for R3 first-stage retrieval.

    Sparse token ids are returned as strings so they share the same term space
    as ``R3Document.sparse_terms`` and Qdrant sparse payload generation.
    Encodings are cached by index identity, modalities, normalized query, and
    QueryPlan version so warm daemon sessions do not re-encode repeated prompts.
    """

    root = Path(index_root)
    manifest = indexer.read_manifest_v3(root)
    encoder_info = manifest.get("encoder", {})
    model_id = str(encoder_info.get("model_id") or "")
    model_version = str(encoder_info.get("model_version") or model_id)
    encoder_cache_key = model_version or model_id
    if model_id != "BAAI/bge-m3":
        return {}
    encoding_cache_key = (
        str(root),
        str(manifest.get("corpus_hash") or ""),
        encoder_cache_key,
        tuple(modalities),
        normalize_query(query),
        query_plan_version,
    )
    cached = _QUERY_ENCODING_CACHE.get(encoding_cache_key)
    if cached is not None:
        return _copy_query_encoding(cached)

    encoder = _SPARSE_QUERY_ENCODER_CACHE.get(encoder_cache_key)
    if encoder is None:
        from scripts.learning.rag.encoders.bge_m3 import BgeM3Encoder

        encoder = BgeM3Encoder(model_id=model_id)
        _SPARSE_QUERY_ENCODER_CACHE[encoder_cache_key] = encoder
    try:
        encoding = encoder.encode_query(query, modalities=modalities)
    except Exception:
        return {}
    out: dict[str, Any] = {}
    if "dense" in modalities:
        dense_vector = _dense_query_vector(encoding.get("dense"))
        if dense_vector is not None:
            out["dense"] = dense_vector
    sparse_list = encoding.get("sparse") or []
    if "sparse" in modalities and sparse_list:
        out["sparse_terms"] = {
            str(int(token_id)): float(weight)
            for token_id, weight in sparse_list[0].items()
        }
    _QUERY_ENCODING_CACHE[encoding_cache_key] = _copy_query_encoding(out)
    while len(_QUERY_ENCODING_CACHE) > _MAX_QUERY_ENCODING_CACHE_ENTRIES:
        oldest = next(iter(_QUERY_ENCODING_CACHE))
        _QUERY_ENCODING_CACHE.pop(oldest, None)
    return _copy_query_encoding(out)


def _copy_query_encoding(encoding: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "dense" in encoding:
        dense = encoding["dense"]
        out["dense"] = list(dense) if isinstance(dense, list) else dense
    if "sparse_terms" in encoding:
        out["sparse_terms"] = dict(encoding["sparse_terms"])
    return out


def encode_runtime_sparse_query(index_root: Path | str, query: str) -> dict[str, float]:
    """Encode a query and return only BGE sparse token ids."""

    encoding = encode_runtime_query(index_root, query, modalities=("sparse",))
    return dict(encoding.get("sparse_terms") or {})


def load_runtime_dense_candidates(
    index_root: Path | str,
    query_vector: Any,
    *,
    limit: int = 100,
) -> list[Candidate]:
    """Return independent dense candidates from the Lance vector index."""

    dense_query = _dense_query_vector(query_vector)
    if dense_query is None:
        return []
    try:
        manifest = indexer.load_manifest(index_root)
    except Exception:
        return []
    if manifest.get("index_version") != indexer.LANCE_INDEX_VERSION:
        return []
    table = indexer.open_lance_table(index_root)
    try:
        rows = (
            table.search(dense_query, vector_column_name="dense_vec")
            .limit(limit)
            .to_list()
        )
    except Exception:
        return []
    candidates: list[Candidate] = []
    for rank, row in enumerate(rows, start=1):
        anchors = _parse_json_list(row.get("anchors"))
        section_path = _parse_json_list(row.get("section_path"))
        section_title = section_path[-1] if section_path else ""
        category = _normalize_optional_text(row.get("category")) or "unknown"
        concept_id = _normalize_optional_text(row.get("concept_id"))
        doc_role = _normalize_optional_text(row.get("doc_role"))
        level = _normalize_optional_text(row.get("level"))
        path = str(row.get("path") or "")
        if not path:
            continue
        candidates.append(
            Candidate(
                path=path,
                chunk_id=str(row.get("chunk_id") or ""),
                retriever="dense",
                rank=rank,
                score=_lance_row_score(row, rank),
                title=str(row.get("title") or ""),
                section_title=section_title,
                metadata={
                    "document": {
                        "category": category,
                        "difficulty": row.get("difficulty"),
                        "concept_id": concept_id or None,
                        "doc_role": doc_role or None,
                        "level": level or None,
                        "index_backend": "lance",
                        "body": str(row.get("body") or ""),
                        "aliases": anchors,
                    }
                },
            )
        )
    return candidates


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
