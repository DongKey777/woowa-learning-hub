from __future__ import annotations

import json
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.eval.verify_real_qrels import (
    _check_cohort_distribution_target,
    _check_concepts_in_catalog,
    _check_manifest_qrels_alignment,
    _check_query_count_metadata,
    _check_report_alignment,
    _check_report_contract_shape,
    _check_report_metric_consistency,
    _check_report_pass_rate_floor,
    _load_stub_concepts,
)


class VerifyRealQrelsTestCase(unittest.TestCase):
    def _write_fixture(self, root: Path, payload: dict) -> Path:
        path = root / "qrels.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


class CohortDistributionTargetTest(VerifyRealQrelsTestCase):

    def test_returns_no_error_when_declared_distribution_matches(self):
        payload = {
            "schema_version": 1,
            "cohort_distribution_target": {
                "paraphrase_human": 1,
                "confusable_pairs": 1,
                "symptom_to_cause": 0,
                "mission_bridge": 0,
                "corpus_gap_probe": 0,
                "forbidden_neighbor": 0,
            },
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
                {
                    "query_id": "confusable_pairs:spring_di:001",
                    "prompt": "DI vs locator?",
                    "language": "ko",
                    "intent": "comparison",
                    "level": "intermediate",
                    "cohort_tag": "confusable_pairs",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            qrels = self._write_fixture(Path(td), payload)
            self.assertEqual(_check_cohort_distribution_target(qrels), [])

    def test_reports_mismatch_and_unknown_extra_tag(self):
        payload = {
            "schema_version": 1,
            "cohort_distribution_target": {
                "paraphrase_human": 2,
                "confusable_pairs": 0,
                "symptom_to_cause": 0,
                "mission_bridge": 0,
                "corpus_gap_probe": 0,
                "forbidden_neighbor": 0,
                "made_up": 1,
            },
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            qrels = self._write_fixture(Path(td), payload)
            errors = _check_cohort_distribution_target(qrels)
        self.assertIn(
            "cohort_distribution_target.paraphrase_human mismatch: declared 2, actual 1",
            errors,
        )
        self.assertIn(
            "cohort_distribution_target has unknown cohort key: made_up",
            errors,
        )


class QueryCountMetadataTest(VerifyRealQrelsTestCase):
    def test_returns_no_error_when_query_count_matches(self):
        payload = {
            "schema_version": 1,
            "query_count": 2,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
                {
                    "query_id": "confusable_pairs:spring_di:001",
                    "prompt": "DI vs locator?",
                    "language": "ko",
                    "intent": "comparison",
                    "level": "intermediate",
                    "cohort_tag": "confusable_pairs",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            qrels = self._write_fixture(Path(td), payload)
            self.assertEqual(_check_query_count_metadata(qrels), [])

    def test_reports_query_count_mismatch(self):
        payload = {
            "schema_version": 1,
            "query_count": 3,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            qrels = self._write_fixture(Path(td), payload)
            self.assertEqual(
                _check_query_count_metadata(qrels),
                ["query_count mismatch: declared 3, actual 1"],
            )


class ConceptStubFallbackTest(VerifyRealQrelsTestCase):
    def test_loads_stub_concepts_from_sidecar_documents(self):
        with TemporaryDirectory() as td:
            sidecar = Path(td) / "sidecar.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "artifact_kind": "r3_lexical_sidecar",
                        "documents": [
                            {"metadata": {"concept_id": None}},
                            {
                                "metadata": {
                                    "concept_id": "software-engineering/repository-interface-contract"
                                }
                            },
                            {
                                "metadata": {
                                    "concept_id": "software-engineering/repository-interface-contract"
                                }
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                _load_stub_concepts(sidecar),
                {"software-engineering/repository-interface-contract"},
            )

    def test_accepts_expected_concept_when_present_in_sidecar_stub(self):
        payload = {
            "schema_version": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:repository_pattern:001",
                    "prompt": "Repository?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "intermediate",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/software-engineering/repository-interface-contract-primer.md"],
                    "expected_concepts": ["software-engineering/repository-interface-contract"],
                },
            ],
        }
        catalog_payload = {"concepts": {}}
        sidecar_payload = {
            "artifact_kind": "r3_lexical_sidecar",
            "documents": [
                {
                    "metadata": {
                        "concept_id": "software-engineering/repository-interface-contract"
                    }
                }
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, payload)
            catalog = root / "concepts.v3.json"
            catalog.write_text(json.dumps(catalog_payload), encoding="utf-8")
            sidecar = root / "sidecar.json"
            sidecar.write_text(json.dumps(sidecar_payload), encoding="utf-8")
            self.assertEqual(
                _check_concepts_in_catalog(qrels, catalog, sidecar),
                [],
            )


class ReportAlignmentTest(VerifyRealQrelsTestCase):
    def test_rejects_lane_summary_artifact_before_alignment_checks(self):
        report_payload = {
            "wave_id": "migration-v3-60-rag-cohort-eval-gate-00022",
            "baseline_report": "reports/rag_eval/migration_v3_60_baseline_migration_v3_60-cycle-20260505T041313Z.json",
            "verification": {"full_verify_status": "pass"},
            "changes": {"pilot_locked_docs_touched": 0},
            "notes": ["wave note, not cohort-eval output"],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            errors = _check_report_contract_shape(report)
        self.assertIn(
            "report is not a cohort-eval baseline artifact: missing ['query_count', 'overall_pass_rate', 'per_cohort', 'per_query', 'metadata']",
            errors,
        )
        self.assertIn(
            "report looks like a lane summary artifact: found ['wave_id', 'baseline_report', 'verification', 'changes', 'notes']",
            errors,
        )

    def test_returns_no_error_when_report_matches_qrels(self):
        qrels_payload = {
            "schema_version": 1,
            "fixture_id": "r3_qrels_real_v1",
            "cohort_distribution_target": {
                "paraphrase_human": 1,
                "confusable_pairs": 0,
                "symptom_to_cause": 0,
                "mission_bridge": 0,
                "corpus_gap_probe": 0,
                "forbidden_neighbor": 0,
            },
            "query_count": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        report_payload = {
            "query_count": 1,
            "metadata": {
                "fixture_id": "r3_qrels_real_v1",
                "schema_version": 1,
                "cohort_distribution_target": {
                    "paraphrase_human": 1,
                    "confusable_pairs": 0,
                    "symptom_to_cause": 0,
                    "mission_bridge": 0,
                    "corpus_gap_probe": 0,
                    "forbidden_neighbor": 0,
                },
            },
            "per_cohort": {
                "paraphrase_human": {"total": 1},
                "confusable_pairs": {"total": 0},
                "symptom_to_cause": {"total": 0},
                "mission_bridge": {"total": 0},
                "corpus_gap_probe": {"total": 0},
                "forbidden_neighbor": {"total": 0},
            },
            "per_query": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "cohort_tag": "paraphrase_human",
                },
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, qrels_payload)
            report = root / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(_check_report_alignment(qrels, report), [])

    def test_reports_report_metadata_and_total_drift(self):
        qrels_payload = {
            "schema_version": 1,
            "fixture_id": "r3_qrels_real_v1",
            "cohort_distribution_target": {
                "paraphrase_human": 1,
                "confusable_pairs": 0,
                "symptom_to_cause": 0,
                "mission_bridge": 0,
                "corpus_gap_probe": 0,
                "forbidden_neighbor": 0,
            },
            "query_count": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        report_payload = {
            "query_count": 2,
            "metadata": {
                "fixture_id": "stale_fixture",
                "schema_version": 2,
                "cohort_distribution_target": {
                    "paraphrase_human": 2,
                    "confusable_pairs": 0,
                    "symptom_to_cause": 0,
                    "mission_bridge": 0,
                    "corpus_gap_probe": 0,
                    "forbidden_neighbor": 0,
                },
            },
            "per_cohort": {
                "paraphrase_human": {"total": 2},
                "confusable_pairs": {"total": 0},
                "symptom_to_cause": {"total": 0},
                "mission_bridge": {"total": 0},
                "corpus_gap_probe": {"total": 0},
                "forbidden_neighbor": {"total": 0},
            },
            "per_query": [
                {
                    "query_id": "paraphrase_human:spring_di:999",
                    "cohort_tag": "paraphrase_human",
                },
                {
                    "query_id": "paraphrase_human:spring_di:999",
                    "cohort_tag": "paraphrase_human",
                },
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, qrels_payload)
            report = root / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            errors = _check_report_alignment(qrels, report)
        self.assertIn("report.query_count mismatch: report 2, qrels 1", errors)
        self.assertIn(
            "report.metadata.fixture_id mismatch: report 'stale_fixture', qrels 'r3_qrels_real_v1'",
            errors,
        )
        self.assertIn(
            "report.metadata.schema_version mismatch: report 2, qrels 1",
            errors,
        )
        self.assertIn("report.metadata.cohort_distribution_target mismatch", errors)
        self.assertIn(
            "report.per_cohort.paraphrase_human.total mismatch: report 2, qrels 1",
            errors,
        )
        self.assertIn(
            "report.per_query duplicate query_ids: ['paraphrase_human:spring_di:999']",
            errors,
        )
        self.assertIn(
            "report.per_query query_id set mismatch; missing=['paraphrase_human:spring_di:001']; unexpected=['paraphrase_human:spring_di:999']",
            errors,
        )

    def test_reports_per_query_cohort_tag_drift(self):
        qrels_payload = {
            "schema_version": 1,
            "fixture_id": "r3_qrels_real_v1",
            "cohort_distribution_target": {
                "paraphrase_human": 1,
                "confusable_pairs": 0,
                "symptom_to_cause": 0,
                "mission_bridge": 0,
                "corpus_gap_probe": 0,
                "forbidden_neighbor": 0,
            },
            "query_count": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        report_payload = {
            "query_count": 1,
            "metadata": {
                "fixture_id": "r3_qrels_real_v1",
                "schema_version": 1,
                "cohort_distribution_target": {
                    "paraphrase_human": 1,
                    "confusable_pairs": 0,
                    "symptom_to_cause": 0,
                    "mission_bridge": 0,
                    "corpus_gap_probe": 0,
                    "forbidden_neighbor": 0,
                },
            },
            "per_cohort": {
                "paraphrase_human": {"total": 1},
                "confusable_pairs": {"total": 0},
                "symptom_to_cause": {"total": 0},
                "mission_bridge": {"total": 0},
                "corpus_gap_probe": {"total": 0},
                "forbidden_neighbor": {"total": 0},
            },
            "per_query": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "cohort_tag": "mission_bridge",
                },
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, qrels_payload)
            report = root / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            errors = _check_report_alignment(qrels, report)
        self.assertIn(
            "report.per_query cohort_tag mismatch for paraphrase_human:spring_di:001: "
            "report 'mission_bridge', qrels 'paraphrase_human'",
            errors,
        )


class ReportMetricConsistencyTest(VerifyRealQrelsTestCase):
    def test_tier_downgraded_contributes_to_refusal_clean_derived_metric(self):
        report_payload = {
            "top_k": 5,
            "overall_pass_rate": 1.0,
            "per_cohort": {
                "paraphrase_human": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "confusable_pairs": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "symptom_to_cause": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "mission_bridge": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "corpus_gap_probe": {
                    "total": 1,
                    "pass_count": 1,
                    "pass_rate": 1.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 1,
                },
                "forbidden_neighbor": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
            },
            "per_query": [
                {
                    "query_id": "corpus_gap_probe:gap:001",
                    "cohort_tag": "corpus_gap_probe",
                    "pass_status": True,
                    "primary_rank": None,
                    "forbidden_hit_rank": None,
                    "actual_outcome": "tier_downgraded",
                },
            ],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(_check_report_metric_consistency(report), [])

    def test_returns_no_error_when_report_metrics_match_per_query_rows(self):
        report_payload = {
            "top_k": 5,
            "overall_pass_rate": 0.5,
            "per_cohort": {
                "paraphrase_human": {
                    "total": 2,
                    "pass_count": 1,
                    "pass_rate": 0.5,
                    "recall_at_5": 0.5,
                    "forbidden_hit_rate_at_5": 0.5,
                    "mrr": 0.125,
                    "refusal_clean": 0,
                },
                "confusable_pairs": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "symptom_to_cause": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "mission_bridge": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "corpus_gap_probe": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "forbidden_neighbor": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
            },
            "per_query": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "cohort_tag": "paraphrase_human",
                    "pass_status": True,
                    "primary_rank": 4,
                    "forbidden_hit_rank": None,
                    "actual_outcome": "primary_hit",
                },
                {
                    "query_id": "paraphrase_human:spring_di:002",
                    "cohort_tag": "paraphrase_human",
                    "pass_status": False,
                    "primary_rank": None,
                    "forbidden_hit_rank": 2,
                    "actual_outcome": "forbidden_hit",
                },
            ],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(_check_report_metric_consistency(report), [])

    def test_reports_overall_and_per_cohort_metric_drift(self):
        report_payload = {
            "top_k": 5,
            "overall_pass_rate": 0.9,
            "per_cohort": {
                "paraphrase_human": {
                    "total": 2,
                    "pass_count": 2,
                    "pass_rate": 1.0,
                    "recall_at_5": 1.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 1.0,
                    "refusal_clean": 1,
                },
                "confusable_pairs": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "symptom_to_cause": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "mission_bridge": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "corpus_gap_probe": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
                "forbidden_neighbor": {
                    "total": 0,
                    "pass_count": 0,
                    "pass_rate": 0.0,
                    "recall_at_5": 0.0,
                    "forbidden_hit_rate_at_5": 0.0,
                    "mrr": 0.0,
                    "refusal_clean": 0,
                },
            },
            "per_query": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "cohort_tag": "paraphrase_human",
                    "pass_status": True,
                    "primary_rank": 4,
                    "forbidden_hit_rank": None,
                    "actual_outcome": "primary_hit",
                },
                {
                    "query_id": "paraphrase_human:spring_di:002",
                    "cohort_tag": "paraphrase_human",
                    "pass_status": False,
                    "primary_rank": None,
                    "forbidden_hit_rank": 2,
                    "actual_outcome": "forbidden_hit",
                },
            ],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            errors = _check_report_metric_consistency(report)
        self.assertIn(
            "report.overall_pass_rate mismatch: report 0.9, derived 0.5",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.pass_count mismatch: report 2, derived 1",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.pass_rate mismatch: report 1.0, derived 0.5",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.recall_at_5 mismatch: report 1.0, derived 0.5",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.forbidden_hit_rate_at_5 mismatch: report 0.0, derived 0.5",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.mrr mismatch: report 1.0, derived 0.125",
            errors,
        )
        self.assertIn(
            "report.per_cohort.paraphrase_human.refusal_clean mismatch: report 1, derived 0",
            errors,
        )


class ReportPassRateFloorTest(VerifyRealQrelsTestCase):
    def test_returns_no_error_when_report_clears_minimum(self):
        report_payload = {
            "overall_pass_rate": 0.94,
            "per_cohort": {},
            "per_query": [],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(_check_report_pass_rate_floor(report, 0.94), [])

    def test_reports_when_report_falls_below_minimum(self):
        report_payload = {
            "overall_pass_rate": 0.9399,
            "per_cohort": {},
            "per_query": [],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(
                _check_report_pass_rate_floor(report, 0.94),
                [
                    "report.overall_pass_rate below minimum: observed 0.9399, minimum 0.9400"
                ],
            )

    def test_reports_when_report_pass_rate_is_not_numeric(self):
        report_payload = {
            "overall_pass_rate": "ninety-four",
            "per_cohort": {},
            "per_query": [],
        }
        with TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.assertEqual(
                _check_report_pass_rate_floor(report, 0.94),
                ["report.overall_pass_rate is not numeric: 'ninety-four'"],
            )


class ManifestQrelsAlignmentTest(VerifyRealQrelsTestCase):
    def test_returns_no_error_when_manifest_matches_fixture(self):
        qrels_payload = {
            "schema_version": 1,
            "fixture_id": "r3_qrels_real_v1",
            "query_count": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, qrels_payload)
            qrels_sha = sha256(qrels.read_bytes()).hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "r3": {
                            "qrels": {
                                "path": qrels.as_posix(),
                                "query_count": 1,
                                "schema_version": "1",
                                "sha256": qrels_sha,
                            }
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.assertEqual(_check_manifest_qrels_alignment(qrels, manifest), [])

    def test_reports_manifest_qrels_drift(self):
        qrels_payload = {
            "schema_version": 1,
            "fixture_id": "r3_qrels_real_v1",
            "query_count": 1,
            "queries": [
                {
                    "query_id": "paraphrase_human:spring_di:001",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/spring-bean-di-basics.md"],
                    "expected_concepts": ["spring/bean-di-basics"],
                },
            ],
        }
        with TemporaryDirectory() as td:
            root = Path(td)
            qrels = self._write_fixture(root, qrels_payload)
            qrels_sha = sha256(qrels.read_bytes()).hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "r3": {
                            "qrels": {
                                "path": "tests/fixtures/stale.json",
                                "query_count": 99,
                                "schema_version": "9",
                                "sha256": "stale",
                            }
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            errors = _check_manifest_qrels_alignment(qrels, manifest)
        self.assertIn(
            "manifest.r3.qrels.path mismatch: manifest 'tests/fixtures/stale.json', qrels "
            f"{qrels.as_posix()!r}",
            errors,
        )
        self.assertIn(
            "manifest.r3.qrels.query_count mismatch: manifest 99, qrels 1",
            errors,
        )
        self.assertIn(
            "manifest.r3.qrels.schema_version mismatch: manifest '9', qrels 1",
            errors,
        )
        self.assertIn(
            "manifest.r3.qrels.sha256 mismatch: manifest 'stale', qrels "
            f"{qrels_sha!r}",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
