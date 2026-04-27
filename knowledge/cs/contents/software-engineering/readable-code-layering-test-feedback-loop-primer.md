# 읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문

> 한 줄 요약: 우테코식 코드 리뷰에서 자주 나오는 "이름이 안 읽힌다", "책임이 섞였다", "테스트가 너무 무겁다"는 결국 같은 질문이다. 변경 이유를 나누고, 바꾼 범위를 가장 싼 테스트부터 빠르게 확인할 수 있게 만들었는가?

**난이도: 🟢 Beginner**

관련 문서:

- [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)
- [클린 코드 기초](./clean-code-basics.md)
- [Controller / Service / Repository before 예시 - 주문 생성 로직이 Controller에 몰린 상태](./layered-architecture-basics.md#before-주문-생성-로직이-controller에-몰린-상태)
- [Controller / Service / Repository after 예시 - 주문 생성 흐름을 Controller Service Repository로 나눈 상태](./layered-architecture-basics.md#after-주문-생성-흐름을-controller-service-repository로-나눈-상태)
- [Service 계층 기초](./service-layer-basics.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [TDD 기초](./tdd-basics.md)
- [리팩토링 기초](./refactoring-basics.md)
- [코드 리뷰 기초](./code-review-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: readable code primer, readable code layering testing primer, 관심사 분리 입문, separation of concerns beginner, controller service repository responsibility, readable service method, unit vs integration test beginner, unit test integration test difference, refactor with tests loop, 테스트 피드백 루프, 테스트로 리팩토링 안전망, 우테코 코드 리뷰 가독성, 우테코 코드 리뷰 테스트, beginner readable code, beginner layering testing, red green refactor review loop, service test unit or integration, beginner layering testing mental model, first mission readability checklist, 30분 10분 분기 예시, beginner pr scenario mapping, 가독성 이슈 분기, 레이어 혼합 분기, 테스트 과잉 분기, pr review symptom branch table

## 핵심 개념

입문 단계에서는 용어를 많이 외우기보다 아래 한 문장을 먼저 잡는 편이 좋다.

**읽기 좋은 코드 = 한 메서드와 한 클래스가 한 질문에 답하는 코드**

이 문장을 네 가지로 풀면 다음과 같다.

- 이름이 바로 의도를 말해야 읽기 쉽다.
- 입력, 유스케이스 조립, 저장을 같은 곳에 몰아넣지 않아야 책임이 보인다.
- 비즈니스 규칙은 빠른 단위 테스트로, 프레임워크/DB 연결은 통합 테스트로 확인해야 피드백이 빨라진다.
- 리팩토링은 테스트를 안전망으로 두고 작은 단계로 나눌수록 코드 리뷰가 쉬워진다.

우테코 리뷰에서 이 네 가지가 함께 자주 언급되는 이유도 같다. 결국 리뷰어는 "이 변경이 어디에 속하는지"와 "안전하게 바뀌었는지"를 보고 있다.

## 먼저 잡는 한 줄 멘탈 모델

처음에는 멋진 아키텍처 이름보다 코드가 아래 흐름으로 읽히는지가 더 중요하다.

```text
입력 해석
  -> 유스케이스 조립
  -> 핵심 규칙 실행
  -> 저장/외부 연동
```

이 흐름이 코드와 테스트에 어떻게 대응되는지만 잡아도, 읽기 좋은 코드와 레이어 분리가 같이 보이기 시작한다.

| 지금 확인하는 질문 | 보통 맡는 곳 | 먼저 붙일 테스트 | 리뷰에서 자주 보는 포인트 |
|---|---|---|---|
| 요청 형식이 맞는가 | Controller, Parser | 통합/슬라이스 테스트 | HTTP, 입력 변환, 응답 형식이 비즈니스 규칙과 섞이지 않았는가 |
| 주문/할인/검증 규칙이 맞는가 | Domain, Service | 단위 테스트 | 메서드 이름과 규칙이 같은 수준에서 읽히는가 |
| DB에 제대로 저장되는가 | Repository, JPA Adapter | 통합 테스트 | SQL/JPA 세부가 Service나 Domain으로 새지 않았는가 |
| 전체 흐름이 이어지는가 | 핵심 유스케이스 경로 | 소수의 통합/E2E 테스트 | 전체는 되지만 중간 책임이 뭉개지지 않았는가 |

초심자에게 가장 중요한 감각은 이것이다.

- **단위 테스트는 규칙을 빠르게 확인하는 도구**
- **통합 테스트는 경계와 연결을 확인하는 도구**

둘은 경쟁 관계가 아니라 역할 분담이다.

## 용어가 낯설면 이렇게 번역해서 읽기

처음 읽을 때는 영어 용어를 정확히 외우기보다, 아래처럼 "지금 무엇을 확인하는 말인지"로 번역하면 된다.

| 문서에서 자주 나오는 말 | 초심자용 해석 |
|---|---|
| 유스케이스 조립 (orchestration) | 한 기능을 끝내기 위해 호출 순서를 정하는 일 |
| 도메인 규칙 (domain rule) | 주문/할인/검증처럼 비즈니스에서 바뀌면 안 되는 규칙 |
| 단위 테스트 (unit test) | 외부 의존을 빼고 규칙만 빠르게 확인하는 테스트 |
| 통합/슬라이스 테스트 (integration/slice test) | 스프링/DB/직렬화처럼 경계 연결이 맞는지 확인하는 테스트 |
| 리팩토링 (refactoring) | 외부 동작은 유지한 채 내부 구조만 읽기 좋게 바꾸는 작업 |

## before / after 짧은 예시로 보기

처음에는 아래처럼 "동작은 하지만 읽기 어려운 코드"가 자주 나온다.

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

    productRepository.save(product);
    orderRepository.save(order);

    return new OrderResponse(order.id(), product.name(), request.quantity());
}
```

이 메서드는 한 번에 너무 많은 질문에 답한다.

- 입력 검증
- 조회
- 재고 규칙
- 상태 변경
- 저장
- 응답 조립

그래서 리뷰에서는 보통 아래처럼 읽힌다.

- `create()`라는 이름만으로는 실제 책임이 보이지 않는다.
- Controller나 Service 한 곳에 규칙과 저장과 응답 조립이 다 몰려 있다.
- 이 코드를 테스트하려면 웹, DB, 비즈니스 규칙이 한 덩어리로 묶여 피드백이 느려진다.

같은 흐름을 더 읽기 쉽게 나누면 보통 아래 방향이 된다.

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

이제 질문이 나뉜다.

- Controller는 입력/응답에 집중한다.
- Service는 유스케이스 조립에 집중한다.
- `Order.place(...)`는 핵심 규칙에 집중한다.

그러면 테스트도 자연스럽게 분리된다.

| 확인하고 싶은 것 | 적합한 테스트 |
|---|---|
| `quantity <= 0`이면 예외인가 | 단위 테스트 |
| 재고 부족이면 주문 생성이 막히는가 | 단위 테스트 |
| JSON 요청이 `CreateOrderRequest`로 잘 매핑되는가 | 통합/슬라이스 테스트 |
| JPA 저장과 조회가 기대대로 동작하는가 | 통합 테스트 |

## unit test와 integration test를 이렇게 나눈다

입문자가 가장 자주 헷갈리는 부분은 "Service를 테스트하면 무조건 통합 테스트 아닌가요?"라는 질문이다.

실용적인 기준은 하나다.

**외부 의존을 실제로 붙였는가, 아니면 대체했는가**

| 구분 | 단위 테스트 | 통합 테스트 |
|---|---|---|
| 주로 보는 것 | 비즈니스 규칙, 분기, 계산 | 스프링 빈 연결, DB 매핑, 직렬화, 트랜잭션 |
| 외부 의존 | Fake, Stub, Mock으로 대체 | 실제 DB, 실제 컨텍스트, 실제 직렬화 사용 |
| 속도 | 빠름 | 상대적으로 느림 |
| 리팩토링 내성 | 결과 중심이면 높음 | 경계 변화에 민감하지만 현실 검증에 강함 |
| 먼저 추가할 곳 | 도메인 규칙, 작은 유스케이스 | Repository, Controller, 외부 연동 경계 |

짧게 기억하면 된다.

- "할인 계산 규칙이 맞나?"는 단위 테스트에 가깝다.
- "JPA 매핑이 맞나?"는 통합 테스트에 가깝다.
- "JSON 요청이 잘 들어오나?"도 통합/슬라이스 테스트에 가깝다.

## 리팩토링할 때의 최소 안전 루프

우테코 리뷰 문화에서 중요한 것은 "한 번에 크게 고치는 용기"보다 "작게 바꾸고 바로 확인하는 리듬"이다.

가장 안전한 초심자용 루프는 아래 순서다.

1. 바꾸려는 규칙이나 버그 근처에 작은 테스트를 먼저 둔다.
2. 이름 변경, 메서드 추출, 책임 이동 중 하나만 한다.
3. 가까운 단위 테스트를 먼저 돌려 빠르게 깨졌는지 본다.
4. 경계가 걸려 있으면 관련 통합 테스트도 함께 확인한다.
5. 기능 변경과 구조 변경을 가능한 한 분리해서 리뷰 가능한 단위로 남긴다.

이 루프는 TDD의 `Red -> Green -> Refactor`와도 이어진다. 꼭 모든 코드를 테스트 먼저 작성하지 않더라도, **리팩토링 전에 안전망을 만들고 작은 단위로 이동한다**는 점이 핵심이다.

## 첫 미션에서 바로 쓰는 15분 적용 체크리스트

코드를 전부 다시 설계하려고 하지 말고, 아래 4가지만 먼저 적용하면 리뷰 난이도가 크게 내려간다.

1. 메서드 하나를 고르고 "이 메서드는 한 질문에 답하는가?"만 확인한다.
2. 답이 두 개 이상이면 이름 붙일 수 있는 단계로 한 번만 분리한다.
3. 분리한 규칙에 단위 테스트 1개를 추가한다.
4. 입력 매핑/DB 저장이 바뀌었다면 통합 또는 슬라이스 테스트 1개를 추가한다.

체크리스트를 적용한 뒤 세부 기준이 더 필요하면:

- 책임 경계가 헷갈리면 [계층형 아키텍처 기초](./layered-architecture-basics.md), [Service 계층 기초](./service-layer-basics.md)
- 테스트 구분이 헷갈리면 [테스트 전략 기초](./test-strategy-basics.md)
- 단계적 개선 방법이 더 필요하면 [리팩토링 기초](./refactoring-basics.md)

## 30분에서 10분 분기로 넘어갈 때: 실제 PR 상황 3개

30분 입문을 읽고 나면, 다음 10분은 문서를 많이 여는 시간보다 **지금 받은 리뷰 코멘트를 어느 바구니에 넣을지 고르는 시간**이다.

짧게 기억하면 된다.

- 코드가 안 읽히면 `코드리딩`
- 책임이 섞였으면 `레이어 설계`
- 테스트가 너무 넓거나 무거우면 `테스트`

| PR에서 바로 보이는 상황 | 지금 먼저 떠올릴 질문 | 10분 분기 | 바로 이어서 읽을 문서 |
|---|---|---|---|
| "메서드 이름은 `validate`인데 조회, 저장, 예외 메시지 조립까지 같이 한다" | 이 코멘트가 네이밍 문제인지, 책임 섞임 문제인지 먼저 분리됐나? | 코드리딩 | [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md) |
| "Service 하나가 `Repository` 조회, 외부 API 호출, 이벤트 발행까지 모두 직접 한다" | 이 로직을 옮길 파일을 찾기 전에, 안/밖 경계를 먼저 설명할 수 있나? | 레이어 설계 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) |
| "주문 수량 검증 하나 바꿨는데 `@SpringBootTest`와 DB 초기화 테스트만 커졌다" | 지금 확인하려는 질문이 규칙인지, wiring인지 분리됐나? | 테스트 | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) |

### 예시 1. 가독성 이슈면 먼저 `코드리딩`

리뷰 예시:

> "이 메서드는 이름보다 훨씬 많은 일을 하네요."

이때 초심자가 자주 하는 실수는 바로 `Service`를 더 쪼개거나 클래스를 옮기는 것이다. 그런데 첫 질문은 구조 변경이 아니라, **무슨 종류의 일이 섞였는지 이름을 붙일 수 있는가**다.

| 바로 보이는 증상 | 먼저 할 일 | 아직 미루는 일 |
|---|---|---|
| 한 메서드에서 검증, 상태 변경, 응답 조립이 한 번에 나온다 | 단계 이름을 붙여 읽기 흐름을 다시 적는다 | 새 패턴 도입, 패키지 재배치 |

- 이 경우 10분 문서는 [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md)가 맞다.
- 이유는 "네이밍 문제처럼 보이지만 사실 책임 분리 문제"인 코멘트를 먼저 번역해 주기 때문이다.
- 그다음에도 Controller/Service 경계가 여전히 흐리면 [계층형 아키텍처 기초](./layered-architecture-basics.md)로 이어간다.

### 예시 2. 레이어 혼합이면 먼저 `레이어 설계`

리뷰 예시:

> "Service가 외부 시스템 세부 구현까지 너무 많이 알고 있어요."

이 코멘트에서 중요한 것은 "Service가 두껍다"가 아니라, **유스케이스 조립과 외부 연동 세부가 같은 레이어에 섞였는가**다.

| 바로 보이는 증상 | 먼저 할 일 | 아직 미루는 일 |
|---|---|---|
| Service 안에서 HTTP client, JPA 세부, 이벤트 발행 코드가 다 보인다 | inbound/outbound로 안과 밖 경계를 먼저 나눈다 | 곧바로 헥사고날 전체 구조를 다 도입한다 |

- 이 경우 10분 문서는 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)가 맞다.
- 이유는 "파일을 어디로 옮길까"보다 "무엇이 안쪽 규칙이고 무엇이 바깥 연결인가"를 먼저 잡게 해 주기 때문이다.
- 영속성 누수까지 같이 보여서 헷갈리면 [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)도 같이 연결하면 된다.

### 예시 3. 테스트 과잉이면 먼저 `테스트`

리뷰 예시:

> "이 변경은 수량 규칙 하나인데 왜 서버 전체를 띄우는 테스트만 있죠?"

여기서 초심자가 놓치기 쉬운 지점은 "테스트를 더 많이 쓰라"가 아니라, **질문보다 큰 테스트를 먼저 골라 피드백이 느려졌는가**다.

| 바로 보이는 증상 | 먼저 할 일 | 아직 미루는 일 |
|---|---|---|
| 규칙 1개 확인인데 `@SpringBootTest`만 늘어난다 | unit / adapter / contract 중 어느 경계를 검증할지 먼저 고른다 | E2E 테스트를 더 추가한다 |

- 이 경우 10분 문서는 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)가 맞다.
- 이유는 "테스트 종류"를 고른 다음 단계인 "어느 경계까지 검증할지"를 정리해 주기 때문이다.
- 첫 테스트 종류 자체가 아직 헷갈리면 먼저 [테스트 전략 기초](./test-strategy-basics.md)로 돌아간다.

## 우테코 코드 리뷰에서 자주 들리는 말의 뜻

| 리뷰에서 자주 보이는 말 | 실제로 묻는 질문 | 바로 해볼 수정 |
|---|---|---|
| "메서드가 두 가지 일을 하는 것 같아요." | 한 메서드가 두 개 이상의 이유로 바뀌지 않는가 | 이름 붙일 수 있는 단계별 메서드로 추출한다 |
| "Controller가 너무 많은 걸 알고 있네요." | 입력/응답과 비즈니스 규칙이 섞이지 않았는가 | 규칙을 Service나 Domain으로 옮긴다 |
| "테스트가 구현에 너무 붙어 있어요." | 내부 호출 순서보다 결과를 검증하고 있는가 | 반환값, 상태 변화, 예외 같은 결과를 중심으로 단언한다 |
| "이 리팩토링이 안전한 근거가 있나요?" | 동작이 유지됐다는 증거가 있는가 | 작은 테스트를 추가하고, 변경 전후 모두 통과시킨다 |

즉 리뷰 코멘트는 서로 다른 주제를 말하는 것처럼 보여도, 실제로는 같은 축으로 모인다.

- 읽기 쉬운 책임 분리
- 빠른 테스트 피드백
- 작은 단위의 안전한 리팩토링

## 흔한 오해와 함정

- "읽기 좋은 코드는 짧은 코드다"라고 생각하기 쉽다.
  - 더 정확한 기준은 짧기보다 **의도가 바로 읽히는가**다.
- "Service는 무조건 얇아야 한다"라고 외우기 쉽다.
  - 중요한 것은 얇기보다 **Controller와 Repository 책임을 대신 떠안지 않는가**다.
- "단위 테스트가 많으면 통합 테스트는 거의 없어도 된다"라고 오해하기 쉽다.
  - 규칙 검증과 경계 검증은 다른 질문이다. 둘 다 필요하다.
- "리팩토링은 예쁘게 다시 짜는 것"이라고 느끼기 쉽다.
  - 리팩토링의 핵심은 외부 동작을 유지하면서 내부 구조만 개선하는 것이다.
- "가독성 이슈면 항상 네이밍만 고치면 된다"라고 생각하기 쉽다.
  - 실제 PR에서는 네이밍 뒤에 책임 혼합이 숨어 있는 경우가 많아, 먼저 증상을 분류해야 한다.
- "레이어 혼합이 보이면 바로 헥사고날 전체 구조로 가야 한다"라고 오해하기 쉽다.
  - 초심자에게는 전체 패턴 도입보다 안/밖 경계를 한 번 말로 설명해 보는 것이 먼저다.
- "테스트 과잉은 테스트 개수를 줄이라는 뜻이다"라고 받아들이기 쉽다.
  - 더 중요한 기준은 개수보다 **질문에 맞는 가장 작은 테스트를 골랐는가**다.

## 다음에 읽을 문서

- 이름, 메서드 크기, 추상화 수준이 더 궁금하면 [클린 코드 기초](./clean-code-basics.md)
- Controller / Service / Repository 책임이 더 헷갈리면 [계층형 아키텍처 기초](./layered-architecture-basics.md), [Service 계층 기초](./service-layer-basics.md)
- 단위/통합 테스트의 기본 배치가 더 필요하면 [테스트 전략 기초](./test-strategy-basics.md)
- Red-Green-Refactor 감각을 더 붙이고 싶다면 [TDD 기초](./tdd-basics.md)
- 작은 단계로 구조를 고치는 기준이 더 필요하면 [리팩토링 기초](./refactoring-basics.md)
- 리뷰 댓글을 읽는 법까지 같이 보고 싶다면 [코드 리뷰 기초](./code-review-basics.md)

## 한 줄 정리

읽기 좋은 코드, 레이어 분리, 테스트 전략, 리팩토링은 따로 놀지 않는다. "한 곳에 한 이유만 남기고, 바꾼 범위는 가장 빠른 테스트로 바로 확인한다"는 같은 습관의 다른 이름이다.
