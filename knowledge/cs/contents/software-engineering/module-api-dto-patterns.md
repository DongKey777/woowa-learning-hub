# Module API DTO Patterns

> 한 줄 요약: 모듈 경계에서는 aggregate나 entity를 직접 넘기기보다, `command/query/result DTO`를 기본값으로 두고, domain object는 명시적 shared kernel의 작은 불변 값일 때만 예외적으로 넘기는 편이 안전하다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [초심자 30초 결정 흐름](#초심자-30초-결정-흐름)
- [먼저 세 가지 질문으로 고르기](#먼저-세-가지-질문으로-고르기)
- [한 장으로 보는 선택 기준](#한-장으로-보는-선택-기준)
- [Command DTO를 쓰는 경우](#command-dto를-쓰는-경우)
- [Query DTO와 Result DTO를 쓰는 경우](#query-dto와-result-dto를-쓰는-경우)
- [Domain object를 넘겨도 되는 좁은 예외](#domain-object를-넘겨도-되는-좁은-예외)
- [안전한 계약과 위험한 계약](#안전한-계약과-위험한-계약)
- [Before: aggregate를 모듈 API 밖으로 노출한다](#before-aggregate를-모듈-api-밖으로-노출한다)
- [After: command/query/result DTO로 계약을 좁힌다](#after-commandqueryresult-dto로-계약을-좁힌다)
- [자주 헷갈리는 지점](#자주-헷갈리는-지점)
- [리뷰 체크리스트](#리뷰-체크리스트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [꼬리질문](#꼬리질문)

</details>

> 관련 문서:
> - [Software Engineering README: Module API DTO Patterns](./README.md#module-api-dto-patterns)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Shared Module Guardrails](./shared-module-guardrails.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)
>
> retrieval-anchor-keywords: module api dto patterns, module boundary dto, command query result dto, command dto, query dto, result dto, public module api, module contract, module facade dto, domain object boundary, aggregate boundary leak, entity boundary leak, safe contract unsafe contract, modular monolith api package, shared kernel value object, cross-module contract, boundary language, order payment module api, beginner dto decision flow, command dto vs patch dto, query result snapshot contract, module api common confusion

## 왜 이 문서가 필요한가

모듈러 모놀리스나 layered 구조에서 가장 자주 생기는 실수는 "같은 코드베이스니까 그냥 객체를 넘기자"다.

- `order`가 `Order` aggregate를 `payment`에 그대로 준다
- `payment`가 `order.internal` 엔티티를 직접 import한다
- 모듈 API가 command/query/result 대신 `Map`, entity, framework 타입을 그대로 노출한다

처음에는 빨라 보이지만, 곧 이런 비용이 붙는다.

- 호출자가 상대 모듈 내부 규칙과 필드 구조를 같이 알아야 한다
- aggregate 변경이 곧바로 다른 모듈 컴파일 에러로 번진다
- 읽기 최적화나 ORM 세부가 모듈 API 계약으로 굳어 버린다
- 외부 모듈이 domain method를 직접 호출하면서 소유권이 흐려진다

핵심은 단순하다.

- **모듈 경계 언어**는 DTO가 맡는다
- **도메인 규칙과 행위**는 소유 모듈 안의 domain object가 맡는다

즉 "객체를 덜 만들자"보다 **변경 이유를 경계에서 끊자**가 더 중요하다.

## 초심자 30초 결정 흐름

처음 설계할 때는 용어보다 "상대 모듈이 원하는 것"만 먼저 본다.

| 상대 모듈이 원하는 것 | 첫 선택 | 이유 |
|---|---|---|
| "이 작업을 수행해 줘" | `Command DTO` | 의도만 전달하고 내부 규칙은 소유 모듈이 지킨다 |
| "현재 상태를 알려 줘" | `Query DTO` + `Result DTO` | 조회 스냅샷만 계약으로 고정한다 |
| "모든 모듈이 같은 의미로 쓰는 작은 값" | 작은 불변 value object | primitive 오염보다 의미가 선명하다 |

즉 초심자 기준 기본값은 "aggregate를 넘긴다"가 아니라 "`의도/조회/공유값`을 분리한다"다.

## 먼저 세 가지 질문으로 고르기

모듈 API를 만들 때는 타입 이름보다 아래 질문 세 개가 먼저다.

1. 상대 모듈이 원하는 것이 **상태 변경 요청**인가?
2. 상대 모듈이 원하는 것이 **읽기 전용 정보 조회**인가?
3. 두 모듈이 정말로 **같은 의미를 공유하는 작은 값 객체**가 있는가?

보통 답은 이렇게 연결된다.

- 상태 변경 요청이면 `Command DTO`
- 읽기 조회면 `Query DTO` + `Result DTO`
- 같은 의미를 공유하는 작은 값이면 제한적으로 domain value object

반대로 아래 판단은 보통 경계 누수 신호다.

- "같은 JVM 안이니까 aggregate를 넘겨도 되겠지"
- "필드가 많으니 entity를 그대로 재사용하자"
- "어차피 내부 호출이라 framework request/response 타입을 써도 되겠지"

## 한 장으로 보는 선택 기준

| 경계에서 필요한 것 | 기본 선택 | 왜 이 선택이 안전한가 | 흔한 위험한 선택 |
|---|---|---|---|
| 다른 모듈에 작업을 요청 | `Command DTO` + 필요하면 `Result DTO` | 호출자는 의도만 말하고, 규칙 적용은 소유 모듈이 한다 | aggregate, entity, 내부 service 구현 노출 |
| 다른 모듈에서 읽기 정보 조회 | `Query DTO` 또는 식별자 + `Result DTO` | 읽기 모양을 계약으로 고정하고 내부 모델 변화와 분리한다 | aggregate 반환, LAZY entity 반환, `Map<String, Object>` |
| 여러 모듈이 같은 의미로 쓰는 작은 값 | 불변 value object/shared kernel | 의미가 안정적이면 primitive보다 더 안전한 계약이 된다 | mutable domain object, 정책/행위가 든 모델 |
| 같은 모듈 내부 협력 | domain object 그대로 사용 가능 | 같은 규칙과 소유권 아래 있으므로 행동을 같이 써도 된다 | 이 내부 모델을 `api` 패키지로 승격 |

짧게 외우면 이렇다.

- **Do**를 넘길 때는 command
- **Know**를 넘길 때는 query/result
- **Behave**는 소유 모듈 안에 둔다

## Command DTO를 쓰는 경우

상대 모듈에게 "이 일을 해 달라"라고 요청할 때는 command DTO가 기본값이다.

예:

- `StartPaymentCommand`
- `ReserveInventoryCommand`
- `CancelShipmentCommand`

좋은 command DTO는 보통 아래 특징을 가진다.

- 유스케이스 의도가 이름에 드러난다
- 필요한 식별자와 입력값만 담는다
- 호출자가 callee 내부 상태 구조를 몰라도 보낼 수 있다
- validation은 형식 수준만 두고, 핵심 규칙 검증은 callee가 한다

예를 들어 `payment`가 주문 결제 가능 여부를 반영해야 한다면 이렇게 요청한다.

```java
package com.example.order.api;

public interface OrderPaymentApi {
    MarkOrderPaidResult markPaid(MarkOrderPaidCommand command);
}

public record MarkOrderPaidCommand(
        OrderId orderId,
        PaymentId paymentId,
        Money paidAmount
) {
}

public record MarkOrderPaidResult(
        OrderId orderId,
        OrderStatus status,
        boolean accepted,
        String rejectionReason
) {
}
```

여기서 `payment`는 주문 aggregate 내부 필드나 메서드를 알 필요가 없다.
그저 "결제가 일어났다"는 의도만 전달한다.

반대로 이런 command는 위험하다.

```java
public record MarkOrderPaidCommand(
        Order order,
        List<OrderLineEntity> lines,
        String paymentTableStatus
) {
}
```

왜 위험한가:

- aggregate와 entity가 같이 새어 나온다
- command가 의도보다 내부 저장 구조를 닮기 시작한다
- callee가 나중에 persistence 구조를 바꾸면 caller도 같이 흔들린다

## Query DTO와 Result DTO를 쓰는 경우

상대 모듈이 필요한 것이 "행위"가 아니라 "현재 읽을 값"이라면 query/result DTO가 맞다.

예:

- 결제 모듈이 주문의 결제 가능 상태를 확인
- 정산 모듈이 결제 완료 요약을 조회
- 알림 모듈이 배송 준비 상태를 읽음

기본 규칙은 이렇다.

- 조회 조건이 단순한 단건이면 식별자 하나만 받아도 된다
- 필터, 페이지, 정렬, 시점 조건이 붙기 시작하면 `Query DTO`를 둔다
- 반환은 caller가 알아야 할 읽기 스냅샷만 담은 `Result DTO`로 좁힌다

예:

```java
package com.example.order.api;

public interface OrderQueryApi {
    OrderPaymentView getPaymentView(GetOrderPaymentViewQuery query);
}

public record GetOrderPaymentViewQuery(
        OrderId orderId
) {
}

public record OrderPaymentView(
        OrderId orderId,
        OrderStatus status,
        Money payableAmount,
        boolean payable
) {
}
```

이 계약의 좋은 점은 두 가지다.

- 주문 모듈은 내부 aggregate 구조와 조회 전략을 바꿔도 된다
- 결제 모듈은 자신에게 필요한 읽기 정보만 안정적으로 받는다

반대로 이런 반환은 위험하다.

```java
public interface OrderQueryApi {
    Order getOrder(OrderId orderId);
}
```

왜 위험한가:

- caller가 `Order`의 행위와 내부 상태를 같이 알게 된다
- 조회 전용 요구가 aggregate 설계를 밀기 시작한다
- mutable object라면 caller가 경계 밖에서 규칙을 우회할 여지가 생긴다

읽기 모델이 커질수록 이 문제는 더 빨리 드러난다.
목록/상세용 읽기 분리는 [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)를 같이 보면 감이 빨라진다.

## Domain object를 넘겨도 되는 좁은 예외

모든 domain object가 금지인 것은 아니다.
다만 예외는 정말 좁다.

보통 아래 둘만 허용해도 충분하다.

1. **작고 불변인 value object**
2. **명시적 shared kernel로 합의된 타입**

예:

- `OrderId`
- `Money`
- `CurrencyCode`
- `TenantId`

이 타입들은

- 의미가 모듈마다 같고
- 내부 행위가 작고 안정적이며
- persistence 세부나 workflow 정책을 담지 않는다

그래서 primitive를 흩뿌리는 것보다 오히려 안전할 수 있다.

반대로 아래는 보통 넘기지 않는다.

- aggregate root
- entity
- domain service
- repository
- mutable collection을 품은 rich domain object
- framework annotation에 묶인 모델

실무 기준으로는 이렇게 보면 된다.

- **공유 의미**는 value object로 건널 수 있다
- **공유 행위**는 거의 항상 건너면 안 된다

## 안전한 계약과 위험한 계약

### 안전한 계약 예시

| 상황 | 안전한 계약 | 이유 |
|---|---|---|
| 주문 결제 반영 | `MarkOrderPaidCommand -> MarkOrderPaidResult` | 의도와 결과만 드러난다 |
| 주문 결제 가능 여부 조회 | `GetOrderPaymentViewQuery -> OrderPaymentView` | 읽기 스냅샷만 노출한다 |
| 공통 금액 표현 | `Money` value object 공유 | 의미가 안정적인 shared kernel이다 |
| 모듈 내부 규칙 실행 | 내부 `Order` aggregate 사용 | 소유 모듈 안에서만 행위를 유지한다 |

### 위험한 계약 예시

| 상황 | 위험한 계약 | 왜 위험한가 |
|---|---|---|
| 주문 결제 반영 | `void markPaid(Order order)` | caller가 주문 aggregate를 직접 쥔다 |
| 주문 상태 조회 | `Order getOrder(Long id)` | 읽기 요구가 aggregate 설계를 침범한다 |
| 임시 범용 API | `Map<String, Object> execute(Map<String, Object> payload)` | 계약이 문서와 코드 양쪽에서 흐려진다 |
| 편의 재사용 | `OrderEntity`, `Page<OrderEntity>` 반환 | ORM/persistence 세부가 경계 밖으로 샌다 |
| 부분 갱신 요청 | `UpdateOrderCommand`에 nullable 필드 20개 | 유스케이스 의도보다 DB patch 모양을 닮는다 |

특히 `nullable 필드가 많은 범용 Update DTO`는 조심해야 한다.
이런 DTO는 대개 "공개 API"가 아니라 "내부 테이블 patch 포맷"이기 쉽다.

## Before: aggregate를 모듈 API 밖으로 노출한다

아래 예시는 `payment`가 주문 aggregate를 직접 받아 쓰는 경우다.

```java
package com.example.order.api;

public interface OrderModuleApi {
    Order load(OrderId orderId);
    void markPaid(Order order, Payment payment);
}
```

이 구조는 곧 이렇게 무너진다.

- `payment`가 `Order` 내부 필드와 메서드에 의존한다
- 주문 모듈이 aggregate 구조를 바꾸면 결제 모듈도 같이 깨진다
- "조회"와 "행위"가 같은 타입에 묶여 caller가 과한 권한을 갖는다
- order 모듈이 내부 규칙을 API 타입 변경 없이 바꾸기 어려워진다

같은 코드베이스라서 괜찮아 보이지만, 사실상 `payment`가 `order.internal`을 직접 붙잡은 상태와 비슷하다.

## After: command/query/result DTO로 계약을 좁힌다

모듈 경계에서 필요한 언어만 남기면 API가 훨씬 안정적이다.

```java
package com.example.order.api;

public interface OrderPaymentApi {
    OrderPaymentView getPaymentView(GetOrderPaymentViewQuery query);
    MarkOrderPaidResult markPaid(MarkOrderPaidCommand command);
}

public record GetOrderPaymentViewQuery(
        OrderId orderId
) {
}

public record OrderPaymentView(
        OrderId orderId,
        OrderStatus status,
        Money payableAmount,
        boolean payable
) {
}

public record MarkOrderPaidCommand(
        OrderId orderId,
        PaymentId paymentId,
        Money paidAmount
) {
}

public record MarkOrderPaidResult(
        OrderId orderId,
        OrderStatus status,
        boolean accepted,
        String rejectionReason
) {
}
```

이후 내부 구현은 자유롭게 바꿀 수 있다.

- 주문 모듈은 aggregate 구조를 바꿔도 된다
- 조회 경로를 projection/query repository로 갈아타도 된다
- 결제 모듈은 필요한 계약만 알면 된다

즉 DTO를 쓰는 목적은 "레이어를 늘리기"가 아니라 **소유 모듈의 내부 진화를 외부 호출자에게서 분리하기**다.

## 자주 헷갈리는 지점

- "내부 호출이면 entity를 넘겨도 되지 않나?"
  - 내부 호출이어도 모듈 경계면 외부 계약이다. 같은 코드베이스와 같은 모듈은 다르다.
- "DTO가 많아지면 오히려 복잡해지지 않나?"
  - DTO 수보다 변경 충돌이 줄어드는지가 핵심이다. 보통 호출자-피호출자 동시 수정 횟수가 줄면 이득이다.
- "`UpdateXxxCommand` 하나에 nullable 필드를 몰아두면 유연하지 않나?"
  - 유연해 보이지만 유스케이스 의도가 사라져 patch 포맷이 된다. `CancelOrderCommand`, `ChangeAddressCommand`처럼 의도별 분리가 안전하다.
- "Result DTO 대신 aggregate를 반환하면 재사용이 쉬운 것 아닌가?"
  - 재사용보다 권한 과다 노출이 먼저 온다. caller가 domain method를 호출해야 한다면 경계가 잘못 설계된 신호다.

## 리뷰 체크리스트

- 이 타입은 상대 모듈에게 **의도**를 전달하나, 아니면 내부 구조를 노출하나?
- 반환 타입이 caller에게 꼭 필요한 읽기 스냅샷만 담고 있는가?
- `Entity`, aggregate, framework 타입이 `api` 패키지로 새고 있지 않은가?
- `Command DTO`가 use case 이름을 갖고 있는가, 아니면 범용 patch 포맷처럼 보이는가?
- 공유하는 domain type이 있다면 정말 작은 불변 value object/shared kernel인가?
- caller가 이 반환 객체를 받아 domain method를 계속 호출해야 한다면, 경계 설계가 잘못된 것은 아닌가?

## 다음에 이어서 볼 문서

- 모듈 공개 범위를 코드로 강제하려면: [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
- shared kernel을 어디까지 허용할지 좁히려면: [Shared Module Guardrails](./shared-module-guardrails.md)
- 읽기 모델이 비대해지기 시작했다면: [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- entity/ORM 세부가 API로 새면: [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)

## 꼬리질문

- 이 모듈 API가 caller의 편의 때문에 callee 내부 모델을 과하게 노출하고 있지 않은가?
- 결과 DTO가 너무 비대해졌다면 query model 분리나 consumer별 facade 분리를 해야 하는가?
- shared kernel로 올린 value object가 정말 안정적인 공통 의미인지, 사실상 특정 모듈 모델 재수출은 아닌가?
- "같은 코드베이스라서 괜찮다"는 판단이 미래 리팩토링 비용을 숨기고 있지 않은가?

## 한 줄 정리

모듈 경계에서는 domain object를 넘겨 협업하는 것보다, command/query/result DTO로 의도와 읽기 계약만 드러내고 domain behavior는 소유 모듈 안에 남겨 두는 쪽이 보통 더 오래 견딘다.
