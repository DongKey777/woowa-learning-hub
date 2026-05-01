"""Apply ko query rewrites to the legacy fixture and emit a new fixture.

Reads `tests/fixtures/cs_rag_golden_queries.json` (the legacy fixture)
and the rewrite map at
`tests/fixtures/cs_rag_golden_queries_ko_rewritten.json`. Produces
`tests/fixtures/cs_rag_golden_queries_ko_rewritten_applied.json` with
ko query prompts swapped where a rewrite is provided. Type A (None
in the rewrite map) keeps the original prompt.

Usage:
    python tests/fixtures/_apply_ko_rewrites.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
FIXTURE = ROOT / "tests/fixtures/cs_rag_golden_queries.json"
REWRITES = ROOT / "tests/fixtures/cs_rag_golden_queries_ko_rewritten.json"
OUT = ROOT / "tests/fixtures/cs_rag_golden_queries_ko_rewritten_applied.json"

base = json.loads(FIXTURE.read_text(encoding="utf-8"))
rew = json.loads(REWRITES.read_text(encoding="utf-8"))
mapping = rew["_query_rewrites"]
mapping = {k: v for k, v in mapping.items() if not k.startswith("_")}

queries = base if isinstance(base, list) else base.get("queries", [])
applied = 0
for q in queries:
    qid = q.get("query_id") or q.get("id")
    if qid in mapping and mapping[qid] is not None:
        q["prompt"] = mapping[qid]
        applied += 1

OUT.write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"applied {applied}/{len(mapping)} ko rewrites")
print(f"wrote {OUT}")
