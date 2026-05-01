"""Load current runtime indexes into R3 prototype document records."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.learning.rag import indexer

from ..candidate import R3Document


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
