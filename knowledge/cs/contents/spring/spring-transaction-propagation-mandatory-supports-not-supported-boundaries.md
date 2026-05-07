---
schema_version: 3
title: Spring Transaction Propagation Mandatory Supports NotSupported Boundaries
concept_id: spring/transaction-propagation-mandatory-supports-not-supported-boundaries
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- transaction-propagation-mandatory
- supports-not-supported
- boundaries
- mandatory-supports-not
aliases:
- MANDATORY SUPPORTS NOT_SUPPORTED
- Spring transaction propagation context
- transaction required boundary
- non transactional section
- propagation contract
- suspend transaction boundary
intents:
- comparison
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md
expected_queries:
- MANDATORY SUPPORTS NOT_SUPPORTED propagation은 언제 써?
- 새 transaction을 만들지 않는 전파 옵션은 어떤 문맥 계약을 표현해?
- NOT_SUPPORTED는 기존 transaction을 suspend하고 어떤 작업을 분리해?
- SUPPORTS는 transaction이 있을 때와 없을 때 동작이 달라서 위험할 수 있어?
contextual_chunk_prefix: |
  이 문서는 MANDATORY, SUPPORTS, NOT_SUPPORTED를 새 transaction 생성 여부보다
  이 method가 어떤 transaction context에서 실행되어야 하는지 고정하는 propagation contract로
  설명한다. suspend, optional transaction, request flow boundary를 다룬다.
---
# Spring Transaction Propagation: `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED` Boundaries

> 한 줄 요약: `MANDATORY`, `SUPPORTS`, `NOT_SUPPORTED`는 "새 트랜잭션을 만들까"보다, **이 메서드가 요청 흐름 어디에서 어떤 트랜잭션 문맥으로 실행되어야 하는가**를 선명하게 고정하는 전파 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: MANDATORY propagation, SUPPORTS propagation, NOT_SUPPORTED propagation, NEVER propagation, non transactional boundary, transaction ownership, transaction suspend, transaction synchronization, request lifecycle transaction boundary, controller direct call mandatory, supports synchronization scope, mandatory tx guardrail, OSIV transaction boundary, async transaction boundary

## 핵심 개념

전파 옵션을 이야기할 때 보통 `REQUIRED`, `REQUIRES_NEW`, `NESTED`에 집중한다.

하지만 아래 옵션들도 경계 설계에서 중요하다.

- `MANDATORY`
- `SUPPORTS`
- `NOT_SUPPORTED`
- `NEVER`

이들은 "트랜잭션을 어떻게 나눌까"보다, **이 메서드가 트랜잭션을 소유하면 안 되는지, 반드시 상위 경계 안에 있어야 하는지, 아니면 중간에 일부러 트랜잭션을 비워야 하는지**를 표현한다.

즉 이 문서의 핵심 질문은 다음이다.

- 이 메서드는 요청 처리 중 어느 지점에서만 호출돼야 하는가
- HTTP 요청 전체와 트랜잭션 경계를 헷갈리고 있지는 않은가
- 호출자에 따라 달라지는 의미를 감수할 만한 메서드인가

## 빠른 의미 표

| 전파 수준 | 기존 tx가 있으면 | 기존 tx가 없으면 | 요청 흐름에서 읽는 의미 |
|---|---|---|---|
| `MANDATORY` | 기존 tx에 참여 | 즉시 예외 | "이 메서드는 유스케이스 tx 안에서만 호출돼야 한다" |
| `SUPPORTS` | 기존 tx에 참여 | 비트랜잭션 실행 | "호출자 문맥을 그대로 따른다" |
| `NOT_SUPPORTED` | 기존 tx를 suspend 후 비트랜잭션 실행 | 비트랜잭션 실행 | "요청 중간에 non-tx 구간을 일부러 뚫는다" |
| `NEVER` | 즉시 예외 | 비트랜잭션 실행 | "이 메서드는 tx 안에서 돌면 설계 오류다" |

`SUPPORTS`는 단순히 "tx 없음"과 완전히 같다고 보기 어렵다.

Spring 문서 기준으로 일부 transaction manager에서는 실제 트랜잭션이 없어도 synchronization/resource sharing scope가 생길 수 있다.
즉 `SUPPORTS`는 "아무 annotation 없음"보다 호출 문맥에 더 민감한 계약이다.

## 깊이 들어가기

### 1. `MANDATORY`는 내부 쓰기 로직의 보호막이다

`MANDATORY`는 현재 트랜잭션이 반드시 이미 있어야 한다.

즉 이 메서드는 스스로 경계를 열지 않는다.

잘 맞는 경우:

- 상위 application service가 유스케이스 경계를 소유해야 한다
- 하위 쓰기 서비스가 단독 호출되면 안 된다
- "조용히 새 tx 생성"보다 "설계 실수 즉시 실패"가 낫다

즉 `MANDATORY`는 기능 옵션이 아니라, **상위 경계 종속성을 강제하는 선언**이다.

특히 request lifecycle 관점에서 보면 의미가 더 분명해진다.

- 보통 filter / interceptor / controller 진입 시점에는 트랜잭션이 아직 없다
- 따라서 controller가 `MANDATORY` 메서드를 직접 치면 바로 실패한다
- 반대로 application service의 `@Transactional` 경계 안에서만 타게 만들면 "어디서 호출돼야 하는가"가 강하게 고정된다

즉 `MANDATORY`는 "내부 write component는 요청 초입에서 바로 호출하지 마라"라는 실행 가능한 가드레일이다.

### 2. `SUPPORTS`는 조회 helper에 맞지만, 호출 경로에 따라 의미가 변한다

`SUPPORTS`는 트랜잭션이 있으면 참여하고, 없으면 비트랜잭션으로 돈다.

겉보기엔 유연하다.

하지만 주의점은 단순히 "tx 안/밖 둘 다 된다"가 아니다.

- 같은 메서드가 어떤 요청 경로에선 tx 안, 어떤 요청 경로에선 tx 밖
- connection 획득 시점, flush timing, lazy loading 체감이 호출자에 따라 달라진다
- `readOnly = true`를 붙여도 기존 tx가 없으면 request 전체를 read-only tx로 만드는 것은 아니다
- 일부 manager에서는 synchronization scope가 생겨 "완전히 아무 경계 없음"과도 다를 수 있다

즉 `SUPPORTS`는 편하지만, **실행 의미를 호출자 문맥에 넘겨 버린다**.

그래서 `SUPPORTS`는 다음 질문에 "예"일 때만 쓰는 편이 안전하다.

- 조회 메서드의 의미가 호출자 문맥에 따라 달라도 괜찮은가
- tx 안에서 호출될 때와 밖에서 호출될 때 차이를 팀이 알고 있는가
- 이 메서드가 request 전체 정책처럼 오해되지 않게 설명할 수 있는가

### 3. `NOT_SUPPORTED`는 요청 중간에 non-tx 구간을 뚫는다

`NOT_SUPPORTED`는 현재 트랜잭션이 있으면 잠시 중단하고 비트랜잭션으로 실행한다.

즉 중요한 포인트는 "요청을 끊는다"가 아니라, **요청 처리 흐름 한가운데에서 트랜잭션만 잠깐 비운다**는 점이다.

자연스러운 경우:

- 긴 외부 HTTP 호출을 tx 안에 두면 안 될 때
- 대용량 read / streaming에서 tx 점유를 피하고 싶을 때
- 락과 커넥션을 빨리 놓고 싶은 구간이 명확할 때

이 전파 수준은 suspend / resume 감각이 없으면 오해하기 쉽다.

- 바깥 tx는 사라진 것이 아니라 잠시 멈춘다
- `NOT_SUPPORTED` 구간 안에서는 transaction synchronization을 기대하면 안 된다
- 메서드가 끝나면 바깥 tx가 다시 이어진다

즉 `NOT_SUPPORTED`는 tx가 부족해서가 아니라, **트랜잭션을 일부러 빼야 하는 구간**을 표시한다.

### 4. HTTP 요청 생명주기 위에 겹쳐 보면 오해가 줄어든다

트랜잭션 전파를 request lifecycle에 겹쳐 읽으면, `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED`가 훨씬 덜 추상적으로 느껴진다.

#### 4-1. HTTP 요청 시작과 트랜잭션 시작은 보통 다르다

전형적인 흐름은 아래와 같다.

```text
HTTP request
  -> filter / interceptor
  -> controller
  -> application service (@Transactional REQUIRED)
  -> repository / domain write
  -> commit
  -> response serialization
```

즉 요청이 들어왔다고 해서 곧바로 tx가 열린 것이 아니다.

그래서 다음이 중요하다.

- `MANDATORY`는 controller 직하 호출을 막는 데 의미가 있다
- `SUPPORTS`는 request 전체를 감싸는 정책이 아니라 "지금 호출자가 tx를 갖고 있나"만 본다
- `NOT_SUPPORTED`는 요청 전체를 비트랜잭션으로 만드는 것이 아니라, service 중간 일부 구간만 비트랜잭션으로 만든다

#### 4-2. `MANDATORY`는 controller / filter / async callback 직접 호출과 잘 충돌한다

이 충돌은 버그가 아니라 의도에 가깝다.

예를 들어 아래 흐름을 보자.

```text
POST /orders/{id}/confirm
  -> controller
  -> orderWriter.confirm()   // MANDATORY
```

상위 `@Transactional` 경계가 없으면 여기서 예외가 난다.

이 실패는 "프레임워크가 까다롭다"가 아니라, **요청 초입에서 핵심 write component를 직접 호출하지 말라**는 설계 피드백이다.

#### 4-3. `SUPPORTS`는 같은 요청 안에서도 의미가 달라질 수 있다

같은 `findSummary()`가 아래 두 경로에서 호출될 수 있다.

```text
GET /orders/{id}
  -> controller
  -> summaryReader.findSummary()   // SUPPORTS, no tx

POST /orders/{id}/confirm
  -> controller
  -> checkoutFacade.confirm()      // REQUIRED
       -> summaryReader.findSummary() // SUPPORTS, inside tx
```

둘 다 같은 HTTP 요청 처리 중이지만, 메서드 의미는 다르다.

- 첫 번째는 비트랜잭션 조회
- 두 번째는 write tx에 참여한 조회

즉 `SUPPORTS`를 쓰면 "이 메서드는 요청마다 같게 동작한다"는 기대를 버려야 한다.

#### 4-4. 응답 직렬화와 OSIV는 전파 옵션과 다른 축이다

`SUPPORTS`나 `NOT_SUPPORTED`를 잘 골랐다고 해서 응답 직렬화 단계까지 tx 의미가 깔끔해지는 것은 아니다.

특히 OSIV가 켜져 있으면:

- 서비스 메서드 tx는 이미 끝났어도
- 요청 끝까지 persistence context가 남을 수 있고
- JSON 직렬화 중 lazy loading이 다시 터질 수 있다

즉 `SUPPORTS`를 "조회 요청이니까 안전하다"라고 읽으면 안 된다.
응답 렌더링 시점의 DB 접근 허용 여부는 OSIV / DTO 경계 / 직렬화 설계가 따로 결정한다.

#### 4-5. async 재디스패치나 다른 스레드로 넘어가면 전파 전제가 깨질 수 있다

Spring 트랜잭션은 보통 현재 스레드에 묶인다.

그래서 MVC async나 `@Async` 조합에서는 다음을 특히 조심해야 한다.

- async callback에서 `MANDATORY` 메서드를 치면 상위 tx가 없어서 실패할 수 있다
- `SUPPORTS`는 worker thread에서 아예 비트랜잭션으로 실행될 수 있다
- `NOT_SUPPORTED`는 원래 caller tx를 worker thread로 옮겨 주지 않는다

즉 이 옵션들은 request id를 기준으로 동작하지 않는다.
**실제 실행 스레드의 현재 transaction context**를 기준으로 동작한다.

### 5. `NEVER`는 더 강한 금지다

`NOT_SUPPORTED`가 "있으면 중단 후 진행"이라면, `NEVER`는 "있으면 예외"다.

즉:

- `NOT_SUPPORTED`: tx 있으면 끊고 실행
- `NEVER`: tx 있으면 설계 오류

적용 범위는 좁지만, tx 금지가 강한 유틸리티나 "절대 lock / flush / tx synchronization 영향권에 들어오면 안 되는 코드"에는 의도를 분명하게 만들 수 있다.

### 6. 이 옵션들의 진짜 가치는 설계 커뮤니케이션이다

중요한 질문은 기술 옵션보다 다음이다.

- 이 메서드는 반드시 상위 유스케이스 tx 안에 있어야 하나
- 이 메서드는 tx 안에서 호출되면 오히려 위험한가
- 이 메서드는 호출자 문맥에 따라 달라져도 괜찮은가
- HTTP 요청 전체와 혼동되지 않게 이 경계를 설명할 수 있는가

즉 `MANDATORY`, `SUPPORTS`, `NOT_SUPPORTED`는 **주석이 아니라 실행 계약으로 경계 의도를 남기는 수단**이다.

### 7. 남용하면 오히려 흐름이 읽기 어려워진다

모든 helper에 전파 옵션을 붙이기 시작하면:

- 호출 그래프가 읽기 어려워진다
- 프레임워크 설정이 도메인 의도를 덮어버린다
- 디버깅 시 실제 경계 추적이 더 어려워진다
- request lifecycle과 transaction lifecycle을 더 자주 혼동하게 된다

그래서 보통은 다음 정도가 안정적이다.

- 기본값은 `REQUIRED`
- 내부 쓰기 서비스 보호가 필요하면 `MANDATORY`
- 특정 non-tx 구간이 중요할 때만 `NOT_SUPPORTED`
- `SUPPORTS`는 조회 helper에 제한적으로
- tx 금지 자체가 계약이면 `NEVER`

## 실전 시나리오

### 시나리오 1: 하위 상태 변경 서비스가 controller에서 가끔 직접 호출된다

핵심 write component가 요청 초입에서 단독 호출되면 유스케이스 경계가 흐려진다.

이 경우 `MANDATORY`가 설계 실수를 더 빨리 드러낸다.

### 시나리오 2: 조회 helper가 read API와 write API 양쪽에서 재사용된다

`SUPPORTS`가 자연스러울 수 있다.

대신 아래 차이를 문서화해야 한다.

- 어떤 경로에선 tx 밖에서 읽는다
- 어떤 경로에선 write tx 안에 참여한다
- lazy loading / flush / connection timing 체감이 다를 수 있다

### 시나리오 3: 주문 확정 중 파트너 API 호출이 lock 시간을 늘린다

주문 상태 변경은 tx 안에 남기고, 느린 외부 호출만 `NOT_SUPPORTED` 또는 상위 구조 분리로 비트랜잭션 구간을 명시할 수 있다.

핵심은 "요청을 끊는 것"이 아니라 "tx를 비우는 것"이다.

### 시나리오 4: MVC async callback에서 같은 서비스 메서드를 재사용한다

원래 동기 요청 경로에서는 tx 안이었더라도, 다른 스레드에서 같은 메서드를 부르면 `MANDATORY` 실패나 `SUPPORTS` 의미 변화가 생길 수 있다.

즉 전파 옵션은 request 이름이 아니라 실제 thread-bound context를 따라간다.

## 코드로 보기

### 요청 흐름 안에서 역할을 나눈 예시

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final CheckoutFacade checkoutFacade;
    private final OrderSummaryReader orderSummaryReader;

    public OrderController(CheckoutFacade checkoutFacade, OrderSummaryReader orderSummaryReader) {
        this.checkoutFacade = checkoutFacade;
        this.orderSummaryReader = orderSummaryReader;
    }

    @PostMapping("/{orderId}/confirm")
    public void confirm(@PathVariable Long orderId) {
        checkoutFacade.confirm(orderId);
    }

    @GetMapping("/{orderId}/summary")
    public OrderSummary summary(@PathVariable Long orderId) {
        return orderSummaryReader.findSummary(orderId);
    }
}
```

```java
@Service
public class CheckoutFacade {

    private final OrderWriter orderWriter;
    private final PartnerGateway partnerGateway;

    public CheckoutFacade(OrderWriter orderWriter, PartnerGateway partnerGateway) {
        this.orderWriter = orderWriter;
        this.partnerGateway = partnerGateway;
    }

    @Transactional
    public void confirm(Long orderId) {
        orderWriter.markConfirmed(orderId);      // MANDATORY
        partnerGateway.reserveShipment(orderId); // NOT_SUPPORTED
        orderWriter.markShipmentRequested(orderId); // MANDATORY
    }
}
```

```java
@Service
public class OrderWriter {

    @Transactional(propagation = Propagation.MANDATORY)
    public void markConfirmed(Long orderId) {
        // 핵심 상태 변경
    }

    @Transactional(propagation = Propagation.MANDATORY)
    public void markShipmentRequested(Long orderId) {
        // 바깥 유스케이스 tx 안에서만 실행돼야 하는 후속 상태 변경
    }
}
```

```java
@Service
public class OrderSummaryReader {

    @Transactional(propagation = Propagation.SUPPORTS, readOnly = true)
    public OrderSummary findSummary(Long orderId) {
        return queryRepository.findSummary(orderId);
    }
}
```

```java
@Service
public class PartnerGateway {

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void reserveShipment(Long orderId) {
        partnerClient.call(orderId);
    }
}
```

이 예시는 다음을 보여 준다.

- `MANDATORY`는 controller direct call을 막고 application service 경계를 강제한다
- `SUPPORTS`는 `GET` 요청에서는 비트랜잭션, `confirm()` 안에서는 기존 tx 참여가 가능하다
- `NOT_SUPPORTED`는 `confirm()` 요청 전체를 비트랜잭션으로 만드는 게 아니라, 파트너 호출 구간만 tx 바깥으로 뺀다

## 트레이드오프

| 선택지 | 장점 | 단점 | 요청 생명주기에서 특히 조심할 점 | 언제 선택하는가 |
|---|---|---|---|---|
| `MANDATORY` | 상위 tx 소유권을 강제한다 | 단독 호출 시 즉시 실패한다 | controller / async callback direct call과 충돌한다 | 하위 쓰기 서비스 보호 |
| `SUPPORTS` | 호출자 문맥에 유연하다 | tx 의미가 흐려지기 쉽다 | 같은 request 안에서도 경로별 의미가 달라질 수 있다 | 조회 helper |
| `NOT_SUPPORTED` | 비트랜잭션 구간을 명시한다 | suspend / resume 감각이 필요하다 | 요청 전체를 비tx로 만드는 것이 아니다 | 느린 외부 호출, 긴 non-tx work |
| `NEVER` | 잘못된 tx 문맥을 즉시 드러낸다 | 적용 범위가 좁다 | tx를 자동으로 비워 주지 않는다. 그냥 실패한다 | tx 금지가 강한 구간 |

핵심은 이 옵션들을 드문 기술 옵션이 아니라, **트랜잭션 소유권과 비트랜잭션 의도를 표현하는 설계 도구**로 보는 것이다.

## 꼬리질문

> Q: `MANDATORY`를 왜 내부 쓰기 서비스 보호에 쓰는가?
> 의도: 상위 경계 소유권 이해 확인
> 핵심: 하위 서비스가 조용히 새 트랜잭션을 열지 못하게 하고, 요청 초입 direct call을 막아 상위 유스케이스 경계에 종속되게 하기 위해서다.

> Q: `SUPPORTS`가 편하면서도 위험한 이유는 무엇인가?
> 의도: 호출자 문맥 의존성 이해 확인
> 핵심: 같은 메서드가 tx 안/밖에서 서로 다른 의미를 가질 수 있고, 일부 manager에서는 synchronization scope까지 달라질 수 있기 때문이다.

> Q: `NOT_SUPPORTED`는 언제 자연스러운가?
> 의도: 비트랜잭션 구간 설계 이해 확인
> 핵심: 긴 외부 호출처럼 tx를 일부러 끊어 lock / connection 점유를 줄여야 하는 구간에서다.

> Q: 왜 `NOT_SUPPORTED`를 "요청 전체를 tx 밖으로 빼는 옵션"이라고 보면 안 되는가?
> 의도: request lifecycle와 tx lifecycle 구분 확인
> 핵심: 이 옵션은 메서드 실행 구간에서만 바깥 tx를 suspend하고, 메서드가 끝나면 상위 tx가 다시 이어지기 때문이다.

> Q: `NEVER`와 `NOT_SUPPORTED`의 차이는 무엇인가?
> 의도: 강도 차이 확인
> 핵심: 전자는 tx가 있으면 예외, 후자는 tx가 있으면 잠시 중단하고 실행한다.

## 한 줄 정리

`MANDATORY`, `SUPPORTS`, `NOT_SUPPORTED`는 희귀 옵션이 아니라, **HTTP 요청 흐름 안에서 어느 지점이 유스케이스 tx이고 어느 지점이 non-tx hole인지**를 선명하게 남기는 경계 도구다.
