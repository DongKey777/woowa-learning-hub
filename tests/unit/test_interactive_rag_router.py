"""Unit tests for `scripts/workbench/core/interactive_rag_router.classify()`.

Covers the 4-tier classification protocol from the v2.2 router design
(see `docs/rag-runtime.md` for runtime semantics).

Test classes mirror the verification matrix:
- Basic 4 cases (Tier 0/1/2/3)
- Tier 3 blocked (preconditions unmet)
- Word boundary regressions (Python `\\b` unicode boundary trap)
- re.escape() (dot in build.gradle/settings.gradle)
- False-positive prevention (signal-only, tool-only, 1-char Korean)
- Override mechanism
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core.interactive_rag_router import (  # noqa: E402  (after sys.path tweak)
    RouterDecision,
    classify,
    infer_experience_level,
)


class BasicTierRoutingTests(unittest.TestCase):
    """The 4 fixed cases from plan §Verification."""

    def test_spring_bean_question_routes_to_tier1(self) -> None:
        d = classify("Spring Bean이 뭐야?")
        self.assertEqual(d.tier, 1)
        self.assertEqual(d.mode, "cheap")
        self.assertEqual(d.experience_level, "beginner")
        self.assertFalse(d.blocked)

    def test_di_vs_service_locator_routes_to_tier2(self) -> None:
        d = classify("DI vs Service Locator 패턴 차이가 뭐예요")
        self.assertEqual(d.tier, 2)
        self.assertEqual(d.mode, "full")

    def test_gradle_question_routes_to_tier0(self) -> None:
        d = classify("Gradle 멀티 프로젝트 어떻게 설정해?")
        self.assertEqual(d.tier, 0)
        self.assertIsNone(d.mode)

    def test_pr_review_routes_to_tier3_when_ready(self) -> None:
        d = classify(
            "내 PR 리뷰해줘",
            repo_context={
                "repo_name": "spring-roomescape",
                "archive_ready": True,
                "has_open_pr": True,
            },
        )
        self.assertEqual(d.tier, 3)
        self.assertEqual(d.mode, "coach-run")
        self.assertFalse(d.blocked)


class Tier3BlockedTests(unittest.TestCase):
    """Tier 3 preconditions unmet → blocked, NOT Tier 1 fallback (peer AI #4)."""

    def test_pr_review_blocked_when_no_repo(self) -> None:
        d = classify("내 PR 리뷰해줘", repo_context=None)
        self.assertEqual(d.tier, 3)
        self.assertTrue(d.blocked)
        self.assertIsNone(d.mode)
        self.assertIn("missing", d.reason.lower())

    def test_pr_review_blocked_when_archive_not_ready(self) -> None:
        d = classify(
            "내 PR 리뷰해줘",
            repo_context={
                "repo_name": "spring-roomescape",
                "archive_ready": False,
                "has_open_pr": True,
            },
        )
        self.assertEqual(d.tier, 3)
        self.assertTrue(d.blocked)

    def test_pr_review_blocked_when_no_open_pr(self) -> None:
        d = classify(
            "내 PR 리뷰해줘",
            repo_context={
                "repo_name": "spring-roomescape",
                "archive_ready": True,
                "has_open_pr": False,
            },
        )
        self.assertEqual(d.tier, 3)
        self.assertTrue(d.blocked)


class AsciiBoundaryRegressionTests(unittest.TestCase):
    """Python `\\b` is unicode word boundary, so `\\bdi\\b` does NOT match
    "DI가". Lookaround `(?<![A-Za-z0-9_])...(?![A-Za-z0-9_])` is required.
    These tests would fail under the v2.1 design."""

    def test_word_boundary_spring_does_not_match_pr_token(self) -> None:
        # "Spring" must match LEARNING token, "pr" inside "spring" must NOT
        # falsely match MISSION/COACH tokens (we excluded bare "pr" anyway,
        # but this confirms the boundary)
        d = classify("Spring Boot가 뭐예요")
        self.assertEqual(d.tier, 1)
        self.assertFalse(d.blocked)

    def test_ascii_boundary_di_followed_by_korean_particle(self) -> None:
        d = classify("DI가 뭐야?")
        self.assertEqual(d.tier, 1)

    def test_ascii_boundary_jpa_followed_by_korean_particle(self) -> None:
        d = classify("JPA는 뭐예요?")
        self.assertEqual(d.tier, 1)

    def test_ascii_boundary_spring_followed_by_korean_particle(self) -> None:
        d = classify("spring이 뭐야?")
        self.assertEqual(d.tier, 1)

    def test_korean_particle_attached_to_token(self) -> None:
        d = classify("트랜잭션이 뭐예요?")
        self.assertEqual(d.tier, 1)

    def test_korean_particle_with_comparison(self) -> None:
        d = classify("캐시가 왜 필요해요?")
        self.assertEqual(d.tier, 2)

    def test_hashmap_question_routes_to_tier1(self) -> None:
        d = classify("HashMap이 뭐야?")
        self.assertEqual(d.tier, 1)


class ExpandedDefinitionSignalTests(unittest.TestCase):
    """학습 세션에서 발견된 자연 한국어 표현이 router에서 빠지지 않도록.

    실제 학습자가 "@Autowired가 어떤거야"처럼 물었을 때 v2.2 router가
    Tier 0으로 떨어뜨리던 케이스를 회귀로 못박는다.
    """

    def test_eotteongeoya_routes_to_tier1_with_domain(self) -> None:
        d = classify("@Autowired가 어떤거야")
        self.assertEqual(d.tier, 1)

    def test_eotteon_geoya_with_space_routes_to_tier1(self) -> None:
        d = classify("Bean이 어떤 거야?")
        self.assertEqual(d.tier, 1)

    def test_mwoeun_uimi_routes_to_tier1(self) -> None:
        d = classify("Bean이 어떤 의미야")
        self.assertEqual(d.tier, 1)

    def test_museun_uimi_routes_to_tier1(self) -> None:
        d = classify("DI는 무슨 의미야")
        self.assertEqual(d.tier, 1)

    def test_eotteon_yeokhal_routes_to_tier1(self) -> None:
        d = classify("DispatcherServlet이 어떤 역할이야")
        self.assertEqual(d.tier, 1)

    def test_mwonya_routes_to_tier1(self) -> None:
        d = classify("트랜잭션이 뭐냐")
        self.assertEqual(d.tier, 1)

    def test_no_domain_definition_signal_alone_stays_tier0(self) -> None:
        # 도메인 토큰이 없으면 정의 시그널만으로는 Tier 0에 머물러야 한다.
        d = classify("이게 어떤거야")
        self.assertEqual(d.tier, 0)

    def test_tool_only_with_new_signal_stays_tier0(self) -> None:
        # Gradle은 TOOL 토큰, 학습 도메인 매치 없음 → Tier 0 유지.
        d = classify("Gradle이 어떤 의미야")
        self.assertEqual(d.tier, 0)


class DiInjectionPhraseTests(unittest.TestCase):
    """`spring-core-1` DependencyInjectionTest 학습 단계에서 자주 등장하는
    DI 방식 phrase가 도메인 매치되도록 보강한 회귀."""

    def test_constructor_injection_question_routes_with_depth(self) -> None:
        d = classify("constructor injection은 어떻게 작동해")
        self.assertEqual(d.tier, 2)

    def test_setter_injection_question_routes_with_depth(self) -> None:
        d = classify("setter injection이 어떻게 동작해")
        self.assertEqual(d.tier, 2)

    def test_field_injection_definition_routes_to_tier1(self) -> None:
        d = classify("field injection이 뭐야")
        self.assertEqual(d.tier, 1)

    def test_korean_phrase_constructor_routes_with_depth(self) -> None:
        d = classify("생성자 주입은 어떻게 작동해")
        self.assertEqual(d.tier, 2)

    def test_korean_phrase_setter_definition_routes_to_tier1(self) -> None:
        d = classify("세터 주입이 뭐야")
        self.assertEqual(d.tier, 1)

    def test_korean_phrase_field_definition_routes_to_tier1(self) -> None:
        d = classify("필드 주입이 어떤거야")
        self.assertEqual(d.tier, 1)

    def test_bare_injection_word_does_not_force_domain_match(self) -> None:
        # phrase로만 등록했으므로 단독 "injection"은 도메인 토큰 매치 안 됨.
        # 다른 도메인 토큰이 있으면 매치되겠지만, "injection" 단독은 의료/생물학
        # 등 false positive 가능성을 막기 위해 의도적으로 제외.
        d = classify("injection이 어떤거야")
        self.assertEqual(d.tier, 0)


class KoreanConceptPhraseAndColloquialSignalTests(unittest.TestCase):
    """학습자가 한글 phrase + 구어체 정의 시그널로 물을 때 router가
    매치하도록 보강한 회귀.
    실제 학습 세션에서 "컴포넌트스캔이 머야"가 Tier 0으로 떨어지던 케이스.
    """

    def test_korean_component_scan_phrase_routes_to_tier1(self) -> None:
        d = classify("컴포넌트 스캔이 뭐야")
        self.assertEqual(d.tier, 1)

    def test_korean_component_scan_no_space_routes_to_tier1(self) -> None:
        d = classify("컴포넌트스캔이 뭐야")
        self.assertEqual(d.tier, 1)

    def test_korean_component_scan_with_meoya_routes_to_tier1(self) -> None:
        # "머야" 구어체 + 한글 phrase 동시 매치 — 학습 세션에서 실제 발생.
        d = classify("컴포넌트스캔이 머야")
        self.assertEqual(d.tier, 1)

    def test_korean_di_phrase_routes_to_tier1(self) -> None:
        d = classify("의존성 주입이 뭐야")
        self.assertEqual(d.tier, 1)

    def test_meoya_with_domain_routes_to_tier1(self) -> None:
        d = classify("Bean이 머야")
        self.assertEqual(d.tier, 1)

    def test_meonya_with_domain_routes_to_tier1(self) -> None:
        d = classify("DI가 머냐")
        self.assertEqual(d.tier, 1)

    def test_meoya_alone_without_domain_stays_tier0(self) -> None:
        # 도메인 없으면 정의 시그널만으로는 Tier 0에 머물러야 한다.
        d = classify("이게 머야")
        self.assertEqual(d.tier, 0)


class ReEscapeTests(unittest.TestCase):
    """`.` in build.gradle / settings.gradle / pom.xml must NOT be regex
    wildcard (peer AI #2)."""

    def test_dot_in_settings_gradle_safe(self) -> None:
        d = classify("settings.gradle 설정 어떻게")
        self.assertEqual(d.tier, 0)

    def test_dot_in_build_gradle_safe(self) -> None:
        d = classify("build.gradle dependency 추가")
        self.assertEqual(d.tier, 0)


class FalsePositivePreventionTests(unittest.TestCase):
    """Signal-only and tool-only prompts must stay Tier 0 (peer AI v2.2 #1)."""

    def test_substring_pr_in_preview_not_matched_as_pr(self) -> None:
        d = classify("preview 기능 뭐야")
        self.assertNotEqual(d.tier, 3)
        self.assertFalse(d.blocked)

    def test_signal_only_question_routes_to_tier0(self) -> None:
        # "왜" alone — no domain match → Tier 0
        d = classify("오늘 점심 왜 없어?")
        self.assertEqual(d.tier, 0)

    def test_tool_with_definition_signal_stays_tier0(self) -> None:
        # Gradle = TOOL, "개념 설명해" = signal — no CS/LEARNING domain
        d = classify("Gradle 개념 설명해줘")
        self.assertEqual(d.tier, 0)

    def test_git_commit_question_stays_tier0(self) -> None:
        # "git commit" matches TOOL_TOKENS, no COACH_REQUEST → Tier 0
        d = classify("git commit 메시지 어떻게 써?")
        self.assertEqual(d.tier, 0)

    def test_deadlock_resolution_routes_to_tier2_not_tier3(self) -> None:
        # "데드락" = CS_DOMAIN, "방법/어떻게" = DEPTH → Tier 2
        # "해결" alone is NOT a Tier 3 trigger (peer AI #2)
        d = classify("데드락 해결 방법 어떻게 돼요?")
        self.assertEqual(d.tier, 2)
        self.assertFalse(d.blocked)

    def test_korean_one_char_token_does_not_match_substring(self) -> None:
        # 1-char Korean tokens excluded from vocabularies (e.g., "락" not in CS_DOMAIN)
        # so "연락" / "호락호락" don't false-positive
        d = classify("연락 왜 안 돼?")
        self.assertEqual(d.tier, 0)


class OverrideTests(unittest.TestCase):
    """User overrides short-circuit normal classification."""

    def test_override_force_skip(self) -> None:
        d = classify("그냥 답해 Bean이 뭐야")
        self.assertEqual(d.tier, 0)
        self.assertTrue(d.override_active)

    def test_override_force_full(self) -> None:
        d = classify("RAG로 깊게 DI vs Service Locator 알려줘")
        self.assertEqual(d.tier, 2)
        self.assertTrue(d.override_active)

    def test_override_force_min1(self) -> None:
        d = classify("RAG로 답해 Bean 알려줘")
        self.assertGreaterEqual(d.tier, 1)
        self.assertTrue(d.override_active)

    def test_override_force_coach_blocked_without_repo(self) -> None:
        d = classify("코치 모드 봐줘")
        self.assertEqual(d.tier, 3)
        self.assertTrue(d.override_active)
        self.assertTrue(d.blocked)


class ExperienceLevelInferenceTests(unittest.TestCase):
    def test_beginner_phrase_returns_beginner(self) -> None:
        self.assertEqual(infer_experience_level("Bean이 뭐야?"), "beginner")
        self.assertEqual(
            infer_experience_level("DI 처음 배우는데 알려줘"), "beginner"
        )

    def test_advanced_jargon_returns_none(self) -> None:
        # Advanced hints don't return "advanced" — they return None to leave
        # boost off (advanced corpus dominates retrieval anyway).
        self.assertIsNone(
            infer_experience_level("MVCC trade-off internals")
        )

    def test_unclear_prompt_returns_none(self) -> None:
        self.assertIsNone(infer_experience_level("그냥 코드 보여줘"))


if __name__ == "__main__":
    unittest.main()
