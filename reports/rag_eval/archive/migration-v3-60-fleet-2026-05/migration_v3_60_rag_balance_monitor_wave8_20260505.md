# migration_v3_60 rag balance monitor wave 8

- Scope: audited the next non-Pilot drift/saturation frontmatter targets and stopped before an out-of-scope write.
- Learner-facing gain: this wave reduces requeue churn by documenting the exact blocker instead of landing corpus edits that would fail the current authoring gate.
- Guardrail: no Pilot-locked docs were touched, and no out-of-scope script change was kept.

## Blocked targets

- `knowledge/cs/contents/software-engineering/anti-corruption-mapping-drift.md`
- `knowledge/cs/contents/design-pattern/event-contract-drift-triage-rebuilds.md`
- `knowledge/cs/contents/operating-system/run-queue-load-average-cpu-saturation.md`

## Blocking condition

- `scripts/lint_cs_authoring.py` still requires the first non-empty line to be `# ...`.
- v3 YAML frontmatter must sit before the H1, so these advanced/expert docs would fail the gate even though their body templates are otherwise exempt.
- This lane's hard write boundary excludes `scripts/**`, so the necessary linter repair has to be queued elsewhere before the corpus docs can be migrated safely.
