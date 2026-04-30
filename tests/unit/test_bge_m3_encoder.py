from __future__ import annotations

import sys
from types import ModuleType

import numpy as np

from scripts.learning.rag.encoders.bge_m3 import BgeM3Encoder, _coerce_sparse_weights


class _FakeBGEM3FlagModel:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def encode(
        self,
        sentences,
        *,
        batch_size=None,
        max_length=None,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=True,
        **kwargs,
    ):
        n = len(sentences)
        out = {}
        if return_dense:
            out["dense_vecs"] = np.ones((n, 1024), dtype=np.float32)
        if return_sparse:
            out["lexical_weights"] = [{"12": np.float32(0.5), "7": 0.25} for _ in sentences]
        if return_colbert_vecs:
            out["colbert_vecs"] = [np.ones((3, 1024), dtype=np.float32) for _ in sentences]
        return out


def test_coerce_sparse_weights_converts_flagembedding_string_ids():
    out = _coerce_sparse_weights({"12": np.float32(0.5), "7": 0.25})
    assert out == {12: 0.5, 7: 0.25}


def test_bge_m3_encoder_wraps_flagembedding(monkeypatch):
    fake_mod = ModuleType("FlagEmbedding")
    fake_mod.BGEM3FlagModel = _FakeBGEM3FlagModel
    monkeypatch.setitem(sys.modules, "FlagEmbedding", fake_mod)

    encoder = BgeM3Encoder(devices="cpu", colbert_storage_dtype="float16")
    out = encoder.encode_corpus(["a", "b"], batch_size=2)

    assert out["dense"].shape == (2, 1024)
    assert out["dense"].dtype == np.float32
    assert out["sparse"] == [{12: 0.5, 7: 0.25}, {12: 0.5, 7: 0.25}]
    assert len(out["colbert"]) == 2
    assert out["colbert"][0].shape == (3, 1024)
    assert out["colbert"][0].dtype == np.float16


def test_bge_m3_encoder_respects_modalities(monkeypatch):
    fake_mod = ModuleType("FlagEmbedding")
    fake_mod.BGEM3FlagModel = _FakeBGEM3FlagModel
    monkeypatch.setitem(sys.modules, "FlagEmbedding", fake_mod)

    encoder = BgeM3Encoder(devices="cpu")
    out = encoder.encode_corpus(["a"], modalities=("dense",))

    assert out["dense"].shape == (1, 1024)
    assert out["sparse"] == [{}]
    assert out["colbert"][0].shape == (0, 1024)

