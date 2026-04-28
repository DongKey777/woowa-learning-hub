"""Regression tests for the topic classifier 3-bug stack.

Pins down the incident where prompt "예약 도메인 객체 설계는 어떻게 해야 해?"
classified as primary_topic="Test" + primary_learning_points=["testing_strategy"]
because:

- B1: mission-map analyzer ignored untracked controller/domain dirs
- B2: TOPIC_RULES had no Korean domain modeling vocabulary
- B3: prompt-silent fallback received raw mission-map score (no cap)

See plan: /Users/idonghun/.claude/plans/gentle-conjuring-spring.md
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.workbench.core.intent import infer_topics
from scripts.workbench.core.mission_map import build_mission_map


class KoreanDomainPromptTest(unittest.TestCase):
    """Case 1: real incident — Korean domain design prompt must NOT route to Test."""

    def test_korean_domain_design_prompt_classifies_as_domain(self) -> None:
        mission_map = {
            "analysis": {
                "likely_review_topics": [
                    {
                        "topic": "Test",
                        "query": "test",
                        "score": 6,
                        "reasons": ["path:test", "dependency:test"],
                    }
                ]
            }
        }
        result = infer_topics("예약 도메인 객체 설계는 어떻게 해야 해?", [], mission_map)
        self.assertEqual(result["primary_topic"], "Domain")


class FallbackScoreCapTest(unittest.TestCase):
    """Case 2 + 2b: F3 — mission-map raw score must not dominate when prompt is silent."""

    def test_mission_map_fallback_does_not_dominate_when_prompt_silent(self) -> None:
        mission_map = {
            "analysis": {
                "likely_review_topics": [
                    {"topic": "Test", "query": "test", "score": 6, "reasons": ["path:test"]}
                ]
            }
        }
        result = infer_topics("그냥 어떻게 해야 할지 모르겠어", [], mission_map)
        # Even if Test wins by name, its score must be capped (≤2) and
        # confidence must be low — single-signal fallback is not authoritative.
        self.assertLessEqual(result["topic_candidates"][0]["score"], 2)
        self.assertEqual(result.get("confidence"), "low")

    def test_default_fallback_marks_low_confidence(self) -> None:
        # No TOPIC_RULES match AND no mission_map → default Repository fallback.
        result = infer_topics("그냥 어떻게 해야 할지 모르겠어", [], None)
        self.assertEqual(result["primary_topic"], "Repository")
        self.assertEqual(result.get("confidence"), "low")


class UntrackedLayersTest(unittest.TestCase):
    """Case 3: F1 — mission-map analyzer must see untracked controller/domain.

    Critical: must use a real git repo with `git init` + `git add` so that
    `_repo_files`'s git ls-files path runs (not the rglob fallback).
    Without git init, the fallback rglob path picks up untracked files
    anyway and the test silently passes regardless of the bug fix.
    """

    def test_mission_map_includes_untracked_layers(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fixture-repo"
            repo.mkdir()
            # Tracked files
            (repo / "src" / "test" / "java").mkdir(parents=True)
            (repo / "src" / "test" / "java" / "MissionStepTest.java").write_text(
                "class MissionStepTest {}\n"
            )
            (repo / "build.gradle").write_text(
                "dependencies { testImplementation 'spring-boot-starter-test' }\n"
            )
            subprocess.run(
                ["git", "init"], cwd=repo, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "add", "src/test/java/MissionStepTest.java", "build.gradle"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@t",
                    "-c",
                    "user.name=t",
                    "commit",
                    "-m",
                    "init",
                ],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            # Untracked — this is what the bug missed
            (repo / "src" / "main" / "java" / "roomescape" / "controller").mkdir(parents=True)
            (
                repo / "src" / "main" / "java" / "roomescape" / "controller" / "Foo.java"
            ).write_text("package roomescape.controller; class Foo {}\n")
            (repo / "src" / "main" / "java" / "roomescape" / "domain").mkdir(parents=True)
            (
                repo / "src" / "main" / "java" / "roomescape" / "domain" / "Bar.java"
            ).write_text("package roomescape.domain; class Bar {}\n")

            mission_map = build_mission_map({"name": "fixture", "path": str(repo)})
            layer_paths = mission_map["codebase_analysis"]["layer_paths"]
            self.assertIn("presentation", layer_paths)
            self.assertIn("domain", layer_paths)
            self.assertIn("testing", layer_paths)


class GoldenRegressionTest(unittest.TestCase):
    """Case 4 / 4b: ensure F2 vocabulary expansion does not steal existing topics."""

    def test_repository_prompt_still_classifies_as_repository(self) -> None:
        # Mirrors tests/golden/fixtures.json java-janggi case.
        result = infer_topics("Repository가 왜 이걸 알면 안 돼?", [], None)
        self.assertEqual(result["primary_topic"], "Repository")

    def test_test_prompt_still_classifies_as_test(self) -> None:
        result = infer_topics("테스트 전략은?", [], None)
        self.assertEqual(result["primary_topic"], "Test")


class EntityCollisionTest(unittest.TestCase):
    """Case 5: peer-AI surfaced entity collision between Domain and DTO.

    DTO rule has `entity` keyword. After F2, Domain also has `entity`.
    Multi-word keywords (entity modeling/entity design/엔티티 설계) ensure
    Domain wins on explicit modeling intent while bare `entity` ties.
    """

    def test_korean_entity_design_classifies_as_domain(self) -> None:
        # Korean — DTO has no Korean keyword, Domain matches both 엔티티 and 엔티티 설계.
        result = infer_topics("엔티티 설계 어떻게?", [], None)
        self.assertEqual(result["primary_topic"], "Domain")

    def test_english_entity_modeling_classifies_as_domain(self) -> None:
        # Bare `entity` ties Domain (3) vs DTO (3) → DTO wins alphabetically.
        # F2 adds multi-word `entity modeling` to Domain → 6 vs 3 → Domain wins.
        result = infer_topics("entity modeling 패턴?", [], None)
        self.assertEqual(result["primary_topic"], "Domain")

    def test_dto_conversion_classifies_as_dto(self) -> None:
        # `dto` only, no Domain match → DTO must still win.
        result = infer_topics("DTO 변환 로직?", [], None)
        self.assertEqual(result["primary_topic"], "DTO")


if __name__ == "__main__":
    unittest.main()
