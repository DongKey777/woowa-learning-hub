# 읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문

> 한 줄 요약: "메서드가 안 읽힌다", "Controller가 너무 많은 걸 안다", "테스트가 너무 무겁다"는 결국 같은 질문이다. 바꾸려는 이유 1개를 고르고, 그 이유를 가장 싼 테스트 1개로 먼저 잠근다.

**난이도: 🟢 Beginner**

관련 문서:

- [클린 코드 기초](./clean-code-basics.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [리팩토링 기초](./refactoring-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [코드 리뷰 기초](./code-review-basics.md)
- [Spring Bean DI 기초](../spring/spring-bean-di-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: readable code primer, layering testing loop, 메서드가 너무 길어요, controller가 너무 많은 걸 알아요, 왜 서버 전체 테스트부터, service 테스트가 통합테스트인가요, 관심사 분리 입문, controller service repository responsibility, unit vs integration test beginner, refactor with tests loop, 테스트 피드백 루프, 우테코 코드 리뷰 가독성

## README 복귀 가이드

- starter 분기가 다시 흐려지면 [Software Engineering README - 30초 starter 지도](./README.md#30초-starter-지도)로 돌아간다.
- 구조보다 `queue/map` 선택이 먼저 막히면 [자료구조 README - 초급 10초 라우터](../data-structure/README.md#초급-10초-라우터)로 잠깐 우회한다.

## 먼저 자르는 3칸 비교

처음에는 용어보다 **리뷰 문장을 어느 칸에 넣을지**만 정하면 된다.

| 지금 들리는 말 | 먼저 붙일 이름 | 바로 확인할 1개 | 다음 문서 |
|---|---|---|---|
| "메서드가 너무 길어요" | 읽기 문제 | 한 메서드가 질문 1개만 답하는가 | [클린 코드 기초](./clean-code-basics.md) |
| "Controller가 너무 많은 걸 알아요" | 레이어 문제 | 입력, 규칙, 저장이 한곳에 섞였는가 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| "왜 서버 전체 테스트부터 돌리죠?" | 테스트 문제 | 지금 검증할 질문 1개가 무엇인가 | [테스트 전략 기초](./test-strategy-basics.md) |

- 짧게 외우면 `읽기 = 질문 분리`, `레이어 = 자리 분리`, `테스트 = 검증 범위 분리`다.

## 먼저 잡는 한 줄 멘탈 모델

초심자에게는 이 흐름이면 충분하다.

```text
입력 해석 -> 규칙 실행 -> 저장/응답
```

- 입력 해석: Controller
- 규칙 실행: Service/Domain
- 저장/응답: Repository, Response DTO

이 흐름이 한 메서드에 한꺼번에 섞이면 읽기 문제가 되고, 한 클래스에 오래 붙어 있으면 레이어 문제가 되며, 한 번에 다 검증하려 들면 테스트가 무거워진다.

## 리뷰 문장을 다음 행동으로 바꾸는 1분 카드

| 리뷰나 셀프리뷰 문장 | 먼저 볼 자리 | 첫 행동 | 바로 다음 링크 |
|---|---|---|---|
| "이름은 단순한데 더 많은 일을 해요" | Service 메서드 단계 | `검증 -> 저장 -> 응답`이 한 메서드에 섞였는지 표시 | [클린 코드 기초](./clean-code-basics.md) |
| "Controller가 규칙까지 다 알아요" | Controller | 업무 규칙과 저장 호출에 밑줄 긋기 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| "Service 테스트가 너무 무거워요" | 테스트 코드 | DB, 스프링, HTTP를 실제로 붙였는지 확인 | [테스트 전략 기초](./test-strategy-basics.md) |
| "`List`/`Set`/`Map` 선택 때문에 규칙 설명이 자꾸 흐려져요" | 규칙 문장 자체 | `순서 / 중복 / key 조회` 중 무엇을 묻는지 한 줄로 다시 적기 | [Java 컬렉션 프레임워크 입문](../language/java/java-collections-basics.md) |
| "구조를 바꾸고 싶은데 불안해요" | 변경 범위 | 바뀌는 규칙 1개를 테스트 1개로 먼저 잠그기 | [리팩토링 기초](./refactoring-basics.md) |

## 초심자가 자주 하는 혼동 한 번에 끊기

| 헷갈리는 첫 판단 | 다시 볼 기준 | 첫 행동 |
|---|---|---|
| 메서드를 둘로 나눴으니 충분하다 | 이름보다 질문 수가 줄었는가 | `검증/저장/응답`이 아직 같이 있으면 한 번 더 자른다 |
| Controller가 얇아졌으니 레이어도 끝났다 | 규칙이 여전히 한 클래스에 몰렸는가 | Service/Domain 쪽에 남을 규칙을 다시 적는다 |
| Service를 테스트했으니 통합 테스트다 | 실제로 붙인 것이 무엇인가 | fake/mock이면 규칙 테스트부터 본다 |

- 짧게 외우면 `메서드 분리 != 책임 분리 완료`, `얇은 Controller != 좋은 경계 완료`, `Service 테스트 != 자동 통합 테스트`다.

## 잘못된 첫 반응 대신 이렇게 시작한다

초심자는 구조 피드백을 들으면 `일단 메서드 추출`, `일단 Service로 이동`, `일단 서버 전체 테스트`처럼 크게 반응하기 쉽다. 아래처럼 **더 작은 첫 행동**으로 줄이면 다음 문서도 덜 헷갈린다.

| 지금 보인 증상 | 자주 하는 큰 반응 | 더 싼 첫 행동 | 바로 다음 문서 |
|---|---|---|---|
| "메서드가 너무 길어요" | 이름만 바꾼 private 메서드를 여러 개 뽑는다 | `검증/저장/응답` 중 어떤 질문이 섞였는지 표시한다 | [클린 코드 기초](./clean-code-basics.md) |
| "Controller가 너무 많은 걸 알아요" | 코드를 통째로 Service로 옮긴다 | `입력 형식`과 `업무 규칙`을 다른 색으로 표시한다 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| "구조를 바꾸기 무서워요" | `@SpringBootTest`부터 크게 붙인다 | 방금 옮길 규칙 1개만 단위 테스트로 먼저 잠근다 | [테스트 전략 기초](./test-strategy-basics.md) |

- 멘탈 모델은 `크게 옮기기`보다 `질문 1개 표시 -> 책임 1개 이동 -> 테스트 1개 고정`이다.

## 같은 주문 생성 코드로 보는 1회 pass

처음부터 구조 전체를 바꾸지 말고 **책임 1개 이동 + 테스트 1개 고정**만 한다.

| 순서 | 이번 pass에서 하는 일 | 먼저 잠글 테스트 |
|---|---|---|
| 1 | `create()` 안에서 `수량 검증 / 저장 / 응답 조립`을 표시한다 | 아직 추가하지 않아도 된다 |
| 2 | `수량은 1개 이상` 규칙만 Service/Domain 쪽으로 옮긴다 | 단위 테스트 1개 |
| 3 | Controller에는 요청 파싱과 응답 반환만 남긴다 | 계약이 바뀌었을 때만 `@WebMvcTest` 1개 |
| 4 | 초록을 확인한 뒤 다음 책임 1개로 넘어간다 | 기존 테스트 재실행 |

- 이 pass에서는 `retry`, `rollback`, 외부 운영 시나리오까지 같이 다루지 않는다.
- 그런 질문은 starter 3축을 정리한 뒤 관련 문서로 넘긴다.

## 지금은 링크만 걸고 지나가는 질문

이 primer의 역할은 `읽기 문제인가 -> 책임 위치 문제인가 -> 첫 테스트 문제인가`를 고르는 데 있다. 아래 질문은 초심자 입구에서 바로 풀기보다, **책임 1개 + 테스트 1개**가 잡힌 뒤에 관련 문서로 넘기는 편이 덜 헷갈린다.

| 지금 들리는 말 | 여기서 바로 깊게 안 파는 이유 | 막혔을 때 여는 문서 |
|---|---|---|
| "재시도 몇 번까지가 맞죠?", "멱등키는 어디까지 퍼져야 하죠?" | 첫 pass가 `규칙 1개 이동`이 아니라 운영 분기표 정리로 커지기 쉽다 | [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md) |
| "함께 저장되거나 함께 실패해야 하나요?" | 읽기/레이어 문제보다 협력 흐름 검증 질문에 가깝다 | [테스트 전략 기초](./test-strategy-basics.md#같은-주문-생성-예시로-보는-레이어-변경---첫-테스트) |
| "배치나 메시지 consumer도 같은 규칙을 써야 해요" | `Controller -> Service -> Repository` starter를 넘어서 진입점/출구 경계 설계가 필요하다 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) |
| "`Map`/`Queue`가 왜 여기서 나오죠?", "`Optional`과 빈 컬렉션을 어디서 나누죠?" | 구조 primer를 건너뛰고 deep dive 구현체로 가면 `규칙 문장`보다 타입 이름만 남기 쉽다 | [Java 컬렉션 프레임워크 입문](../language/java/java-collections-basics.md) -> [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) |

- stop rule: 아직 `이번 pass에서 옮길 책임 1개`를 말할 수 없다면 이 표의 문서는 읽지 않고 starter 표로 돌아간다.
- 초심자 첫 pass에서는 `retry`, `incident`, `rollback` 같은 운영 단어가 보여도 본문에서 붙잡지 않는다. 이 문서는 링크만 건네고, starter 3축을 정한 뒤 follow-up으로 넘긴다.

## 첫 10분 실행 순서

| 순서 | 지금 할 일 | 끝났다고 볼 기준 |
|---|---|---|
| 1 | 리뷰 문장을 `읽기 / 레이어 / 테스트` 중 하나로 이름 붙인다 | 어느 표를 볼지 정해진다 |
| 2 | 코드에서 책임이 섞인 줄 1곳만 표시한다 | 이번 pass에서 옮길 책임 1개가 정해진다 |
| 3 | 그 변경을 가장 싸게 검증할 테스트 1개를 고른다 | 다음 행동이 `코드 1곳 + 테스트 1개`로 줄어든다 |

- 여기까지 정해졌다면 이 primer의 역할은 끝이다.
- 다음 행동도 `코드 1곳 + 테스트 1개`보다 커지면, 더 읽기보다 다시 이 표로 돌아와 범위를 줄인다.

## before / after 짧은 예시로 보기

```java
public OrderResponse create(CreateOrderRequest request) {
    if (request.quantity() <= 0) {
        throw new IllegalArgumentException("수량은 1개 이상이어야 합니다.");
    }

    Product product = productRepository.findById(request.productId())
            .orElseThrow(() -> new IllegalArgumentException("상품이 없습니다."));

    if (product.stock() < request.quantity()) {
        throw new IllegalStateException("재고가 부족합니다.");
    }

    product.decrease(request.quantity());
    Order order = new Order(product.id(), request.quantity());
    orderRepository.save(order);

    return new OrderResponse(order.id(), product.name(), request.quantity());
}
```

위 코드는 동작은 하지만 질문이 많다. 입력 검증, 조회, 재고 규칙, 저장, 응답 조립이 한 메서드에 몰려 있다.

```java
public OrderResponse create(CreateOrderRequest request) {
    OrderId orderId = orderService.place(request.toCommand());
    return OrderResponse.from(orderId);
}
```

```java
public OrderId place(CreateOrderCommand command) {
    Product product = productRepository.get(command.productId());
    Order order = Order.place(product, command.quantity());
    orderRepository.save(order);
    return order.id();
}
```

이제 초심자는 "Controller는 입력/응답", "Service는 흐름 조립", "Domain은 규칙"처럼 읽을 수 있다.

## unit test와 integration test를 이렇게 나눈다

| 지금 확인할 질문 | 먼저 붙일 테스트 | 이유 |
|---|---|---|
| 수량이 0이면 예외가 나는가 | unit test | 규칙만 빠르게 깨져야 구조 정리가 쉽다 |
| 잘못된 요청이 400으로 막히는가 | `@WebMvcTest` | 웹 계약은 HTTP 경계에서 확인하는 게 빠르다 |
| 저장/조회 매핑이 맞는가 | `@DataJpaTest` | JPA와 SQL은 실제 연결이 필요하다 |
| 주문 저장과 재고 차감이 함께 묶이는가 | 소수의 통합 테스트 | 여러 경계가 실제로 이어지는지 보는 질문이다 |

## 다음에 읽을 문서

- 읽기 문제가 더 크면 [클린 코드 기초](./clean-code-basics.md)
- 자리 문제가 더 크면 [계층형 아키텍처 기초](./layered-architecture-basics.md)
- 첫 테스트 선택이 더 막히면 [테스트 전략 기초](./test-strategy-basics.md)
- 구조를 안전하게 옮기는 순서가 더 필요하면 [리팩토링 기초](./refactoring-basics.md)

## 한 줄 정리

읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프는 다른 주제가 아니라 `책임 1개를 분리하고 그 책임을 가장 싼 테스트 1개로 잠그는 같은 작업`이다.
