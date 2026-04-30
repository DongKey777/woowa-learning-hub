# RAG Index Rollback Runbook

Purpose: restore the legacy v2 CS RAG index if the R2 LanceDB cutover fails.

The learner does not run these commands. An AI session runs them and reports
one Korean status line per step.

## Preconditions

- Current repository root: `/Users/idonghun/IdeaProjects/woowa-learning-hub`
- Legacy archive exists under `state/cs_rag_archive/v2_<stamp>/`
- Current production index is `state/cs_rag/`
- No `bin/coach-run` or `bin/rag-ask` process is actively using the index

Check active processes:

```bash
pgrep -fl 'coach-run|rag-ask|cs-index-build'
```

If any long-running index/search process is active, wait for it to finish
before moving directories.

## Restore Steps

Set a timestamp in the shell running the restore:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
```

Move the failed Lance index aside:

```bash
mv state/cs_rag "state/cs_rag_failed_lance_${STAMP}"
```

Restore the archived v2 directory. Replace `<v2_stamp>` with the archive
directory chosen for rollback:

```bash
mv "state/cs_rag_archive/v2_<v2_stamp>" state/cs_rag
```

Verify the restored manifest is legacy v2:

```bash
python3 - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("state/cs_rag/manifest.json").read_text(encoding="utf-8"))
assert manifest.get("index_version") == 2, manifest
assert Path("state/cs_rag/index.sqlite3").exists()
assert Path("state/cs_rag/dense.npz").exists()
print("legacy_v2_manifest_ok")
PY
```

Run offline smoke:

```bash
HF_HUB_OFFLINE=1 bin/rag-ask "트랜잭션 격리수준"
HF_HUB_OFFLINE=1 bin/rag-ask "Spring Bean이 뭐야"
HF_HUB_OFFLINE=1 bin/rag-ask "What is dependency injection"
```

Expected smoke result:

- JSON output is produced for all three commands.
- `decision.tier` is 1 or 2 for each learning prompt.
- `hits.meta.rag_ready` is `true`.
- each prompt has at least three returned hits in `hits.by_fallback_key`.

## If Restore Smoke Fails

1. Do not delete `state/cs_rag_failed_lance_<stamp>`.
2. Run `bin/doctor`.
3. Run `bin/cs-index-build --backend legacy --mode full`.
4. Re-run the three offline smoke commands.
5. Record the failure and recovery notes in a worklog under `docs/worklogs/`.

## Post-Restore Notes

- The failed Lance index directory is intentionally preserved for diagnosis.
- Do not retry cutover until the cutover comparator and smoke failure are both
  explained.
- After a successful restore, `integration.augment()` should report
  `meta.backend == "legacy"` because the restored manifest has
  `index_version == 2`.
