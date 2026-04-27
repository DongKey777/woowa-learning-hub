# Modular Monolith Boundary Enforcement

> 한 줄 요약: 모듈러 모놀리스는 폴더를 나누는 구조가 아니라, `public API + internal 패키지 + 가벼운 아키텍처 테스트`로 경계를 계속 지키게 만드는 운영 방식이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: modular monolith boundary enforcement basics, modular monolith boundary enforcement beginner, modular monolith boundary enforcement intro, software engineering basics, beginner software engineering, 처음 배우는데 modular monolith boundary enforcement, modular monolith boundary enforcement 입문, modular monolith boundary enforcement 기초, what is modular monolith boundary enforcement, how to modular monolith boundary enforcement
<details>
<summary>Table of Contents</summary>

- [왜 이 문서부터 보면 좋은가](#왜-이-문서부터-보면-좋은가)
- [먼저 세 가지 규칙으로 이해하기](#먼저-세-가지-규칙으로-이해하기)
- [패키지 규칙을 어떻게 잡나](#패키지-규칙을-어떻게-잡나)
- [공개 모듈 API를 어떻게 설계하나](#공개-모듈-api를-어떻게-설계하나)
- [가장 작은 폴더 구조 예시](#가장-작은-폴더-구조-예시)
- [가벼운 아키텍처 테스트부터 시작하기](#가벼운-아키텍처-테스트부터-시작하기)
- [브라운필드에서 도입 순서](#브라운필드에서-도입-순서)
- [자주 무너지는 신호](#자주-무너지는-신호)
- [처음 적용할 때 체크리스트](#처음-적용할-때-체크리스트)
- [꼬리질문](#꼬리질문)

</details>

> 관련 문서:
> - [Software Engineering README: Modular Monolith Boundary Enforcement](./README.md#modular-monolith-boundary-enforcement)
> - [Module API DTO Patterns](./module-api-dto-patterns.md)
> - [Shared Module Guardrails](./shared-module-guardrails.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
>
> retrieval-anchor-keywords: modular monolith starter guide, modular monolith boundary enforcement, package rule, package by feature, public module api, internal package, module facade, module contract, module boundary test, architecture test starter, ArchUnit starter, no internal package access, cycle detection, dependency rule, distributed monolith warning, brownfield modularization, package-private limitation, shared/common guardrails, shared kernel, common module anti pattern

## 왜 이 문서부터 보면 좋은가

모듈러 모놀리스는 "언젠가 MSA로 가기 전 중간 단계"로만 오해되기 쉽다.
하지만 실무에서 더 중요한 가치는 **경계를 코드로 연습하는 것**이다.

- 배포는 하나로 유지한다.
- 대신 기능 경계는 여러 모듈로 나눈다.
- 그리고 그 경계를 사람의 합의가 아니라 규칙과 테스트로 강제한다.

즉 핵심은 "모듈이 있다"가 아니라, **다른 모듈이 내부를 마음대로 건드리지 못하게 막고 있는가**다.

## 먼저 세 가지 규칙으로 이해하기

처음에는 이 세 가지만 잡아도 충분하다.

1. 각 모듈은 외부에 공개할 `api` 패키지를 가진다.
2. 다른 모듈은 그 `api` 외의 `internal` 구현을 직접 참조하지 않는다.
3. 이 규칙은 리뷰 문구가 아니라 테스트와 CI로 검증한다.

이 세 규칙이 없으면 보통 이런 식으로 무너진다.

- `payment`가 `order.internal.domain.Order`를 바로 import한다.
- `inventory`가 `payment` 내부 서비스까지 직접 호출한다.
- 급한 기능을 붙이다 보니 `shared` 패키지가 공용 쓰레기통이 된다.

그 순간 모듈러 모놀리스는 "기능별 폴더만 있는 큰 모놀리스"가 된다.

## 패키지 규칙을 어떻게 잡나

패키지 규칙은 복잡하게 시작할 필요가 없다.
처음엔 "외부가 볼 수 있는 곳"과 "외부가 보면 안 되는 곳"만 분리하면 된다.

권장 출발점은 아래 형태다.

| 패키지 | 역할 | 외부 모듈 접근 |
|---|---|---|
| `com.example.order.api` | 주문 모듈의 공개 진입점과 DTO | 허용 |
| `com.example.order.internal.application` | 유스케이스 구현 | 금지 |
| `com.example.order.internal.domain` | 도메인 모델과 규칙 | 금지 |
| `com.example.order.internal.infrastructure` | DB, 외부 연동, 이벤트 발행 구현 | 금지 |

이 구조의 의도는 단순하다.

- 외부 모듈은 `api`에만 의존한다.
- 내부 구현은 자유롭게 바꾸되, 외부 계약은 좁게 유지한다.
- 모듈 간 결합은 클래스 단위가 아니라 **계약 단위**로 만든다.

언어 차원의 접근 제한도 도움이 되지만, 그것만으로는 충분하지 않다.

- Java의 `package-private`는 같은 패키지 안에서만 강하다.
- 하위 패키지 경계나 "다른 모듈이 `internal`을 import하지 못하게 하기"는 별도 테스트가 필요하다.
- Kotlin `internal`, JPMS 같은 강한 도구가 있더라도 팀 규칙과 테스트는 여전히 필요하다.

실무에서는 아래 네 규칙부터 잡으면 대부분의 누수를 막을 수 있다.

1. 모듈 외부에서는 `..order.api..`만 참조할 수 있다.
2. 모듈 내부 구현은 다른 모듈의 `internal`에 의존할 수 없다.
3. 모듈 간 순환 의존을 허용하지 않는다.
4. `shared`나 `common`은 기술적 공통 관심사만 담고, 비즈니스 규칙을 밀어 넣지 않는다.

4번 규칙의 허용 기준과 회수 신호를 더 구체적으로 보려면 [Shared Module Guardrails](./shared-module-guardrails.md)를 같이 보는 편이 좋다.

## 공개 모듈 API를 어떻게 설계하나

`api` 패키지는 "모듈의 정문"이다.
그래서 내부 엔티티를 그대로 노출하는 곳이 아니라, **다른 모듈이 알아야 할 최소 계약만 담는 곳**이어야 한다.

보통 아래 세 가지면 충분하다.

- 다른 모듈이 호출할 인터페이스
- 요청/응답용 command, query, result DTO
- 모듈 경계를 넘겨도 안전한 읽기 모델

command/query/result DTO와 domain object를 어디서 끊을지 헷갈리면 [Module API DTO Patterns](./module-api-dto-patterns.md)를 바로 이어서 보면 된다.

반대로 아래는 `api`에 두지 않는 편이 좋다.

- JPA Entity
- 내부 Repository
- 내부 서비스 구현 클래스
- 트랜잭션 세부 정책
- 특정 프레임워크 타입

예를 들어 `payment`가 주문 정보를 알아야 한다면, 주문 엔티티를 직접 보게 하지 말고 공개 API만 통하게 만든다.

```java
package com.example.order.api;

public interface OrderQueryApi {
    OrderSummary getOrderSummary(OrderId orderId);
}

public record OrderSummary(
    OrderId orderId,
    OrderStatus status,
    Money totalAmount
) {}
```

구현은 내부에 숨긴다.

```java
package com.example.order.internal.application;

import com.example.order.api.OrderId;
import com.example.order.api.OrderQueryApi;
import com.example.order.api.OrderSummary;

class OrderQueryFacade implements OrderQueryApi {
    @Override
    public OrderSummary getOrderSummary(OrderId orderId) {
        // 내부 도메인 모델을 조회한 뒤 API용 읽기 모델로 변환
        return new OrderSummary(orderId, OrderStatus.CREATED, Money.wons(12000));
    }
}
```

핵심은 `payment`가 `Order` 엔티티를 아는 대신, `OrderSummary`라는 계약만 알게 만드는 것이다.
이렇게 해야 주문 모듈 내부 구조를 바꿔도 영향이 API 경계에서 멈춘다.

## 가장 작은 폴더 구조 예시

입문 단계에서는 아래처럼 시작하면 충분하다.

```text
src/main/java/com/example/
  order/
    api/
      OrderCommandApi.java
      OrderQueryApi.java
      OrderSummary.java
      StartOrderPaymentCommand.java
    internal/
      application/
        OrderCommandFacade.java
        OrderQueryFacade.java
      domain/
        Order.java
        OrderPolicy.java
      infrastructure/
        persistence/
          OrderJpaRepository.java
        event/
          OrderEventPublisher.java
  payment/
    api/
      PaymentCommandApi.java
      PaymentResult.java
    internal/
      application/
      domain/
      infrastructure/
```

이 구조를 읽는 법은 간단하다.

- `order/api`는 외부 모듈이 봐도 되는 계약이다.
- `order/internal`은 주문 모듈 팀이 자유롭게 바꾸는 구현이다.
- `payment`는 `order/internal/*`가 아니라 `order/api/*`를 통해서만 주문과 대화한다.

이미 레이어드 구조를 쓰는 팀이라면, 모듈마다 `api`와 `internal`을 나눈 뒤 내부에 `application/domain/infrastructure`를 두는 식으로 섞어 써도 된다.
즉 "모듈 경계"와 "레이어 경계"는 경쟁 관계가 아니라 겹쳐서 쓸 수 있다.

## 가벼운 아키텍처 테스트부터 시작하기

경계 enforcement의 핵심은 거대한 플랫폼이 아니라 **작고 빠른 테스트 몇 개**다.
처음에는 아래 세 가지를 추천한다.

1. 다른 모듈이 `internal` 패키지를 참조하면 실패한다.
2. 모듈 간 순환 의존이 생기면 실패한다.
3. 웹/배치/메시지 진입점이 다른 모듈의 내부 구현을 직접 호출하면 실패한다.

Java 계열 프로젝트라면 ArchUnit으로 빠르게 시작할 수 있다.

```java
@AnalyzeClasses(packages = "com.example")
class ModularMonolithArchitectureTest {

    @ArchTest
    static final ArchRule no_cross_module_internal_access =
        noClasses()
            .that().resideOutsideOfPackage("..order..")
            .should().dependOnClassesThat().resideInAnyPackage("..order.internal..");

    @ArchTest
    static final ArchRule no_module_cycles =
        slices().matching("com.example.(*)..")
            .should().beFreeOfCycles();
}
```

모듈이 여러 개라면 규칙을 조금 일반화해도 된다.

- `..*.api..`만 외부 접근 허용
- `..*.internal..`은 외부 접근 금지
- 모듈 slice 사이 순환 금지

중요한 점은 처음부터 완벽한 규칙 세트를 만들려 하지 않는 것이다.
경계를 잘 지키게 만드는 최소 테스트가 먼저다.

### 처음 넣을 때의 운영 팁

- 기존 위반이 많으면 "새 위반 금지"부터 시작한다.
- 테스트가 느리면 PR마다 돌 수 없다. 1초대 규칙부터 우선 고정한다.
- 예외가 필요하면 코드 주석이 아니라 allowlist나 ADR로 남긴다.
- 실패 메시지는 "어떤 import가 왜 금지인지"가 바로 보이게 만든다.

즉 architecture test의 목적은 위엄 있는 프레임워크 도입이 아니라, **경계가 무너지는 순간을 제일 빨리 잡는 것**이다.

## 브라운필드에서 도입 순서

이미 섞인 모놀리스라면 한 번에 다 고치려 하면 실패하기 쉽다.
보통 아래 순서가 현실적이다.

1. 변경이 자주 엉키는 모듈 두세 개만 먼저 고른다.
2. 각 모듈에 `api` 패키지를 만들고, 외부 진입 계약을 여기에 모은다.
3. 다른 모듈이 직접 참조하던 내부 타입을 API DTO나 facade 호출로 바꾼다.
4. `internal` 직접 참조 금지 테스트를 추가한다.
5. 마지막으로 순환 의존 금지, `shared` 축소 같은 더 넓은 규칙을 붙인다.

브라운필드에서는 "모든 구조를 이상적으로 바꾸기"보다, **다음 변경부터 덜 망가지게 만드는 것**이 더 중요하다.

## 자주 무너지는 신호

아래 신호가 보이면 경계 enforcement가 약하다는 뜻이다.

- 다른 모듈이 내 모듈 엔티티를 그대로 응답/이벤트/메서드 파라미터로 사용한다.
- `shared`, `common`, `util`에 도메인 규칙이 몰린다.
- 새 기능 하나 넣는데 모듈 세 곳의 내부 클래스를 같이 수정해야 한다.
- 순환 의존이 "지금만 급해서"라는 이유로 반복 허용된다.
- 아키텍처 테스트가 느리거나 시끄럽다는 이유로 `@Ignore` 처리된다.

이런 신호는 대부분 "팀이 규칙을 모른다"보다 **규칙이 코드에 없거나, 있어도 실패하지 않는다**에서 나온다.

## 처음 적용할 때 체크리스트

- 모듈마다 외부 공개 지점이 `api` 패키지로 모여 있는가?
- 다른 모듈이 `internal`을 import하지 못하게 막는 테스트가 있는가?
- 모듈 간 순환 의존을 잡는 테스트가 있는가?
- 공개 API가 엔티티나 ORM 모델 대신 DTO나 읽기 모델을 반환하는가?
- `shared/common`이 비즈니스 덤프 공간이 되지 않도록 기준이 있는가?
- 새 예외가 생길 때 allowlist, ADR, 만료 시점이 함께 기록되는가?

## 꼬리질문

- `api` 패키지에는 어디까지 공개하고 어디서부터 내부로 감춰야 하는가?
- package-private, Kotlin `internal`, JPMS 중 무엇이 테스트를 가장 많이 대체할 수 있는가?
- 기존 위반이 많은 브라운필드에서 "새 위반 금지"를 어떤 방식으로 운영할 것인가?
- `shared` 모듈이 꼭 필요한 경우와, 사실상 경계 파괴 신호인 경우를 어떻게 구분할 것인가?

## 한 줄 정리

모듈러 모놀리스 enforcement의 출발점은 거창한 분해가 아니라, `api`는 공개하고 `internal`은 숨기며 그 규칙을 작은 아키텍처 테스트로 계속 검증하는 것이다.
