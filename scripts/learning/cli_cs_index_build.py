"""CLI: build the CS RAG index.

Usage
-----
    bin/cs-index-build [--corpus knowledge/cs] [--out state/cs_rag] [--force]

The AI session — not the learner — runs this during the First-Run Protocol
or when cs_readiness.state != "ready".
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
    elif stage == "write_dense":
        print(f"[cs-index] 5/5 dense 벡터 저장 — shape={info.get('shape')}", flush=True)
    elif stage == "write_manifest":
        print(
            f"[cs-index] 5/5 manifest 저장 — row_count={info.get('row_count')}, "
            f"corpus_hash={info.get('corpus_hash', '')[:12]}…",
            flush=True,
        )
    else:
        print(f"[cs-index] {stage} {info}", flush=True)


def main(argv: list[str] | None = None) -> int:
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
        help="Rebuild even if is_ready() reports ready.",
    )
    args = parser.parse_args(argv)

    # Make scripts.* importable when invoked as a script.
    sys.path.insert(0, str(repo_root))

    from scripts.learning.rag import indexer  # noqa: WPS433

    readiness = indexer.is_ready(args.out, args.corpus)
    if readiness.state == "ready" and not args.force:
        print(
            f"[cs-index] already ready — corpus_hash={readiness.corpus_hash[:12]}… "
            "(use --force to rebuild)",
            flush=True,
        )
        return 0

    print(f"[cs-index] state={readiness.state} reason={readiness.reason} → rebuild", flush=True)

    start = time.time()
    try:
        manifest = indexer.build_index(
            index_root=args.out,
            corpus_root=args.corpus,
            progress=_progress,
        )
    except indexer.IndexDependencyMissing as exc:
        print(f"[cs-index] ERROR: {exc}", file=sys.stderr, flush=True)
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[cs-index] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1

    elapsed = time.time() - start
    print(
        f"[cs-index] 완료 — row_count={manifest['row_count']} "
        f"({elapsed:.1f}s)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
