"""Compare legacy-vs-Lance RAG evaluation reports for production cutover."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "reports" / "rag_eval"
REGRESSION_TOLERANCE = -0.01
FLOAT_EPSILON = 1e-12


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_run(payload: dict[str, Any]) -> dict[str, Any]:
    runs = payload.get("runs")
    if isinstance(runs, list) and runs:
        best_modalities = tuple(payload.get("best_modalities") or ())
        if best_modalities:
            for run in runs:
                if tuple(run.get("modalities") or ()) == best_modalities:
                    return run
        return max(
            runs,
            key=lambda run: float(run.get("primary_ndcg_macro") or float("-inf")),
        )
    if "run_report" in payload:
        return payload
    return {"run_report": payload}


def _run_report(run: dict[str, Any]) -> dict[str, Any]:
    report = run.get("run_report")
    return report if isinstance(report, dict) else run


def _axis_report(report: dict[str, Any], metric: str, axis: str) -> dict[str, Any]:
    macro_reports = report.get("macro_reports") or {}
    metric_reports = macro_reports.get(metric) or {}
    axis_report = metric_reports.get(axis) or {}
    return axis_report if isinstance(axis_report, dict) else {}


def _bucket_value(report: dict[str, Any], metric: str, axis: str, bucket: str) -> float | None:
    values = _axis_report(report, metric, axis).get("per_bucket_mean") or {}
    value = values.get(bucket)
    return float(value) if isinstance(value, (int, float)) else None


def _bucket_count(report: dict[str, Any], metric: str, axis: str, bucket: str) -> int | None:
    values = _axis_report(report, metric, axis).get("per_bucket_count") or {}
    value = values.get(bucket)
    return int(value) if isinstance(value, int) else None


def _macro_primary(run: dict[str, Any], report: dict[str, Any]) -> float | None:
    value = run.get("primary_ndcg_macro")
    if isinstance(value, (int, float)):
        return float(value)
    value = _axis_report(report, "primary_ndcg", "category").get("macro_mean")
    return float(value) if isinstance(value, (int, float)) else None


def _overall(report: dict[str, Any], metric: str) -> float | None:
    value = (report.get("overall_means") or {}).get(metric)
    return float(value) if isinstance(value, (int, float)) else None


def _metric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return right - left


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _compare_axis(
    legacy_report: dict[str, Any],
    lance_report: dict[str, Any],
    *,
    axis: str,
) -> list[dict[str, Any]]:
    legacy_buckets = set(
        (_axis_report(legacy_report, "primary_ndcg", axis).get("per_bucket_mean") or {}).keys()
    )
    lance_buckets = set(
        (_axis_report(lance_report, "primary_ndcg", axis).get("per_bucket_mean") or {}).keys()
    )
    rows: list[dict[str, Any]] = []
    for bucket in sorted(legacy_buckets | lance_buckets):
        legacy_ndcg = _bucket_value(legacy_report, "primary_ndcg", axis, bucket)
        lance_ndcg = _bucket_value(lance_report, "primary_ndcg", axis, bucket)
        legacy_recall = _bucket_value(legacy_report, "recall", axis, bucket)
        lance_recall = _bucket_value(lance_report, "recall", axis, bucket)
        legacy_forbidden = _bucket_value(legacy_report, "forbidden_rate", axis, bucket)
        lance_forbidden = _bucket_value(lance_report, "forbidden_rate", axis, bucket)
        rows.append(
            {
                "axis": axis,
                "bucket": bucket,
                "legacy_primary_ndcg": legacy_ndcg,
                "lance_primary_ndcg": lance_ndcg,
                "primary_ndcg_delta": _metric_delta(legacy_ndcg, lance_ndcg),
                "legacy_recall": legacy_recall,
                "lance_recall": lance_recall,
                "recall_delta": _metric_delta(legacy_recall, lance_recall),
                "legacy_forbidden_rate": legacy_forbidden,
                "lance_forbidden_rate": lance_forbidden,
                "forbidden_rate_delta": _metric_delta(legacy_forbidden, lance_forbidden),
                "legacy_count": _bucket_count(legacy_report, "primary_ndcg", axis, bucket),
                "lance_count": _bucket_count(lance_report, "primary_ndcg", axis, bucket),
            }
        )
    return rows


def compare_reports(
    legacy_path: Path,
    lance_path: Path,
    *,
    tolerance: float = REGRESSION_TOLERANCE,
) -> dict[str, Any]:
    legacy_payload = _load_json(legacy_path)
    lance_payload = _load_json(lance_path)
    legacy_run = _select_run(legacy_payload)
    lance_run = _select_run(lance_payload)
    legacy_report = _run_report(legacy_run)
    lance_report = _run_report(lance_run)

    bucket_rows = [
        *_compare_axis(legacy_report, lance_report, axis="category"),
        *_compare_axis(legacy_report, lance_report, axis="language"),
    ]
    regressions = [
        row
        for row in bucket_rows
        if row["primary_ndcg_delta"] is not None
        and row["primary_ndcg_delta"] < tolerance - FLOAT_EPSILON
    ]

    legacy_global = _macro_primary(legacy_run, legacy_report)
    lance_global = _macro_primary(lance_run, lance_report)
    global_delta = _metric_delta(legacy_global, lance_global)
    global_gate_pass = global_delta is not None and global_delta >= 0.0
    bucket_gate_pass = not regressions

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "legacy_path": str(legacy_path),
        "lance_path": str(lance_path),
        "tolerance": tolerance,
        "legacy_selected_modalities": legacy_run.get("modalities"),
        "lance_selected_modalities": lance_run.get("modalities"),
        "global": {
            "legacy_primary_ndcg_macro": legacy_global,
            "lance_primary_ndcg_macro": lance_global,
            "primary_ndcg_macro_delta": global_delta,
            "legacy_primary_ndcg_micro": _overall(legacy_report, "primary_ndcg"),
            "lance_primary_ndcg_micro": _overall(lance_report, "primary_ndcg"),
            "legacy_recall_micro": _overall(legacy_report, "recall"),
            "lance_recall_micro": _overall(lance_report, "recall"),
            "legacy_forbidden_rate_micro": _overall(legacy_report, "forbidden_rate"),
            "lance_forbidden_rate_micro": _overall(lance_report, "forbidden_rate"),
        },
        "gate": {
            "pass": global_gate_pass or bucket_gate_pass,
            "global_gate_pass": global_gate_pass,
            "bucket_gate_pass": bucket_gate_pass,
            "regression_count": len(regressions),
        },
        "bucket_rows": bucket_rows,
        "regressions": regressions,
    }


def _print_table(summary: dict[str, Any]) -> None:
    global_metrics = summary["global"]
    gate = summary["gate"]
    print(
        "Global primary nDCG macro: "
        f"legacy={_fmt(global_metrics['legacy_primary_ndcg_macro'])} "
        f"lance={_fmt(global_metrics['lance_primary_ndcg_macro'])} "
        f"delta={_fmt(global_metrics['primary_ndcg_macro_delta'])}"
    )
    print(
        "Gate: "
        f"pass={gate['pass']} "
        f"global_gate={gate['global_gate_pass']} "
        f"bucket_gate={gate['bucket_gate_pass']} "
        f"regressions={gate['regression_count']}"
    )
    print()
    print("axis       bucket                    legacy   lance    delta    recallΔ  forbidΔ")
    print("---------  ------------------------  -------  -------  -------  -------  -------")
    for row in summary["bucket_rows"]:
        print(
            f"{row['axis']:<9}  "
            f"{row['bucket'][:24]:<24}  "
            f"{_fmt(row['legacy_primary_ndcg']):>7}  "
            f"{_fmt(row['lance_primary_ndcg']):>7}  "
            f"{_fmt(row['primary_ndcg_delta']):>7}  "
            f"{_fmt(row['recall_delta']):>7}  "
            f"{_fmt(row['forbidden_rate_delta']):>7}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare legacy and LanceDB RAG eval reports for cutover gates."
    )
    parser.add_argument("--legacy", required=True, type=Path, help="Legacy eval report JSON.")
    parser.add_argument("--lance", required=True, type=Path, help="Lance eval report JSON.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Summary JSON output path. Defaults to reports/rag_eval/cutover_legacy_vs_lance_<timestamp>.json.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=REGRESSION_TOLERANCE,
        help="Allowed per-bucket primary nDCG delta before regression (default: -0.01).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = compare_reports(args.legacy, args.lance, tolerance=args.tolerance)
    out_path = args.out
    if out_path is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_path = DEFAULT_OUT_DIR / f"cutover_legacy_vs_lance_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _print_table(summary)
    print()
    print(f"summary_json={out_path}")
    return 0 if summary["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
