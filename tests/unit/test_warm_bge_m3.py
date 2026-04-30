"""Unit tests for the BGE-M3 warm helper retry logic (R1 v2/v3 fix)."""

from __future__ import annotations

from unittest import mock

import pytest

from scripts.remote import _warm_bge_m3 as W


def test_main_returns_0_on_first_attempt_success(monkeypatch):
    """Happy path — single call to _warm_once, return 0."""
    calls = []

    def fake_warm(model_id):
        calls.append(model_id)

    monkeypatch.setattr(W, "_warm_once", fake_warm)
    monkeypatch.setattr(W.time, "sleep", lambda _: None)

    rc = W.main()

    assert rc == 0
    assert calls == [W.MODEL_ID]


def test_main_retries_on_transient_failure(monkeypatch):
    """First 2 attempts fail, third succeeds — return 0 after backoff."""
    attempts = {"n": 0}
    sleeps: list[int] = []

    def fake_warm(model_id):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("rate limit (simulated)")

    monkeypatch.setattr(W, "_warm_once", fake_warm)
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    rc = W.main()

    assert rc == 0
    assert attempts["n"] == 3
    # Backoff for attempts 1 and 2 only (success on attempt 3, no sleep)
    assert sleeps == [W.BASE_BACKOFF_S * 1, W.BASE_BACKOFF_S * 2]


def test_main_returns_1_after_all_attempts_exhausted(monkeypatch):
    """All MAX_ATTEMPTS fail — return 1, do not raise."""
    attempts = {"n": 0}
    sleeps: list[int] = []

    def fake_warm(model_id):
        attempts["n"] += 1
        raise ConnectionError("HF Hub down (simulated)")

    monkeypatch.setattr(W, "_warm_once", fake_warm)
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    rc = W.main()

    assert rc == 1
    assert attempts["n"] == W.MAX_ATTEMPTS
    # Backoff between every attempt except the last
    assert len(sleeps) == W.MAX_ATTEMPTS - 1


def test_main_sets_hf_hub_download_timeout(monkeypatch):
    """Timeout env var is set so HF client doesn't hang on slow shards."""
    monkeypatch.delenv("HF_HUB_DOWNLOAD_TIMEOUT", raising=False)
    monkeypatch.setattr(W, "_warm_once", lambda _: None)

    W.main()

    assert W.os.environ.get("HF_HUB_DOWNLOAD_TIMEOUT") == "300"


def test_main_does_not_overwrite_user_supplied_timeout(monkeypatch):
    """Use setdefault — user override (e.g. HF_HUB_DOWNLOAD_TIMEOUT=600) wins."""
    monkeypatch.setenv("HF_HUB_DOWNLOAD_TIMEOUT", "600")
    monkeypatch.setattr(W, "_warm_once", lambda _: None)

    W.main()

    assert W.os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] == "600"


def test_backoff_grows_linearly(monkeypatch):
    """30s, 60s, 90s, 120s — linear, not exponential (rate-limit windows
    are typically 60-120s on HF Hub)."""
    sleeps: list[int] = []
    monkeypatch.setattr(W, "_warm_once",
                        mock.Mock(side_effect=RuntimeError("fail")))
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    W.main()

    expected = [W.BASE_BACKOFF_S * i for i in range(1, W.MAX_ATTEMPTS)]
    assert sleeps == expected
