# Agent Operating Contract

## Purpose

This is the canonical operating contract for agents working in `woowa-mission-coach`.

## Core Rules

- Use `coach-run` as the default top-level backend.
- Mission repos are read-only unless the user explicitly asks for code changes.
- Prefer JSON artifacts under `state/repos/<repo>/...` over markdown.
- Treat score as retrieval support only, not as final truth.
- Prefer grounded review evidence over generic PR body text.
- If memory confidence is low, current evidence should dominate.

## First-Run Protocol

When a learner makes their first request on a freshly cloned workbench — or any time the environment is unknown — the AI drives the entire setup itself. The learner never runs CLI commands.

Step through these checks in order. Skip a step only when it is already satisfied.

1. **Workbench directories**. If `state/` or `missions/` does not exist at the repo root, run `./bin/bootstrap`. This is idempotent.
2. **Environment health**. Run `./bin/doctor`. If it reports a FAIL (missing `python3`, unauthenticated `gh`, etc.), surface the exact fix to the learner in Korean and stop — do not fabricate a session.
3. **Mission repo present**. If the learner gave a mission repo URL and `missions/<name>` does not exist, `git clone` it into `missions/`. If only a path was given, trust the path.
4. **Registry entry**. Run `./bin/list-repos`. If the target repo is not registered, run `./bin/onboard-repo` with `--path`, `--upstream`, `--track`, `--mission`, and `--title-contains` inferred from the learner's request and the repo's `origin`/`upstream`/branch. Ask the learner only for fields you cannot infer.
5. **Archive bootstrap**. Read `state/repos/<repo>/archive/status.json`. If `bootstrap_state != ready`, run `./bin/bootstrap-repo --repo <name>`. Warn the learner this can take a few minutes on large repos.
6. **Learner State Assessment**. Before calling `coach-run`, the AI must directly inspect the learner's own repository state. `coach-run` retrieves peer PR evidence; it does **not** read the learner's code. Skipping this step leads to coaching from reviewer comment text alone without ever looking at the code those comments refer to.

   **Budget caps (hard limits)**. This step is a focused scan, not a full audit. Stop at whichever limit comes first.

   | Limit | Cap |
   |---|---|
   | Active PRs deep-dived | 1 (the `target PR` — see selection rule below). Additional open PRs are listed in the snapshot but not deep-dived. |
   | Pending comments read per PR | 20 most recent unresolved threads |
   | File regions read | 10 files, ±20 lines each |
   | GraphQL / REST calls total | 8 |
   | Wall-clock | ~60s; if exceeded, persist what you have and continue |

   If a cap is hit, mark the snapshot `coverage: "partial"` with a `skipped` list and proceed. Do not block the session on a full scan.

   **Target PR selection rule** (deterministic, do not ask the learner unless ambiguous):

   1. If the learner's prompt references a PR number, use it.
   2. Else, if `HEAD` of `missions/<name>` matches the `headRefName` of exactly one open PR, use that PR.
   3. Else, use the most recently updated open PR authored by the learner.
   4. Else (no open PR), there is no target PR — record the state and skip sections E/F code-reading; assessment still runs for A–D and records the snapshot.

   **Cycle is a heuristic, not an identifier**. The learner's work is identified by `(branch, PR number)`. "Cycle" is a best-effort label derived from branch-name patterns (`step\d+`, `cycle-\d+`, `mainN`, etc.) and is stored as `cycle_hint` only. Never block the session on cycle ambiguity. Never ask the learner "which cycle" — ask "which PR or branch" if confirmation is needed.

   **Persistence**. After running sections A–G below, write the result to `state/repos/<repo>/contexts/learner-state.json` (see schema in `schemas/learner-state.schema.json`). This artifact is authoritative for the current and follow-up turns until `coach-run` produces a new one. On subsequent turns of the same session, re-read this file instead of re-running the full scan; re-run if **any** of the following is true:

   - `git rev-parse HEAD` differs from `head_sha`
   - the active PR head SHA differs from `target_pr_detail.number`'s recorded `headRefOid`
   - the **working copy fingerprint** differs (see below) — catches the "learner edited files without committing" case
   - more than 10 minutes elapsed since `computed_at`

   **Working copy fingerprint**. Computed as `sha256(git status --porcelain=v1 output)`. This captures every uncommitted modification, staged change, and untracked file without needing full diff content. Stored in the snapshot as `working_copy.fingerprint`. It is cheap (one `git status` call) and catches the dirty-but-unchanged-HEAD case.

   Perform sections A–G in order. Each sub-step lists a fallback when its primary command fails.

   **A. Repository topology**

   1. `git -C missions/<name> remote -v` — confirm `origin` (learner fork) and `upstream` (woowacourse). If `upstream` is missing, add it: `git -C missions/<name> remote add upstream <upstream-url>` then `git -C missions/<name> fetch upstream`. If the repo has no `upstream` and is itself the canonical repo (same-repo PR workflow), set `upstream_remote = origin` in the snapshot and continue.
   2. `git -C missions/<name> fetch --all --prune` — refresh remote tracking refs. On network failure, continue with stale refs and set `snapshot.fetch_state = "stale"`.
   3. `git -C missions/<name> branch -a` — list local + remote branches. Record as-is; do not force them into a cycle taxonomy.
   4. `git -C missions/<name> log --all --oneline --decorate --graph -n 30` — recent commit topology.

   **B. Working copy state**

   5. `git -C missions/<name> status --porcelain=v1 -b` — current branch, tracking, ahead/behind, uncommitted/untracked. Record the **working copy fingerprint** (`sha256` of the porcelain output) in `working_copy.fingerprint`. If uncommitted changes exist, surface them before coaching — they may be the actual question subject.
   6. `git -C missions/<name> rev-parse --abbrev-ref HEAD` and `git rev-parse HEAD` — current branch name and SHA (SHA is the cache key for re-scan detection).
   7. `git -C missions/<name> log -n 10 --oneline` on the current branch.

   **C. Learner identity**

   8. Parse the GitHub owner from `git -C missions/<name> remote get-url origin`.
   9. Optional sanity check: `gh api user --jq .login`. If it fails (unauthenticated, rate limit), skip — origin-derived owner is sufficient.

   **D. Upstream PR state**

   10. Open PRs authored by the learner:
       `gh pr list --repo <upstream> --author <learner-login> --state open --json number,title,headRefName,baseRefName,url,reviewDecision,isDraft,headRefOid,createdAt,updatedAt`
   11. Recently closed/merged PRs (last 10), same fields plus `mergedAt,closedAt`. Used to show progression, not for coaching.
   12. Build a `prs` table in the snapshot. Each row: `{number, title, head_ref, base_ref, head_sha, review_decision, state, cycle_hint}`. `cycle_hint` is derived from `head_ref` via simple regex and is allowed to be `null`.
   13. Apply the **Target PR selection rule** above to pick exactly one `target_pr`. Record the rule branch that matched.

   **E. Target-PR deep dive** (only the `target_pr`; other PRs are listed but not deep-dived)

   14. `gh pr view <target_pr.number> --repo <upstream> --json number,title,body,headRefName,baseRefName,headRefOid,reviewDecision,reviews,reviewRequests,files,comments,commits,statusCheckRollup`.
   15. `gh api repos/<upstream>/pulls/<target_pr.number>/comments --paginate` — inline review comments. Preserve `in_reply_to_id`. Apply the cap: read the most recent 20 unresolved threads' worth of comments.
   16. **Thread reconstruction**: group by `in_reply_to_id` chain; record role sequence.
   17. **Resolved-state detection** (best-effort, not mandatory):
       - Primary: `gh api graphql` with `repository.pullRequest.reviewThreads(first: 50) { nodes { isResolved, comments { nodes { databaseId } } } }`. Map each `databaseId` back to the REST comment and mark threads `resolved: true|false`.
       - Fallback on GraphQL failure (scope, rate limit, schema change): mark every thread `resolved: "unknown"` and proceed. Coaching should treat `unknown` like `pending` but label them as such in the snapshot.
   18. **Bot filtering**: exclude `coderabbitai`, `github-actions[bot]`, `dependabot[bot]` and other accounts listed in `docs/evidence-roles.md` from the mentor-feedback set. Bots are stored separately in the snapshot for reference.
   19. **Resolve diff refs from actual topology**. Do not hardcode remote names. Resolve both ends, then diff:
       - `base_ref_full = <upstream-remote>/<target_pr.baseRefName>` where `<upstream-remote>` is the remote whose URL matches the upstream repo (fallback: `origin` if same-repo PR).
       - `head_ref_full`: if the PR is from a fork, use `<upstream-remote>/pull/<number>/head` after `git fetch <upstream-remote> pull/<number>/head:pr-<number>` (preferred), or fall back to `<fork-remote>/<headRefName>` if the fork is added as a remote. If the PR is same-repo, use `<upstream-remote>/<headRefName>`.
       - Then: `git -C missions/<name> diff <base_ref_full>...<head_ref_full>`. This is the canonical delta under review — not the PR body text.
       - Record both refs in the snapshot as `diff.base_ref` and `diff.head_ref` so re-runs are reproducible.

   **F. Code reading** (capped; this is where skipping most often hides)

   20. For each pending or unknown-resolved thread on the `target_pr` (up to 10 files, ±20 lines each): open the file at `target_pr.headRefOid` in `missions/<name>` and read the region. Do not quote a reviewer comment without having read the underlying code. If the cited line shifted but the file still exists, use `git blame -L` to locate the current line.
   21. For each thread read, classify as `{still-applies, likely-fixed, already-fixed, ambiguous}`:
       - `already-fixed` requires **strong** evidence. The only accepted strong signal is GraphQL `reviewThread.isResolved=true` (mentor explicitly marked the thread resolved). Textual heuristics alone cannot promote to `already-fixed`.
       - `likely-fixed` is the **weak positive** class. Emit it when the `+` lines from the review comment's `diff_hunk` (the learner's PR code at review time — note: the `-` lines are base-branch code and are meaningless against head) are no longer present in the learner's file at `head_sha`. This means the learner changed that code, but we cannot prove the change addresses the mentor's concern without semantic analysis. Downstream must surface `likely-fixed` as "probably done, verify with `git show`", not as "done."
       - `still-applies` when the cited `+` code is still present (in region or anywhere in the file — pure line-number drift still counts as still-applies, not already-fixed).
       - `ambiguous` is the fallback when evidence is missing (no tokens extractable, file unreadable, budget cap, no head SHA).
       - `classification_reason` on each thread records the machine tag for the decision (`isResolved`, `cited_code_present_in_region`, `cited_code_drift`, `cited_code_removed`, `tokens_missing`, `file_read_cap`, `file_unreadable`, `head_or_path_missing`).
       - Default to `ambiguous` over `likely-fixed` when unsure. False negatives are safer than falsely telling the learner "this is already done."
   22. Read the mission `README.md` and any step-specific requirement docs on the current branch. The requirement spec constrains what "good" means.

   **G. Snapshot emission**

   23. Write `state/repos/<repo>/contexts/learner-state.json` conforming to `schemas/learner-state.schema.json`. Required top-level fields:
       - `computed_at` (ISO8601)
       - `repo`, `mission_path`
       - `head_branch`, `head_sha` (re-scan cache key)
       - `fetch_state`: `"fresh" | "stale"`
       - `upstream_remote`
       - `working_copy`: `{clean, ahead, behind, uncommitted_files, untracked_files}`
       - `prs`: array of rows from step 12
       - `target_pr_number` (nullable) and `target_pr_selection_reason`
       - `target_pr_detail`: **required** field. MUST be `null` iff `target_pr_number` is `null` (selection reason `no_open_pr`). Otherwise MUST be a non-null object containing `threads` with `{id, path, line, author, role, resolved, classification, body_excerpt}`.
       - `diff`: `{base_ref, head_ref}` for reproducibility
       - `coverage`: `"full" | "partial"`; if partial, `skipped` lists what was dropped and why (which cap hit)
       - `cycle_hint` (nullable, derived, informational only)
   24. Produce the learner-facing Korean summary following the **Response Contract** section below. This contract is canonical for all AI runtimes (Claude, Codex, Gemini). Ask for confirmation **only** when the Target PR selection rule hit branch 4 (no open PR) or when the learner's prompt conflicts with the selected target. Never ask "which cycle".

   Only after this assessment, call `./bin/coach-run --path missions/<name> --context coach --prompt "<learner question>"` and proceed with the Standard Operating Flow below. The `learner-state.json` snapshot is authoritative for what the learner's code currently says; `coach-run` output is authoritative for peer evidence. If they conflict on learner-side facts, trust the snapshot and note the discrepancy.

If any step fails, report the failure to the learner in Korean, include the exact command that failed, and suggest the next action. Never silently skip a step.

## Response Contract

This section is **canonical for every AI runtime**. Claude Code, Codex, Gemini, and any skill bundles must enforce it identically — agent-specific files reference this section instead of redefining it.

### Required first block — 상태 요약 (snapshot)

Every learner-facing response begins with a `## 상태 요약` block whose numbers are derived **directly** from `contexts/learner-state.json`. The snapshot reflects the pipeline's classification at `computed_at`. Do not mutate it in the narrative; any turn-local upgrades go in the separate block below.

**Copy, do not recompute.** The pipeline now pre-renders this block as `coach-run.json.response_contract.snapshot_block.markdown`. Paste it verbatim at the top of your reply instead of re-tallying counts. If `snapshot_block.markdown` is `null`, inspect `snapshot_block.reason` (`blocked` / `error` / `no_target_pr`) and follow the matching execution-status handling below.

```
## 상태 요약 (snapshot, computed_at={computed_at})
- 타깃: {head_branch} / PR #{target_pr_number}
- 작업 트리: clean={working_copy.clean}, ahead={ahead}, behind={behind}
- 스레드 {N}개:
  - 이미 반영됨 (already-fixed): {n_af}        ← isResolved=true
  - 반영된 듯 (likely-fixed):   {n_lf}        ← 코드 휴리스틱 기반 약한 증거
  - 남은 피드백 (still-applies): {n_sa}
  - 확인 필요 (ambiguous):       {n_amb}
  - 읽지 않음 (unread):          {n_un}
- 학습자 응답:
  - 텍스트 답글:   {n_text}
  - 이모지 반응:   {n_react}
  - 없음:          {n_none}
  - 불명(fetch 실패): {n_unknown}
```

Rules:
- The five classification counts are `group_by(classification)` over `target_pr_detail.threads[]`. They must match the JSON exactly.
- `이모지 반응` = threads where `learner_acknowledged === true`.
- `불명(fetch 실패)` = threads where `learner_acknowledged === "unknown"` (GraphQL fetch failed). Never merge `"unknown"` into `없음`.
- `텍스트 답글` = threads where some `participants[]` entry has `role=self` and non-empty text. Mutually exclusive with `이모지 반응`/`없음` in that priority order (text wins if both).
- If any field is missing or a value cannot be computed, write `?` and one sentence explaining why. Never invent a number.

### Turn-local verification block

When the narrative upgrades or downgrades any thread — by running `git show` on the learner's file, reading the diff, or any other same-turn evidence — record the delta in a **separate** block. The snapshot block above is immutable per turn.

```
## 이 턴에 직접 확인
- ambiguous {X}건 확인 → already-fixed {a}, still-applies {s}, 여전히 ambiguous {z}
- likely-fixed {Y}건 확인 → already-fixed {a'}, still-applies {s'}
- 수동 확인 필요: {list — 예산 초과 등으로 확인 못 한 항목}
```

This separation resolves the "stats vs. narrative" conflict: the snapshot stays faithful to the JSON, the verification block shows what the agent learned this turn. The learner can see both sides.

### Per-item narrative — dual axis

When discussing any individual thread, show **both axes** on separate lines — never conflate text-reply presence with code-reflection status:

```
- [path:line] 학습 포인트: ...
  - 코드 상태: {classification} (reason: {classification_reason}[, 이 턴에 git show로 확인])
  - 답변 상태: 텍스트 답글 있음 | 이모지 {learner_reactions 원본 값 그대로} | 없음 | 불명
```

- `코드 상태` draws from `classification` + `classification_reason`. If you verified in-turn, append `, 이 턴에 git show로 확인`.
- For `답변 상태 = 이모지`: list every value from `learner_reactions` as-is (e.g. `THUMBS_UP, ROCKET`). Do not normalize them all to 👍.
- If `learner_reactions` mixes positive (`THUMBS_UP`, `HEART`, `HOORAY`, `ROCKET`, `LAUGH`, `EYES`) with dissenting (`THUMBS_DOWN`, `CONFUSED`), annotate as `이모지 혼합 — 일부 이견 가능성`.
- `already-fixed + 답변 없음` and `likely-fixed + 이모지 🚀` are valid states. Narrate them as such.

### `ambiguous` and `likely-fixed` must be verified

For every thread the snapshot classifies as `ambiguous` or `likely-fixed`, run `git show <head_sha>:<path>` on the learner's mission repo **before** writing any narrative about it, within the step-F file-read budget.

- After verification, record the item in the **turn-local block**, not by mutating the snapshot numbers. Promote to `still-applies` or `already-fixed` (or leave as-is if verification is inconclusive).
- If the budget caps you out, list unverified items under `수동 확인 필요`. Never silently assume `ambiguous ≈ still-applies` or `likely-fixed ≈ already-fixed`.

The exact list is pre-rendered at `coach-run.json.response_contract.verification`:
- `verification.required_count == 0` → omit the block entirely.
- Otherwise every entry in `verification.thread_refs[]` must be resolved in the reply by **one** of: (a) a same-turn `git show <head_sha>:<path>` followed by a promotion inside `## 이 턴에 직접 확인`, or (b) copying `verification.stub_markdown` into a `## 수동 확인 필요` section. A `thread_refs` entry that gets neither treatment is a direct-observation gate violation.

### First-response direct-observation gate

No thread may be narrated as `이미 반영됨` or `아직 남아있음` in the first response unless **one** of the following is true:

1. `classification` in `learner-state.json` is exactly `already-fixed` or `still-applies` (not `likely-fixed`, not `ambiguous`, not `unread`), **or**
2. The agent ran `git show <head_sha>:<path>` on the cited path in the current turn.

`likely-fixed` is a **weak** signal and does not satisfy the gate on its own. Either verify with `git show` in the same turn or label the item `수동 확인 필요`. Guessing from thread metadata alone is not allowed.

### Back-end to Standard Operating Flow

After the 상태 요약 + (optional) 이 턴에 직접 확인 blocks, proceed with the normal narrative: current situation, strongest peer evidence, smallest useful next actions, what not to change yet. Distinguish repeated learning point to deepen from underexplored learning point to broaden.

## Standard Operating Flow

1. Resolve repo from path or registry.
   - If this is the first session on a repo or bootstrap state is unclear, run `repo-readiness` first.
2. Auto-detect:
   - origin / upstream
   - branch hint
   - current PR title hint
3. **Check `archive/status.json` before calling `coach-run`**.
   - `uninitialized` → explain that initial learning material collection is needed before full coaching.
   - `bootstrapping` → explain that the learner can continue, but the current answer is based on limited evidence.
   - `ready` → proceed normally.
4. Read `coach-run.json` first. Its embedded `memory` field is the authoritative snapshot for the current session.
5. Read `analysis/mission-map.json` to understand the learner repo itself.
6. Do **not** re-read `memory/profile.json` or `memory/summary.json` by default. They are the next-session initial context, not a primary source. Open them only when the embedded snapshot is missing a field you specifically need.
7. Read `coach-candidate-interpretation.json` and `coach-focus.json` if you need stronger peer evidence.
8. Read `coach-response.json` only as a reference artifact.
9. Drill into lower-level packet artifacts only if needed. Consult `docs/token-budget.md` before opening packet files.
10. Answer with:
   - current situation
   - strongest evidence
   - immediate next actions
   - what not to change yet

## Coach-Run Contract

- `coach-run.json` is the canonical top-level artifact.
- It should always keep the same top-level shape.
- State differences should be expressed by `execution_status`, not by returning a fundamentally different object.
- Expected values:
  - `execution_status=ready`
  - `execution_status=blocked` — data insufficient, session not started
  - `execution_status=error` — session started but commit/save failed

If blocked:

- `archive_status` explains why
- `archive_sync` contains the next bootstrap action
- `session` and `memory` still exist as fields
- `coach_reply` still exists as a user-facing explanation
- the explanation should say:
  - why the current evidence is limited
  - that initial collection is a one-time setup step

If error:

- `error_detail` contains `phase`, `message`, `timestamp`
- `memory` still contains the latest computed snapshot (may not be persisted to disk yet)
- AI should read `memory` for context but note that evidence from the current session may be incomplete
- AI should suggest retrying the session and inform the learner that the previous attempt encountered a system issue
- If canonical `actions/coach-run.json` write itself failed, the error payload is written to the sidecar `actions/coach-run.error.json`. In that case the return payload sets `canonical_write_failed: true`, `error_detail.sidecar_path` points to the sidecar, and `json_path` reflects the sidecar location. AI consumers should read the sidecar when `coach-run.json` is stale or missing after an error and `coach-run.error.json` exists.

## Bootstrap vs. Coaching

`coach-run` never performs a full PR collection. It runs only incremental syncs on an already-bootstrapped repo.

The first-time data collection for a repo must go through:

- `bin/bootstrap-repo --repo <name>` (or `bin/onboard-repo` followed by `bin/bootstrap-repo`)

Bootstrap state is recorded in `state/repos/<repo>/archive/status.json`:

- `bootstrap_state`: `uninitialized` | `bootstrapping` | `ready`
- `data_confidence`: `bootstrap` | `partial` | `ready`

If `coach-run` is called on an `uninitialized` repo, the returned payload keeps the canonical shape (`run_type: "coach_run"`) but sets `execution_status: "blocked"`. The bootstrap instruction lives in `archive_sync.next_command`, and `archive_sync.blocked=true` signals that no session ran.

## Canonical Artifact Priority

1. `actions/coach-run.json` (the embedded `memory` field is authoritative)
2. `analysis/mission-map.json`
3. `contexts/coach-candidate-interpretation.json`
4. `contexts/coach-focus.json`
5. `actions/coach-response.json` as an optional reference
6. `memory/profile.json` and `memory/summary.json` only when the embedded snapshot is insufficient
7. lower-level packets only when interpretation + focus are insufficient

See:

- [artifact-catalog.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/artifact-catalog.md)

## Recommendation Rules

- Do not recommend a PR only because it has the highest retrieval score.
- Organize peer recommendations by learning point.
- Distinguish:
  - deepen repeated learning points
  - broaden underexplored learning points
- Prefer recommendations with grounded evidence quotes.
- If a recommendation has no grounded evidence quote, do not make it the primary recommendation.
- If learning-memory profile confidence is low, say that explicitly.

## Memory Rules

- Use question and diff fingerprints to separate learner repetition from repeated processing of the same diff.
- Use decay so recent sessions matter more than stale sessions.
- Use confidence to decide whether memory should meaningfully steer recommendation priority.
- `memory/profile.json` is persisted truth. `coach-run.json.unified_profile` is a derived per-turn projection — never write back.

## CS Readiness and Intent-Aware Blocks

- `cs_readiness.state` is reported separately from `execution_status`. Missing/stale indexes never downgrade `execution_status=ready`; `blocked` is reserved for archive/bootstrap issues.
- On `intent_decision.detected_intent == "cs_only"` with `cs_readiness.state != "ready"`: the 1st `coach-run` payload is a diagnostic, **not** learner-facing. Run `bin/cs-index-build` (the command surfaced in `cs_readiness.next_command`) and re-invoke `coach-run`. Only the 2nd payload is used to compose the learner reply. If the 2nd attempt still fails, report the failure in Korean and degrade to peer-only.
- On `mission_only`: rebuild is advisory. Use the 1st payload directly.
- On `mixed` / `drill_answer`: rebuild is advisory; AI decides based on `cs_augmentation` completeness.
- `response_contract.{cs_block, drill_block, drill_result_block}` each carry an `applicability_hint ∈ {primary, supporting, omit}`. This is advisory — include the `primary` and `supporting` blocks, skip `omit`. AI may reinterpret based on the learner's question.
- `cs_block` is a rendered view of `cs_augmentation`. If they disagree, trust `cs_augmentation` and re-render.

## Drill UX Rules

- Drill offers are optional. Learners may ignore or decline with no penalty.
- Do not re-offer within 3 turns of a previous offer (handled by `drill.build_offer_if_due`).
- `drill_block.markdown` should be copied as-is into the reply when `applicability_hint != "omit"`, but wording should make opt-out trivial.
- When `drill_result_block` is present, acknowledge the previous drill briefly but keep the main focus on the learner's current question.
- A turn classified as `drill_answer` never produces a new drill offer — `build_offer_if_due` refuses to avoid stacking feedback loops.

## Safety

- Do not modify the mission repo during learning-only questions.
- Keep all state changes inside `woowa-mission-coach/state`.
- If evidence is weak, say that it is weak.

## Outputs

A good answer should include:

- what is going on now
- why the evidence supports that interpretation
- what to do next
- what to postpone
- one useful follow-up question

Do not treat `coach-response.json` as a final answer to copy.
It is only a reference bundle that may help structure the answer.
