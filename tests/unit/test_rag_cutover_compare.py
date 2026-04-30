from __future__ import annotations

import json

from scripts.learning.cli_rag_cutover_compare import compare_reports, main


def _report(category_values: dict[str, float], language_values: dict[str, float]) -> dict:
    def axis(values: dict[str, float]) -> dict:
        return {
            "per_bucket_mean": values,
            "per_bucket_count": {bucket: 3 for bucket in values},
            "macro_mean": sum(values.values()) / len(values),
        }

    return {
        "runs": [
            {
                "modalities": ["fts", "dense"],
                "primary_ndcg_macro": sum(category_values.values()) / len(category_values),
                "run_report": {
                    "overall_means": {
                        "primary_ndcg": 0.5,
                        "recall": 0.6,
                        "forbidden_rate": 0.0,
                    },
                    "macro_reports": {
                        "primary_ndcg": {
                            "category": axis(category_values),
                            "language": axis(language_values),
                        },
                        "recall": {
                            "category": axis({k: 1.0 for k in category_values}),
                            "language": axis({k: 1.0 for k in language_values}),
                        },
                        "forbidden_rate": {
                            "category": axis({k: 0.0 for k in category_values}),
                            "language": axis({k: 0.0 for k in language_values}),
                        },
                    },
                },
            }
        ],
        "best_modalities": ["fts", "dense"],
    }


def test_compare_reports_passes_when_global_ndcg_improves(tmp_path):
    legacy = tmp_path / "legacy.json"
    lance = tmp_path / "lance.json"
    legacy.write_text(
        json.dumps(_report({"database": 0.7, "spring": 0.5}, {"ko": 0.2})),
        encoding="utf-8",
    )
    lance.write_text(
        json.dumps(_report({"database": 0.8, "spring": 0.51}, {"ko": 0.19})),
        encoding="utf-8",
    )

    summary = compare_reports(legacy, lance)

    assert summary["gate"]["pass"] is True
    assert summary["gate"]["global_gate_pass"] is True
    assert summary["global"]["primary_ndcg_macro_delta"] > 0


def test_compare_reports_fails_when_global_and_bucket_gate_regress(tmp_path):
    legacy = tmp_path / "legacy.json"
    lance = tmp_path / "lance.json"
    legacy.write_text(
        json.dumps(_report({"database": 0.7, "spring": 0.5}, {"ko": 0.2})),
        encoding="utf-8",
    )
    lance.write_text(
        json.dumps(_report({"database": 0.68, "spring": 0.49}, {"ko": 0.18})),
        encoding="utf-8",
    )

    summary = compare_reports(legacy, lance)

    assert summary["gate"]["pass"] is False
    assert summary["gate"]["global_gate_pass"] is False
    assert summary["gate"]["bucket_gate_pass"] is False
    assert {row["bucket"] for row in summary["regressions"]} == {"database", "ko"}


def test_cli_writes_summary_and_returns_nonzero_on_gate_failure(tmp_path, capsys):
    legacy = tmp_path / "legacy.json"
    lance = tmp_path / "lance.json"
    out = tmp_path / "summary.json"
    legacy.write_text(
        json.dumps(_report({"database": 0.7}, {"ko": 0.2})),
        encoding="utf-8",
    )
    lance.write_text(
        json.dumps(_report({"database": 0.68}, {"ko": 0.18})),
        encoding="utf-8",
    )

    code = main(["--legacy", str(legacy), "--lance", str(lance), "--out", str(out)])

    captured = capsys.readouterr()
    assert code == 2
    assert out.exists()
    assert "Global primary nDCG macro" in captured.out
    assert "summary_json=" in captured.out
