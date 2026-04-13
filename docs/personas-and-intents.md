# Personas And Intents

## Learner Personas

### Beginner

Traits:
- Cannot immediately interpret review comments.
- Does not know which file to read first.
- Fixing errors is more urgent than comparing structures.

Agent behavior:
- Summarize in plain language.
- Cite file and review locations explicitly.
- Propose one next action at a time.

### Intermediate

Traits:
- Wants to learn by comparing with other crew implementations.
- Wants to identify a reviewer's repeated perspective.
- Weighs structure refactoring against test coverage.

Agent behavior:
- Compare across packets.
- Provide reviewer lens.
- Propose 2–3 prioritized actions.

### Advanced

Traits:
- Treats design trade-offs themselves as learning targets.
- Evaluates "is it worth changing now?".
- Distinguishes between replying with explanation vs. reflecting in code.

Agent behavior:
- Interpret in terms of trade-offs.
- Explain change cost and effect.
- Separate code-change, explanation-reply, and postpone responses.

## Profile Layer

The system can store a per-repo learner profile.

Example fields:
- `experience_level`
- `preferred_depth`
- `focus`
- `recent_weaknesses`

The agent reads the profile to adjust explanation depth and the number of next actions.

## Reviewer Lens Bundles

### Convention Lens

- getters, naming, blank lines, variable names, column names

### Responsibility Lens

- Repository / DAO / Service / Domain boundaries

### Consistency Lens

- transactions
- atomicity
- rollback
- data integrity

### Test Lens

- state-change tests
- scenario tests
- test name matching behavior

### Explanation Lens

- PR body clarity
- design rationale
- question clarity

Reviewer profiles infer these lenses from representative comments and hotspot paths and persist them.

## Intent Taxonomy

### `review_triage`

Example questions:
- "What should I do next based on my review?"
- "What should I fix first?"

Required inputs:
- my-pr context
- reviewer packet
- PR report

### `concept_explanation`

Example questions:
- "Why shouldn't Repository know this?"
- "What is a transaction boundary?"

Required inputs:
- topic packet
- current repo diff

### `peer_comparison`

Example questions:
- "How did other crews handle this?"
- "What is the structural difference between crew X and me?"

Required inputs:
- compare packet
- topic packet

### `reviewer_lens`

Example questions:
- "From this reviewer's perspective, what is the core point?"

Required inputs:
- reviewer packet
- PR report
- reviewer candidates

### `implementation_planning`

Example questions:
- "How should I split this refactor?"
- "In what order should I refactor?"

Required inputs:
- coach context
- git diff

### `testing_strategy`

Example questions:
- "Which test should I add first?"
- "How do I verify this change?"

Required inputs:
- git diff
- review comments
- next-action
- intent scoring that weights test-related wording strongly

### `pr_response`

Example questions:
- "How should I reply to this review?"
- "Reply with explanation or fix in code?"

Required inputs:
- PR report
- reviewer packet
- current diff

## Expected Output By Intent

### Shared output

- conclusion
- evidence
- file/review location
- next action

### Intent-specific additions

- `review_triage`: priority ordering
- `concept_explanation`: concept explanation
- `peer_comparison`: comparison points
- `reviewer_lens`: repeated perspective
- `implementation_planning`: step-by-step fix order
- `testing_strategy`: test scenarios
- `pr_response`: reply draft direction
