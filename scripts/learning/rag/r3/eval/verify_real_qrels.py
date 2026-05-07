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
5. ``cohort_eval`` smoke run with a deterministic stub search →
   confirms the harness accepts every record under the current
   Phase 9.3 refusal contract (corpus_gap_probe receives the
   no_confident_match sentinel, forbidden_neighbor sees an empty hit
   list, standard cohorts fail cleanly with a classified failure_class)

Used as: ``python -m scripts.learning.rag.r3.eval.verify_real_qrels
--qrels tests/fixtures/r3_qrels_real_v1.json --report <baseline>.json
--min-report-pass-rate 0.94``

Returns 0 only when every gate is clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from .cohort_eval import _is_refusal_clean_outcome, evaluate_suite
from .cohort_qrels import VALID_COHORTS, load_cohort_qrels


def _load_stub_concepts(sidecar_path: Path) -> set[str]:
    """Load concept IDs already materialized in the lexical sidecar.

    The sidecar is a lane-local artifact generated from the current v3
    corpus. When a concept ID is present there but not yet promoted into
    ``concepts.v3.json``, treat it as a valid stub rather than failing the
    real-qrel gate on catalog lag alone.
    """
    blob = json.loads(sidecar_path.read_text(encoding="utf-8"))
    documents = blob.get("documents") if isinstance(blob, dict) else None
    if not isinstance(documents, list):
        return set()

    concept_ids: set[str] = set()
    for row in documents:
        if not isinstance(row, dict):
            continue
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            continue
        concept_id = metadata.get("concept_id")
        if isinstance(concept_id, str) and concept_id:
            concept_ids.add(concept_id)
    return concept_ids


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
    qrel_path: Path,
    catalog_path: Path,
    sidecar_path: Path | None = None,
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
    if sidecar_path is not None and sidecar_path.exists():
        known.update(_load_stub_concepts(sidecar_path))
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


def _check_cohort_distribution_target(qrel_path: Path) -> list[str]:
    """Validate the declared cohort distribution matches the actual suite.

    The real qrel fixture uses ``cohort_distribution_target`` as the
    baseline contract for cohort-aware regressions. When the declared
    counts drift from the actual query list, the cohort pass rates in
    reports look stable while the measured population has silently
    changed.
    """
    blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    if not isinstance(blob, dict):
        return []
    target = blob.get("cohort_distribution_target")
    queries = blob.get("queries") or []
    if target is None:
        return []
    if not isinstance(target, dict):
        return ["cohort_distribution_target must be an object"]

    actual = Counter((q or {}).get("cohort_tag") for q in queries)
    errors: list[str] = []
    for tag in sorted(VALID_COHORTS):
        declared_raw = target.get(tag, 0)
        try:
            declared = int(declared_raw)
        except (TypeError, ValueError):
            errors.append(
                f"cohort_distribution_target.{tag} is not an integer: "
                f"{declared_raw!r}"
            )
            continue
        observed = actual.get(tag, 0)
        if declared != observed:
            errors.append(
                f"cohort_distribution_target.{tag} mismatch: "
                f"declared {declared}, actual {observed}"
            )
    extra_tags = sorted(set(target) - set(VALID_COHORTS))
    for tag in extra_tags:
        errors.append(f"cohort_distribution_target has unknown cohort key: {tag}")
    return errors


def _check_query_count_metadata(qrel_path: Path) -> list[str]:
    """Validate optional top-level query_count matches the real suite size.

    ``load_cohort_qrels`` already rejects mismatches, but surfacing this as
    a dedicated verification stage makes metadata drift obvious in gate logs
    instead of burying it in a generic loader failure.
    """
    blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    if not isinstance(blob, dict) or "query_count" not in blob:
        return []
    declared_raw = blob.get("query_count")
    queries = blob.get("queries") or []
    try:
        declared = int(declared_raw)
    except (TypeError, ValueError):
        return [f"query_count is not an integer: {declared_raw!r}"]
    if not isinstance(queries, list):
        return []
    actual = len(queries)
    if declared != actual:
        return [f"query_count mismatch: declared {declared}, actual {actual}"]
    return []


def _check_report_contract_shape(report_path: Path) -> list[str]:
    """Validate the supplied report is a cohort-eval artifact, not a wave note.

    Several lane-local JSON artifacts live under ``reports/rag_eval``. The
    cohort gate should fail fast with a direct message when a migration wave
    summary is passed to ``--report`` instead of the baseline cohort-eval
    output that carries ``per_query`` and 94.0 gate metrics.
    """
    report_blob = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report_blob, dict):
        return ["report root must be a JSON object"]

    required_top_level = ("query_count", "overall_pass_rate", "per_cohort", "per_query")
    missing_top_level = [
        key for key in required_top_level if key not in report_blob
    ]
    metadata = report_blob.get("metadata")
    missing_metadata = []
    if not isinstance(metadata, dict):
        missing_metadata = ["metadata"]
    else:
        required_metadata = (
            "fixture_id",
            "schema_version",
            "cohort_distribution_target",
            "qrel_sha256",
        )
        missing_metadata = [
            f"metadata.{key}" for key in required_metadata if key not in metadata
        ]

    if not missing_top_level and not missing_metadata:
        return []

    artifact_hints = [
        key for key in ("wave_id", "baseline_report", "verification", "changes", "notes")
        if key in report_blob
    ]
    errors = [
        "report is not a cohort-eval baseline artifact: "
        f"missing {missing_top_level + missing_metadata}"
    ]
    if artifact_hints:
        errors.append(
            "report looks like a lane summary artifact: "
            f"found {artifact_hints}"
        )
    return errors


def _check_report_alignment(qrel_path: Path, report_path: Path) -> list[str]:
    """Validate a cohort-eval report still matches the current qrel contract.

    This catches the easy-to-miss failure mode where the 94.0 baseline
    report is reused after the fixture changes underneath it.
    """
    qrel_blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    report_blob = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(qrel_blob, dict):
        return []

    errors: list[str] = []
    qrel_queries = qrel_blob.get("queries") or []
    qrel_count = len(qrel_queries) if isinstance(qrel_queries, list) else None
    report_count = report_blob.get("query_count")
    if qrel_count is not None and report_count != qrel_count:
        errors.append(
            f"report.query_count mismatch: report {report_count}, qrels {qrel_count}"
        )
    qrel_query_ids = [
        (q or {}).get("query_id")
        for q in qrel_queries
        if isinstance(q, dict)
    ]
    qrel_query_by_id = {
        (q or {}).get("query_id"): q
        for q in qrel_queries
        if isinstance(q, dict) and (q or {}).get("query_id")
    }

    qrel_fixture_id = qrel_blob.get("fixture_id")
    report_fixture_id = (report_blob.get("metadata") or {}).get("fixture_id")
    if qrel_fixture_id != report_fixture_id:
        errors.append(
            "report.metadata.fixture_id mismatch: "
            f"report {report_fixture_id!r}, qrels {qrel_fixture_id!r}"
        )

    qrel_schema = qrel_blob.get("schema_version")
    report_schema = (report_blob.get("metadata") or {}).get("schema_version")
    if qrel_schema != report_schema:
        errors.append(
            "report.metadata.schema_version mismatch: "
            f"report {report_schema!r}, qrels {qrel_schema!r}"
        )

    qrel_target = qrel_blob.get("cohort_distribution_target")
    report_target = (report_blob.get("metadata") or {}).get("cohort_distribution_target")
    if qrel_target != report_target:
        errors.append("report.metadata.cohort_distribution_target mismatch")

    qrel_sha = _sha256_file(qrel_path)
    report_sha = (report_blob.get("metadata") or {}).get("qrel_sha256")
    if report_sha != qrel_sha:
        errors.append(
            "report.metadata.qrel_sha256 mismatch: "
            f"report {report_sha!r}, qrels {qrel_sha!r}"
        )

    report_per_cohort = report_blob.get("per_cohort")
    if isinstance(report_per_cohort, dict):
        actual = Counter((q or {}).get("cohort_tag") for q in qrel_queries)
        for tag in sorted(VALID_COHORTS):
            total = (report_per_cohort.get(tag) or {}).get("total")
            observed = actual.get(tag, 0)
            if total != observed:
                errors.append(
                    f"report.per_cohort.{tag}.total mismatch: report {total}, qrels {observed}"
                )
    report_per_query = report_blob.get("per_query")
    if not isinstance(report_per_query, list):
        errors.append("report.per_query missing or not a list")
        return errors

    report_query_ids = [
        (q or {}).get("query_id")
        for q in report_per_query
        if isinstance(q, dict)
    ]
    duplicate_report_ids = sorted(
        query_id for query_id, count in Counter(report_query_ids).items()
        if query_id and count > 1
    )
    if duplicate_report_ids:
        errors.append(
            f"report.per_query duplicate query_ids: {duplicate_report_ids}"
        )
    missing_query_ids = sorted(set(qrel_query_ids) - set(report_query_ids))
    unexpected_query_ids = sorted(set(report_query_ids) - set(qrel_query_ids))
    if missing_query_ids or unexpected_query_ids:
        msg = ["report.per_query query_id set mismatch"]
        if missing_query_ids:
            msg.append(f"missing={missing_query_ids[:5]}")
        if unexpected_query_ids:
            msg.append(f"unexpected={unexpected_query_ids[:5]}")
        errors.append("; ".join(msg))
    for row in report_per_query:
        if not isinstance(row, dict):
            continue
        query_id = row.get("query_id")
        qrel_query = qrel_query_by_id.get(query_id)
        if not qrel_query:
            continue
        report_cohort = row.get("cohort_tag")
        expected_cohort = qrel_query.get("cohort_tag")
        if report_cohort != expected_cohort:
            errors.append(
                "report.per_query cohort_tag mismatch for "
                f"{query_id}: report {report_cohort!r}, qrels {expected_cohort!r}"
            )
    return errors


def _check_report_metric_consistency(report_path: Path) -> list[str]:
    """Validate report-level aggregates still match the per-query rows.

    This catches stale derived metrics when someone edits ``per_query`` or
    ``per_cohort`` by hand and forgets to recompute the summary fields that
    the 94.0 gate reads first.
    """
    report_blob = json.loads(report_path.read_text(encoding="utf-8"))
    report_per_query = report_blob.get("per_query")
    report_per_cohort = report_blob.get("per_cohort")
    if not isinstance(report_per_query, list):
        return []
    if not isinstance(report_per_cohort, dict):
        return []

    top_k_raw = report_blob.get("top_k", 5)
    try:
        top_k = int(top_k_raw)
    except (TypeError, ValueError):
        return [f"report.top_k is not an integer: {top_k_raw!r}"]

    errors: list[str] = []
    total_queries = len(report_per_query)
    pass_count = sum(1 for row in report_per_query if (row or {}).get("pass_status"))
    observed_overall = round(pass_count / total_queries, 4) if total_queries else 0.0
    report_overall = report_blob.get("overall_pass_rate")
    if report_overall != observed_overall:
        errors.append(
            "report.overall_pass_rate mismatch: "
            f"report {report_overall}, derived {observed_overall}"
        )

    for tag in sorted(VALID_COHORTS):
        rows = [
            row for row in report_per_query
            if isinstance(row, dict) and row.get("cohort_tag") == tag
        ]
        metrics = report_per_cohort.get(tag)
        if metrics is None:
            errors.append(f"report.per_cohort missing cohort key: {tag}")
            continue
        total = len(rows)
        cohort_pass_count = sum(1 for row in rows if row.get("pass_status"))
        primary_hit_top_k = sum(
            1
            for row in rows
            if (rank := row.get("primary_rank")) is not None and rank <= top_k
        )
        forbidden_hit_top_k = sum(
            1
            for row in rows
            if (rank := row.get("forbidden_hit_rank")) is not None and rank <= top_k
        )
        refusal_clean = sum(
            1
            for row in rows
            if _is_refusal_clean_outcome(str(row.get("actual_outcome")))
        )
        reciprocal_rank_sum = sum(
            1.0 / row["primary_rank"]
            for row in rows
            if row.get("primary_rank") is not None and row["primary_rank"] <= top_k
        )
        expected_metrics = {
            "total": total,
            "pass_count": cohort_pass_count,
            "pass_rate": round(cohort_pass_count / total, 4) if total else 0.0,
            f"recall_at_{top_k}": round(primary_hit_top_k / total, 4) if total else 0.0,
            f"forbidden_hit_rate_at_{top_k}": (
                round(forbidden_hit_top_k / total, 4) if total else 0.0
            ),
            "mrr": round(reciprocal_rank_sum / total, 4) if total else 0.0,
            "refusal_clean": refusal_clean,
        }
        for key, expected in expected_metrics.items():
            observed = metrics.get(key)
            if observed != expected:
                errors.append(
                    f"report.per_cohort.{tag}.{key} mismatch: "
                    f"report {observed}, derived {expected}"
                )
    extra_tags = sorted(set(report_per_cohort) - set(VALID_COHORTS))
    for tag in extra_tags:
        errors.append(f"report.per_cohort has unknown cohort key: {tag}")
    return errors


def _check_report_pass_rate_floor(report_path: Path, minimum: float) -> list[str]:
    """Validate a candidate baseline report still clears the contract floor."""
    report_blob = json.loads(report_path.read_text(encoding="utf-8"))
    observed_raw = report_blob.get("overall_pass_rate")
    try:
        observed = float(observed_raw)
    except (TypeError, ValueError):
        return [f"report.overall_pass_rate is not numeric: {observed_raw!r}"]
    if observed < minimum:
        return [
            "report.overall_pass_rate below minimum: "
            f"observed {observed:.4f}, minimum {minimum:.4f}"
        ]
    return []


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_manifest_qrels_alignment(qrel_path: Path, manifest_path: Path) -> list[str]:
    """Validate the index manifest still points at the current real-qrel fixture."""
    manifest_blob = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_qrels = (((manifest_blob.get("r3") or {}).get("qrels")) or {})
    if not isinstance(manifest_qrels, dict):
        return ["manifest.r3.qrels missing or not an object"]

    qrel_blob = json.loads(qrel_path.read_text(encoding="utf-8"))
    qrel_queries = qrel_blob.get("queries") if isinstance(qrel_blob, dict) else qrel_blob
    qrel_count = len(qrel_queries or []) if isinstance(qrel_queries, list) else None
    qrel_schema = qrel_blob.get("schema_version") if isinstance(qrel_blob, dict) else None
    qrel_sha = _sha256_file(qrel_path)

    errors: list[str] = []
    manifest_path_value = manifest_qrels.get("path")
    qrel_path_value = qrel_path.as_posix()
    if manifest_path_value != qrel_path_value:
        errors.append(
            f"manifest.r3.qrels.path mismatch: manifest {manifest_path_value!r}, qrels {qrel_path_value!r}"
        )

    manifest_query_count = manifest_qrels.get("query_count")
    if qrel_count is not None and manifest_query_count != qrel_count:
        errors.append(
            "manifest.r3.qrels.query_count mismatch: "
            f"manifest {manifest_query_count}, qrels {qrel_count}"
        )

    manifest_schema = manifest_qrels.get("schema_version")
    if qrel_schema is not None and str(manifest_schema) != str(qrel_schema):
        errors.append(
            "manifest.r3.qrels.schema_version mismatch: "
            f"manifest {manifest_schema!r}, qrels {qrel_schema!r}"
        )

    manifest_sha = manifest_qrels.get("sha256")
    if manifest_sha != qrel_sha:
        errors.append(
            f"manifest.r3.qrels.sha256 mismatch: manifest {manifest_sha!r}, qrels {qrel_sha!r}"
        )
    return errors


def _smoke_eval(qrel_path: Path) -> dict:
    suite = load_cohort_qrels(qrel_path)
    corpus_gap_prompts = {
        q.prompt for q in suite.queries if q.cohort_tag == "corpus_gap_probe"
    }

    def _stub_search(prompt, *, debug=None, **kwargs):
        if prompt in corpus_gap_prompts:
            if debug is not None:
                debug["r3_final_paths"] = ["<sentinel:no_confident_match>"]
            return [{
                "path": "<sentinel:no_confident_match>",
                "sentinel": "no_confident_match",
                "rejected_score": -1.0,
            }]
        if debug is not None:
            debug["r3_final_paths"] = []
        return []

    report = evaluate_suite(suite, _stub_search, top_k=5, qrel_path=str(qrel_path))
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
    """The deterministic smoke stub MUST yield:
    - corpus_gap_probe: 100% pass (tier_downgraded refusal sentinel)
    - forbidden_neighbor: 100% pass (no forbidden hit possible)
    - All other cohorts: 0% pass
    """
    errors: list[str] = []
    for tag, metrics in suite_smoke["by_cohort"].items():
        if tag in {"corpus_gap_probe", "forbidden_neighbor"}:
            if metrics["pass_rate"] != 1.0:
                errors.append(
                    f"{tag} stub-smoke pass_rate {metrics['pass_rate']} != 1.0 "
                    f"— refusal cohort should pass on the no_confident_match sentinel or empty hits"
                )
        else:
            if metrics["pass_rate"] != 0.0:
                errors.append(
                    f"{tag} stub-smoke pass_rate {metrics['pass_rate']} != 0.0 "
                    f"— standard cohort should fail under the deterministic empty-hit stub"
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
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=Path("state/cs_rag/r3_lexical_sidecar.json"),
        help="Optional lexical sidecar artifact used to accept current-corpus concept stubs.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional cohort-eval report to verify against the qrel contract.",
    )
    parser.add_argument(
        "--min-report-pass-rate",
        type=float,
        default=None,
        help="Optional minimum overall_pass_rate required when --report is supplied.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("state/cs_rag/manifest.json"),
        help="Optional index manifest whose r3.qrels metadata must match the current fixture.",
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
        errs = _check_concepts_in_catalog(args.qrels, args.catalog, args.sidecar)
        if errs:
            fails.append(("concepts", errs))
    else:
        print(f"[verify-qrels] WARN: catalog missing: {args.catalog}")

    errs = _check_cohort_distribution_target(args.qrels)
    if errs:
        fails.append(("cohort_distribution_target", errs))

    errs = _check_query_count_metadata(args.qrels)
    if errs:
        fails.append(("query_count", errs))

    if args.manifest is not None:
        if args.manifest.exists():
            errs = _check_manifest_qrels_alignment(args.qrels, args.manifest)
            if errs:
                fails.append(("manifest_qrels_alignment", errs))
        else:
            fails.append(("manifest_qrels_alignment", [f"manifest missing: {args.manifest}"]))

    if args.report is not None:
        if args.report.exists():
            errs = _check_report_contract_shape(args.report)
            if errs:
                fails.append(("report_contract_shape", errs))
            else:
                errs = _check_report_alignment(args.qrels, args.report)
                if errs:
                    fails.append(("report_alignment", errs))
                errs = _check_report_metric_consistency(args.report)
                if errs:
                    fails.append(("report_metrics", errs))
                if args.min_report_pass_rate is not None:
                    errs = _check_report_pass_rate_floor(
                        args.report, args.min_report_pass_rate,
                    )
                    if errs:
                        fails.append(("report_pass_rate_floor", errs))
        else:
            fails.append(("report_alignment", [f"report missing: {args.report}"]))

    # Only run smoke if loader passed (otherwise it would re-raise)
    if not any(stage == "loader" for stage, _ in fails):
        try:
            smoke = _smoke_eval(args.qrels)
            invariant_errs = _expected_smoke_invariants(smoke)
            if invariant_errs:
                fails.append(("smoke", invariant_errs))
            print(f"[verify-qrels] stub smoke pass_rate: {smoke['overall_pass_rate']}")
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
