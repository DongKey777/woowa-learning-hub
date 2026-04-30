"""CLI: build the CS RAG index.

Usage
-----
    bin/cs-index-build [--corpus knowledge/cs] [--out state/cs_rag]
                       [--force] [--mode auto|full|incremental]
                       [--backend legacy|lance]

The AI session — not the learner — runs this during the First-Run Protocol
or when cs_readiness.state != "ready".

Modes (plan §P5.6):
- ``auto`` (default): full rebuild if is_ready != ready, else
  incremental rebuild (re-encode only changed chunks).
- ``full``: force a full rebuild regardless of state. Use when the
  on-disk index is suspected corrupt or after embedding model swap.
- ``incremental``: force the incremental path. Falls back to full
  internally if the index is missing / model_id mismatch / schema
  bump (see incremental_indexer._full_rebuild_reason).

The legacy ``--force`` flag still works and means "full rebuild even
when ready"; equivalent to ``--mode full --force``.

Experimental LanceDB v3 backend:
- ``--backend lance`` explicitly builds the bge-m3/LanceDB index path.
- It is full-build only until the LanceDB incremental wrapper is implemented.
- Default remains ``legacy`` so First-Run Protocol and production readiness
  continue to use the SQLite/NPZ v2 path during the SOTA migration.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    # Fallback: two levels up (scripts/learning/cli_cs_index_build.py)
    return here.parents[2]


def _progress(stage: str, info: dict) -> None:
    # Korean status lines so the AI session can mirror them to the learner
    # without re-formatting.
    if stage == "load_corpus":
        print("[cs-index] 1/5 코퍼스 스캔 중…", flush=True)
    elif stage == "load_corpus_done":
        print(f"[cs-index] 1/5 코퍼스 스캔 완료 — chunks={info.get('chunk_count')}", flush=True)
    elif stage == "open_sqlite":
        print("[cs-index] 2/5 SQLite FTS5 인덱스 열기…", flush=True)
    elif stage == "insert_chunks":
        print(f"[cs-index] 3/5 메타/FTS 삽입 중 ({info.get('count')} chunks)…", flush=True)
    elif stage == "load_embedder":
        print(f"[cs-index] 4/5 임베딩 모델 로드 중 — {info.get('model')}", flush=True)
    elif stage == "encode":
        print(f"[cs-index] 4/5 임베딩 계산 중 ({info.get('count')} chunks, 수 분 소요)…", flush=True)
    elif stage == "encode_progress":
        done = info.get("done", 0)
        total = info.get("total", 0)
        pct = (done / total * 100) if total else 0
        eta_s = info.get("eta_s", 0)
        rate = info.get("rate_per_s", 0)
        # Format ETA as min:sec when long, raw seconds when short
        if eta_s >= 60:
            mins, secs = divmod(int(eta_s), 60)
            eta_str = f"{mins}m{secs:02d}s"
        else:
            eta_str = f"{eta_s:.1f}s"
        print(
            f"[cs-index] 4/5 임베딩 진행 — "
            f"{done}/{total} ({pct:.1f}%) "
            f"rate={rate}/s eta={eta_str}",
            flush=True,
        )
    elif stage == "write_dense":
        print(f"[cs-index] 5/5 dense 벡터 저장 — shape={info.get('shape')}", flush=True)
    elif stage == "write_lance":
        print(f"[cs-index] 5/6 LanceDB 테이블 작성 중 ({info.get('count')} chunks)…", flush=True)
    elif stage == "create_indices":
        print(f"[cs-index] 6/6 LanceDB 인덱스 생성 중 ({info.get('count')} chunks)…", flush=True)
    elif stage == "write_manifest":
        print(
            f"[cs-index] 5/5 manifest 저장 — row_count={info.get('row_count')}, "
            f"corpus_hash={info.get('corpus_hash', '')[:12]}…",
            flush=True,
        )
    else:
        print(f"[cs-index] {stage} {info}", flush=True)


def _default_production_embedder():
    """Production-side lazy SentenceTransformer factory bound to the
    embed model declared in indexer.EMBED_MODEL. Tests inject fakes
    via the ``embedder_factory`` parameter on ``main``."""
    from scripts.learning.rag import indexer  # noqa: WPS433
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer(indexer.EMBED_MODEL)


def _resolve_lance_device(raw: str) -> str:
    if raw != "auto":
        return raw
    try:
        import torch  # type: ignore

        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _resolve_lance_fp16(precision: str, device: str) -> bool:
    if precision == "fp16":
        return True
    if precision == "fp32":
        return False
    return device in {"mps", "cuda"}


def _default_lance_encoder(
    *,
    device: str = "auto",
    precision: str = "auto",
    max_length: int = 1024,
    batch_size: int = 64,
):
    """Production bge-m3 encoder factory for the explicit LanceDB backend."""
    from scripts.learning.rag.encoders.bge_m3 import BgeM3Encoder  # noqa: WPS433

    resolved_device = _resolve_lance_device(device)
    # FlagEmbedding accepts CPU as a plain string, but MPS/CUDA are more
    # reliable as an explicit device list. In this environment
    # ``devices="mps"`` raises a misleading macOS-version error while
    # ``devices=["mps"]`` works.
    devices = [resolved_device] if resolved_device in {"mps", "cuda"} else resolved_device
    return BgeM3Encoder(
        devices=devices,
        use_fp16=_resolve_lance_fp16(precision, resolved_device),
        max_length=max_length,
        batch_size=batch_size,
    )


def _parse_modalities(raw: str) -> tuple[str, ...]:
    allowed = {"dense", "sparse", "colbert", "fts"}
    modalities = tuple(part.strip() for part in raw.split(",") if part.strip())
    unknown = sorted(set(modalities) - allowed)
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown modalities: {', '.join(unknown)}; allowed: {', '.join(sorted(allowed))}"
        )
    if not modalities:
        raise argparse.ArgumentTypeError("at least one modality is required")
    return modalities


def _format_bytes(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


def _existing_disk_root(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def _estimate_lance_disk_budget(corpus_root: str, out_root: str) -> dict:
    """Estimate LanceDB v3 footprint before loading bge-m3.

    The estimate is intentionally conservative enough for an abort gate, not a
    precise storage model. It mirrors the H2 plan: dense vectors + learned
    sparse payload + candidate ColBERT storage + LanceDB overhead, then requires
    2x free space for safe rebuild/write amplification.
    """
    from scripts.learning.rag import corpus_loader  # noqa: WPS433

    chunk_count = len(corpus_loader.load_corpus(corpus_root))
    dense_bytes = chunk_count * 1024 * 4
    sparse_bytes = chunk_count * 120 * (4 + 4)
    colbert_bytes = chunk_count * 27 * 1024
    overhead_bytes = int((dense_bytes + sparse_bytes + colbert_bytes) * 0.10)
    total_bytes = dense_bytes + sparse_bytes + colbert_bytes + overhead_bytes
    required_free_bytes = total_bytes * 2
    disk_root = _existing_disk_root(Path(out_root).expanduser()).resolve()
    free_bytes = shutil.disk_usage(disk_root).free
    return {
        "chunk_count": chunk_count,
        "dense_bytes": dense_bytes,
        "sparse_bytes": sparse_bytes,
        "colbert_bytes": colbert_bytes,
        "overhead_bytes": overhead_bytes,
        "total_bytes": total_bytes,
        "required_free_bytes": required_free_bytes,
        "free_bytes": free_bytes,
        "disk_root": str(disk_root),
        "ok": free_bytes >= required_free_bytes,
    }


def _print_lance_disk_budget(budget: dict) -> None:
    print(
        f"[cs-index] disk budget estimate ({budget['chunk_count']} chunks):",
        flush=True,
    )
    print(f"  dense (1024 fp32):      {_format_bytes(budget['dense_bytes'])}", flush=True)
    print(f"  sparse (~120 nonzero):  {_format_bytes(budget['sparse_bytes'])}", flush=True)
    print(f"  colbert candidate data: {_format_bytes(budget['colbert_bytes'])}", flush=True)
    print(f"  LanceDB overhead (~10%): {_format_bytes(budget['overhead_bytes'])}", flush=True)
    print(f"  total estimate:         {_format_bytes(budget['total_bytes'])}", flush=True)
    marker = "✓" if budget["ok"] else "✗"
    print(
        f"  free at {budget['disk_root']}: {_format_bytes(budget['free_bytes'])} {marker}",
        flush=True,
    )


def _is_lance_ready(indexer_module, out_root: str) -> bool:
    try:
        indexer_module.read_manifest_v3(out_root)
        table = indexer_module.open_lance_table(out_root)
        table.count_rows()
    except Exception:
        return False
    return True


def _seed_lance_fingerprints(index_root: str, corpus_root: str, model_version: str) -> None:
    """Seed H5 fingerprint sidecar after an explicit LanceDB full build."""
    from scripts.learning.rag import corpus_loader  # noqa: WPS433
    from scripts.learning.rag import incremental_indexer  # noqa: WPS433

    chunks = corpus_loader.load_corpus(corpus_root)
    fingerprints = incremental_indexer.compute_chunk_fingerprints(chunks)
    incremental_indexer.atomic_save_model_chunk_hashes(
        index_root=index_root,
        model_version=model_version,
        fingerprints=fingerprints,
    )


def main(
    argv: list[str] | None = None,
    *,
    embedder_factory=None,
    lance_encoder_factory=None,
) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(description="Build the CS RAG index.")
    parser.add_argument(
        "--corpus",
        default=str(repo_root / "knowledge" / "cs"),
        help="Path to the CS corpus root (default: knowledge/cs).",
    )
    parser.add_argument(
        "--out",
        default=str(repo_root / "state" / "cs_rag"),
        help="Output index root (default: state/cs_rag).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild even if is_ready() reports ready (forces --mode full).",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "full", "incremental"),
        default="auto",
        help=(
            "Build mode (default: auto). "
            "auto: full when is_ready != ready, else incremental. "
            "full: always full rebuild. "
            "incremental: re-encode only changed chunks "
            "(falls back to full on schema/model mismatch)."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=("legacy", "lance"),
        default="legacy",
        help=(
            "Index backend (default: legacy). "
            "legacy: SQLite FTS5 + dense.npz v2. "
            "lance: experimental LanceDB v3 bge-m3 full build only."
        ),
    )
    parser.add_argument(
        "--encoder",
        choices=("bge-m3",),
        default="bge-m3",
        help="Encoder for --backend lance (default: bge-m3).",
    )
    parser.add_argument(
        "--modalities",
        type=_parse_modalities,
        default=("dense", "sparse", "colbert", "fts"),
        help="Comma-separated modalities for --backend lance.",
    )
    parser.add_argument(
        "--lance-colbert-dtype",
        choices=("float16", "float32"),
        default="float16",
        help="ColBERT token storage dtype for --backend lance.",
    )
    parser.add_argument(
        "--lance-device",
        choices=("auto", "cpu", "mps", "cuda"),
        default="auto",
        help="Device for bge-m3 LanceDB builds (default: auto prefers MPS/CUDA).",
    )
    parser.add_argument(
        "--lance-precision",
        choices=("auto", "fp16", "fp32"),
        default="auto",
        help="bge-m3 precision for LanceDB builds (default: auto uses fp16 on MPS/CUDA).",
    )
    parser.add_argument(
        "--lance-max-length",
        type=int,
        default=1024,
        help=(
            "Max token length for bge-m3 corpus/query encoding in LanceDB builds "
            "(default: 1024; CS chunks are capped at 1600 chars)."
        ),
    )
    parser.add_argument(
        "--lance-batch-size",
        type=int,
        default=64,
        help="Batch size for bge-m3 LanceDB corpus encoding (default: 64).",
    )
    args = parser.parse_args(argv)

    # Make scripts.* importable when invoked as a script.
    sys.path.insert(0, str(repo_root))

    from scripts.learning.rag import indexer  # noqa: WPS433
    from scripts.learning.rag import incremental_indexer  # noqa: WPS433

    readiness = indexer.is_ready(args.out, args.corpus)
    print(
        f"[cs-index] state={readiness.state} reason={readiness.reason}",
        flush=True,
    )

    # Resolve effective mode
    effective_mode = args.mode
    if args.force:
        effective_mode = "full"
    elif args.mode == "auto":
        # auto: ready → incremental (will short-circuit if no changes);
        # not ready → full
        if readiness.state == "ready":
            effective_mode = "incremental"
        else:
            effective_mode = "full"
    if args.backend == "lance" and args.mode == "auto" and not args.force:
        # v3 readiness is not the production readiness contract yet. Resolve
        # LanceDB auto mode against the v3 manifest/table explicitly instead
        # of reusing the legacy SQLite readiness result above.
        effective_mode = "incremental" if _is_lance_ready(indexer, args.out) else "full"

    if effective_mode == "full" and readiness.state == "ready" and not args.force:
        # Explicit --mode full but no actual reason to rebuild: still
        # rebuild (caller asked) but log clearly.
        print(
            "[cs-index] --mode full requested even though index is ready; "
            "proceeding with full rebuild",
            flush=True,
        )

    print(f"[cs-index] mode={effective_mode}", flush=True)
    start = time.time()
    try:
        if args.backend == "lance":
            lance_device = _resolve_lance_device(args.lance_device)
            lance_fp16 = _resolve_lance_fp16(args.lance_precision, lance_device)
            print(
                f"[cs-index] lance runtime — device={lance_device} fp16={lance_fp16}",
                flush=True,
            )
            if effective_mode == "full":
                budget = _estimate_lance_disk_budget(args.corpus, args.out)
                _print_lance_disk_budget(budget)
                if not budget["ok"]:
                    print(
                        "[cs-index] ERROR: INSUFFICIENT_DISK for LanceDB rebuild "
                        f"(need >= {_format_bytes(budget['required_free_bytes'])}, "
                        f"free {_format_bytes(budget['free_bytes'])})",
                        file=sys.stderr,
                        flush=True,
                    )
                    return 2
                factory = lance_encoder_factory or (
                    lambda: _default_lance_encoder(
                        device=lance_device,
                        precision=args.lance_precision,
                        max_length=args.lance_max_length,
                        batch_size=args.lance_batch_size,
                    )
                )
                encoder = factory()
                print(
                    "[cs-index] lance encoder — "
                    f"devices={getattr(encoder, 'devices', None)!r} "
                    f"use_fp16={getattr(encoder, 'use_fp16', None)!r} "
                    f"max_length={getattr(encoder, 'max_length', None)!r} "
                    f"batch_size={getattr(encoder, 'batch_size', None)!r}",
                    flush=True,
                )
                manifest = indexer.build_lance_index(
                    index_root=args.out,
                    corpus_root=args.corpus,
                    encoder=encoder,
                    modalities=args.modalities,
                    progress=_progress,
                    colbert_dtype=args.lance_colbert_dtype,
                )
                try:
                    model_version = manifest.get("encoder", {}).get("model_version")
                    if not model_version:
                        model_version = encoder.model_version
                    _seed_lance_fingerprints(
                        args.out,
                        args.corpus,
                        model_version,
                    )
                except Exception as exc:  # noqa: BLE001 - safe over-work on next run
                    print(
                        f"[cs-index] WARN: fingerprint sidecar seed failed: {type(exc).__name__}: {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
                row_count = manifest["row_count"]
                mode_descriptor = "lance-full"
                extra_summary = (
                    f" — encoder={manifest.get('encoder', {}).get('model_version', args.encoder)} "
                    f"modalities={','.join(args.modalities)}"
                )
            else:
                factory = lance_encoder_factory or (
                    lambda: _default_lance_encoder(
                        device=lance_device,
                        precision=args.lance_precision,
                        max_length=args.lance_max_length,
                        batch_size=args.lance_batch_size,
                    )
                )
                encoder = factory()
                print(
                    "[cs-index] lance encoder — "
                    f"devices={getattr(encoder, 'devices', None)!r} "
                    f"use_fp16={getattr(encoder, 'use_fp16', None)!r} "
                    f"max_length={getattr(encoder, 'max_length', None)!r} "
                    f"batch_size={getattr(encoder, 'batch_size', None)!r}",
                    flush=True,
                )
                result = incremental_indexer.incremental_lance_build_index(
                    encoder=encoder,
                    index_root=args.out,
                    corpus_root=args.corpus,
                    modalities=args.modalities,
                    progress=_progress,
                    colbert_dtype=args.lance_colbert_dtype,
                )
                row_count = result.manifest["row_count"]
                mode_descriptor = f"lance-{result.mode}"
                stats = result.diff_stats
                extra_summary = (
                    f" — added={stats.get('added', 0)} "
                    f"modified={stats.get('modified', 0)} "
                    f"deleted={stats.get('deleted', 0)} "
                    f"unchanged={stats.get('unchanged', 0)} "
                    f"encoded={result.encoded_chunk_count}"
                )
                if result.lance_version_before is not None:
                    extra_summary += (
                        f" lance_version={result.lance_version_before}"
                        f"→{result.lance_version_after}"
                    )
                if result.fallback_reason:
                    extra_summary += f" (fallback: {result.fallback_reason})"
        elif effective_mode == "full":
            manifest = indexer.build_index(
                index_root=args.out,
                corpus_root=args.corpus,
                progress=_progress,
            )
            row_count = manifest["row_count"]
            mode_descriptor = "full"
            extra_summary = ""
        else:
            # incremental
            factory = embedder_factory or _default_production_embedder
            model = factory()
            result = incremental_indexer.incremental_build_index(
                model=model,
                model_id=indexer.EMBED_MODEL,
                embed_dim=indexer.EMBED_DIM,
                index_root=args.out,
                corpus_root=args.corpus,
                progress=_progress,
            )
            row_count = result.manifest["row_count"]
            mode_descriptor = result.mode  # "incremental" or "full" (fallback)
            stats = result.diff_stats
            extra_summary = (
                f" — added={stats.get('added', 0)} "
                f"modified={stats.get('modified', 0)} "
                f"deleted={stats.get('deleted', 0)} "
                f"unchanged={stats.get('unchanged', 0)} "
                f"encoded={result.encoded_chunk_count}"
            )
            if result.fallback_reason:
                extra_summary += f" (fallback: {result.fallback_reason})"
    except indexer.IndexDependencyMissing as exc:
        print(f"[cs-index] ERROR: {exc}", file=sys.stderr, flush=True)
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[cs-index] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1

    elapsed = time.time() - start
    print(
        f"[cs-index] 완료 — mode={mode_descriptor} row_count={row_count}"
        f"{extra_summary} ({elapsed:.1f}s)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
