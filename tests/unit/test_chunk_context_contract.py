from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import cli_chunk_context_prepare as CLI
from scripts.learning.rag import corpus_loader, indexer


def _chunk() -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id="doc123",
        chunk_id="doc123#0",
        path="contents/database/tx.md",
        title="트랜잭션",
        category="database",
        section_title="격리 수준",
        section_path=["트랜잭션", "격리 수준"],
        body="트랜잭션 격리 수준은 동시에 실행되는 작업이 서로 관찰하는 범위를 정한다.",
        char_len=40,
        anchors=[],
        difficulty="beginner",
    )


def test_embed_text_prepends_valid_chunk_context(monkeypatch, tmp_path):
    chunk = _chunk()
    monkeypatch.setenv("WOOWA_CHUNK_CONTEXT_ROOT", str(tmp_path))
    (tmp_path / f"{chunk.chunk_id}.output.json").write_text(
        json.dumps(
            {
                "schema_id": "chunk-context-v1.output",
                "chunk_id": chunk.chunk_id,
                "context": "입문자가 트랜잭션 격리 수준을 검색할 때 동시성, dirty read, repeatable read를 함께 찾도록 돕는 맥락.",
                "retrieval_only": True,
                "scored_by": "ai_session",
                "produced_at": "2026-05-01T00:00:00Z",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text = indexer._embed_text(chunk)

    assert "[retrieval context]" in text
    assert "dirty read" in text
    assert text.endswith(chunk.body)


def test_embed_text_ignores_malformed_chunk_context(monkeypatch, tmp_path):
    chunk = _chunk()
    monkeypatch.setenv("WOOWA_CHUNK_CONTEXT_ROOT", str(tmp_path))
    (tmp_path / f"{chunk.chunk_id}.output.json").write_text(
        json.dumps(
            {
                "schema_id": "chunk-context-v1.output",
                "chunk_id": "other#0",
                "context": "wrong chunk",
                "retrieval_only": True,
            }
        ),
        encoding="utf-8",
    )

    text = indexer._embed_text(chunk)

    assert "[retrieval context]" not in text
    assert "wrong chunk" not in text


def test_embed_text_ignores_context_not_scored_by_ai_session(monkeypatch, tmp_path):
    chunk = _chunk()
    monkeypatch.setenv("WOOWA_CHUNK_CONTEXT_ROOT", str(tmp_path))
    (tmp_path / f"{chunk.chunk_id}.output.json").write_text(
        json.dumps(
            {
                "schema_id": "chunk-context-v1.output",
                "chunk_id": chunk.chunk_id,
                "context": "스키마는 맞지만 scored_by 값이 계약과 달라서 무시되어야 한다.",
                "retrieval_only": True,
                "scored_by": "other",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text = indexer._embed_text(chunk)

    assert "[retrieval context]" not in text
    assert "스키마는 맞지만" not in text


def test_chunk_context_prepare_writes_input_for_selected_path(tmp_path, capsys):
    corpus_root = tmp_path / "knowledge" / "cs"
    doc = corpus_root / "contents" / "database" / "tx.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(
        """# 트랜잭션

> 한 줄 요약: 트랜잭션 격리 수준을 설명한다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords: transaction isolation, dirty read, repeatable read, 격리 수준

## 격리 수준

트랜잭션 격리 수준은 동시에 실행되는 작업이 서로 관찰하는 범위를 정한다. 입문자는 dirty read와 repeatable read를 먼저 비교한다.
""",
        encoding="utf-8",
    )
    out_root = tmp_path / "chunk_contexts"

    rc = CLI.main(
        [
            "--corpus-root",
            str(corpus_root),
            "--out-root",
            str(out_root),
            "--path",
            "contents/database/tx.md",
        ]
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1
    input_path = Path(payload["written"][0]["input"])
    data = json.loads(input_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "chunk-context-v1.input"
    assert data["path"] == "contents/database/tx.md"
    assert data["requirements"]["retrieval_only"] is True
    assert data["expected_output_path"].endswith(".output.json")
