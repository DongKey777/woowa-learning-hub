"""Runtime index provenance helpers for RAG eval entrypoints.

The eval CLIs must be able to compare a legacy v2 archive against the
current LanceDB v3 production root without relying on process defaults.
This module keeps that manifest parsing in one place so baseline-only,
reranker A/B, and future cutover tooling record the same provenance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.learning.rag import indexer


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_LOCK = REPO_ROOT / "config" / "rag_models.json"


@dataclass(frozen=True)
class RuntimeIndexInfo:
    """Resolved runtime identity for one on-disk RAG index."""

    index_root: Path
    backend: str
    manifest: dict[str, Any]
    corpus_hash: str
    index_version: int
    embedding_model: str
    model_revision: str | None
    embedding_dim: int
    encoder: dict[str, Any]
    lancedb: dict[str, Any]
    modalities: tuple[str, ...]


def detect_backend(index_root: Path | str) -> str:
    """Return ``legacy`` or ``lance`` from the manifest version."""
    manifest = indexer.load_manifest(index_root)
    return "lance" if int(manifest.get("index_version", 0)) == indexer.LANCE_INDEX_VERSION else "legacy"


def resolve_runtime_index_info(
    index_root: Path | str,
    *,
    backend: str = "auto",
    model_lock_path: Path | str = DEFAULT_MODEL_LOCK,
) -> RuntimeIndexInfo:
    """Load v2/v3 manifest identity and normalise it for eval manifests."""
    root = Path(index_root)
    if backend not in ("auto", "legacy", "lance"):
        raise ValueError(f"unknown backend: {backend}")

    raw = indexer.load_manifest(root)
    detected = "lance" if int(raw.get("index_version", 0)) == indexer.LANCE_INDEX_VERSION else "legacy"
    resolved_backend = detected if backend == "auto" else backend
    if resolved_backend != detected:
        raise ValueError(
            f"backend={resolved_backend!r} does not match index manifest "
            f"version={raw.get('index_version')!r} at {root}"
        )

    if resolved_backend == "legacy":
        return RuntimeIndexInfo(
            index_root=root,
            backend="legacy",
            manifest=raw,
            corpus_hash=str(raw["corpus_hash"]),
            index_version=int(raw["index_version"]),
            embedding_model=str(raw["embed_model"]),
            model_revision=None,
            embedding_dim=int(raw["embed_dim"]),
            encoder={},
            lancedb={},
            modalities=(),
        )

    manifest = indexer.read_manifest_v3(root)
    encoder = dict(manifest.get("encoder") or {})
    lancedb = dict(manifest.get("lancedb") or {})
    model_id = str(encoder.get("model_id") or "")
    if not model_id:
        raise ValueError(f"v3 manifest missing encoder.model_id: {root / indexer.MANIFEST_NAME}")

    return RuntimeIndexInfo(
        index_root=root,
        backend="lance",
        manifest=manifest,
        corpus_hash=str(manifest["corpus_hash"]),
        index_version=int(manifest["index_version"]),
        embedding_model=model_id,
        model_revision=str(encoder.get("model_version") or "") or None,
        embedding_dim=_resolve_dense_dim(
            manifest,
            model_lock_path=Path(model_lock_path),
        ),
        encoder=encoder,
        lancedb=lancedb,
        modalities=tuple(str(m) for m in manifest.get("modalities") or ()),
    )


def _resolve_dense_dim(manifest: dict[str, Any], *, model_lock_path: Path) -> int:
    encoder = dict(manifest.get("encoder") or {})
    for key in ("dense_dim", "embedding_dim"):
        value = encoder.get(key)
        if isinstance(value, int) and value > 0:
            return value

    locked = _dense_dim_from_model_lock(manifest, model_lock_path=model_lock_path)
    if locked is not None:
        return locked

    # Backward compatibility for R2 artifacts built before dense_dim was
    # added to the v3 manifest. Keep this narrow to avoid silently accepting
    # unknown encoders.
    if encoder.get("model_id") == "BAAI/bge-m3":
        return 1024

    raise ValueError(
        "v3 manifest missing encoder.dense_dim and no matching model lock "
        f"entry was found for encoder.model_id={encoder.get('model_id')!r}"
    )


def _dense_dim_from_model_lock(
    manifest: dict[str, Any],
    *,
    model_lock_path: Path,
) -> int | None:
    if not model_lock_path.exists():
        return None
    try:
        lock = json.loads(model_lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    encoder = dict(manifest.get("encoder") or {})
    locked_encoder = dict(lock.get("encoder") or {})
    locked_index = dict(lock.get("index") or {})
    if locked_encoder.get("model_id") != encoder.get("model_id"):
        return None

    # A matching corpus hash is the strongest proof that this lock describes
    # the exact production artifact. If the lock omits the hash, keep the
    # model-id match as a weaker compatibility fallback for test fixtures.
    locked_hash = locked_index.get("corpus_hash")
    if locked_hash and locked_hash != manifest.get("corpus_hash"):
        return None

    dense_dim = locked_encoder.get("dense_dim")
    return int(dense_dim) if isinstance(dense_dim, int) and dense_dim > 0 else None
