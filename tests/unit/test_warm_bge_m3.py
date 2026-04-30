"""Unit tests for the BGE-M3 warm helper retry + timeout logic."""

from __future__ import annotations

import subprocess
from unittest import mock

from scripts.remote import _warm_bge_m3 as W


# ---------------------------------------------------------------------------
# Retry loop (main)
# ---------------------------------------------------------------------------

def test_main_returns_0_on_first_attempt_success(monkeypatch):
    calls = []

    def fake_attempt(model_id, timeout_s):
        calls.append((model_id, timeout_s))
        return 0

    monkeypatch.setattr(W, "_warm_attempt", fake_attempt)
    monkeypatch.setattr(W.time, "sleep", lambda _: None)

    rc = W.main()

    assert rc == 0
    assert calls == [(W.MODEL_ID, W.ATTEMPT_TIMEOUT_S)]


def test_main_retries_on_transient_failure(monkeypatch):
    """First 2 attempts return non-zero, third succeeds — return 0."""
    rcs = iter([1, -1, 0])  # rate-limit, then stall-killed, then success
    sleeps: list[int] = []

    monkeypatch.setattr(W, "_warm_attempt", lambda *_: next(rcs))
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    rc = W.main()

    assert rc == 0
    assert sleeps == [W.BASE_BACKOFF_S * 1, W.BASE_BACKOFF_S * 2]


def test_main_returns_1_after_all_attempts_exhausted(monkeypatch):
    sleeps: list[int] = []
    monkeypatch.setattr(W, "_warm_attempt", lambda *_: 1)
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    rc = W.main()

    assert rc == 1
    # MAX_ATTEMPTS attempts, MAX_ATTEMPTS-1 sleeps between them
    assert len(sleeps) == W.MAX_ATTEMPTS - 1


def test_main_sets_hf_hub_download_timeout(monkeypatch):
    monkeypatch.delenv("HF_HUB_DOWNLOAD_TIMEOUT", raising=False)
    monkeypatch.setattr(W, "_warm_attempt", lambda *_: 0)

    W.main()

    assert os.environ.get("HF_HUB_DOWNLOAD_TIMEOUT") == "300"


def test_main_does_not_overwrite_user_supplied_timeout(monkeypatch):
    monkeypatch.setenv("HF_HUB_DOWNLOAD_TIMEOUT", "600")
    monkeypatch.setattr(W, "_warm_attempt", lambda *_: 0)

    W.main()

    assert os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] == "600"


def test_backoff_grows_linearly(monkeypatch):
    sleeps: list[int] = []
    monkeypatch.setattr(W, "_warm_attempt", mock.Mock(return_value=1))
    monkeypatch.setattr(W.time, "sleep", lambda s: sleeps.append(s))

    W.main()

    expected = [W.BASE_BACKOFF_S * i for i in range(1, W.MAX_ATTEMPTS)]
    assert sleeps == expected


# ---------------------------------------------------------------------------
# Subprocess timeout (_warm_attempt)
# ---------------------------------------------------------------------------

def test_warm_attempt_returns_subprocess_rc(monkeypatch):
    """Happy path — subprocess.Popen + wait returns 0."""
    fake_proc = mock.Mock()
    fake_proc.wait.return_value = 0
    fake_proc.pid = 12345

    popen_calls = []

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        return fake_proc

    monkeypatch.setattr(W.subprocess, "Popen", fake_popen)

    rc = W._warm_attempt("BAAI/bge-m3", 900)

    assert rc == 0
    # Subprocess command embeds the model id
    assert any("BAAI/bge-m3" in arg for arg in popen_calls[0][0])
    # start_new_session=True for process group kill on timeout
    assert popen_calls[0][1].get("start_new_session") is True


def test_warm_attempt_kills_on_timeout(monkeypatch):
    """If wait raises TimeoutExpired, kill the process group and return -1."""
    fake_proc = mock.Mock()
    fake_proc.pid = 12345
    fake_proc.wait.side_effect = [
        subprocess.TimeoutExpired(cmd="x", timeout=900),
        0,  # cleanup wait after kill
    ]

    monkeypatch.setattr(W.subprocess, "Popen", lambda *a, **k: fake_proc)

    killed_groups: list[tuple[int, int]] = []

    def fake_killpg(pgid, sig):
        killed_groups.append((pgid, sig))

    monkeypatch.setattr(W.os, "killpg", fake_killpg)
    monkeypatch.setattr(W.os, "getpgid", lambda pid: pid)

    rc = W._warm_attempt("BAAI/bge-m3", 900)

    assert rc == -1
    assert killed_groups == [(12345, W.signal.SIGKILL)]


def test_warm_attempt_falls_back_to_proc_kill_if_killpg_fails(monkeypatch):
    """Race condition: process exits between wait+killpg — fall back to kill()."""
    fake_proc = mock.Mock()
    fake_proc.pid = 12345
    fake_proc.wait.side_effect = [
        subprocess.TimeoutExpired(cmd="x", timeout=900),
        0,
    ]

    monkeypatch.setattr(W.subprocess, "Popen", lambda *a, **k: fake_proc)
    monkeypatch.setattr(W.os, "getpgid", lambda pid: pid)

    def boom(pgid, sig):
        raise ProcessLookupError("already gone")

    monkeypatch.setattr(W.os, "killpg", boom)

    rc = W._warm_attempt("BAAI/bge-m3", 900)

    assert rc == -1
    fake_proc.kill.assert_called_once()


# Need os import for the timeout-env test above
import os  # noqa: E402
