"""Learner cohort year resolution.

Peer PR archives mix multiple cohort years (e.g. 2024 and 2025 entries
within the same `prs.sqlite3`), but the schema has no cohort field. To
let downstream layers tag PRs with a freshness caveat, we resolve the
*learner's* current cohort year here.

Resolution order:
  1. ``state/learner/identity.json``'s ``cohort_year`` override (set by
     the learner via ``bin/learner-profile cohort <year>``).
  2. UTC current year as a fallback so first-run learners get a
     reasonable default.

The override is the load-bearing path — we expect every active learner
to set it once. The fallback is only there so unconfigured environments
don't crash.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .paths import learner_identity_path


def current_cohort_year() -> int:
    """Return the learner's cohort year.

    Reads ``state/learner/identity.json`` first; falls back to
    UTC ``datetime.now().year`` only if that file is missing or has no
    valid override.
    """
    try:
        identity = json.loads(learner_identity_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        identity = {}
    override = identity.get("cohort_year") if isinstance(identity, dict) else None
    if isinstance(override, int) and 2000 <= override <= 2100:
        return override
    return datetime.now(timezone.utc).year
