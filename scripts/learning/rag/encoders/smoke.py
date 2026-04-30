"""H0 capability proof for the bge-m3 + LanceDB plan.

Run manually:

    HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.learning.rag.encoders.smoke

The command writes ``state/cs_rag/dep_probe.json`` so later phases can
consume observed capabilities instead of assuming library behavior.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

import numpy as np

from .bge_m3 import BgeM3Encoder


def _version(module_name: str) -> str | None:
    try:
        module = __import__(module_name)
    except ImportError:
        return None
    return getattr(module, "__version__", "unknown")


def _as_plain_list(value) -> list:
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _probe_kiwipiepy() -> dict:
    import kiwipiepy  # type: ignore

    kiwi = kiwipiepy.Kiwi()
    tokens = [tok.form for tok in kiwi.tokenize("스프링 빈은 컨테이너가 관리한다")]
    return {
        "version": getattr(kiwipiepy, "__version__", "unknown"),
        "tokenize_smoke_ok": all(expected in tokens for expected in ("스프링", "빈", "컨테이너")),
        "sample_tokens": tokens,
    }


def _probe_lancedb() -> dict:
    import lancedb  # type: ignore
    import pyarrow as pa  # type: ignore
    import kiwipiepy  # type: ignore

    tmp = tempfile.mkdtemp(prefix="woowa-lancedb-smoke-")
    db = lancedb.connect(tmp)
    kiwi = kiwipiepy.Kiwi()

    def search_terms(text: str) -> str:
        return " ".join(tok.form for tok in kiwi.tokenize(text))

    vector_table = db.create_table(
        "vector_smoke",
        data=[
            {
                "id": str(i),
                "body": f"트랜잭션 격리 수준 {i}",
                "search_terms": search_terms(f"트랜잭션 격리 수준 {i}"),
                "vec": [float(i == j) for j in range(8)],
            }
            for i in range(8)
        ],
        schema=pa.schema(
            [
                ("id", pa.string()),
                ("body", pa.string()),
                ("search_terms", pa.string()),
                ("vec", pa.list_(pa.float32(), 8)),
            ]
        ),
        mode="overwrite",
    )
    vector_hit = vector_table.search(
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        vector_column_name="vec",
    ).limit(1).to_list()

    fts_tokenizer = "none"
    fts_ok = False
    try:
        vector_table.create_fts_index(
            "search_terms",
            replace=True,
            base_tokenizer="ngram",
            ngram_min_length=2,
            ngram_max_length=3,
            stem=False,
            remove_stop_words=False,
            ascii_folding=False,
        )
        fts_hit = vector_table.search(
            "트랜잭션",
            query_type="fts",
            fts_columns="search_terms",
        ).limit(1).to_list()
        fts_ok = bool(fts_hit)
        fts_tokenizer = "ngram" if fts_ok else "kiwipiepy_external"
    except Exception:
        fts_tokenizer = "kiwipiepy_external"

    multivector_results: dict[str, str] = {}
    for dtype_name, pa_type in (("float16", pa.float16()), ("float32", pa.float32())):
        try:
            mv_table = db.create_table(
                f"mv_{dtype_name}",
                data=[
                    {
                        "id": str(i),
                        "mv": [
                            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        ],
                    }
                    for i in range(20)
                ],
                schema=pa.schema(
                    [
                        ("id", pa.string()),
                        ("mv", pa.list_(pa.list_(pa_type, 8))),
                    ]
                ),
                mode="overwrite",
            )
            mv_table.search(
                [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
                vector_column_name="mv",
            ).limit(1).to_list()
            try:
                mv_table.create_index(
                    vector_column_name="mv",
                    metric="cosine",
                    index_type="IVF_FLAT",
                    num_partitions=2,
                )
                multivector_results[dtype_name] = "supported_indexed"
            except Exception:
                multivector_results[dtype_name] = "supported_exact_only"
        except Exception as exc:
            multivector_results[dtype_name] = f"unsupported:{type(exc).__name__}"

    sparse_table = db.create_table(
        "sparse_smoke",
        data=[
            {
                "id": "s1",
                "sparse_vec": {"indices": [1, 2, 3], "values": [0.2, 0.4, 0.6]},
            }
        ],
        schema=pa.schema(
            [
                ("id", pa.string()),
                (
                    "sparse_vec",
                    pa.struct(
                        [
                            ("indices", pa.list_(pa.int32())),
                            ("values", pa.list_(pa.float32())),
                        ]
                    ),
                ),
            ]
        ),
        mode="overwrite",
    )
    sparse_roundtrip = sparse_table.to_pandas().to_dict("records")[0]["sparse_vec"]
    sparse_indices = _as_plain_list(sparse_roundtrip["indices"])

    merge_table = db.create_table(
        "merge_smoke",
        data=[{"id": "1", "value": 1}, {"id": "2", "value": 2}],
        schema=pa.schema([("id", pa.string()), ("value", pa.int64())]),
        mode="overwrite",
    )
    before = merge_table.version
    merge_table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(
        [{"id": "2", "value": 20}, {"id": "3", "value": 30}]
    )
    after = merge_table.version

    return {
        "version": getattr(lancedb, "__version__", "unknown"),
        "vector_search_ok": bool(vector_hit),
        "fts_korean_tokenizer": fts_tokenizer,
        "fts_korean_smoke_ok": fts_ok,
        "multivector_api": multivector_results,
        "multivector_dtype": "float16"
        if multivector_results.get("float16", "").startswith("supported")
        else "float32",
        "sparse_native": "rescore_only",
        "sparse_roundtrip_ok": sparse_indices == [1, 2, 3],
        "merge_insert_ok": merge_table.count_rows() == 3 and after > before,
        "versioning_ok": after > before,
        "search_api_signature": "table.search(query, vector_column_name=..., query_type=...).where(...).text(...).rerank(...).limit(...).to_list()",
    }


def _probe_real_encoder(args: argparse.Namespace) -> dict:
    encoder = BgeM3Encoder(
        model_id=args.model_id,
        devices=args.device,
        use_fp16=args.fp16,
        colbert_storage_dtype=args.colbert_dtype,
    )
    samples = [
        "트랜잭션 격리 수준이 뭐야?",
        "Spring Bean DI",
        "HTTP 캐시는 언제 쓰나요?",
        "equals hashCode가 헷갈려요",
        "큐와 스택 차이",
    ]
    started = time.time()
    out = encoder.encode_corpus(samples, batch_size=2, max_length=args.max_length)
    elapsed = time.time() - started
    first_sparse = out["sparse"][0]
    return {
        "model_id": encoder.model_id,
        "model_version": encoder.model_version,
        "bge_m3_load_ok": True,
        "dense_shape": list(out["dense"].shape),
        "dense_dtype": str(out["dense"].dtype),
        "sparse_len": len(out["sparse"]),
        "sparse_key_type": type(next(iter(first_sparse.keys()))).__name__ if first_sparse else "empty",
        "colbert_len": len(out["colbert"]),
        "colbert_dim": int(out["colbert"][0].shape[1]) if out["colbert"] else None,
        "colbert_dtype": str(out["colbert"][0].dtype) if out["colbert"] else None,
        "elapsed_s": round(elapsed, 2),
    }


def build_probe(args: argparse.Namespace) -> dict:
    probe = {
        "probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": {
            "version": ".".join(str(part) for part in __import__("sys").version_info[:3]),
        },
        "lancedb": _probe_lancedb(),
        "pyarrow": {"version": _version("pyarrow")},
        "FlagEmbedding": {"version": _version("FlagEmbedding")},
        "kiwipiepy": _probe_kiwipiepy(),
    }
    if args.skip_real_model:
        probe["bge_m3"] = {"bge_m3_load_ok": None, "skipped": True}
    else:
        probe["bge_m3"] = _probe_real_encoder(args)
    return probe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="BAAI/bge-m3")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--colbert-dtype", choices=("float16", "float32"), default="float16")
    parser.add_argument("--skip-real-model", action="store_true")
    parser.add_argument("--out", default="state/cs_rag/dep_probe.json")
    args = parser.parse_args(argv)

    probe = build_probe(args)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bge = probe.get("bge_m3", {})
    if bge.get("bge_m3_load_ok"):
        print(
            f"dense={bge['dense_shape'][1]} colbert={bge['colbert_dim']} "
            f"sparse={BgeM3Encoder().sparse_vocab_size}"
        )
    else:
        print("real-model=skipped")
    print(f"lancedb={probe['lancedb']['version']} fts={probe['lancedb']['fts_korean_tokenizer']}")
    print(f"dep_probe={out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
