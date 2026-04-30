"""Run manifest schema + dataclass + JSON Schema validation.

Plan §P1.1 step 4: every run report MUST carry a manifest with the
fields below so it is unambiguous which commit / model / device the
metrics came from.

Required fields:
    corpus_hash, index_version, embedding_model, model_revision,
    embedding_dim, device, reranker_model, fusion_weights, top_k, mode,
    latency_p50_warm, latency_p95_warm, cold_start_ms

Optional H7 fields:
    backend, modalities, encoder, lancedb

The dataclass and JSON Schema are kept in lock-step — the schema is
the contract for validating untrusted dicts (loaded reports), the
dataclass is the in-memory builder used by runner code.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

# ---------------------------------------------------------------------------
# JSON Schema (validates untrusted manifest blobs)
# ---------------------------------------------------------------------------

MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "RunManifest",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "corpus_hash",
        "index_version",
        "embedding_model",
        "model_revision",
        "embedding_dim",
        "device",
        "reranker_model",
        "fusion_weights",
        "top_k",
        "mode",
        "latency_p50_warm",
        "latency_p95_warm",
        "cold_start_ms",
    ],
    "properties": {
        "corpus_hash": {"type": "string", "minLength": 1},
        "index_version": {"type": "integer", "minimum": 1},
        "embedding_model": {"type": "string", "minLength": 1},
        "model_revision": {
            "anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}],
        },
        "embedding_dim": {"type": "integer", "minimum": 1},
        "device": {"type": "string", "enum": ["cpu", "mps", "cuda", "auto"]},
        "reranker_model": {
            "anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}],
        },
        "fusion_weights": {
            "type": "object",
            "additionalProperties": False,
            "required": ["k", "w_bm25", "w_dense"],
            "properties": {
                "k": {"type": "integer", "minimum": 1},
                "w_bm25": {"type": "number", "minimum": 0},
                "w_dense": {"type": "number", "minimum": 0},
            },
        },
        "top_k": {"type": "integer", "minimum": 1},
        "mode": {"type": "string", "enum": ["cheap", "full"]},
        "latency_p50_warm": {"type": "number", "minimum": 0},
        "latency_p95_warm": {"type": "number", "minimum": 0},
        "cold_start_ms": {"type": "number", "minimum": 0},
        "backend": {"type": "string", "enum": ["legacy", "lance"]},
        "modalities": {
            "type": "array",
            "items": {"enum": ["dense", "sparse", "colbert", "fts"]},
            "uniqueItems": True,
        },
        "encoder": {
            "type": "object",
            "additionalProperties": True,
        },
        "lancedb": {
            "type": "object",
            "additionalProperties": True,
        },
    },
}

DEFAULT_FUSION_WEIGHTS = {"k": 60, "w_bm25": 1.0, "w_dense": 1.0}
"""Mirrors the current static RRF in searcher.py:259-271. P3.2 will
auto-tune these and emit fusion_ab_report.json; P8 commits the chosen
weights to config/rag_fusion.json. Until then the runner injects this
default into manifests so reports stay schema-valid."""


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FusionWeights:
    k: int
    w_bm25: float
    w_dense: float

    @classmethod
    def default(cls) -> "FusionWeights":
        return cls(**DEFAULT_FUSION_WEIGHTS)

    def to_dict(self) -> dict[str, float | int]:
        return {"k": self.k, "w_bm25": self.w_bm25, "w_dense": self.w_dense}


@dataclass(frozen=True)
class RunManifest:
    """Per-run identity + measurement metadata."""

    corpus_hash: str
    index_version: int
    embedding_model: str
    model_revision: str | None
    embedding_dim: int
    device: str  # "cpu" | "mps" | "cuda" | "auto"
    reranker_model: str | None
    fusion_weights: FusionWeights
    top_k: int
    mode: str  # "cheap" | "full"
    latency_p50_warm: float
    latency_p95_warm: float
    cold_start_ms: float
    backend: str = "legacy"
    modalities: tuple[str, ...] = field(default_factory=tuple)
    encoder: dict[str, Any] = field(default_factory=dict)
    lancedb: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Conversion + validation
# ---------------------------------------------------------------------------

def manifest_to_dict(manifest: RunManifest) -> dict[str, Any]:
    """Serialise to a schema-valid dict. Validates before returning so
    runner code can't accidentally emit a non-conforming manifest."""
    blob = asdict(manifest)
    # asdict turns FusionWeights into nested dict already; ensure shape.
    blob["fusion_weights"] = manifest.fusion_weights.to_dict()
    blob["modalities"] = list(manifest.modalities)
    validate_manifest(blob)
    return blob


def dict_to_manifest(blob: dict[str, Any]) -> RunManifest:
    """Validate + materialise a manifest dict. Raises ValidationError if
    the blob doesn't match MANIFEST_SCHEMA."""
    validate_manifest(blob)
    fw = blob["fusion_weights"]
    return RunManifest(
        corpus_hash=blob["corpus_hash"],
        index_version=int(blob["index_version"]),
        embedding_model=blob["embedding_model"],
        model_revision=blob["model_revision"],
        embedding_dim=int(blob["embedding_dim"]),
        device=blob["device"],
        reranker_model=blob["reranker_model"],
        fusion_weights=FusionWeights(
            k=int(fw["k"]),
            w_bm25=float(fw["w_bm25"]),
            w_dense=float(fw["w_dense"]),
        ),
        top_k=int(blob["top_k"]),
        mode=blob["mode"],
        latency_p50_warm=float(blob["latency_p50_warm"]),
        latency_p95_warm=float(blob["latency_p95_warm"]),
        cold_start_ms=float(blob["cold_start_ms"]),
        backend=blob.get("backend", "legacy"),
        modalities=tuple(blob.get("modalities") or ()),
        encoder=dict(blob.get("encoder") or {}),
        lancedb=dict(blob.get("lancedb") or {}),
    )


def validate_manifest(blob: dict[str, Any]) -> None:
    """Validate a manifest dict against MANIFEST_SCHEMA. Raises
    jsonschema.ValidationError on mismatch.

    Use this at I/O boundaries — reading a saved manifest, accepting one
    over RPC, etc. Do not call from the dataclass constructor (that
    would create a circular dependency on the dict shape)."""
    jsonschema.validate(instance=blob, schema=MANIFEST_SCHEMA)


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> RunManifest:
    """Read a manifest JSON file, validate, return the dataclass."""
    blob = json.loads(path.read_text(encoding="utf-8"))
    return dict_to_manifest(blob)


def dump_manifest(manifest: RunManifest, path: Path) -> None:
    """Write the manifest JSON to ``path`` after validating."""
    blob = manifest_to_dict(manifest)
    path.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")
