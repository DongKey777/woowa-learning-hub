from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MISSIONS_DIR = ROOT / "missions"
STATE_DIR = ROOT / "state"
REGISTRY_PATH = STATE_DIR / "repo-registry.json"
PR_ARCHIVE_DIR = ROOT / "scripts" / "pr_archive"
DEFAULT_SCHEMA_PATH = PR_ARCHIVE_DIR / "schema.sql"
LEGACY_PR_DATASETS_DIR = STATE_DIR / "pr-datasets"
ORCHESTRATOR_DIR = STATE_DIR / "orchestrator"
LEARNER_DIR = STATE_DIR / "learner"


def ensure_global_layout() -> None:
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "cache").mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text(json.dumps({"repos": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_orchestrator_layout() -> Path:
    ensure_global_layout()
    ORCHESTRATOR_DIR.mkdir(parents=True, exist_ok=True)
    return ORCHESTRATOR_DIR


def repo_state_dir(repo_name: str) -> Path:
    return STATE_DIR / "repos" / repo_name


def ensure_repo_layout(repo_name: str) -> Path:
    ensure_global_layout()
    repo_dir = repo_state_dir(repo_name)
    (repo_dir / "archive").mkdir(parents=True, exist_ok=True)
    (repo_dir / "analysis").mkdir(parents=True, exist_ok=True)
    (repo_dir / "packets").mkdir(parents=True, exist_ok=True)
    (repo_dir / "contexts").mkdir(parents=True, exist_ok=True)
    (repo_dir / "actions").mkdir(parents=True, exist_ok=True)
    (repo_dir / "cache").mkdir(parents=True, exist_ok=True)
    (repo_dir / "profiles").mkdir(parents=True, exist_ok=True)
    (repo_dir / "memory").mkdir(parents=True, exist_ok=True)
    _migrate_legacy_archive_db(repo_name, repo_dir / "archive" / "prs.sqlite3")
    return repo_dir


def _migrate_legacy_archive_db(repo_name: str, target_db: Path) -> None:
    legacy_db = LEGACY_PR_DATASETS_DIR / f"{repo_name}-prs.sqlite3"
    if target_db.exists() and target_db.stat().st_size > 0:
        return
    if legacy_db.exists() and legacy_db.stat().st_size > 0:
        shutil.copy2(legacy_db, target_db)


def repo_archive_db(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "archive" / "prs.sqlite3"


def repo_packet_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "packets"


def repo_analysis_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "analysis"


def repo_context_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "contexts"


def repo_action_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "actions"


def repo_profile_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "profiles"


def repo_memory_dir(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "memory"


def ensure_learner_layout() -> Path:
    ensure_global_layout()
    LEARNER_DIR.mkdir(parents=True, exist_ok=True)
    return LEARNER_DIR


def learner_history_path() -> Path:
    return LEARNER_DIR / "history.jsonl"


def learner_profile_path() -> Path:
    return LEARNER_DIR / "profile.json"


def learner_summary_path() -> Path:
    return LEARNER_DIR / "summary.json"


def learner_identity_path() -> Path:
    return LEARNER_DIR / "identity.json"


def learner_drill_pending_path() -> Path:
    return LEARNER_DIR / "drill-pending.json"


def learner_response_quality_path() -> Path:
    return LEARNER_DIR / "response-quality.jsonl"
