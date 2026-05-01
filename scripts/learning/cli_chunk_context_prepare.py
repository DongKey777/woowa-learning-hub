"""Prepare chunk-context-v1 input artifacts for retrieval-only context."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.learning.rag import corpus_loader


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=corpus_loader.DEFAULT_CORPUS_ROOT,
    )
    parser.add_argument("--out-root", type=Path, default=Path("state/cs_rag/chunk_contexts"))
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Repo-relative corpus path under knowledge/cs, repeatable. Defaults to all chunks.",
    )
    return parser


def _chunk_input(chunk: corpus_loader.CorpusChunk, *, produced_at: str) -> dict:
    return {
        "schema_id": "chunk-context-v1.input",
        "chunk_id": chunk.chunk_id,
        "path": chunk.path,
        "title": chunk.title,
        "category": chunk.category,
        "section_path": chunk.section_path,
        "body": chunk.body,
        "anchors": chunk.anchors,
        "difficulty": chunk.difficulty,
        "requirements": {
            "retrieval_only": True,
            "language": "ko",
            "token_budget": {"min": 50, "max": 100},
            "do_not_repeat_body_verbatim": True,
        },
        "produced_at": produced_at,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    wanted = set(args.path)
    chunks = corpus_loader.load_corpus(args.corpus_root)
    if wanted:
        chunks = [chunk for chunk in chunks if chunk.path in wanted]
    args.out_root.mkdir(parents=True, exist_ok=True)
    produced_at = _now()
    written = []
    for chunk in chunks:
        input_path = args.out_root / f"{chunk.chunk_id}.input.json"
        output_path = args.out_root / f"{chunk.chunk_id}.output.json"
        payload = _chunk_input(chunk, produced_at=produced_at)
        payload["expected_output_path"] = str(output_path)
        input_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        written.append(
            {
                "chunk_id": chunk.chunk_id,
                "path": chunk.path,
                "input": str(input_path),
                "expected_output": str(output_path),
            }
        )
    print(json.dumps({"written": written, "count": len(written)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
