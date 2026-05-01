# R3 Remote Strict Harness Dry Run - 2026-05-01T19:11Z

Command:

```bash
.venv/bin/python -m scripts.remote.runpod_rag_full_build \
  --r-phase r3 \
  --dry-run \
  --repo-root . \
  --ledger-path /tmp/rag-r3-remote-dry-ledger.json \
  --max-cost 5.0 \
  --max-duration 30 \
  --modalities fts,dense,sparse \
  --max-length 512
```

Result:

| Field | Value |
|---|---|
| exit code | 0 |
| run id | `r3-6f9c09d-2026-05-01T1911` |
| pod terminated | `true` |
| dry run | `true` |
| error | `null` |

Verified code contract:

- R3 remote package command includes `--strict-r3`.
- Strict metadata includes build command, `pyproject.toml` sha256 package lock, qrel sha256, and M5 local runtime profile.
- Live `step_5_to_11_remote_build` calls `verify_artifact_dir(..., strict_r3=True, verify_import=True)` after artifact download.
- Verification output is written to `artifact_contract.json` in the artifact directory.
- Verification failure raises and therefore prevents a remote build from being reported as successful.

Tests:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_runpod_rag_full_build.py \
  tests/unit/test_remote_artifact_contract.py \
  tests/unit/test_package_rag_artifact.py
```

Result: `76 passed, 2 warnings`.

Live RunPod status:

- `RUNPOD_API_KEY`: unset in this environment.
- Actual remote artifact import remains blocked until a live RunPod credential is available or installed into the session.
