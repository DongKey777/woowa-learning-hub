# External AI Review Checklist

Use this when another AI is reviewing the system itself rather than answering a learner question.

## Architecture

- Are retrieval, shortlist, interpretation, response, and memory separated cleanly?
- Is any layer redundant or too coupled?
- Are artifact boundaries stable and testable?

## Retrieval

- Is mission relevance too dependent on title/stage heuristics?
- Is same-stage reranking overly biased by noisy file overlaps?
- Are generic PR template texts filtered well enough?

## Interpretation

- Does learning-point interpretation meaningfully improve over raw ranking?
- Is the taxonomy too broad, too narrow, or too Java/JDBC-specific?
- Are explanations grounded in real review evidence?

## Memory

- Does memory store enough to identify actual learning patterns?
- Does the system distinguish repeated focus from stale repetition?
- Are underexplored learning points computed sensibly?

## Recommendation Quality

- Does the final answer distinguish:
  - deepen repeated learning points
  - broaden underexplored learning points
- Does the system avoid presenting raw score as final truth?

## Safety

- Does every agent-facing path preserve mission repo read-only by default?
- Are state artifacts kept outside the mission repo?

## Maintainability

- Are schemas updated with every new artifact?
- Is there a canonical document set that another AI can follow without guesswork?
