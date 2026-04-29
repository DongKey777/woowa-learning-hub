"""Per-candidate artifact cleanup — disk-pressure mitigation for A/B sweeps.

Plan §10 + 학습자 요구 (`feedback_storage_request.md`): when running
the four-candidate sweep on a 14-GB-free machine, the cumulative cost
(model caches ~3.7 GB + per-candidate indexes ~120 MB) can exceed
free space. The simplest answer is to evict each candidate's
artifacts as soon as it's been measured.

Two artifact classes per candidate:

1. **Eval index** at ``state/cs_rag_eval/<candidate_id>/`` — always
   safe to delete after measurement, even for the control candidate
   (production index lives at ``state/cs_rag/`` separately).
2. **HF model cache** at ``~/.cache/huggingface/hub/models--<org>--<repo>/``
   — must NOT be evicted for the control candidate because the
   production system depends on it for everyday retrieval. Only
   non-control upgrades get their HF cache dropped.

Returns a CleanupReport dataclass with bytes freed so callers can
print the running total back to the operator in the sweep log.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HF_CACHE_ROOT = Path.home() / ".cache" / "huggingface" / "hub"


@dataclass(frozen=True)
class CleanupReport:
    """Bytes freed by a single cleanup pass over one candidate."""

    candidate_id: str
    index_dir_freed_mb: float
    hf_cache_freed_mb: float
    skipped_hf_cache_due_to_control: bool

    @property
    def total_freed_mb(self) -> float:
        return self.index_dir_freed_mb + self.hf_cache_freed_mb


def _du_mb(path: Path) -> float:
    """Sum of file sizes under ``path`` in MB. Returns 0.0 if missing.

    Uses Path.rglob — small enough for index dirs and HF caches; we're
    not doing this often.
    """
    if not path.exists():
        return 0.0
    total = 0
    for sub in path.rglob("*"):
        if sub.is_file():
            try:
                total += sub.stat().st_size
            except OSError:
                continue
    return total / (1024 * 1024)


def hf_cache_dir_for(hf_model_id: str, *, root: Path = HF_CACHE_ROOT) -> Path:
    """HF Hub cache layout: models--<org>--<repo>/ under cache root.

    The org/repo separator is replaced with the literal ``--`` token.
    """
    safe = hf_model_id.replace("/", "--")
    return root / f"models--{safe}"


def cleanup_candidate_artifacts(
    candidate: Any,  # EmbeddingCandidate, duck-typed
    *,
    base_dir: Path | str,
    drop_hf_cache: bool = True,
    hf_cache_root: Path | None = None,
) -> CleanupReport:
    """Remove the candidate's eval index; optionally remove HF cache.

    Args:
        candidate: must have .candidate_id, .hf_model_id, .is_control,
            and .index_dir_name() helper.
        base_dir: parent of state/cs_rag_eval/ — usually
            ab_sweep.DEFAULT_AB_BASE_DIR.
        drop_hf_cache: when False, only the index dir is removed; the
            model cache stays. When True the cache is dropped too,
            EXCEPT for control candidates (production depends on
            their cache).
        hf_cache_root: override the HF cache location for tests.

    Returns:
        CleanupReport with bytes freed and a flag indicating whether
        the HF cache deletion was skipped because the candidate is
        control.
    """
    base = Path(base_dir)
    cache_root = hf_cache_root if hf_cache_root is not None else HF_CACHE_ROOT

    # 1. Index dir
    idx_dir = base / candidate.index_dir_name()
    index_freed = _du_mb(idx_dir)
    if idx_dir.exists():
        shutil.rmtree(idx_dir, ignore_errors=False)

    # 2. HF cache
    skipped = False
    cache_freed = 0.0
    if drop_hf_cache:
        if candidate.is_control:
            skipped = True
        else:
            cache_dir = hf_cache_dir_for(candidate.hf_model_id, root=cache_root)
            cache_freed = _du_mb(cache_dir)
            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=False)

    return CleanupReport(
        candidate_id=candidate.candidate_id,
        index_dir_freed_mb=index_freed,
        hf_cache_freed_mb=cache_freed,
        skipped_hf_cache_due_to_control=skipped,
    )
