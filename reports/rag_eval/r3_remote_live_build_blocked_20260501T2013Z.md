# R3 Remote Live Build Blocked - 2026-05-01T20:13Z

Scope: verify that the live RunPod build path fails closed when required
credentials are absent, and record remaining prerequisites for the actual R3
remote artifact gate.

Live command:

```bash
RUNPOD_API_KEY= bin/rag-remote-build --r-phase r3
```

Observed result:

- exit code: `2`
- error: `[runpod] RUNPOD_API_KEY env var not set. Either export RUNPOD_API_KEY="$(cat ~/.runpod/api_key)" or add --dry-run.`

Dry-run command:

```bash
bin/rag-remote-build --r-phase r3 --dry-run
```

Observed dry-run result:

- exit code: `0`
- run id: `r3-350fb25-2026-05-01T2013`
- strict R3 package command includes `--strict-r3`
- remote command sequence includes `scripts.learning.rag.r3.index.lexical_sidecar`
- Pod cleanup path reports `pod_terminated=true`
- warnings:
  - working tree not clean, so a fallback path is needed for uncommitted local changes;
  - local branch is `47` commits ahead of `origin/main`, so live `git clone + checkout` requires push or a source-tar/bundle fallback before RunPod can see the selected SHA.

Superseding dry-run:

`reports/rag_eval/r3_remote_source_bundle_dry_run_20260501T2015Z.md` verifies
that committed local changes ahead of `origin/main` now use git bundle source
transfer in dry-run:

- `git clone /workspace/woowa-learning-hub.bundle /workspace/repo`
- `git checkout fde5b6aea757ac9b78ecac3f6ed2cb74b5d62205`

Decision:

The remote harness is fail-closed and still enforces strict R3 packaging in
dry-run, but the actual cutover artifact gate is not complete. A live RunPod
build now requires:

1. `RUNPOD_API_KEY` available in the AI session environment.

Committed local changes ahead of origin are covered by the git bundle fallback.
Dirty uncommitted work is intentionally not included in the bundle; remote
builds must be based on an explicit commit.
