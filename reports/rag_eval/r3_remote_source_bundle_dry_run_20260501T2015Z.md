# R3 Remote Source Bundle Dry Run - 2026-05-01T20:15Z

Scope: verify that the RunPod harness can build from local committed work even
when the selected commit is ahead of `origin/main`.

Command:

```bash
bin/rag-remote-build --r-phase r3 --dry-run
```

Observed result:

- exit code: `0`
- run id: `r3-fde5b6a-2026-05-01T2015`
- local branch state: `48` commits ahead of origin
- selected source mode: git bundle
- dry-run transfer: create bundle for `fde5b6aea757ac9b78ecac3f6ed2cb74b5d62205` and upload to `/workspace/woowa-learning-hub.bundle`
- remote source commands:
  - `git clone /workspace/woowa-learning-hub.bundle /workspace/repo`
  - `cd /workspace/repo && git checkout fde5b6aea757ac9b78ecac3f6ed2cb74b5d62205`
- R3-specific commands still present:
  - `scripts.learning.rag.r3.index.lexical_sidecar`
  - `scripts.remote.package_rag_artifact ... --strict-r3`
- cleanup path: `pod_terminated=true`

Live blocker after this change:

`RUNPOD_API_KEY` is still unset, so live RunPod execution remains blocked by
credentials. The earlier source visibility blocker is removed for committed
local changes; dirty uncommitted work is intentionally not bundled.
