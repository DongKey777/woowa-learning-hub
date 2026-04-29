# Controller 계약 변경 vs Service 규칙 변경 첫 failing test 미니 카드

> 한 줄 요약: 같은 주문 생성 예시라도 `HTTP 계약이 바뀐 것`인지 `비즈니스 규칙이 바뀐 것`인지 먼저 나누면, 첫 failing test를 `@WebMvcTest`와 단위 테스트 중 어디에 둘지 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [테스트 전략 기초](./test-strategy-basics.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [주문 예시로 보는 `@Valid`/바인딩 에러 vs 도메인 규칙 첫 테스트 카드](./order-validation-annotation-vs-domain-rule-card.md)
- [리팩토링과 첫 failing test 연결 브리지](./refactoring-first-failing-test-bridge.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: controller contract vs service rule, http contract change first failing test, business rule change first test, 주문 예시 http 계약 변경, 주문 예시 비즈니스 규칙 변경, controller service 테스트 뭐부터, webmvctest vs unit test basics, 처음 테스트 뭐부터 헷갈려요, controller contract beginner, service rule beginner, request dto response dto contract, what is http contract change

## 핵심 개념

처음 막히는 지점은 "`Controller`에서 바뀐 것처럼 보이는데 왜 단위 테스트라고 하지?" 혹은 "`Service`를 건드렸는데 왜 `@WebMvcTest`라고 하지?"다. 이때 클래스 이름보다 먼저 봐야 하는 것은 **바뀐 질문의 종류**다.

- `HTTP 계약 변경`은 요청/응답의 모양, 상태 코드, 검증 에러 포맷이 바뀌는 경우다.
- `비즈니스 규칙 변경`은 주문 가능 여부, 할인, 재고 부족 같은 업무 판단이 바뀌는 경우다.

짧게 외우면 `모양이 바뀌면 웹 계약 테스트`, `판단이 바뀌면 규칙 테스트`다.

## 한눈에 보기

| 같은 주문 생성 변경 | 먼저 붙일 이름 | 첫 failing test | 왜 여기부터 보나 |
|---|---|---|---|
| `POST /orders`가 이제 `quantity` 누락 시 `400`과 에러 JSON을 내려야 한다 | HTTP 계약 변경 | `@WebMvcTest` | 요청 바인딩, `@Valid`, 상태 코드, 에러 응답 모양을 가장 싸게 검증한다 |
| `quantity` 필드 이름이 `amount`로 바뀌었다 | HTTP 계약 변경 | `@WebMvcTest` | 클라이언트가 보내는 JSON 계약이 달라졌는지 본다 |
| 재고가 부족하면 주문을 막는 규칙이 추가됐다 | 비즈니스 규칙 변경 | 단위 테스트 | 업무 판단이 맞는지만 빠르게 잠근다 |
| VIP는 한 번에 최대 10개까지만 주문 가능해졌다 | 비즈니스 규칙 변경 | 단위 테스트 | HTTP 모양은 그대로이고 판단만 바뀌었다 |

- 첫 질문이 `클라이언트와 약속한 모양`이면 `@WebMvcTest`가 starter다.
- 첫 질문이 `주문을 허용할지 말지`면 단위 테스트가 starter다.

## 같은 주문 예시를 두 갈래로 자르기

같은 `POST /orders`라도 아래처럼 갈라서 보면 초심자가 가장 덜 헷갈린다.

| 장면 | 바뀐 내용 | 바뀌지 않은 것 | 먼저 실패시킬 테스트 |
|---|---|---|---|
| 계약 변경 pass | `quantity`가 없으면 `400`, 응답 본문에 `errorCode`를 넣는다 | 재고 부족 판단, 할인 계산 | `@WebMvcTest` |
| 규칙 변경 pass | 재고가 3개인데 5개 주문하면 실패한다 | 요청 JSON 이름, 응답 상태 코드 형식 | 단위 테스트 |

여기서 중요한 점은 "`Controller` 파일을 고쳤는가"가 아니다. **클라이언트 계약을 고쳤는지, 업무 판단을 고쳤는지**가 first-test 선택 기준이다.

## 처음 고를 때 쓰는 3문항

아래 3문항 중 먼저 `Yes`가 되는 곳이 starter다.

| 질문 | Yes면 | No면 |
|---|---|---|
| 요청 JSON 필드, 응답 JSON 모양, 상태 코드가 바뀌었나 | `@WebMvcTest`부터 | 2번으로 |
| 주문 가능/불가 판단, 계산식, 상태 전이가 바뀌었나 | 단위 테스트부터 | 3번으로 |
| 저장 순서, 롤백, 여러 빈 협력이 같이 바뀌었나 | `@SpringBootTest` follow-up 검토 | 더 싼 테스트 1개부터 다시 고른다 |

- `HTTP 계약`과 `비즈니스 규칙`이 동시에 바뀌면, 보통 더 작은 변경부터 두 pass로 나누는 편이 안전하다.
- 한 번에 못 나누겠으면 "클라이언트가 먼저 깨지나, 업무 판단이 먼저 깨지나"를 묻는다.

## 흔한 오해와 함정

- "`@Valid`가 있으니 수량 0 검사도 다 Controller 테스트 아닌가요?"
  - `null`, 형식 오류, 누락처럼 HTTP 입력 형식에 가까우면 Controller 쪽이다. 재고 부족, 최대 주문 수량처럼 업무 의미가 있으면 Service/Domain 쪽이다.
  - `@Valid`/binding error와 도메인 규칙을 주문 예시 한 장으로 다시 자르고 싶으면 [주문 예시로 보는 `@Valid`/바인딩 에러 vs 도메인 규칙 첫 테스트 카드](./order-validation-annotation-vs-domain-rule-card.md)를 바로 이어 읽으면 된다.
- "Service 메서드를 고쳤으니 무조건 통합 테스트 아닌가요?"
  - 규칙만 바뀌었다면 단위 테스트가 더 싸고 실패 이유도 선명하다.
- "에러 메시지가 바뀌었는데 규칙 테스트만 고치면 되죠?"
  - 응답 본문의 필드 구조나 상태 코드까지 바뀌면 그건 HTTP 계약 변경도 섞인 것이다.

## 실무에서 쓰는 모습

주문 생성 리뷰에서 아래 두 요청이 따로 들어왔다고 해 보자.

1. `quantity` 누락 시 `400`과 `{ "errorCode": "INVALID_QUANTITY" }`를 내려 주세요.
2. 재고가 부족하면 주문을 막아 주세요.

이때 beginner-safe 순서는 이렇다.

| 순서 | 먼저 실패시킬 것 | 이유 |
|---|---|---|
| 1 | `quantity` 누락 시 `400`을 검증하는 `@WebMvcTest` | 클라이언트 계약 변경을 먼저 고정한다 |
| 2 | `재고 부족이면 예외` 단위 테스트 | 업무 판단 변경을 빠르게 고정한다 |
| 3 | 둘을 한 PR에 같이 넣어야 한다면 테스트도 둘로 나눈다 | 실패 이유가 섞이지 않게 한다 |

즉 같은 주문 예시라도 `400 계약`과 `재고 부족 규칙`은 같은 질문이 아니다. 테스트도 같은 곳에서 시작하지 않는다.

## 더 깊이 가려면

- [테스트 전략 기초](./test-strategy-basics.md): `규칙 / 웹 계약 / JPA / 협력 흐름` 전체 선택표로 넓히고 싶을 때
- [계층형 아키텍처 기초](./layered-architecture-basics.md): 같은 주문 예시로 Controller와 Service 자리를 다시 보고 싶을 때
- [Service 계층 기초](./service-layer-basics.md): 규칙 변경이 왜 Service/Domain 쪽 질문인지 더 분명히 보고 싶을 때
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md): `@WebMvcTest`와 `@SpringBootTest` 차이를 Spring 관점에서 이어 볼 때

## 한 줄 정리

같은 주문 생성 코드라도 `HTTP 모양이 바뀌면 @WebMvcTest`, `업무 판단이 바뀌면 단위 테스트`부터 시작하면 첫 failing test를 훨씬 덜 헷갈린다.
