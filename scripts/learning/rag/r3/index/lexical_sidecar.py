"""Prebuilt lexical sidecar artifact for R3 local serving."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scripts.learning.rag import indexer

from ..candidate import R3Document
from .lexical_store import LEXICAL_FIELDS, LexicalStore
from .runtime_loader import load_lance_documents


SIDECAR_FILENAME = "r3_lexical_sidecar.json"
SCHEMA_VERSION = 1
ARTIFACT_KIND = "r3_lexical_sidecar"
_SIDECAR_CACHE: dict[tuple[str, str, int], "LoadedLexicalSidecar"] = {}


@dataclass(frozen=True)
class LoadedLexicalSidecar:
    store: LexicalStore
    metadata: dict[str, Any]


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return str(value)


def _sidecar_path(index_root: Path | str, output: Path | None = None) -> Path:
    return output or (Path(index_root) / SIDECAR_FILENAME)


def _document_blob(
    document: R3Document,
    store: LexicalStore,
    *,
    include_body: bool,
) -> dict[str, Any]:
    metadata = dict(document.metadata)
    if include_body and document.body and not metadata.get("body"):
        metadata["body"] = document.body
    if document.aliases and not metadata.get("aliases"):
        metadata["aliases"] = document.aliases
    field_terms = store.field_terms_for(document)
    if not include_body:
        metadata.pop("body", None)
        field_terms = {**field_terms, "body": ()}
    return {
        "path": document.path,
        "chunk_id": document.chunk_id,
        "title": document.title,
        "section_title": document.section_title,
        "body": document.body if include_body else "",
        "aliases": list(document.aliases),
        "signals": list(document.signals),
        "metadata": _jsonable(metadata),
        "field_terms": {
            field: list(field_terms.get(field, ()))
            for field in LEXICAL_FIELDS
        },
    }


def build_sidecar_payload(
    documents: Iterable[R3Document],
    *,
    manifest: dict[str, Any],
    include_body: bool = False,
) -> dict[str, Any]:
    docs = tuple(
        documents
        if include_body
        else (
            R3Document(
                path=document.path,
                chunk_id=document.chunk_id,
                title=document.title,
                section_title=document.section_title,
                body="",
                aliases=document.aliases,
                dense_vector=document.dense_vector,
                sparse_terms=document.sparse_terms,
                signals=document.signals,
                metadata={
                    key: value
                    for key, value in document.metadata.items()
                    if key != "body"
                },
            )
            for document in documents
        )
    )
    store = LexicalStore.from_documents(docs)
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_hash": manifest.get("corpus_hash"),
        "row_count": manifest.get("row_count"),
        "document_count": len(docs),
        "fields": list(LEXICAL_FIELDS),
        "body_terms_included": include_body,
        "documents": [
            _document_blob(document, store, include_body=include_body)
            for document in docs
        ],
    }


def write_lexical_sidecar(
    index_root: Path | str,
    *,
    output: Path | None = None,
    documents: Iterable[R3Document] | None = None,
    manifest: dict[str, Any] | None = None,
    include_body: bool = False,
) -> Path:
    root = Path(index_root)
    index_manifest = manifest or indexer.read_manifest_v3(root)
    docs = tuple(documents) if documents is not None else tuple(load_lance_documents(root))
    payload = build_sidecar_payload(
        docs,
        manifest=index_manifest,
        include_body=include_body,
    )
    out_path = _sidecar_path(root, output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _SIDECAR_CACHE.clear()
    return out_path


def _document_from_blob(blob: dict[str, Any]) -> R3Document:
    metadata = dict(blob.get("metadata") or {})
    body = str(blob.get("body") or metadata.get("body") or "")
    aliases = tuple(str(item) for item in blob.get("aliases") or metadata.get("aliases") or ())
    return R3Document(
        path=str(blob["path"]),
        chunk_id=blob.get("chunk_id"),
        title=str(blob.get("title") or ""),
        section_title=str(blob.get("section_title") or ""),
        body=body,
        aliases=aliases,
        signals=tuple(str(item) for item in blob.get("signals") or ()),
        metadata=metadata,
    )


def _load_payload(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"lexical sidecar is corrupt: {path}: {exc}") from exc


def load_lexical_sidecar(index_root: Path | str) -> LoadedLexicalSidecar | None:
    root = Path(index_root)
    path = root / SIDECAR_FILENAME
    if not path.exists():
        return None
    manifest = indexer.read_manifest_v3(root)
    stat = path.stat()
    cache_key = (
        str(path.resolve()),
        str(manifest.get("corpus_hash")),
        stat.st_mtime_ns,
    )
    cached = _SIDECAR_CACHE.get(cache_key)
    if cached is not None:
        return cached

    payload = _load_payload(path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported lexical sidecar schema: {payload.get('schema_version')!r}"
        )
    if payload.get("artifact_kind") != ARTIFACT_KIND:
        raise ValueError(f"not an R3 lexical sidecar: {path}")
    if payload.get("corpus_hash") != manifest.get("corpus_hash"):
        return None
    if payload.get("row_count") != manifest.get("row_count"):
        return None

    documents = tuple(_document_from_blob(blob) for blob in payload.get("documents") or ())
    field_terms = {}
    for document, blob in zip(documents, payload.get("documents") or ()):
        fields = blob.get("field_terms") or {}
        for field in LEXICAL_FIELDS:
            field_terms[(document.path, document.chunk_id, field)] = tuple(
                str(term) for term in fields.get(field) or ()
            )
    loaded = LoadedLexicalSidecar(
        store=LexicalStore.from_precomputed(documents, field_terms),
        metadata={
            "path": str(path),
            "schema_version": payload.get("schema_version"),
            "corpus_hash": payload.get("corpus_hash"),
            "row_count": payload.get("row_count"),
            "document_count": len(documents),
            "fields": list(payload.get("fields") or ()),
            "bytes": stat.st_size,
        },
    )
    _SIDECAR_CACHE[cache_key] = loaded
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--include-body",
        action="store_true",
        help="Include full body text and body lexical terms. Default ships metadata terms only.",
    )
    args = parser.parse_args(argv)

    path = write_lexical_sidecar(
        args.index_root,
        output=args.out,
        include_body=args.include_body,
    )
    payload = _load_payload(path)
    print(json.dumps({
        "artifact_kind": ARTIFACT_KIND,
        "path": str(path),
        "schema_version": payload.get("schema_version"),
        "corpus_hash": payload.get("corpus_hash"),
        "row_count": payload.get("row_count"),
        "document_count": payload.get("document_count"),
        "body_terms_included": payload.get("body_terms_included"),
        "bytes": path.stat().st_size,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
