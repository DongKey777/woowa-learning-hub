# LazyInitializationException Debug Sequence

> 한 줄 요약: `LazyInitializationException`은 "연관을 못 읽었다"보다 "연관을 읽은 위치가 transaction 경계 밖이었다"에 가깝기 때문에, 초급자는 먼저 `어디서 접근했는지`를 따라가며 transaction boundary, DTO 변환 시점, OSIV 설정을 차례대로 분리해서 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md)
- [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)
- [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)

retrieval-anchor-keywords: lazyinitializationexception debug sequence, lazy initialization exception beginner, jpa lazy loading debug order, transaction boundary lazy loading, dto mapping lazy initialization, osiv lazy initialization check, spring jpa lazy exception 어디서, lazy loading controller service boundary, open session in view beginner, lazy loading debug checklist, 왜 lazyinitializationexception 나지, 초급자 lazy loading 디버깅, spring lazyinitializationexception debug sequence basics, spring lazyinitializationexception debug sequence beginner, spring lazyinitializationexception debug sequence intro

## 핵심 개념

`LazyInitializationException`은 보통 "JPA가 고장 났다"가 아니다.

대부분은 아래 셋 중 하나다.

- transaction이 이미 끝났는데 lazy 연관에 접근했다
- DTO 변환이 controller나 serializer 쪽으로 밀렸다
- OSIV가 켜져 있거나 꺼져 있어서 증상이 다르게 보인다

초급자는 예외 메시지를 길게 읽기보다 먼저 이렇게 기억하면 된다.

- `LAZY` 연관은 접근하는 순간 SQL이 더 필요할 수 있다
- 그 SQL은 보통 열린 persistence context와 transaction 경계 안에서만 안전하다
- 그래서 "무슨 연관이 lazy였나?"보다 "`어디서` 그 getter를 불렀나?"가 더 중요하다

## 한눈에 보기

| 먼저 볼 질문 | 그렇다면 의심할 축 | 가장 흔한 해석 |
|---|---|---|
| 예외가 controller, serializer, view 쪽에서 났나 | transaction boundary 또는 DTO 변환 시점 | service 안에서 DTO를 닫지 못했다 |
| service 메서드 안에서 DTO를 만들었는데도 났나 | 조회 계획 부족 | 필요한 연관을 fetch join / `@EntityGraph`로 미리 안 읽었다 |
| OSIV on에서는 안 나고 off에서는 나나 | OSIV가 문제를 숨기고 있다 | 경계 위반이 있었는데 on에서 늦게 SQL을 허용했다 |
| 엔티티를 API 응답으로 직접 내보내나 | DTO 변환 시점 문제 | Jackson 직렬화가 lazy getter를 건드렸을 수 있다 |

디버그 순서는 "예외 위치 확인 -> DTO 변환 위치 확인 -> transaction 경계 확인 -> OSIV 해석" 순서가 가장 덜 헷갈린다.

## 디버그 순서

아래 순서는 초급자가 원인을 가장 빨리 좁히는 기본 루틴이다.

예외 위치를 먼저 잡고, DTO 변환 위치와 transaction 경계를 확인한 뒤, 마지막에 OSIV를 해석한다.

## 1단계: 예외가 난 정확한 접근 지점을 찾는다

stack trace에서 `getMember()`, `getOrders()`, `toResponse()`, `serialize` 같은 지점을 먼저 찾는다.

이 단계에서 보고 싶은 것은 "어떤 연관이 lazy였는가"보다 아래 두 가지다.

- 누가 그 getter를 불렀나
- 그 코드가 service 안인지, controller 밖인지

초급자 기준으로는 예외 라인이 아래 위치면 거의 방향이 잡힌다.

- service 밖 controller: 경계 밖 lazy 접근 가능성 큼
- response serializer/Jackson: 엔티티 직접 반환 가능성 큼
- service 내부 DTO 생성: fetch plan 부족 가능성 큼

## 2단계: DTO를 어디서 만드는지 본다

가장 먼저 확인할 질문은 이것이다.

"엔티티를 service 밖으로 들고 나가고 있나?"

```java
@GetMapping("/orders/{id}")
public OrderResponse find(@PathVariable Long id) {
    Order order = orderService.findById(id);
    return new OrderResponse(order.getId(), order.getMember().getName());
}
```

이 코드는 초급자가 가장 자주 만나는 패턴이다.

- `orderService.findById()`가 엔티티를 반환한다
- DTO 변환은 controller에서 한다
- `order.getMember()`가 lazy면 transaction 밖 접근이 되기 쉽다

이 경우는 먼저 "DTO 변환을 service 안으로 옮길 수 있는가"를 본다.

## 3단계: service transaction 경계를 확인한다

다음으로 service 메서드가 실제로 transaction 안에서 실행되는지 본다.

```java
@Transactional(readOnly = true)
public OrderResponse findById(Long id) {
    Order order = orderRepository.findById(id).orElseThrow();
    return new OrderResponse(order.getId(), order.getMember().getName());
}
```

여기서 체크할 것은 두 가지다.

- `@Transactional`이 DTO 변환을 감싸고 있는가
- DTO에 필요한 연관 접근이 그 메서드 안에서 끝나는가

둘 다 만족하면 "경계 밖 접근"보다는 "조회 시점에 필요한 연관을 안 읽었다" 쪽으로 좁혀진다.

## 4단계: 조회 계획이 부족한지 본다

service 안에서 DTO를 만들더라도, 필요한 연관을 미리 읽지 않으면 같은 transaction 안에서 추가 SQL이 나간다.

이건 바로 예외가 아니라 다음 문제로 이어질 수 있다.

- N+1
- controller까지 엔티티를 넘기고 싶은 유혹
- OSIV on에 기대는 구조

DTO에 꼭 필요한 연관이면 조회 메서드에서 먼저 드러내는 편이 안전하다.

- fetch join
- `@EntityGraph`

즉 "`@Transactional`이 있으니 됐다"가 아니라, "DTO가 읽을 연관을 조회 시점에 준비했나"까지 같이 본다.

## 5단계: OSIV 설정을 마지막에 해석한다

`spring.jpa.open-in-view`는 원인 자체라기보다 **증상을 보이게 하거나 숨기는 설정**에 가깝다.

| 관찰된 모습 | 해석 |
|---|---|
| OSIV off에서만 예외가 난다 | 원래 있던 경계 위반이 빨리 드러난 것일 수 있다 |
| OSIV on에서는 정상처럼 보인다 | controller/serializer에서 늦은 SQL이 허용됐을 수 있다 |
| OSIV on인데도 예외가 난다 | 비동기 경계, 세션 종료 시점, detached 상태 등 더 강한 경계 문제가 있을 수 있다 |

초급자 기본값은 이것이다.

- OSIV on: 예외를 가릴 수 있다
- OSIV off: 경계 위반을 빨리 드러낸다

그래서 예외를 없애려고 먼저 OSIV를 켜는 것보다, **왜 service 안에서 DTO를 닫지 못했는지**를 먼저 보는 쪽이 안전하다.

## 원인 축을 3개로 분리해서 판단하기

| 축 | 이런 증상이 보이면 먼저 의심 | 첫 대응 |
|---|---|---|
| transaction boundary | controller, view, serializer에서 lazy getter 접근 | 엔티티 반환을 줄이고 service 안 DTO 변환으로 이동 |
| DTO mapping point | `toResponse()`, `from(entity)`, Jackson 직렬화에서 예외 | DTO 생성 위치를 service 안으로 당긴다 |
| OSIV settings | on/off에 따라 동작이 크게 달라짐 | 설정을 해결책으로 보기보다 증상 차이 해석용으로 사용 |

아래처럼 생각하면 덜 헷갈린다.

- controller에서 DTO를 만들고 있었다 -> DTO mapping point 문제
- 그 DTO 변환이 transaction 밖이었다 -> transaction boundary 문제
- OSIV on에서만 통과했다 -> 문제를 고친 게 아니라 숨겼을 가능성

즉 셋은 서로 경쟁하는 원인이 아니라, **같은 문제를 다른 각도에서 보여 주는 체크포인트**다.

## 흔한 오해와 함정

- "`@Transactional`만 붙이면 LazyInitializationException이 사라진다"가 아니다. DTO 변환이 그 바깥에 있으면 그대로 난다.
- "`EAGER`로 바꾸면 해결"이 아니다. 전역 fetch를 무겁게 만들고 다른 조회까지 끌고 온다.
- "OSIV on이면 안전하다"가 아니다. 예외가 안 보여도 controller SQL, 숨은 N+1이 남을 수 있다.
- "repository가 엔티티를 반환하니 controller에서 조금 만져도 된다"가 아니다. 초급자 기본값은 service 안 DTO 반환이다.

## 실무에서 쓰는 가장 짧은 점검 루틴

1. stack trace에서 lazy getter가 실제로 호출된 위치를 찾는다.
2. 그 위치가 service 밖이면 DTO 변환 위치부터 옮긴다.
3. service 안이면 `@Transactional` 경계가 DTO 생성까지 감싸는지 본다.
4. 그래도 필요 연관 접근이 많으면 fetch join 또는 `@EntityGraph`로 조회 계획을 드러낸다.
5. 마지막으로 `spring.jpa.open-in-view` 값을 보고, OSIV가 예외를 숨기고 있었는지 해석한다.

이 순서가 중요한 이유는, 초급자가 자주 하는 역순이 "OSIV부터 바꾸기"이기 때문이다.

OSIV를 먼저 만지면 원인 분리가 흐려진다.

## 더 깊이 가려면

- DTO 변환 위치를 더 자세히 보고 싶으면 [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- persistence context와 transaction 큰 그림을 다시 맞추려면 [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- OSIV의 장단점을 따로 보고 싶으면 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- 조회 시점 fetch plan 선택을 짧게 비교하려면 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)
- lazy loading 뒤에서 같이 터지는 N+1은 [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)

## 한 줄 정리

`LazyInitializationException`을 만나면 "lazy라서 터졌다"보다 "어느 경계 밖에서 lazy getter를 호출했는가"를 먼저 따라가고, 그다음 DTO 변환 위치와 OSIV가 증상을 어떻게 바꿨는지 차례대로 분리해서 보면 된다.
