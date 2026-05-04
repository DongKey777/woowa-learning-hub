"""Phase 9.3 Step B — R3 refusal sentinel.

When the reranker's top-1 cross-encoder score falls below
``R3Config.refusal_threshold``, R3 returns a single ``sentinel`` hit
instead of top-K reranked candidates. The sentinel is the signal that
``integration.augment`` lifts to a tier downgrade so the AI session
falls back to training knowledge with an explicit corpus_gap
disclaimer (Step C/D).

Threshold reads ``cross_encoder_score`` from the reranked candidate's
metadata (where ``CrossEncoderReranker`` stores the raw model score),
NOT the fused RRF score (which is a 1/(k+rank) micro-value).

Default threshold = ``None`` (disabled). Phase 9.3 ships gated on
``WOOWA_RAG_REFUSAL_THRESHOLD`` so production behavior does not change
until calibration measurement runs.
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from scripts.learning.rag.r3 import search as r3_search
from scripts.learning.rag.r3.candidate import Candidate
from scripts.learning.rag.r3.config import R3Config


def _candidate(
    path: str,
    *,
    rank: int = 1,
    score: float = 0.05,
    cross_encoder_score: float | None = None,
) -> Candidate:
    metadata: dict = {}
    if cross_encoder_score is not None:
        metadata["cross_encoder_score"] = cross_encoder_score
    return Candidate(
        path=path,
        retriever="reranker:test",
        rank=rank,
        score=score,
        chunk_id=f"{path}#0",
        title=path.rsplit("/", 1)[-1].removesuffix(".md"),
        section_title="primer",
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Config plumbing
# ---------------------------------------------------------------------------

class RefusalThresholdConfigTest(unittest.TestCase):
    def test_default_is_none(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WOOWA_RAG_REFUSAL_THRESHOLD", None)
            config = R3Config.from_env()
            self.assertIsNone(config.refusal_threshold)

    def test_env_parses_float(self):
        with mock.patch.dict(os.environ, {"WOOWA_RAG_REFUSAL_THRESHOLD": "0.5"}):
            self.assertEqual(R3Config.from_env().refusal_threshold, 0.5)

    def test_env_off_keyword_disables(self):
        with mock.patch.dict(os.environ, {"WOOWA_RAG_REFUSAL_THRESHOLD": "off"}):
            self.assertIsNone(R3Config.from_env().refusal_threshold)

    def test_env_non_numeric_disables(self):
        with mock.patch.dict(os.environ, {"WOOWA_RAG_REFUSAL_THRESHOLD": "garbage"}):
            self.assertIsNone(R3Config.from_env().refusal_threshold)


# ---------------------------------------------------------------------------
# Sentinel decision helper
# ---------------------------------------------------------------------------

class SentinelDecisionTest(unittest.TestCase):
    def test_no_sentinel_when_threshold_disabled(self):
        config = R3Config()  # refusal_threshold=None
        fused = [_candidate("knowledge/cs/contents/spring/x.md", cross_encoder_score=-2.0)]
        applied, _info = r3_search._evaluate_refusal_sentinel(
            fused=fused,
            reranker_active=True,
            config=config,
        )
        self.assertFalse(applied)

    def test_no_sentinel_when_reranker_inactive(self):
        config = R3Config(refusal_threshold=0.0)
        fused = [_candidate("knowledge/cs/contents/spring/x.md", cross_encoder_score=-2.0)]
        applied, _info = r3_search._evaluate_refusal_sentinel(
            fused=fused,
            reranker_active=False,
            config=config,
        )
        self.assertFalse(applied)

    def test_sentinel_when_top_ce_below_threshold(self):
        config = R3Config(refusal_threshold=0.0)
        fused = [
            _candidate("knowledge/cs/contents/spring/x.md", cross_encoder_score=-1.5),
            _candidate("knowledge/cs/contents/spring/y.md", cross_encoder_score=-2.0),
        ]
        applied, info = r3_search._evaluate_refusal_sentinel(
            fused=fused,
            reranker_active=True,
            config=config,
        )
        self.assertTrue(applied)
        self.assertEqual(info["rejected_top_path"], "knowledge/cs/contents/spring/x.md")
        self.assertAlmostEqual(info["rejected_top_score"], -1.5)
        self.assertEqual(info["threshold"], 0.0)

    def test_no_sentinel_when_top_ce_at_or_above_threshold(self):
        config = R3Config(refusal_threshold=0.0)
        fused = [_candidate("knowledge/cs/contents/spring/x.md", cross_encoder_score=0.5)]
        applied, _info = r3_search._evaluate_refusal_sentinel(
            fused=fused,
            reranker_active=True,
            config=config,
        )
        self.assertFalse(applied)

    def test_no_sentinel_when_ce_score_missing(self):
        """When metadata has no cross_encoder_score (e.g., reranker
        skipped or upstream contract changed), refusal check is a no-op
        — never spuriously emit sentinel."""
        config = R3Config(refusal_threshold=0.0)
        fused = [_candidate("knowledge/cs/contents/spring/x.md")]  # no ce_score
        applied, _info = r3_search._evaluate_refusal_sentinel(
            fused=fused,
            reranker_active=True,
            config=config,
        )
        self.assertFalse(applied)

    def test_no_sentinel_when_fused_empty(self):
        config = R3Config(refusal_threshold=0.0)
        applied, _info = r3_search._evaluate_refusal_sentinel(
            fused=[],
            reranker_active=True,
            config=config,
        )
        self.assertFalse(applied)


# ---------------------------------------------------------------------------
# Sentinel hit shape
# ---------------------------------------------------------------------------

class SentinelHitShapeTest(unittest.TestCase):
    def test_sentinel_hit_carries_discriminator_and_rejected_top(self):
        hit = r3_search._make_refusal_sentinel(
            top_path="knowledge/cs/contents/spring/x.md",
            top_score=-1.5,
            threshold=0.0,
        )
        # discriminator the consumer (integration.augment) reads
        self.assertEqual(hit["sentinel"], "no_confident_match")
        # diagnostic — what the system would have returned
        self.assertEqual(hit["rejected_top"], "knowledge/cs/contents/spring/x.md")
        self.assertAlmostEqual(hit["rejected_score"], -1.5)
        self.assertAlmostEqual(hit["threshold"], 0.0)
        # path is a sentinel marker (NOT a real corpus path) so anything
        # downstream that mistakes it for a real hit will be obviously
        # broken
        self.assertTrue(hit["path"].startswith("<sentinel"))
        # score field carries the rejected score so existing scoring
        # consumers still see something numeric
        self.assertAlmostEqual(hit["score"], -1.5)
        # Same outer shape as a normal hit (so mismatch on any consumer
        # that reads keys yields immediate KeyError, not silent None)
        for key in ("path", "title", "category", "section_title",
                    "section_path", "score", "snippet_preview", "anchors"):
            self.assertIn(key, hit)


if __name__ == "__main__":
    unittest.main()
