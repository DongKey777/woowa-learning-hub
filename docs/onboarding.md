# Onboarding

## 1. Base Setup

```bash
./bin/bootstrap
./bin/doctor
```

## 2. Mission Repo Setup

The recommended location is under `missions/`.

```bash
cd missions
git clone https://github.com/woowacourse/java-janggi.git
cd ..
```

## 3. Repo Registration (optional)

```bash
./bin/onboard-repo \
  --path missions/java-janggi \
  --upstream woowacourse/java-janggi \
  --track java \
  --mission java-janggi \
  --title-contains "사이클2"

./bin/list-repos
```

## 4. Check Readiness Before the First Session

```bash
./bin/repo-readiness --path missions/java-janggi
./bin/mission-map --path missions/java-janggi
```

This step verifies:

- whether the current repo can be auto-registered
- whether `gh` is authenticated
- whether bootstrap is needed
- what the immediate next step is
- how the mission repo itself was understood

## 5. PR Collection

If the repo has no initial full collection yet:

```bash
./bin/bootstrap-repo --repo java-janggi
```

This step is a one-time preparation that pulls peer PRs and reviews as learning material. Once collected, later sessions reuse this archive and run much faster.

If bootstrap fails:

- the command does not just end with an error string
- it returns the current `archive_status`
- it returns a retriable next step in structured form

To inspect the current archive state:

```bash
./bin/archive-status --repo java-janggi
```

```bash
./bin/sync-prs \
  --repo java-janggi \
  --mode full
```

Collected data is stored under:

- `state/repos/<repo>/archive/prs.sqlite3`

If `track`, `mission`, and `title-contains` are stored via `onboard-repo`, `sync-prs` reuses them as defaults.

## 6. Agent Sessions Start From `coach-run`

```bash
./bin/coach-run --path missions/java-janggi --context coach --prompt "이 리뷰 기준 다음 액션 뭐야?"
```

This command:

- auto-detects repo metadata
- auto-resolves the upstream repo
- checks PR archive freshness and syncs when needed
- generates context, next-action, response, and memory artifacts

## 7. Lower-Level Commands (use only when needed)

```bash
./bin/topic --repo java-janggi --topic Repository --query Repository
./bin/reviewer --repo java-janggi --reviewer syoun602
./bin/compare --repo java-janggi --prs 346 338 277
./bin/my-pr --repo java-janggi --pr 346
./bin/coach --repo java-janggi --prompt "내 리뷰 기준 다음 액션 뭐야?"
./bin/coach --repo java-janggi --pr 346 --prompt "이 PR 기준으로 지금 뭘 먼저 고쳐야 해?"
./bin/coach --repo java-janggi --reviewer syoun602 --prompt "이 리뷰어 관점에서 내 코드의 리스크가 뭐야?"
./bin/next-action --repo java-janggi --context coach
```

## 8. Developer Verification Tools

```bash
./bin/validate-state --repo java-janggi
./bin/mission-map --repo java-janggi
./bin/golden
./bin/registry-audit
```

- `validate-state`: verifies that current repo artifacts satisfy the latest schema contracts
- `mission-map`: verifies that mission analysis artifacts have the expected structure
- `golden`: regression check that the key structural fields of `coach-run` are preserved
- `registry-audit`: inspects multiple mission repos at once to verify generalization

## 9. Next Steps

- Read the packets and interpret them against `playbooks/pr-learning-pipeline.md`.
- Connect the interpretation back to the learner's own code and PR.
- `./bin/coach` infers the topic and learning intent from the prompt and current diff, and when needed bundles reviewer packets and PR context so the agent can start interpretation immediately.
- `./bin/next-action` reads the generated context and outputs the ordered list of actions to perform right now.
