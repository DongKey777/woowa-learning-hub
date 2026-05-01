from __future__ import annotations

import json

from scripts.learning.rag.r3.rerankers.profile import main, profile_reranker


class FakeModel:
    def predict(self, pairs, show_progress_bar=False):
        del show_progress_bar
        return [len(pair[1]) for pair in pairs]


def test_profile_reranker_records_runtime_shape():
    profile = profile_reranker(
        "fake-reranker",
        [["q", "passage"], ["q", "longer passage"]],
        model_factory=lambda _: FakeModel(),
    )

    assert profile.model_id == "fake-reranker"
    assert profile.pair_count == 2
    assert profile.load_ms >= 0.0
    assert profile.score_ms >= 0.0
    assert profile.per_pair_p95_ms >= profile.per_pair_p50_ms
    assert profile.rss_peak_mb > 0


def test_profile_cli_writes_json(tmp_path, monkeypatch):
    pairs = tmp_path / "pairs.json"
    out = tmp_path / "profile.json"
    pairs.write_text(json.dumps([["q", "p"]]), encoding="utf-8")

    monkeypatch.setattr(
        "scripts.learning.rag.r3.rerankers.profile.default_model_factory",
        lambda _: FakeModel(),
    )

    assert main(["--model-id", "fake", "--pairs-json", str(pairs), "--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["model_id"] == "fake"
    assert payload["pair_count"] == 1
