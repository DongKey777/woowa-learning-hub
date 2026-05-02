"""Real-qrel verification helper used during Phase 4.7 expansion.

Runs a full strictness gate over a candidate qrel JSON before it is
committed to the suite:

1. JSON Schema (``tests/fixtures/r3_qrels_schema.json``) validation
2. ``cohort_qrels.load_cohort_qrels`` loads without raising (catches
   primary ⊥ forbidden disjoint, cohort_tag enum, refusal-cohort rule)
3. Every path under ``primary_paths`` / ``acceptable_paths`` /
   ``forbidden_paths`` exists on disk under ``corpus_root`` (with the
   ``contents/`` prefix consistent with v3 frontmatter linked_paths)
4. Every ``expected_concepts`` entry exists as a v3 concept (or stub)
   in ``concepts.v3.json``
5. ``cohort_eval`` smoke run with a no-op search → confirms the harness
   accepts every record (refusal cohorts pass at 100%, others fail
   cleanly with a classified failure_class)

Used as: ``python -m scripts.learning.rag.r3.eval.verify_real_qrels
--qrels tests/fixtures/r3_qrels_real_v1.json``

Returns 0 only when every gate is clean.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .cohort_eval import evaluate_suite
from .cohort_qrels import VALID_COHORTS, load_cohort_qrels


def _check_schema(qrel_path: Path, schema_path: Path) -> list[str]:
    try:
        from jsonschema.validators import Draft202012Validator
    except Exception as exc:  # pragma: no cover — soft-import for environments without jsonschema
        return [f"jsonschema unavailable: {exc!r}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(blob), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errs]


def _check_paths_exist(qrel_path: Path, corpus_root: Path) -> list[str]:
    blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    queries = blob.get("queries") if isinstance(blob, dict) else blob
    errors: list[str] = []
    for q in queries or []:
        qid = q.get("query_id", "<unknown>")
        for field in ("primary_paths", "acceptable_paths", "forbidden_paths"):
            for p in q.get(field) or []:
                if not isinstance(p, str):
                    errors.append(f"{qid}: {field} entry is not a string: {p!r}")
                    continue
                # Paths in qrels start with `contents/...`; resolve under corpus_root
                if p.startswith("contents/"):
                    abs_p = corpus_root / p[len("contents/"):]
                else:
                    abs_p = corpus_root / p
                if not abs_p.exists():
                    errors.append(f"{qid}: {field} path missing: {p}")
    return errors


def _check_concepts_in_catalog(
    qrel_path: Path, catalog_path: Path,
) -> list[str]:
    """Validate every expected_concept resolves to a catalog entry.

    Exception: ``frontier/*`` is a documented gap-marker namespace used
    by corpus_gap_probe queries to signal *intentionally missing*
    concepts. Those entries are accepted without a catalog match.
    """
    blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    queries = blob.get("queries") if isinstance(blob, dict) else blob
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    known = set(catalog.get("concepts", {}).keys())
    errors: list[str] = []
    for q in queries or []:
        qid = q.get("query_id", "<unknown>")
        cohort = q.get("cohort_tag")
        for cid in q.get("expected_concepts") or []:
            if not cid or cid in known:
                continue
            if cohort == "corpus_gap_probe" and cid.startswith("frontier/"):
                continue  # documented gap marker
            errors.append(f"{qid}: expected_concept missing from catalog: {cid}")
    return errors


def _smoke_eval(qrel_path: Path) -> dict:
    suite = load_cohort_qrels(qrel_path)
    # No-op search returns empty hits → refusal cohorts pass, others fail
    def _no_op(prompt, *, debug=None, **kwargs):
        if debug is not None:
            debug["r3_final_paths"] = []
        return []
    report = evaluate_suite(suite, _no_op, top_k=5, qrel_path=str(qrel_path))
    out = {
        "query_count": report.query_count,
        "overall_pass_rate": round(report.overall_pass_rate, 4),
        "by_cohort": {},
    }
    for tag, metrics in report.per_cohort.items():
        if metrics.total > 0:
            d = metrics.to_dict(top_k=report.top_k)
            out["by_cohort"][tag] = {
                "total": d["total"],
                "pass_rate": d["pass_rate"],
            }
    return out


def _expected_smoke_invariants(suite_smoke: dict) -> list[str]:
    """The no-op smoke MUST yield:
    - corpus_gap_probe: 100% pass (clean refusal)
    - forbidden_neighbor: 100% pass (no forbidden hit possible)
    - All other cohorts: 0% pass
    """
    errors: list[str] = []
    for tag, metrics in suite_smoke["by_cohort"].items():
        if tag in {"corpus_gap_probe", "forbidden_neighbor"}:
            if metrics["pass_rate"] != 1.0:
                errors.append(
                    f"{tag} no-op pass_rate {metrics['pass_rate']} != 1.0 "
                    f"— refusal cohort should pass clean on empty hits"
                )
        else:
            if metrics["pass_rate"] != 0.0:
                errors.append(
                    f"{tag} no-op pass_rate {metrics['pass_rate']} != 0.0 "
                    f"— standard cohort should fail when no hits"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("tests/fixtures/r3_qrels_schema.json"),
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=Path("knowledge/cs/contents"),
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("knowledge/cs/catalog/concepts.v3.json"),
    )
    args = parser.parse_args(argv)

    if not args.qrels.exists():
        print(f"[verify-qrels] qrel file missing: {args.qrels}", file=sys.stderr)
        return 2

    blob = json.loads(args.qrels.read_text(encoding="utf-8"))
    queries = blob.get("queries") if isinstance(blob, dict) else blob
    print(f"[verify-qrels] file: {args.qrels}")
    print(f"[verify-qrels] queries: {len(queries or [])}")

    cohort_dist = Counter((q or {}).get("cohort_tag") for q in queries or [])
    print("[verify-qrels] cohort distribution:")
    for tag in sorted(VALID_COHORTS):
        print(f"  {tag:25s} : {cohort_dist.get(tag, 0)}")

    fails: list[tuple[str, list[str]]] = []

    if args.schema.exists():
        errs = _check_schema(args.qrels, args.schema)
        if errs:
            fails.append(("schema", errs))
    else:
        print(f"[verify-qrels] WARN: schema not found at {args.schema} (skipping)")

    try:
        load_cohort_qrels(args.qrels)
    except Exception as exc:
        fails.append(("loader", [f"{type(exc).__name__}: {exc}"]))

    if args.corpus_root.exists():
        errs = _check_paths_exist(args.qrels, args.corpus_root)
        if errs:
            fails.append(("paths", errs))
    else:
        print(f"[verify-qrels] WARN: corpus_root missing: {args.corpus_root}")

    if args.catalog.exists():
        errs = _check_concepts_in_catalog(args.qrels, args.catalog)
        if errs:
            fails.append(("concepts", errs))
    else:
        print(f"[verify-qrels] WARN: catalog missing: {args.catalog}")

    # Only run smoke if loader passed (otherwise it would re-raise)
    if not any(stage == "loader" for stage, _ in fails):
        try:
            smoke = _smoke_eval(args.qrels)
            invariant_errs = _expected_smoke_invariants(smoke)
            if invariant_errs:
                fails.append(("smoke", invariant_errs))
            print(f"[verify-qrels] no-op smoke pass_rate: {smoke['overall_pass_rate']}")
            for tag, metrics in sorted(smoke["by_cohort"].items()):
                print(f"  {tag:25s} pass_rate={metrics['pass_rate']:.2%} n={metrics['total']}")
        except Exception as exc:
            fails.append(("smoke_run", [f"{type(exc).__name__}: {exc}"]))

    if fails:
        print()
        print("[verify-qrels] FAIL — gate(s) not satisfied:")
        for stage, errs in fails:
            print(f"\n  --- {stage} ({len(errs)} error{'s' if len(errs) != 1 else ''}) ---")
            for e in errs[:20]:
                print(f"  {e}")
            if len(errs) > 20:
                print(f"  ... and {len(errs) - 20} more")
        return 1

    print()
    print("[verify-qrels] PASS — schema + loader + paths + concepts + smoke all clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
