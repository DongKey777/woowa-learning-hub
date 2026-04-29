# 주문 예시로 보는 `@Valid`/바인딩 에러 vs 도메인 규칙 첫 테스트 카드

> 한 줄 요약: 주문 생성에서 `@Valid`와 바인딩 에러는 "요청을 읽을 수 있는가"를 묻고, 도메인 규칙은 "읽힌 요청이 지금 주문 상태에서 허용되는가"를 묻기 때문에 첫 테스트도 `@WebMvcTest`와 단위 테스트로 갈라진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Validation Boundary Mini Bridge](./validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- [Controller 계약 변경 vs Service 규칙 변경 첫 failing test 미니 카드](./controller-contract-vs-service-rule-first-test-mini-card.md)
- [Service 계층 기초](./service-layer-basics.md)
- [Spring Validation and Binding Error Pipeline](../spring/spring-validation-binding-error-pipeline.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: order validation annotation vs domain rule, @valid vs domain rule order, binding error vs domain invariant order, 주문 @valid 도메인 규칙 차이, 주문 validation 400 vs business rule, @webmvctest vs unit test validation, binding error first test order, domain invariant first test order, 처음 @valid 헷갈려요, 왜 controller test 부터인가요, validation basics order, what is binding error vs business rule

## 핵심 개념

초심자가 가장 자주 섞는 것은 "`수량이 잘못됐다`"라는 한 문장이다. 그런데 이 문장은 두 질문을 섞는다.

- `@Valid`와 바인딩 에러: 요청 JSON, path variable, DTO 제약이 읽히는가?
- 도메인 규칙: 읽힌 뒤에도 주문 상태와 재고 규칙이 허용되는가?

짧게 외우면 `읽기 실패는 controller`, `의미 실패는 domain`이다. 다만 이 비유는 시작점일 뿐이다. 실제 구현에서는 service가 도메인 규칙을 호출해 막을 수도 있으니, "domain"은 보통 `Service/Entity/Aggregate` 쪽 최종 보호선을 뜻한다.

## 한눈에 보기

| 주문 생성 장면 | 실패 이유 | 먼저 확인할 테스트 | 보통 응답/결과 |
|---|---|---|---|
| `quantity`가 `null`인데 `@NotNull`이 있다 | validation annotation 실패 | `@WebMvcTest` | `400 Bad Request` |
| `orderId=abc`처럼 숫자 변환이 안 된다 | binding/conversion 실패 | `@WebMvcTest` | `400 Bad Request` |
| `quantity=5`지만 재고가 3개뿐이다 | 도메인 규칙 실패 | 단위 테스트 | 예외 또는 실패 결과 |
| 주문 상태가 `CANCELLED`인데 다시 결제한다 | 도메인 불변식 실패 | 단위 테스트 | 예외 또는 상태 전이 거부 |

- `400`이 난다고 모두 같은 층이 아니다.
- 보통 Spring MVC 기준으로 바인딩/validation은 controller 진입 전후에서 드러나고, 도메인 규칙은 service/domain 로직을 태울 때 드러난다.

## 첫 failing test 예시

같은 주문 예시를 테스트 시작점으로 자르면 아래처럼 정리된다.

| 질문 | starter test | 왜 이 테스트가 가장 싼가 |
|---|---|---|
| "`quantity` 누락이면 `400`이 나나?" | `@WebMvcTest` | 요청 본문, `@Valid`, 상태 코드만 빠르게 본다 |
| "`orderId`가 문자면 controller 전에 막히나?" | `@WebMvcTest` | conversion/binding 경계만 검증하면 된다 |
| "재고 부족이면 주문 생성이 거절되나?" | service/domain 단위 테스트 | HTTP 없이 규칙만 바로 검증한다 |
| "취소 주문은 다시 결제 불가인가?" | entity 또는 service 단위 테스트 | 상태 전이 규칙을 가장 직접적으로 잠근다 |

예시는 이렇게 나눠 읽으면 된다.

```java
// @WebMvcTest starter: quantity 누락 -> 400
mockMvc.perform(post("/orders")
        .contentType(APPLICATION_JSON)
        .content("{\"productId\":1}"))
    .andExpect(status().isBadRequest());

// Unit starter: 재고 부족 -> 예외
assertThatThrownBy(() -> orderService.place(1L, 5))
    .isInstanceOf(OutOfStockException.class);
```

핵심은 `같은 주문 생성 기능`이어도 질문이 다르면 첫 테스트가 달라진다는 점이다.

## 흔한 오해와 함정

- "`@Valid`가 있으니 재고 부족도 막겠죠?"  
  아니다. `@Valid`는 보통 DTO 형식과 기본 제약을 본다. 현재 재고 조회나 상태 전이는 도메인 규칙이다.
- "`400`이니까 전부 controller 문제 아닌가요?"  
  아니다. 팀이 도메인 예외를 `400`이나 `409`로 번역할 수도 있다. 중요한 것은 HTTP 숫자보다 실패 원인이 형식인지 의미인지다.
- "controller에서도 재고를 한번 보면 더 안전한가요?"  
  빠른 메시지용 중복 검사는 할 수 있지만, 최종 규칙은 다른 진입점에서도 지켜야 하므로 service/domain 안쪽에 남겨야 한다.

## 실무에서 쓰는 모습

리뷰에서 "`quantity`가 비면 `400` 내려 주세요"와 "`재고 없으면 주문 막아 주세요`"가 같이 오면, 한 테스트로 뭉치지 않는 편이 좋다.

1. `@WebMvcTest`로 `quantity` 누락 `400`을 먼저 고정한다.
2. 단위 테스트로 `재고 부족` 예외를 고정한다.
3. 마지막에 필요하면 예외 번역용 통합 테스트를 얇게 추가한다.

이 순서를 쓰면 `요청 계약`과 `업무 규칙`이 섞이지 않는다. 특히 "왜 첫 테스트가 `MockMvc`예요?" 또는 "왜 이번에는 unit test예요?" 같은 질문에 답이 선명해진다.

## 더 깊이 가려면

- [Validation Boundary Mini Bridge](./validation-boundary-input-vs-domain-invariant-mini-bridge.md): 입력 검증과 도메인 불변식 경계를 먼저 더 짧게 잡고 싶을 때
- [Controller 계약 변경 vs Service 규칙 변경 첫 failing test 미니 카드](./controller-contract-vs-service-rule-first-test-mini-card.md): `HTTP 계약 변경`과 `비즈니스 규칙 변경` 전체 선택표로 넓히고 싶을 때
- [Spring Validation and Binding Error Pipeline](../spring/spring-validation-binding-error-pipeline.md): `@Valid`, binding error, conversion failure 순서를 Spring MVC 기준으로 따라가고 싶을 때
- [Service 계층 기초](./service-layer-basics.md): 왜 재고 부족이나 상태 전이가 service/domain 질문인지 구조 관점에서 다시 보고 싶을 때

## 한 줄 정리

주문 예시에서 `@Valid`와 바인딩 에러는 "`요청이 읽히는가`"라서 `@WebMvcTest`부터, 재고 부족과 상태 전이는 "`읽힌 요청이 허용되는가`"라서 단위 테스트부터 시작하면 덜 헷갈린다.
