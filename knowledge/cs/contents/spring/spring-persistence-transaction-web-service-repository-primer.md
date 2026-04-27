# Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기

> 한 줄 요약: 초급자는 `@Transactional`을 "DB 저장 스위치"가 아니라, service 메서드 안에서 persistence context를 열고 닫으며 commit 전까지 변경을 모아 두는 경계로 보면 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)
- [Spring Data JPA Test `flush` / `clear` / rollback visibility pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring persistence context beginner, transaction mental model, transactional persistence context primer, flush commit difference beginner, lazy loading beginner, lazy initialization exception beginner, controller service repository transactional 어디, transactional 어디까지, service layer transaction boundary beginner, web service repository transaction boundary, jpa persistence context 큰 그림, 영속성 컨텍스트 큰 그림, 플러시 커밋 차이, 지연 로딩 입문, osiv beginner

## 먼저 mental model 한 줄

한 HTTP 요청에서 DB 일이 필요하면 보통 이렇게 본다.

```text
Controller는 요청/응답을 받고
Service는 유스케이스를 묶고
Repository는 DB와 대화하고
@Transactional은 그 service 작업을 하나의 commit 단위로 감싼다
Persistence Context는 그 안에서 엔티티를 기억하고 변경을 모아 둔다
```

초급자에게 중요한 건 용어보다 이 순서다.

- `@Transactional`은 주로 service 경계에 붙는다.
- repository 호출이 여러 번 나가도 같은 transaction 안이면 같은 작업 묶음일 수 있다.
- 엔티티를 바꾸자마자 바로 DB에 쓰는 게 아니라, persistence context가 먼저 상태를 들고 있다가 `flush` 때 SQL로 보낸다.
- lazy loading은 "나중에 필요해지면 SQL을 더 날릴 수 있는 프록시 접근"이다.

## 30초 그림

```text
HTTP 요청
  -> Controller
  -> Service (@Transactional 시작)
  -> Persistence Context 생성
  -> Repository 조회/저장
  -> 엔티티 변경은 Persistence Context가 추적
  -> 필요 시 flush(SQL 전송)
  -> Service 종료
  -> commit 또는 rollback
  -> Persistence Context 종료
```

핵심은 `repository.save()` 한 줄이 아니라, **service 메서드 전체가 작업 단위**라는 점이다.

## 한눈에 보는 역할 분리

| 레이어 | 초급자용 역할 | 여기서 보통 하지 않는 일 | 지금 기억할 한 줄 |
|---|---|---|---|
| Controller | HTTP 요청을 받고 응답으로 바꾼다 | 트랜잭션 경계 설계, 비즈니스 상태 전이 결정 | 웹 입구다 |
| Service | 유스케이스를 실행하고 commit 단위를 잡는다 | SQL 세부 구현 직접 관리 | 보통 트랜잭션 주인이다 |
| Repository | 엔티티 조회/저장 쿼리를 수행한다 | 유스케이스 전체 원자성 결정 | DB 통로다 |
| Persistence Context | 조회한 엔티티를 기억하고 변경을 추적한다 | 요청 전체 비즈니스 의미 결정 | transaction 안의 작업 메모리다 |

## 용어를 최소로 다시 묶기

| 용어 | 초급자 언어로 다시 말하면 |
|---|---|
| `@Transactional` | "이 service 메서드는 같이 성공하거나 같이 실패한다"는 선언 |
| transaction boundary | commit/rollback이 결정되는 경계 |
| persistence context | transaction 동안 엔티티를 들고 있으면서 변경을 추적하는 작업 메모리 |
| `flush` | 메모리에 모인 변경을 SQL로 내보내는 동기화 |
| commit | transaction을 최종 확정하는 순간 |
| lazy loading | 연관 객체를 지금 말고 나중에 SQL로 가져오게 미뤄 둔 상태 |

## `flush`와 commit은 다르다

초급자가 가장 많이 섞는 두 개다.

| 질문 | `flush` | commit |
|---|---|---|
| 무엇을 하나 | SQL을 DB로 보낸다 | transaction 결과를 최종 확정한다 |
| 아직 rollback 가능한가 | 가능하다 | 보통 끝났다 |
| 다른 transaction에서 항상 보이나 | 보장하지 않는다 | commit 이후에 보인다 |
| 왜 쓰나 | 제약 조건 오류를 미리 드러내거나, 뒤 SQL 전에 동기화하려고 | 정상 종료 시 최종 반영하려고 |

짧게 외우면 이렇다.

- `flush`는 "보내기"다.
- commit은 "확정"이다.

## 가장 흔한 흐름 예시

```java
@Service
public class OrderService {

    private final OrderRepository orderRepository;

    @Transactional
    public void changeAddress(Long orderId, String address) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow();

        order.changeAddress(address); // 아직 바로 commit 아님
    }
}
```

이 코드를 초급자 눈으로 순서만 보면 된다.

1. service 메서드 진입 시 transaction이 시작된다.
2. `findById`로 가져온 `order`는 persistence context가 관리한다.
3. `changeAddress()`로 객체 상태가 바뀌면 dirty checking 대상이 된다.
4. 메서드 끝나기 전 `flush` 시점에 `update` SQL이 나갈 수 있다.
5. 마지막에 commit 되면 변경이 확정된다.

즉 `save()`를 안 불렀다고 항상 저장이 안 되는 것이 아니다. managed 엔티티 변경은 transaction 종료 과정에서 반영될 수 있다.

## 왜 service에 `@Transactional`을 많이 두나

repository는 "한 번 조회, 한 번 저장" 같은 개별 DB 동작을 담당한다.
그런데 유스케이스는 보통 한 번의 호출로 끝나지 않는다.

예를 들면 주문 생성은 이렇게 묶일 수 있다.

- 주문 저장
- 재고 차감
- 쿠폰 사용 처리

이 셋이 같이 성공하거나 같이 실패해야 하면 repository 각각이 아니라 **이 작업을 묶는 service 메서드**가 transaction 경계를 잡는 편이 자연스럽다.

| 위치 | 초급자에게 자주 생기는 오해 | 더 나은 기본값 |
|---|---|---|
| Controller | "요청 하나니까 여기서 transaction 열까?" | 웹 경계보다 유스케이스 경계가 중요하다 |
| Repository | "DB랑 가까우니 여기서 끝내면 되나?" | 여러 repository 호출을 service에서 같이 묶는 편이 많다 |
| Service | "여기가 너무 중간 아닌가?" | 보통 여기가 유스케이스와 commit 단위가 만난다 |

## lazy loading은 왜 controller에서 문제처럼 보이나

초급자에게는 "service에서 조회했는데 왜 controller JSON 만들 때 SQL이 또 나가지?"가 큰 혼란이다.

그 이유는 보통 연관 객체가 lazy 상태이기 때문이다.

```java
@GetMapping("/orders/{id}")
public OrderResponse find(@PathVariable Long id) {
    Order order = orderService.findOrder(id);
    return OrderResponse.from(order);
}
```

`OrderResponse.from(order)` 안에서 `order.getMember().getName()` 같은 lazy 연관 접근이 있으면 그 시점에 추가 SQL이 나갈 수 있다.

| 보이는 현상 | 실제로는 무슨 일인가 |
|---|---|
| controller/직렬화에서 갑자기 SQL이 찍힌다 | lazy loading이 늦게 실행됐다 |
| `LazyInitializationException`이 난다 | transaction/persistence context가 이미 닫힌 뒤 lazy 접근했다 |
| 개발 중엔 되는데 운영에서 쿼리가 이상하게 많다 | OSIV가 늦은 lazy loading을 숨기고 있을 수 있다 |

초급자 기준 한 줄은 이것이다.

- service 안에서 필요한 데이터를 다 준비하면 경계가 명확해진다.
- controller는 가능하면 엔티티보다 DTO를 받는 쪽이 안전하다.

## OSIV를 초급자 눈으로만 이해하기

OSIV(Open Session In View)는 "웹 응답이 끝날 때까지 persistence context를 조금 더 열어 둔다" 정도로만 먼저 보면 된다.

| OSIV off에 가까운 감각 | OSIV on에 가까운 감각 |
|---|---|
| service가 끝나면 lazy 접근이 빨리 실패한다 | controller/직렬화에서도 lazy 접근이 될 수 있다 |
| 경계가 빨리 드러난다 | 편하지만 숨은 SQL이 늦게 튀어나올 수 있다 |

OSIV 자체를 지금 외우기보다, 초급자는 먼저 아래만 기억하면 충분하다.

- "service 밖에서 엔티티를 계속 만지면 SQL이 늦게 나갈 수 있다."
- "그래서 DTO로 필요한 값만 넘기는 연습이 중요하다."

## 자주 하는 혼동 5개

- "`@Transactional` = SQL 한 줄마다 commit"이 아니다. 보통 service 메서드 전체가 한 transaction이다.
- "`flush` = commit"이 아니다. SQL을 보냈어도 rollback될 수 있다.
- "`repository.save()`를 안 했으니 update가 안 된다"가 아니다. managed 엔티티는 dirty checking으로 반영될 수 있다.
- "`lazy loading`은 그냥 성능 옵션"만이 아니다. transaction 경계 밖 접근에서 예외나 숨은 SQL 문제로 이어질 수 있다.
- "`controller에도 @Transactional 붙이면 편하다`"가 아니다. 웹 경계와 DB 경계를 섞어 오래 잡는 쪽으로 흐르기 쉽다.

## 초급자용 안전한 기본값

| 상황 | 먼저 잡을 기본값 |
|---|---|
| 상태 변경 유스케이스 | service 메서드에 `@Transactional` |
| 조회 응답 만들기 | service 안에서 필요한 데이터 준비 후 DTO 반환 |
| `flush`가 헷갈림 | "SQL 전송"과 "최종 확정"을 분리해서 기억 |
| lazy loading이 헷갈림 | service 밖에서 엔티티를 오래 끌고 가지 않기 |
| controller/service/repository 역할이 섞임 | controller는 HTTP, service는 유스케이스, repository는 DB 통로로 다시 자르기 |

## 어디까지 읽고, 다음에 어디로 갈까

| 지금 막히는 질문 | 다음 문서 |
|---|---|
| "`@Transactional`이 왜 안 먹지?" | [@Transactional 기초](./spring-transactional-basics.md) |
| "service를 어떻게 나눠야 하지?" | [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md) |
| "`flush`, `clear`, `detach` 차이를 더 정확히 알고 싶다" | [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md) |
| "lazy loading과 OSIV를 더 제대로 보고 싶다" | [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md) |
| "테스트에서는 왜 보이는데 운영에서는 다르게 보이지?" | [Spring Data JPA Test `flush` / `clear` / rollback visibility pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md) |

## 한 줄 정리

초급자 기준으로 Spring persistence와 transaction은 "service 메서드가 transaction 경계를 잡고, 그 안에서 persistence context가 엔티티를 추적하며, `flush`는 SQL 전송이고 commit은 최종 확정이며, lazy loading은 그 경계 밖으로 나가면 문제를 드러낸다"로 기억하면 된다.
