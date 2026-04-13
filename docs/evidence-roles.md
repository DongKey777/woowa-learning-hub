# Evidence Roles

## Purpose

This document defines how review evidence is labeled by role and how agents should consume each role.

Evidence in this system comes from three channels:

1. inline review comments (`pull_request_review_comments_current`)
2. review bodies (`pull_request_reviews_current`)
3. PR issue comments (`pull_request_issue_comments_current`)

Each channel carries a role label that distinguishes bot output, mentor feedback, and learner self-replies. Agents must respect these labels when building learner-facing recommendations.

## Role Definitions

### Review comments (`comment_role`)

| Role | Condition | Agent treatment |
|---|---|---|
| `bot` | author is in `BOT_USERS` (coderabbitai, github-actions, dependabot) | excluded from evidence |
| `mentor_original` | root comment by non-author | strongest mentor signal |
| `mentor_followup` | reply by non-author whose parent is a crew reply | strong mentor signal |
| `crew_self_reply` | reply by the PR author | reference only, not mentor evidence |
| `crew_self_original` | root comment by the PR author | reference only |

Scoring weight applied in `session_focus.py`:

- `mentor_original` = 1.0
- `mentor_followup` = 0.8
- `crew_self_reply` = 0.3
- `crew_self_original` = 0.2
- `bot` = 0.0 (excluded before scoring)

### Review bodies (`reviewer_role`)

| Role | Condition |
|---|---|
| `bot` | author in `BOT_USERS` |
| `mentor` | author is not the PR author |
| `self` | author is the PR author |

### Issue comments (`comment_role`)

Same values as review bodies: `bot`, `mentor`, `self`.

## Packet Buckets

`packets.py` splits review comments into role buckets so that agents do not mistake learner self-replies for mentor feedback:

| Bucket | Contents | Use |
|---|---|---|
| `mentor_comment_samples` | `mentor_original` + `mentor_followup` | primary teaching evidence |
| `crew_response_samples` | `crew_self_reply` | learner response examples only |
| `crew_original_samples` | `crew_self_original` | learner self-note examples only |

Backward compatibility: `representative_comments` is still present as a flattened view with mentor rows sorted first. New consumers should read the bucket fields directly.

## Thread Reconstruction

For review comments, `thread_builder.py` reconstructs reply chains via `in_reply_to_github_comment_id`. Each thread sample carries:

- `thread_id`
- `path`, `line`
- `role_sequence` (e.g., `mentor→crew→mentor`)
- `participants[]` with `role`, `author`, `body_excerpt`

Budget caps:

- max 5 thread samples per packet
- max 3 turns per thread (root + 2 replies)
- root excerpt 220 chars, reply excerpt 150 chars

Agents should prefer the last mentor turn in a thread when quoting, because it represents the closing feedback after the learner responded.

## Agent Rules

1. Never cite a `bot` row as mentor feedback.
2. Never cite `crew_self_reply` as "what the mentor said". It is the learner's own reply.
3. When a thread has depth ≥ 2, prefer the last mentor turn as the primary quote.
4. When showing "what the learner previously answered", label it explicitly as the learner's response, not as mentor feedback.
5. Mention role sequence (e.g., "mentor pointed this out, learner replied, mentor closed with…") when it clarifies the teaching direction.

## Migration Safety

Legacy databases without role columns are handled via `_has_column()` check in the query layer. Queries fall back to the unfiltered form when the column is missing. Null role values are treated as "pending classification" and not filtered out, so older archives keep working until `classify_*` is rerun.

## Related Code

- `scripts/workbench/core/comment_classifier.py`
- `scripts/workbench/core/thread_builder.py`
- `scripts/workbench/core/packets.py`
- `scripts/workbench/core/session_focus.py`
- `scripts/workbench/core/candidate_interpretation.py`
- `scripts/workbench/core/response.py`
