---
schema_version: 3
title: ArchUnit Brownfield Rollout Playbook
concept_id: software-engineering/archunit-brownfield-rollout-playbook
canonical: false
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 78
mission_ids: []
review_feedback_tags:
- archunit-rollout-sequencing
- fail-new-only-gate
- baseline-vs-allowlist
aliases:
- archunit brownfield rollout
- archunit playbook
- legacy violation baseline
- fail new only gate
- architecture test allowlist
- archunit ratchet
- 모놀리스 ArchUnit 도입 순서
- 기존 위반 baseline 동결
- brownfield 아키텍처 테스트 도입
symptoms:
- ArchUnit을 넣고 싶은데 기존 위반이 너무 많아 첫날부터 CI를 막을 수 없어요
- baseline 파일이 영구 면죄부처럼 남을까 봐 rollout 순서를 모르겠어요
- fail-new-only gate와 allowlist를 어떻게 나눠야 하는지 헷갈려요
intents:
- design
- troubleshooting
prerequisites:
- software-engineering/modular-monolith-boundary-enforcement
- software-engineering/architectural-fitness-functions
- software-engineering/policy-as-code-rollout-stages
next_docs:
- software-engineering/brownfield-modularization
- software-engineering/policy-as-code
- software-engineering/override-burndown-exemption-debt
linked_paths:
- contents/software-engineering/modular-monolith-boundary-enforcement.md
- contents/software-engineering/brownfield-modularization-strategy.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/policy-as-code-rollout-adoption-stages.md
- contents/software-engineering/architecture-runway-refactoring-window.md
- contents/software-engineering/override-burn-down-and-exemption-debt.md
confusable_with:
- software-engineering/modular-monolith-boundary-enforcement
- software-engineering/policy-as-code-rollout-stages
- software-engineering/brownfield-modularization
forbidden_neighbors: []
expected_queries:
- 기존 모놀리스에 ArchUnit을 넣을 때 첫날부터 hard fail로 막지 않는 순서는 어떻게 잡아?
- legacy 위반이 많은 프로젝트에서 fail-new-only gate를 어떻게 시작하면 돼?
- baseline 파일과 allowlist를 같은 것으로 두지 말라는 이유가 뭐야?
- ArchUnit 도입할 때 observe, freeze, ratchet 단계를 왜 나눠야 해?
- 브라운필드에서 아키텍처 테스트 예외 부채를 줄이려면 어떤 rollout 정책이 필요해?
contextual_chunk_prefix: |
  이 문서는 brownfield 모놀리스에 ArchUnit 규칙을 넣을 때 기존 위반과 새
  위반을 분리해 rollout 전략으로 막는 playbook이다. 첫날부터 CI를 세게 막기
  어렵다, baseline이 영구 예외가 될까 걱정된다, 새 위반만 끊는 gate를 어디서
  여나, allowlist와 legacy freeze를 어떻게 나누나, 언제 hard fail로 올리나
  같은 자연어 paraphrase가 본 문서의 단계별 운영 가이드에 매핑된다.
---
# ArchUnit Brownfield Rollout Playbook

> 한 줄 요약: 운영 중인 모놀리스에 ArchUnit을 넣을 때는 `전수조사 -> legacy baseline freeze -> fail-new-only gate -> module ratchet -> hard fail` 순서로 올려야 기존 위반과 새 위반을 분리하면서 예외 부채를 줄일 수 있다.

**난이도: 🔴 Advanced**

<details>
<summary>Table of Contents</summary>

- [왜 별도 playbook이 필요한가](#왜-별도-playbook이-필요한가)
- [먼저 어떤 규칙부터 잡나](#먼저-어떤-규칙부터-잡나)
- [단계별 rollout wave](#단계별-rollout-wave)
- [baseline과 allowlist를 어떻게 분리하나](#baseline과-allowlist를-어떻게-분리하나)
- [fail-new-only gate를 어떻게 설계하나](#fail-new-only-gate를-어떻게-설계하나)
- [ratchet을 어떻게 굴리나](#ratchet을-어떻게-굴리나)
- [코드와 정책 예시](#코드와-정책-예시)
- [흔한 실패 패턴](#흔한-실패-패턴)
- [꼬리질문](#꼬리질문)

</details>

> 관련 문서:
> - [Software Engineering README: ArchUnit Brownfield Rollout Playbook](./README.md#archunit-brownfield-rollout-playbook)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)

> retrieval-anchor-keywords:
> - ArchUnit brownfield rollout
> - ArchUnit playbook
> - brownfield architecture test adoption
> - legacy violation baseline
> - architecture test allowlist
> - fail-new-only gate
> - freeze rule baseline
> - modular monolith ArchUnit rollout
> - legacy monolith dependency rule
> - ratcheting architecture tests
> - exception debt burn-down
> - rule hardening sequence

## 왜 별도 playbook이 필요한가

greenfield에서는 아키텍처 규칙을 처음부터 hard fail로 걸어도 된다.
하지만 brownfield monolith는 이미 규칙 위반이 쌓여 있고, 그 위에 기능 배포가 계속 돈다.

이때 가장 흔한 실패는 둘 중 하나다.

- 첫날부터 모든 위반을 막아서 delivery를 멈춘다.
- 반대로 warning만 쌓고 baseline을 영구 allowlist로 방치한다.

그래서 핵심은 "ArchUnit을 넣는다"가 아니라, **기존 위반과 새 위반을 다른 문제로 다루는 rollout 설계**다.

---

## 먼저 어떤 규칙부터 잡나

처음 wave에서는 false positive가 적고 remediation 방향이 분명한 규칙만 고르는 편이 좋다.

권장 출발점:

1. 모듈 간 `internal` 패키지 직접 참조 금지
2. 최상위 feature/module slice 순환 의존 금지
3. controller, batch, consumer 같은 inbound adapter가 다른 모듈의 repository/internal service를 직접 호출하지 못하게 제한
4. 새로 만드는 패키지/모듈은 day-1부터 hard fail

초기 wave에서 피하는 편이 좋은 것:

- naming convention만으로 판정하는 규칙
- 예외가 너무 많은 annotation 기반 규칙
- package 구조가 아직 굳지 않은 레이어링 규칙
- 규칙을 어기면 무엇으로 고쳐야 하는지 합의가 없는 경우

brownfield에서는 coverage보다 **규칙 신뢰도**가 먼저다.

---

## 단계별 rollout wave

| wave | CI 동작 | 주된 산출물 | exit 기준 |
|---|---|---|---|
| `0. observe` | 결과만 수집, build pass | violation inventory, top offender 목록 | 규칙 정확도와 위반 분포를 이해한다 |
| `1. freeze baseline` | legacy 위반을 baseline으로 동결 | generated freeze store, rule id별 owner | "기존 위반" 범위가 고정된다 |
| `2. fail-new-only` | baseline 대비 순증만 block | changed-scope gate, 신규 모듈 hard fail | 새 위반이 유입되지 않는다 |
| `3. ratchet` | 허용 budget을 점진 축소 | burn-down target, module별 cut line | 특정 모듈/룰이 clean 상태가 된다 |
| `4. hard fail` | baseline 없이 즉시 실패 | rule standard, 예외 최소화 | 룰이 조직 기본값이 된다 |

실무에서는 `wave 1`과 `wave 2` 사이가 가장 중요하다.
여기서 baseline을 그냥 "면죄부 파일"로 두면 이후 ratchet이 멈춘다.

### wave 0. observe

첫 단계에서 해야 할 일은 교정이 아니라 관찰이다.

- 어떤 규칙이 얼마나 많이 깨지는지 본다
- violation이 특정 모듈에 몰리는지 본다
- false positive와 "구조적으로 당장 못 고치는 영역"을 분리한다
- remediation path가 있는 규칙만 다음 wave로 올린다

이 단계의 목표는 "규칙을 더 많이 쓰기"가 아니라, **block해도 신뢰받을 규칙만 남기기**다.

### wave 1. freeze baseline

기존 위반은 baseline으로 동결한다.
여기서 baseline은 "현재 snapshot"이지, "영구 허용 목록"이 아니다.

- baseline은 자동 생성 파일로 두되 저장소 안에 둔다
- rule scope가 바뀌지 않는 한 baseline 재생성은 제한한다
- baseline 생성 시점의 위반 수, top package, owner를 같이 기록한다
- rule별로 "이 baseline을 줄일 책임 팀"을 지정한다

핵심은 **기존 부채를 보이게 얼려 두는 것**이다.

### wave 2. fail-new-only

이제부터는 build가 아예 pass/free인 것이 아니라, baseline보다 더 나빠지는 순간 실패해야 한다.

실전에서는 보통 아래 셋을 같이 건다.

1. baseline violation count가 증가하면 실패
2. 변경된 package/module에서 새로운 violation fingerprint가 생기면 실패
3. 새로 만든 module/package는 baseline 예외 없이 hard fail

즉 "기존 부채 때문에 아무것도 못 막는 상태"에서 벗어나, **새 부채 유입만큼은 즉시 차단**하는 단계다.

### wave 3. ratchet

fail-new-only가 안정화되면 baseline을 줄여야 한다.

권장 ratchet 방식:

- 분기마다 rule별 허용 budget을 일정 비율로 낮춘다
- 변경이 많은 모듈부터 clean cut line을 정한다
- 이미 clean해진 모듈은 baseline으로 되돌리지 않는다
- 새 feature package는 ratchet 예외 없이 hard fail 유지

baseline total만 보는 것보다, **어느 모듈이 clean 상태로 승격됐는지**를 관리하는 편이 운영에 유리하다.

### wave 4. hard fail

다음 조건이 충족되면 hard fail로 올릴 수 있다.

- false positive가 사실상 정리됐다
- remediation guide가 있다
- owner와 review path가 있다
- allowlist가 오래된 영구 예외 저장소가 아니다
- 새 위반 유입이 일정 기간 0에 가깝다

hard fail은 규칙의 시작점이 아니라, **baseline이 거의 소거된 뒤의 종착점**이다.

---

## baseline과 allowlist를 어떻게 분리하나

많은 팀이 여기서 실패한다.
generated baseline과 reviewed allowlist를 같은 것으로 취급하면 예외 부채가 안 보인다.

| artifact | 의미 | 작성 방식 | 기대 수명 |
|---|---|---|---|
| baseline freeze store | 현재 legacy 위반 snapshot | 도구 생성 + 리뷰 | 짧아져야 한다 |
| explicit allowlist | 의도적으로 잠깐 허용한 예외 | 사람이 승인하고 메타데이터 기록 | expiry가 있어야 한다 |
| hard-fail ruleset | 예외 없이 지킬 기본 규칙 | 코드와 CI 기본값 | 장기 |

allowlist에는 최소한 아래 필드가 필요하다.

- `rule_id`
- `violation target` 또는 package/module 범위
- `reason`
- `owner`
- `expires_at`
- `replacement path`

중요한 운영 규칙:

- baseline refresh는 rule definition 변경 시에만 한다
- allowlist는 생성 파일이 아니라 리뷰 대상 데이터여야 한다
- allowlist 항목은 만료일이 없으면 merge하지 않는다
- "일단 baseline regenerate"를 쉬운 해결책으로 두지 않는다

baseline은 debt snapshot이고, allowlist는 **승인된 임시 우회**다.

---

## fail-new-only gate를 어떻게 설계하나

fail-new-only는 단순히 "총 개수 증가 금지"로 끝나면 약하다.
큰 정리 작업 한 번으로 숫자가 줄어든 뒤, 다른 모듈에서 새 위반이 생겨도 총량만 같으면 통과해 버릴 수 있다.

그래서 보통 아래 두 축을 같이 본다.

### 1. global budget gate

- rule별 총 baseline count는 증가 금지
- ratchet 시점마다 허용 상한을 다시 낮춘다

이 축은 전체 부채가 커지는 것을 막는다.

### 2. changed-scope gate

- 이번 PR이 건드린 package/module에서는 새로운 violation을 금지
- clean module은 다시 더러워지지 않게 고정
- 신규 package는 처음부터 baseline 없이 검증

이 축은 "내가 건드린 곳은 더 나빠지지 않는다"를 보장한다.

실무에서 제일 강한 조합은 다음이다.

1. 전체 baseline 순증 금지
2. 변경 scope 신규 위반 금지
3. 신규 모듈 zero-baseline

이 세 가지를 합치면 brownfield에서도 CI gate가 꽤 실전적이 된다.

---

## ratchet을 어떻게 굴리나

ratchet은 의지의 문제가 아니라 운영 리듬의 문제다.

좋은 ratchet은:

- 배포 cadence와 맞물린다
- 모듈 owner가 명확하다
- runway가 있는 refactor window와 연결된다
- 줄어든 예외를 다시 baseline으로 되돌리지 않는다

권장 단위는 아래 둘 중 하나다.

- `module-first`: 주문, 결제, 정산처럼 도메인 모듈별로 clean 선언
- `rule-first`: cycle 금지, internal 접근 금지 같은 룰별 소거

보통 brownfield monolith에서는 `module-first`가 설명과 ownership이 쉽다.
반면 전사 플랫폼 룰은 `rule-first`로 운영하기 쉽다.

봐야 할 지표:

- rule별 baseline 잔량
- 30일 신규 violation 수
- allowlist 평균 age와 만료 경과 건수
- hard-fail로 승격된 module 비율

이 지표가 없으면 ArchUnit 도입은 테스트 추가가 아니라 **느린 방치**가 된다.

---

## 코드와 정책 예시

ArchUnit 예시는 보통 아래처럼 baseline freeze에서 시작한다.

```java
import static com.tngtech.archunit.library.freeze.FreezingArchRule.freeze;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

@AnalyzeClasses(packages = "com.example", importOptions = ImportOption.DoNotIncludeTests.class)
class LegacyArchitectureRulesTest {

    @ArchTest
    static final ArchRule no_cycles_between_modules =
        freeze(
            slices().matching("com.example.(*)..")
                .should().beFreeOfCycles()
        );

    @ArchTest
    static final ArchRule order_internal_is_not_used_from_other_modules =
        freeze(
            noClasses()
                .that().resideOutsideOfPackage("..order..")
                .should().dependOnClassesThat().resideInAnyPackage("..order.internal..")
        );
}
```

여기에 운영 메타데이터를 별도로 붙이면 rollout이 쉬워진다.

```yaml
rule_id: order_internal_boundary
stage: fail_new_only
baseline_store: src/test/resources/archunit-store/order-internal.store
changed_scope_gate: changed_packages_clean
owner: commerce-platform
target_modules:
  - order
  - payment
allowlist:
  - target: settlement-batch -> order.internal.LegacyOrderReader
    reason: settlement facade migration pending
    replacement_path: order.api.OrderQueryApi
    expires_at: 2026-06-30
```

중요한 점은 ArchUnit rule 코드와 rollout metadata를 분리해도, **source of truth는 저장소 안의 버전 관리 대상**이어야 한다는 것이다.

---

## 흔한 실패 패턴

### 1. baseline을 재생성하면서 부채를 숨긴다

매번 freeze store를 새로 만들면 "새 위반"과 "원래 있던 위반"의 경계가 사라진다.
baseline regenerate는 rule definition 변경 같은 예외 상황으로 좁혀야 한다.

### 2. allowlist가 영구 예외 창고가 된다

owner, expiry, replacement path 없이 쌓인 allowlist는 사실상 governance 부재다.
allowlist는 예외 기록이 아니라 **종료 예정 우회로**여야 한다.

### 3. hard fail을 너무 빨리 건다

정확하지 않은 규칙을 build blocker로 올리면 팀은 규칙보다 우회 경로를 먼저 배운다.
초기 신뢰를 잃으면 나중 ratchet도 어렵다.

### 4. 신규 모듈까지 legacy baseline에 묶는다

새로 만든 모듈은 brownfield 핑계를 대면 안 된다.
새 영역은 day-1부터 clean boundary를 요구하는 편이 장기적으로 훨씬 싸다.

### 5. count만 보고 changed scope를 안 본다

총량만 보면 PR 작성자가 자기 변경에서 새 위반을 넣고도 통과할 수 있다.
global budget과 changed-scope gate를 같이 둬야 한다.

---

## 꼬리질문

- 어떤 규칙이 false positive가 낮아 first wave에 적합한가?
- baseline refresh를 누가 승인하는가?
- allowlist 만료가 지나면 build를 막을 것인가, 경고만 낼 것인가?
- 신규 모듈과 기존 모듈의 enforcement level을 어떻게 다르게 둘 것인가?
- ratchet cadence를 분기 단위로 할지 release train과 묶을지 정했는가?

## 한 줄 정리

ArchUnit brownfield rollout의 핵심은 기존 모놀리스의 위반을 baseline으로 얼리고, 새 위반만 먼저 차단한 뒤, allowlist와 ratchet으로 예외 부채를 줄여 hard fail로 승격하는 운영 순서를 설계하는 것이다.
