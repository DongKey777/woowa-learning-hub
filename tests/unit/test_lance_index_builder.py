from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from jsonschema import validate

from scripts.learning.rag import corpus_loader, indexer


class FakeMultiModalEncoder:
    model_id = "fake/bge-m3"
    model_version = "fake/bge-m3@test"
    dense_dim = 8
    colbert_dim = 8
    sparse_vocab_size = 128
    max_length = 512
    batch_size = 32

    def encode_corpus(
        self,
        texts,
        *,
        batch_size=16,
        max_length=8192,
        modalities=("dense", "sparse", "colbert"),
        progress=None,
    ):
        dense = np.zeros((len(texts), self.dense_dim), dtype=np.float32)
        sparse = []
        colbert = []
        for i, _text in enumerate(texts):
            dense[i, i % self.dense_dim] = 1.0
            sparse.append({i + 1: 1.0, 42: 0.25})
            colbert.append(
                np.full((2, self.colbert_dim), float(i + 1), dtype=np.float16)
            )
        return {"dense": dense, "sparse": sparse, "colbert": colbert}

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        return self.encode_corpus([text], modalities=modalities)


def _write_doc(root: Path, category: str, slug: str, title: str, body: str) -> None:
    path = root / "contents" / category / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# {title}

> 한 줄 요약: 테스트용 문서입니다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords:
- {title.lower()} basics
- {title} 처음 배우는데
- {title} 왜 필요해요

## 핵심 개념

{body}
""",
        encoding="utf-8",
    )


def _fake_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    _write_doc(
        root,
        "database",
        "transaction-basics",
        "트랜잭션 기초",
        "트랜잭션은 여러 데이터 변경을 하나의 작업 단위로 묶는 약속입니다. "
        "입문자는 커밋과 롤백이 언제 일어나는지 먼저 이해해야 합니다. " * 3,
    )
    _write_doc(
        root,
        "spring",
        "bean-basics",
        "Spring Bean 기초",
        "스프링 빈은 컨테이너가 만들고 관리하는 객체입니다. "
        "입문자는 객체 생성 위치와 의존성 주입 흐름을 함께 봐야 합니다. " * 3,
    )
    return root


def test_build_lance_index_writes_v3_manifest_and_table(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    progress = []
    expected_count = len(corpus_loader.load_corpus(corpus_root))

    manifest = indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=FakeMultiModalEncoder(),
        progress=lambda stage, info: progress.append((stage, info)),
    )

    schema = json.loads(Path("schemas/cs-index-manifest-v3.json").read_text(encoding="utf-8"))
    validate(manifest, schema)

    assert manifest["index_version"] == 3
    assert manifest["row_count"] == expected_count
    assert manifest["encoder"]["model_version"] == "fake/bge-m3@test"
    assert manifest["encoder"]["max_length"] == 512
    assert manifest["encoder"]["batch_size"] == 32
    assert manifest["modalities"] == ["dense", "sparse", "colbert", "fts"]
    assert (index_root / indexer.LANCE_DIR_NAME).exists()

    persisted = indexer.read_manifest_v3(index_root)
    assert persisted == manifest

    table = indexer.open_lance_table(index_root)
    assert table.count_rows() == expected_count

    rows = table.to_pandas().to_dict("records")
    first = rows[0]
    assert first["chunk_id"]
    assert first["path"].startswith("contents/")
    assert any("트랜잭션" in row["body"] for row in rows)
    assert first["search_terms"]
    assert list(first["sparse_vec"]["indices"]) == [1, 42]
    assert list(first["sparse_vec"]["values"]) == [1.0, 0.25]
    assert first["encoder_version"] == "fake/bge-m3@test"
    assert len(first["dense_vec"]) == FakeMultiModalEncoder.dense_dim
    assert table.search("트랜잭션", query_type="fts").limit(1).to_list()

    stages = [stage for stage, _info in progress]
    assert stages == [
        "load_corpus",
        "load_corpus_done",
        "encode",
        "write_lance",
        "create_indices",
        "write_manifest",
    ]


def test_build_lance_index_replaces_previous_table_and_manifest(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    first_expected_count = len(corpus_loader.load_corpus(corpus_root))

    first = indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )
    _write_doc(
        corpus_root,
        "network",
        "http-basics",
        "HTTP 기초",
        "HTTP는 클라이언트와 서버가 요청과 응답을 주고받는 규칙입니다. " * 4,
    )
    second_expected_count = len(corpus_loader.load_corpus(corpus_root))
    second = indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )

    assert first["row_count"] == first_expected_count
    assert second["row_count"] == second_expected_count
    assert indexer.open_lance_table(index_root).count_rows() == second_expected_count


def test_build_lance_index_rejects_empty_corpus(tmp_path):
    with pytest.raises(RuntimeError, match="corpus .* is empty"):
        indexer.build_lance_index(
            index_root=tmp_path / "index",
            corpus_root=tmp_path / "empty-corpus",
            encoder=FakeMultiModalEncoder(),
        )


def test_create_lance_indices_uses_exact_scan_for_small_samples():
    class FakeTable:
        def __init__(self):
            self.vector_index_calls = 0
            self.fts_columns = []

        def create_index(self, **_kwargs):
            self.vector_index_calls += 1

        def create_fts_index(self, column, **_kwargs):
            self.fts_columns.append(column)

    table = FakeTable()
    indices = indexer._create_lance_indices(table, row_count=283)

    assert table.vector_index_calls == 0
    assert table.fts_columns == ["search_terms", "body"]
    assert indices["dense"]["type"] == "unindexed"
    assert indices["colbert"]["type"] == "sidecar"


def test_create_lance_indices_builds_ann_for_production_sized_tables():
    class FakeTable:
        def __init__(self):
            self.vector_index_calls = 0

        def create_index(self, **_kwargs):
            self.vector_index_calls += 1

        def create_fts_index(self, *_args, **_kwargs):
            pass

    table = FakeTable()
    indices = indexer._create_lance_indices(table, row_count=indexer.LANCE_ANN_MIN_ROWS)

    assert table.vector_index_calls == 2
    assert indices["dense"]["type"] in {"IVF_FLAT", "IVF_PQ"}
    assert indices["colbert"]["type"] == "MULTI_VECTOR"


def test_create_lance_indices_honors_dense_ivf_overrides():
    class FakeTable:
        def __init__(self):
            self.vector_index_calls = []

        def create_index(self, **kwargs):
            self.vector_index_calls.append(kwargs)

        def create_fts_index(self, *_args, **_kwargs):
            pass

    table = FakeTable()
    indices = indexer._create_lance_indices(
        table,
        row_count=indexer.LANCE_ANN_MIN_ROWS,
        dense_num_partitions=7,
        dense_num_sub_vectors=128,
    )

    dense_call = table.vector_index_calls[0]
    colbert_call = table.vector_index_calls[1]
    assert dense_call["index_type"] == "IVF_PQ"
    assert dense_call["num_partitions"] == 7
    assert dense_call["num_sub_vectors"] == 128
    assert colbert_call["num_partitions"] == 7
    assert colbert_call["num_sub_vectors"] == 128
    assert indices["dense"]["num_partitions"] == 7
    assert indices["dense"]["num_sub_vectors"] == 128


def test_create_lance_indices_rejects_non_positive_ivf_values():
    class FakeTable:
        def create_index(self, **_kwargs):
            pass

        def create_fts_index(self, *_args, **_kwargs):
            pass

    with pytest.raises(ValueError, match="dense_num_partitions"):
        indexer._create_lance_indices(FakeTable(), row_count=2048, dense_num_partitions=0)
    with pytest.raises(ValueError, match="dense_num_sub_vectors"):
        indexer._create_lance_indices(FakeTable(), row_count=2048, dense_num_sub_vectors=0)
