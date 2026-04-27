# Controller Entity Return vs DTO Return Primer

> 한 줄 요약: controller가 엔티티를 그대로 반환하면 Jackson 직렬화가 lazy 연관 getter를 건드리면서 응답 생성 중 SQL이 나가거나 `LazyInitializationException`이 날 수 있어서, 초급자 기본값은 service 안에서 DTO로 닫아 반환하는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- [LazyInitializationException Debug Sequence](./spring-lazyinitializationexception-debug-sequence.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- [DTO Projection vs Entity Loading Mini Card for Read-Only Responses](./spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md)
- [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)

retrieval-anchor-keywords: controller entity return vs dto return, spring controller entity return primer, entity direct return jackson lazy loading, serialization time lazy loading, response serialization lazy loading, controller returns entity why bad, dto return beginner, lazy loading during json serialization, lazyinitializationexception controller response, osiv entity return response, jackson getter triggers query, restcontroller entity return beginner, controller 엔티티 반환 dto 반환, 직렬화 시점 lazy loading, 응답 직렬화 중 sql, controller에서 엔티티 반환하면 왜 안되나, 초급자 dto 반환 primer

## 먼저 mental model 한 줄

controller가 반환한 객체는 끝이 아니다.

`@RestController`에서는 그 뒤에 Jackson이 객체를 JSON으로 바꾸는 **직렬화 단계**가 한 번 더 있다.

- DTO 반환: JSON으로 바꿀 값이 이미 다 들어 있다
- 엔티티 반환: Jackson이 getter를 따라가다가 lazy 연관을 뒤늦게 읽을 수 있다

초급자 기준 핵심은 이것이다.

**"controller 메서드가 끝난 뒤에도, JSON 만드는 동안 getter가 더 호출될 수 있다."**

## 왜 엔티티 반환이 문제를 늦게 터뜨리나

흐름을 가장 짧게 그리면 이렇다.

```text
Controller가 엔티티 반환
  -> Spring/Jackson이 JSON 직렬화 시작
  -> 엔티티 getter 접근
  -> lazy 연관 getter도 따라감
  -> 추가 SQL 또는 LazyInitializationException
```

즉 DB 조회는 service에서 끝났다고 생각했는데, 실제 SQL은 응답을 만드는 마지막 순간에 다시 나갈 수 있다.

## 30초 비교표

| 반환 방식 | 초급자 기본 해석 | 자주 생기는 문제 | 더 안전한 기본값 |
|---|---|---|---|
| 엔티티 직접 반환 | "JPA 객체를 그대로 응답으로 내보냄" | 직렬화 시점 lazy loading, 숨은 N+1, 순환 참조, 응답 shape 불안정 | 가능하면 피한다 |
| DTO 반환 | "응답용 데이터만 따로 담아 반환" | 매핑 코드를 써야 한다 | 초급자 기본값으로 권장 |

한 줄로 줄이면 이렇다.

- 엔티티 반환: 짧아 보여도 응답 단계에서 DB 접근이 다시 열릴 수 있다
- DTO 반환: 응답 경계를 미리 닫는다

## 가장 단순한 예시

주문 상세 응답에서 아래 값만 내려준다고 하자.

- 주문 id
- 주문 상태
- 주문자 이름

### 1. 헷갈리기 쉬운 엔티티 직접 반환

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/{id}")
    public Order getOrder(@PathVariable Long id) {
        return orderService.findById(id);
    }
}
```

겉보기에는 짧지만, 실제 응답에서는 이런 일이 생길 수 있다.

- Jackson이 `getId()`, `getStatus()`를 읽는다
- 연관이 노출돼 있으면 `getMember()`도 따라간다
- `member`가 lazy면 그 순간 SQL이 추가로 나간다
- transaction/persistence context가 이미 닫혔으면 `LazyInitializationException`이 날 수 있다

### 2. 초급자 기본값인 DTO 반환

```java
@Transactional(readOnly = true)
public OrderResponse findOrder(Long id) {
    Order order = orderRepository.findDetailById(id)
        .orElseThrow();

    return new OrderResponse(
        order.getId(),
        order.getStatus().name(),
        order.getMember().getName()
    );
}
```

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/{id}")
    public OrderResponse getOrder(@PathVariable Long id) {
        return orderService.findOrder(id);
    }
}
```

이 흐름에서는 중요한 읽기가 service 안에서 끝난다.

- 어떤 연관이 필요한지 service/repository에서 먼저 정한다
- DTO 생성도 transaction 안에서 끝낸다
- controller는 완성된 응답만 반환한다

## "직렬화 시점 lazy loading"이 정확히 뭐냐

초급자가 많이 놓치는 점은 "내가 getter를 안 불렀는데 왜 SQL이 나가나?"다.

실제로는 Jackson이 JSON을 만들기 위해 getter를 호출한다.

```java
public class Order {

    @ManyToOne(fetch = FetchType.LAZY)
    private Member member;

    public Member getMember() {
        return member;
    }
}
```

Jackson이 엔티티를 JSON으로 바꾸려면 필드를 읽어야 하므로 `getMember()`를 호출할 수 있다.
그 순간 `member`가 아직 초기화되지 않았다면 lazy loading이 터진다.

즉 문제의 핵심은 "controller에서 직접 `getMember()`를 썼는가"가 아니라,
**"응답 직렬화 과정에서 누군가 getter를 호출할 수 있는 구조인가"**다.

## OSIV on/off에서 왜 다르게 보이나

| 상황 | 보이는 증상 |
|---|---|
| OSIV off에 가까움 | service 밖 lazy 접근이 빨리 실패해서 `LazyInitializationException`이 드러난다 |
| OSIV on에 가까움 | 예외 없이 동작할 수 있지만, 직렬화 시점 SQL과 숨은 N+1이 남을 수 있다 |

초급자 기준으로는 이렇게 해석하면 충분하다.

- OSIV off: 문제를 빨리 보여 준다
- OSIV on: 문제를 고친 것이 아니라 늦게 보이게 할 수 있다

그래서 "OSIV on이니까 엔티티 반환해도 괜찮다"는 해석은 안전하지 않다.

## 초반에 빨리 알아채는 신호

아래 신호가 보이면 "엔티티를 응답으로 직접 내보내고 있나?"를 먼저 의심하면 된다.

- controller는 단순한데 응답 직전에 SQL 로그가 추가로 찍힌다
- `LazyInitializationException` stack trace가 Jackson/serializer/controller 근처에서 난다
- 목록 API에서 예상보다 쿼리가 많이 나가며 N+1이 붙는다
- 응답 JSON에 원하지 않은 연관 필드가 섞여 나온다

## 초급자용 빠른 점검표

1. controller 메서드 반환 타입이 엔티티인가, DTO인가
2. service가 엔티티를 그대로 controller까지 넘기고 있나
3. DTO 생성이 service transaction 안에서 끝나는가
4. DTO에 필요한 연관을 fetch join 또는 `@EntityGraph`로 미리 읽었나
5. OSIV on이라서 문제가 가려진 것은 아닌가

위 다섯 줄만 확인해도 초기 감지는 대부분 된다.

## 자주 하는 오해 5개

- "응답이 단순하니 엔티티 그대로 줘도 된다"가 아니다. 단순해 보여도 직렬화가 getter를 더 부를 수 있다.
- "`@JsonIgnore` 몇 개 붙이면 충분하다"가 아니다. 일부 필드를 숨겨도 응답 경계와 lazy loading 문제 자체가 사라지는 것은 아니다.
- "OSIV on이면 안전하다"가 아니다. 예외를 가릴 뿐, 늦은 SQL과 N+1은 남을 수 있다.
- "DTO는 너무 번거롭다"가 아니다. 초급자에게는 오히려 응답 shape와 DB 접근 경계를 분리해 주는 가장 쉬운 안전장치다.
- "엔티티 반환이 항상 완전 금지"라고 외울 필요는 없다. 하지만 초급자 기본값으로는 DTO 반환이 훨씬 덜 위험하다.

## 지금 바로 적용할 기본 규칙

| 상황 | 먼저 적용할 기본값 |
|---|---|
| REST 응답 만들기 | controller는 DTO를 반환한다 |
| DTO에 연관 값이 필요함 | service 안에서 DTO로 변환한다 |
| lazy 연관이 있음 | 조회 시점에 필요한 연관만 미리 준비한다 |
| OSIV on이라 예외가 안 남 | 정상처럼 보여도 직렬화 시점 SQL 로그를 확인한다 |

## 같이 보면 좋은 다음 문서

- DTO 변환 시점 자체를 더 짧게 점검하고 싶으면 [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)를 본다.
- 이미 `LazyInitializationException`이 났다면 [LazyInitializationException Debug Sequence](./spring-lazyinitializationexception-debug-sequence.md) 순서대로 원인을 좁힌다.
- "엔티티를 읽을지, 아예 DTO projection으로 바로 읽을지"가 헷갈리면 [DTO Projection vs Entity Loading Mini Card for Read-Only Responses](./spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md)를 본다.
- OSIV가 왜 증상을 숨기는지 더 보고 싶으면 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)를 본다.

## 한 줄 정리

controller가 엔티티를 그대로 반환하면 응답 직렬화 단계가 lazy loading을 뒤늦게 실행할 수 있으므로, 초급자 기본값은 service transaction 안에서 필요한 데이터를 DTO로 닫아 반환하는 것이다.
