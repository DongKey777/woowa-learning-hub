# Shared Module Guardrails

> 한 줄 요약: 모듈러 모놀리스에서 `shared/common`은 "중복이 보인다"가 아니라, **도메인 중립적이거나 명시적 shared kernel이며 ownership과 lint 규칙까지 갖췄다**는 조건을 만족할 때만 허용된다.

**난이도: 🟡 Intermediate**

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 세 가지 질문으로 걸러내기](#먼저-세-가지-질문으로-걸러내기)
- [언제 `shared/common`이 acceptable한가](#언제-sharedcommon이-acceptable한가)
- [언제 넣으면 안 되는가](#언제-넣으면-안-되는가)
- [이름보다 중요한 것은 ownership이다](#이름보다-중요한-것은-ownership이다)
- [덤프 공간이 되지 않게 하는 guardrails](#덤프-공간이-되지-않게-하는-guardrails)
- [가장 작은 구조 예시](#가장-작은-구조-예시)
- [위험 신호](#위험-신호)
- [체크리스트](#체크리스트)
- [꼬리질문](#꼬리질문)

</details>

> 관련 문서:
> - [Software Engineering README: Shared Module Guardrails](./README.md#shared-module-guardrails)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Shared Library vs Platform Service Trade-offs](./shared-library-vs-platform-service-tradeoffs.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
>
> retrieval-anchor-keywords: shared module guardrails, shared/common module, modular monolith shared kernel, shared kernel criteria, common module anti pattern, domain dumping ground, boundary erosion, cross-cutting shared code, shared runtime module, architecture lint shared module, duplication over accidental coupling

## 왜 이 문서가 필요한가

모듈러 모놀리스를 도입한 팀이 가장 빨리 만드는 예외가 `shared`나 `common`이다.
처음에는 중복 제거처럼 보이지만, 기준 없이 키우면 결국 모든 경계가 이 폴더를 통해 다시 연결된다.

핵심은 간단하다.

- 중복 자체는 비용이지만, 잘못된 공유는 더 큰 결합 비용을 만든다.
- `shared/common`은 "여러 곳에서 쓴다"가 아니라 "여러 모듈이 같은 의미로 안정적으로 써도 된다"일 때만 허용된다.
- 판단이 애매하면 보통 `shared`보다 **원래 모듈에 두고 API로 노출하는 쪽**이 더 안전하다.

즉 이 문서는 "`shared/common`을 아예 금지할 것인가"보다, **언제 허용하고 어디서 끊어야 하는가**를 정리한다.

## 먼저 세 가지 질문으로 걸러내기

새 코드를 `shared/common`으로 보내기 전에 아래 세 질문부터 본다.

1. 이 코드는 도메인 중립적인가, 아니면 여러 컨텍스트에서 의미가 완전히 같은 명시적 shared kernel인가?
2. 모든 소비자가 거의 같은 속도로 바뀌어도 괜찮을 만큼 변화 빈도가 낮은가?
3. 이 코드를 유지하기 위해 feature 모듈의 `internal`, 엔티티, 정책 클래스를 다시 참조하지 않아도 되는가?

셋 중 하나라도 `아니오`라면, 보통 `shared/common`으로 보내지 않는 편이 낫다.

- 원래 소유 모듈에 둔다.
- 다른 모듈에는 `api`나 facade, 이벤트, ACL로 노출한다.
- 중복이 조금 남더라도 경계를 보존한다.

모듈러 모놀리스에서는 **조금의 중복이 애매한 공유보다 싸다**.

## 언제 `shared/common`이 acceptable한가

허용되는 경우는 대체로 아래 세 가지뿐이다.

### 1. 기술적 공통 관심사

도메인 규칙이 아니라 모든 모듈이 공통으로 쓰는 기술적 기능이다.

- `Clock`, `IdGenerator`, `JsonSerializer`
- tracing, logging correlation, feature flag client wrapper
- 인증된 사용자 컨텍스트를 읽는 얇은 abstraction

이런 코드는 특정 도메인 용어를 몰라도 동작해야 한다.

### 2. 명시적 shared kernel

DDD의 shared kernel처럼, 몇 개의 컨텍스트가 **같은 의미로 공동 소유**하는 작은 모델만 허용한다.

- `TenantId`, `CurrencyCode`, `CountryCode`
- 모든 관련 팀이 같은 규칙으로 이해하는 작은 value object

단, shared kernel은 "공용 도메인 폴더"가 아니다.
의미가 완전히 같고, 변경 시 공동 리뷰가 가능하며, 크기가 작을 때만 유지된다.

### 3. 테스트 전용 재사용

테스트 fixture, contract stub, test helper처럼 운영 코드 경계를 흔들지 않는 재사용은 별도 `testkit` 성격으로 분리할 수 있다.

- 운영 코드 의존성에 섞지 않는다.
- `src/test` 범위나 별도 test module로 한정한다.

아래 표처럼 판단하면 빠르다.

| 후보 | 판단 | 이유 |
|---|---|---|
| `Clock`, `IdGenerator` | 허용 가능 | 기술적 공통 관심사 |
| `TenantId`, `CurrencyCode` | 조건부 허용 | 작고 안정적인 shared kernel |
| `OrderDiscountPolicy` | 금지 | 주문 도메인 규칙 |
| `PaymentRepository` | 금지 | persistence 세부 구현 |
| `CommonCheckoutFacade` | 금지 | 여러 모듈 orchestration은 application 경계 문제 |

## 언제 넣으면 안 되는가

아래 경우는 거의 항상 안 된다.

- "세 군데에서 쓰니까"라는 이유만 있다.
- 한 모듈의 정책, 상태 전이, validation 규칙을 밖으로 빼고 싶다.
- 엔티티, repository, ORM 타입, 외부 API DTO를 공통화하려 한다.
- 소비자별 분기문이 `if (consumer == ...)` 식으로 늘어난다.
- `shared`가 여러 모듈을 직접 호출하는 orchestration layer가 된다.

특히 아래 이름은 경고 신호다.

- `common.order`
- `shared.payment`
- `common.service`
- `shared.util` 안의 비즈니스 규칙 클래스

이름만 일반적일 뿐 실제로는 특정 모듈의 관심사를 빼낸 경우가 많다.
이럴 때는 shared가 아니라 **원래 모듈 API를 더 잘 설계해야 하는 문제**다.

## 이름보다 중요한 것은 ownership이다

`common`이라는 이름은 너무 넓어서 거의 항상 덤프 공간이 된다.
가능하면 용도별로 더 좁은 이름을 쓴다.

- `shared/runtime`: 기술적 공통 관심사
- `shared/kernel`: 명시적 shared kernel
- `shared/testkit`: 테스트 전용 재사용

그리고 각 shared 영역에는 아래가 있어야 한다.

- owner 또는 co-owner
- 허용된 소비자와 사용 목적
- 변경 리뷰 규칙
- 주기적 축소/재검토 시점

설명할 때 "이건 원래 어느 도메인이 책임지는가?"에 답이 모호하면 shared로 보내면 안 된다.

## 덤프 공간이 되지 않게 하는 guardrails

`shared/common`을 허용하더라도 free-for-all로 두면 바로 무너진다.
최소한 아래 guardrail은 같이 둔다.

1. **입장 규칙**: 새 항목을 넣을 때 `왜 원래 모듈 API가 아닌가`, `owner는 누구인가`, `변화 빈도는 낮은가`, `exit 조건은 무엇인가`를 PR/ADR에 남긴다.
2. **의존 방향 고정**: `shared`는 feature 모듈에 의존하지 않는다. `shared/kernel`은 feature 모듈의 `internal`, ORM, web adapter를 참조하지 않는다.
3. **용도별 분리**: `shared/common` 루트에 파일을 계속 추가하지 말고 `runtime`, `kernel`, `testkit`처럼 목적별 하위 모듈로만 받는다.
4. **금지 타입 선언**: 기본적으로 entity, repository, application service, workflow policy, controller 성격 코드는 shared에 두지 않는다.
5. **변경 감시**: `shared` 변경이 잦거나 소비자별 분기문이 늘면, duplication이나 module API/ACL로 되돌리는 검토를 강제한다.
6. **아키텍처 lint**: CI에서 `shared -> feature module` 의존, `shared/kernel -> framework-heavy package` 의존, 루트 `common` 신규 추가를 막는다.

이미 거대한 `shared/common`이 있다면 한 번에 완벽히 고치려 하지 말고 순서를 고정한다.

1. 루트 신규 추가를 먼저 동결한다.
2. 기존 항목을 `runtime`, `kernel`, `testkit`, `원래 소유 모듈`로 분류한다.
3. 고변화 항목과 소비자별 분기문이 많은 항목부터 shared 밖으로 되돌린다.

## 가장 작은 구조 예시

아래 정도면 출발점으로 충분하다.

```text
src/main/java/com/example/
  shared/
    runtime/
      api/
        Clock.java
        IdGenerator.java
    kernel/
      api/
        TenantId.java
        CurrencyCode.java
  order/
    api/
    internal/
  payment/
    api/
    internal/

src/test/java/com/example/
  shared/
    testkit/
```

핵심은 두 가지다.

- 운영 코드용 `shared`는 목적이 좁아야 한다.
- `shared/common`이라는 넓은 루트는 임시 이행 경로일 수는 있어도, 영구적인 기본 폴더가 되면 안 된다.

## 위험 신호

아래 신호가 보이면 shared가 이미 경계를 먹고 있다는 뜻이다.

- `shared`가 `order`, `payment`, `inventory` 같은 feature 패키지를 다시 import한다.
- `shared` 변경 하나에 여러 도메인 팀이 동시에 재검증해야 한다.
- 클래스 이름에 `Order`, `Coupon`, `Settlement` 같은 특정 도메인 용어가 늘어난다.
- 소비자별 예외 처리가 `shared` 안의 조건문으로 커진다.
- shared owner를 물었을 때 모두가 "다 같이 쓰는 거라..."라고 답한다.

이 단계까지 오면 중복 제거를 잘한 것이 아니라, **소유권을 잃은 재결합**이 일어난 것이다.

## 체크리스트

- 이 코드는 기술적 공통 관심사이거나, 의미가 완전히 같은 작은 shared kernel인가?
- 원래 소유 모듈의 `api`로 해결하는 쪽보다 shared가 정말 더 단순한가?
- shared가 feature 모듈이나 그 `internal`에 의존하지 않는가?
- owner, 리뷰 규칙, 축소 시점이 문서화되어 있는가?
- entity, repository, workflow policy 같은 타입이 shared로 새고 있지 않은가?
- 애매하면 공유보다 duplication 또는 ACL이 더 안전하다는 합의가 팀에 있는가?

## 꼬리질문

- 중복 제거와 경계 보존이 충돌할 때 어떤 기준으로 duplication을 허용할 것인가?
- shared kernel과 "사실상 주문 모듈 모델 재수출"을 어떻게 구분할 것인가?
- 이미 거대한 `common` 패키지가 있을 때 신규 추가 금지를 어떤 lint/리뷰 규칙으로 고정할 것인가?
- shared가 한계를 넘었을 때 library 축소, module API 재설계, platform service 분리 중 무엇을 고를 것인가?

## 한 줄 정리

모듈러 모놀리스의 `shared/common`은 편의상 만들어 두는 기본 폴더가 아니라, 기술적 공통 관심사나 아주 작은 shared kernel만 엄격한 ownership과 lint 규칙 아래 담는 예외 구역이어야 한다.
