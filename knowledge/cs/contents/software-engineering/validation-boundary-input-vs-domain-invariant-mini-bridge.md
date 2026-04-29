# Validation Boundary Mini Bridge

> 한 줄 요약: 입력 검증은 "문 앞에서 형식을 확인하는 일"이고, 도메인 불변식은 "안으로 들어온 뒤에도 절대 깨지면 안 되는 규칙"이다.

**난이도: 🟢 Beginner**

관련 문서:

- [입력값 검증 기초](../security/input-validation-basics.md)
- [Spring Validation and Binding Error Pipeline](../spring/spring-validation-binding-error-pipeline.md)
- [Layered Validation Pattern: 입력, 도메인, 정책을 층별로 검증하기](../design-pattern/layered-validation-pattern.md)
- [주문 예시로 보는 `@Valid`/바인딩 에러 vs 도메인 규칙 첫 테스트 카드](./order-validation-annotation-vs-domain-rule-card.md)
- [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)

retrieval-anchor-keywords: validation boundary mini bridge, input validation vs domain invariant beginner, 형식 검증 vs 도메인 불변식, 요청 검증 도메인 규칙 차이, validation boundary card, dto validation vs invariant, @valid vs domain invariant, beginner validation invariant bridge, 입력 검증 경계 입문, 도메인 불변식 입문 브리지, validation boundary input vs domain invariant mini bridge basics, validation boundary input vs domain invariant mini bridge beginner, validation boundary input vs domain invariant mini bridge intro, software engineering basics, beginner software engineering

## 먼저 멘탈 모델

처음에는 검증을 `문 앞 검사`와 `집 안 규칙`으로 나누면 덜 헷갈린다.

- 입력 검증: "들어오는 값의 모양이 맞는가?"
- 도메인 불변식: "이 상태를 우리 시스템이 허용하는가?"

짧게 외우면 이 한 줄이면 된다.

> 형식은 입구에서, 규칙은 안쪽에서 지킨다.

## 10초 비교표

| 구분 | 초급자용 질문 | 예시 | 보통 막는 위치 |
|---|---|---|---|
| 입력 검증 | "이 값이 요청으로 읽히나?" | 이메일 형식, 숫자 여부, 필수값 누락 | DTO, controller, request validator |
| 도메인 불변식 | "읽힌 뒤에도 이 상태가 말이 되나?" | 취소된 주문을 다시 결제 완료로 변경, 잔액을 음수로 만들기 | entity, aggregate, domain service |

## 같은 주문 도메인으로 보는 1페이지 비교표

같은 주문 결제 시나리오를 한 장으로 놓고 보면 `Controller`와 `Service/Domain` 경계가 더 선명해진다.

| 장면 | 요청/현재 상태 | 먼저 보는 질문 | 보통 책임 위치 | 왜 여기인가 |
|---|---|---|---|---|
| 입력 형식 검증 | `POST /orders/1/pay` + body `{ "paymentMethod": "" }` | "`paymentMethod`가 비어 있는데 이 요청을 읽을 수 있나?" | Controller / request DTO | HTTP 요청의 모양과 필수값 문제라서 입구에서 바로 거절하는 편이 빠르다 |
| 입력 형식 검증 | `POST /orders/abc/pay` | "경로 변수 `orderId`를 숫자로 읽을 수 있나?" | Controller / binding layer | 아직 주문 규칙을 보기 전 단계다 |
| 업무 규칙 검증 | body `{ "paymentMethod": "CARD" }`, 현재 주문 상태 `CANCELLED` | "형식은 맞지만, 취소된 주문을 결제 완료로 바꿔도 되나?" | Service / Domain | 주문 상태 전이 규칙은 웹 말고 배치나 이벤트 소비자에서도 지켜야 한다 |
| 업무 규칙 검증 | body `{ "paymentMethod": "CARD" }`, 현재 주문 상태 `PAID` | "이미 결제된 주문을 다시 결제해도 되나?" | Service / Domain | 현재 주문 상태를 조회해 판단하는 업무 규칙이기 때문이다 |

짧게 보면 이 흐름이다.

1. Controller는 `요청이 읽히는지` 본다.
2. Service/Domain은 `읽힌 요청이 지금 주문 상태에서 허용되는지` 본다.

## 같은 주문 예시를 코드 위치로 번역하면

```java
// Controller: 요청 형식을 먼저 거른다
@PostMapping("/orders/{orderId}/pay")
void pay(@PathVariable Long orderId, @Valid @RequestBody PayOrderRequest request) {
    orderService.pay(orderId, request.paymentMethod());
}

// Service/Domain: 형식이 맞아도 주문 상태 규칙은 여기서 다시 지킨다
void pay(Long orderId, String paymentMethod) {
    Order order = orderRepository.getById(orderId);
    order.markPaid(paymentMethod); // CANCELLED, PAID 상태면 여기서 막힘
}
```

즉 `paymentMethod`가 비었는지는 Controller에서 빨리 막고, `취소된 주문은 결제 불가` 같은 상태 규칙은 `Order`나 `OrderService`가 끝까지 지킨다.

## 자주 헷갈리는 지점

- `@Positive`, `@NotBlank` 같은 검증이 있으면 "도메인도 안전해졌다"고 생각하기 쉽다. 하지만 다른 진입점(batch, admin tool, event consumer)에서는 DTO 검증을 건너뛸 수 있다.
- `Controller에서 이미 막았는데 Service에서 또 보나?`라는 질문도 많다. 바깥 검증은 빠른 실패용이고, 안쪽 규칙은 진입점이 바뀌어도 깨지지 않게 하는 최종 보호선이다.
- 어떤 규칙은 요청 DTO와 도메인 둘 다에 보일 수 있다. 이때 바깥 검증은 "빨리 거절하기"용이고, 안쪽 불변식은 "어디로 들어오든 최종 보호"용이다.
- "값이 잘못됐다"는 문장 하나로 뭉개면 안 된다. 형식이 틀린 것과, 형식은 맞지만 상태가 금지된 것은 수정 위치와 책임이 다르다.

## 초급자용 판단 순서

1. 이 값이 아예 파싱/변환/형식 검사에서 막혀야 하나?
2. 형식은 맞지만, 현재 상태나 전이가 우리 서비스 규칙을 깨나?
3. 빠른 피드백이 필요하면 바깥에서도 검사하되, 최종 규칙은 도메인 안쪽에도 남겨 뒀나?

## 다음에 어디로 가면 좋은가

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| 서버 입력 검증 자체가 아직 흐리다 | [입력값 검증 기초](../security/input-validation-basics.md) |
| `@Valid`, 바인딩 실패, 검증 실패 순서가 헷갈린다 | [Spring Validation and Binding Error Pipeline](../spring/spring-validation-binding-error-pipeline.md) |
| 주문 예시로 `@WebMvcTest`와 단위 테스트를 어디서 가를지 헷갈린다 | [주문 예시로 보는 `@Valid`/바인딩 에러 vs 도메인 규칙 첫 테스트 카드](./order-validation-annotation-vs-domain-rule-card.md) |
| 입력, 도메인, 정책을 세 층으로 더 넓게 보고 싶다 | [Layered Validation Pattern: 입력, 도메인, 정책을 층별로 검증하기](../design-pattern/layered-validation-pattern.md) |
| 도메인 불변식을 계약 수준으로 더 깊게 보고 싶다 | [Domain Invariants as Contracts](./domain-invariants-as-contracts.md) |

## 한 줄 정리

입력 검증은 "요청 모양이 맞는지"를 거르는 문 앞 검사이고, 도메인 불변식은 "형식이 맞아도 절대 깨지면 안 되는 상태 규칙"을 지키는 안쪽 보호선이다.
