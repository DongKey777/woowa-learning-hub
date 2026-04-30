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


def _default_lance_encoder():
    """Production bge-m3 encoder factory for the explicit LanceDB backend."""
    from scripts.learning.rag.encoders.bge_m3 import BgeM3Encoder  # noqa: WPS433

    return BgeM3Encoder()


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
        # v3 readiness is not the production readiness contract yet.  An
        # explicit LanceDB build should therefore mean "build v3 now", not
        # "reuse the legacy v2 readiness result and choose incremental".
        effective_mode = "full"

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
            if effective_mode == "incremental":
                print(
                    "[cs-index] ERROR: --backend lance supports only full builds until "
                    "the LanceDB incremental wrapper lands. Use --mode full.",
                    file=sys.stderr,
                    flush=True,
                )
                return 2
            factory = lance_encoder_factory or _default_lance_encoder
            encoder = factory()
            manifest = indexer.build_lance_index(
                index_root=args.out,
                corpus_root=args.corpus,
                encoder=encoder,
                modalities=args.modalities,
                progress=_progress,
                colbert_dtype=args.lance_colbert_dtype,
            )
            row_count = manifest["row_count"]
            mode_descriptor = "lance-full"
            extra_summary = (
                f" — encoder={manifest.get('encoder', {}).get('model_version', args.encoder)} "
                f"modalities={','.join(args.modalities)}"
            )
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
