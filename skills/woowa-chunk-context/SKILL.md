# Woowa Chunk Context

Use this skill when filling `chunk-context-v1.output` artifacts prepared by
`bin/chunk-context-prepare`.

## Task

Read one `chunk-context-v1.input` JSON file and write the matching
`chunk-context-v1.output` JSON file at `expected_output_path`.

The output context is retrieval-only. It is prepended before embedding and FTS
term generation, but it must not be rendered to learners as document body.

## Output Schema

```json
{
  "schema_id": "chunk-context-v1.output",
  "chunk_id": "same as input",
  "context": "50-100 Korean tokens of chunk-specific retrieval context",
  "retrieval_only": true,
  "scored_by": "ai_session",
  "produced_at": "ISO 8601"
}
```

## Writing Rules

- Write in Korean unless the source chunk is primarily code or English terms.
- Keep the context specific to this chunk's role inside its document.
- Include likely learner search wording, Korean aliases, and canonical CS terms.
- Do not quote long source passages. Paraphrase instead.
- Do not introduce facts that are not supported by the chunk title, section path,
  body, anchors, or difficulty.
- Keep the output JSON only; no markdown wrapper.
