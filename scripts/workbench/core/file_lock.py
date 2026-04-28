"""Cross-platform advisory file locking helper.

Unix(macOS/Linux/WSL)는 `fcntl.flock`으로 advisory lock을 잡고, native
Windows는 `fcntl` 모듈이 없어서 no-op으로 떨어진다. 학습 워크벤치는
single-user 환경이라 단일 프로세스 안의 동시 append를 보호하면 충분하고
이는 fcntl 없이도 OS 레벨 append 원자성으로 어느 정도 안전.

진짜 multi-process 동시성이 필요한 orchestrator(개발자 영역)는 동일한
헬퍼를 쓰되, native Windows에서 worker fleet을 돌리려면 추가적으로
filelock/portalocker 같은 라이브러리 도입이 필요할 수 있다 — 학습자
흐름에는 영향 없음.

Usage:
    from .file_lock import lock_exclusive, unlock

    with path.open("a") as handle:
        lock_exclusive(handle)
        try:
            handle.write(line)
        finally:
            unlock(handle)
"""

from __future__ import annotations

try:
    import fcntl as _fcntl  # type: ignore[import]
    _HAS_FCNTL = True
except ImportError:  # native Windows
    _fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


def lock_exclusive(handle) -> None:
    """Acquire an exclusive advisory lock on `handle` if the platform supports it.

    On native Windows (no `fcntl`), this is a no-op. The workbench is
    single-user so within-process append serialization handled by the
    OS append semantics is sufficient.
    """
    if _HAS_FCNTL:
        _fcntl.flock(handle, _fcntl.LOCK_EX)


def unlock(handle) -> None:
    """Release the advisory lock if held."""
    if _HAS_FCNTL:
        _fcntl.flock(handle, _fcntl.LOCK_UN)


def has_native_lock() -> bool:
    """Diagnostic: True iff fcntl-based locking is available on this platform."""
    return _HAS_FCNTL
