from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .coach_run import run_coach
from .paths import ROOT


DEFAULT_GOLDEN_FIXTURES = ROOT / "tests" / "golden" / "fixtures.json"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_fixtures(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lookup(payload, dotted_path: str):
    current = payload
    for token in dotted_path.split("."):
        if isinstance(current, list):
            current = current[int(token)]
            continue
        current = current[token]
    return current


def _assert_result(assertion: dict, payload: dict) -> dict:
    path = assertion["path"]
    try:
        actual = _lookup(payload, path)
    except Exception as e:  # noqa: BLE001
        return {
            "path": path,
            "status": "failed",
            "error": str(e),
        }

    if "equals" in assertion:
        expected = assertion["equals"]
        passed = actual == expected
        return {
            "path": path,
            "status": "passed" if passed else "failed",
            "expected": expected,
            "actual": actual,
        }

    if "contains" in assertion:
        expected = assertion["contains"]
        if isinstance(actual, list):
            passed = expected in actual
        else:
            passed = str(expected) in str(actual)
        return {
            "path": path,
            "status": "passed" if passed else "failed",
            "expected_contains": expected,
            "actual": actual,
        }

    if assertion.get("truthy"):
        passed = bool(actual)
        return {
            "path": path,
            "status": "passed" if passed else "failed",
            "actual": actual,
        }

    if assertion.get("not_empty"):
        passed = bool(actual)
        return {
            "path": path,
            "status": "passed" if passed else "failed",
            "actual": actual,
        }

    if "equals_lookup" in assertion:
        try:
            expected = _lookup(payload, assertion["equals_lookup"])
        except Exception as e:  # noqa: BLE001
            return {
                "path": path,
                "status": "failed",
                "error": f"equals_lookup: {e}",
            }
        return {
            "path": path,
            "status": "passed" if actual == expected else "failed",
            "expected_from": assertion["equals_lookup"],
            "expected": expected,
            "actual": actual,
        }

    if "dict_value_sum_equals_lookup" in assertion:
        if not isinstance(actual, dict):
            return {"path": path, "status": "failed", "error": "not a dict"}
        try:
            expected = _lookup(payload, assertion["dict_value_sum_equals_lookup"])
        except Exception as e:  # noqa: BLE001
            return {
                "path": path,
                "status": "failed",
                "error": f"dict_value_sum_equals_lookup: {e}",
            }
        total = sum(actual.values())
        return {
            "path": path,
            "status": "passed" if total == expected else "failed",
            "sum": total,
            "expected": expected,
        }

    if "list_length_equals_lookup" in assertion:
        if not isinstance(actual, list):
            return {"path": path, "status": "failed", "error": "not a list"}
        try:
            expected = _lookup(payload, assertion["list_length_equals_lookup"])
        except Exception as e:  # noqa: BLE001
            return {
                "path": path,
                "status": "failed",
                "error": f"list_length_equals_lookup: {e}",
            }
        return {
            "path": path,
            "status": "passed" if len(actual) == expected else "failed",
            "length": len(actual),
            "expected": expected,
        }

    return {
        "path": path,
        "status": "failed",
        "error": "unsupported assertion",
    }


def run_golden(fixtures_path: Path | None = None, *, stop_on_failure: bool = False) -> dict:
    resolved_path = fixtures_path or DEFAULT_GOLDEN_FIXTURES
    fixtures = _load_fixtures(resolved_path)
    cases_output = []
    passed_count = 0
    failed_count = 0

    for case in fixtures.get("cases", []):
        try:
            payload = run_coach(
                repo_name=case.get("repo"),
                repo_path=case.get("path"),
                prompt=case.get("prompt"),
                pr_number=case.get("pr"),
                reviewer=case.get("reviewer"),
                context=case.get("context", "coach"),
            )
            assertion_results = [_assert_result(assertion, payload) for assertion in case.get("assertions", [])]
            failures = [item for item in assertion_results if item["status"] != "passed"]
            status = "passed" if not failures else "failed"
            if status == "passed":
                passed_count += 1
            else:
                failed_count += 1
            cases_output.append({
                "name": case.get("name"),
                "status": status,
                "assertions": assertion_results,
                "summary": {
                    "execution_status": payload.get("execution_status"),
                    "primary_intent": ((payload.get("session") or {}).get("primary_intent")),
                    "primary_topic": ((payload.get("session") or {}).get("primary_topic")),
                    "question_focus": ((((payload.get("coach_reply") or {}).get("response")) or {}).get("question_focus")),
                },
            })
            if failures and stop_on_failure:
                break
        except Exception as e:  # noqa: BLE001
            failed_count += 1
            cases_output.append({
                "name": case.get("name"),
                "status": "error",
                "error": str(e),
            })
            if stop_on_failure:
                break

    return {
        "report_type": "golden_result",
        "generated_at": _timestamp(),
        "fixtures_path": str(resolved_path),
        "case_count": len(fixtures.get("cases", [])),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "cases": cases_output,
    }
