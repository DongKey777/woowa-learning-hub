# 테스트 전략 기초 (Test Strategy Basics)

> 한 줄 요약: 테스트는 단위/통합/E2E로 범위가 나뉘고, 비용과 신뢰도의 트레이드오프를 이해하면 어느 계층에 어떤 테스트를 얼마나 쓸지 판단할 수 있다.

**난이도: 🟢 Beginner**

[30분 후속 분기표로 돌아가기](./common-confusion-wayfinding-notes.md#자주-헷갈리는-3개-케이스)

관련 문서:

- [Service 계층 기초](./service-layer-basics.md)
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [design-pattern 카테고리 인덱스](../design-pattern/README.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: test strategy basics, 첫 테스트 선택표, webmvctest 최소 예시, datajpatest 최소 예시, 401 403 혼동, mockmvc csrf test, withmockuser webmvctest, csrf 때문에 403, 권한 때문에 403, addfilters false, 테스트 전용 보안 설정, security focused test, datajpatest flush clear, 서비스 읽고 테스트 전략, beginner testing

## 먼저 잡는 한 줄 멘탈 모델

테스트 전략의 출발점은 "많이 쓰기"가 아니라, **"이번 변경에서 가장 먼저 깨질 1개를 가장 싼 테스트로 고정"**하는 것이다.

## Service 문서에서 넘어왔다면 먼저 이렇게 본다

[Service 계층 기초](./service-layer-basics.md)를 읽고 왔다면, 용어를 더 늘리기보다 **"바뀐 Service 책임이 규칙 쪽인지, 협력 흐름 쪽인지"**만 먼저 고르면 된다.

| Service에서 바뀐 것 | 여기서 먼저 볼 행 | 첫 테스트 |
|---|---|---|
| 계산, 검증, 상태 전이 같은 규칙 | `계산식/검증 로직 변경` | 단위 테스트 |
| 저장 순서, 롤백, 여러 컴포넌트 연결 | `트랜잭션 경계/여러 컴포넌트 협력 흐름 변경` | `@SpringBootTest` 통합 테스트 |
| Controller 요청 검증까지 같이 수정 | `Controller 입력 검증/응답 포맷 변경` | `@WebMvcTest` |

- 한 줄 연결: `Service 책임을 읽었다 -> 바뀐 책임 종류를 고른다 -> 아래 첫 테스트 선택표의 같은 행으로 내려간다.`

## 30초 자가진단 카드 (5문항 Yes/No)

아래 5문항은 아래쪽 `첫 테스트 선택표`의 앞 5개 행과 **같은 이름**으로 맞춘 빠른 체크리스트다. 질문에서 고른 문구를 그대로 표에서 다시 찾으면 된다.

| 질문 (Yes/No) | Yes면 | No면 |
|---|---|---|
| 1. 계산식/검증 로직 변경인가? | 단위 테스트부터 시작 | 2번 질문으로 |
| 2. Controller 입력 검증/응답 포맷 변경인가? | `@WebMvcTest`부터 시작 | 3번 질문으로 |
| 3. 보안 규칙 자체가 변경인가? | security-focused 테스트부터 시작 | 4번 질문으로 |
| 4. JPA 쿼리/매핑/인덱스 관련 변경인가? | `@DataJpaTest`부터 시작 | 5번 질문으로 |
| 5. 트랜잭션 경계/여러 컴포넌트 협력 흐름 변경인가? | `@SpringBootTest` 통합 테스트 1개부터 | 단위 테스트 1개를 먼저 쓰고 필요 시 올린다 |

- 판단이 겹치면: **더 싼 테스트(단위/슬라이스) 1개를 먼저 잠그고** 다음 레벨 테스트를 추가한다.
- 예: "외부 API 재시도 정책 변경"은 보통 단위 테스트(분기 규칙) + 통합 테스트 1개(wiring) 조합이 가장 안전하다.

## 체크리스트 문구와 선택표 행 라벨 매핑

초심자 기준으로는 "질문에서는 HTTP라고 했는데, 표에서는 Controller라고 쓰네?" 같은 용어 차이만으로도 멈추기 쉽다. 이 문서에서는 아래 5개를 **같은 뜻의 같은 라벨**로 고정한다.

| 체크리스트 질문 번호 | 선택표에서 다시 찾을 행 라벨 | 첫 테스트 |
|---|---|---|
| 1번 | 계산식/검증 로직 변경 | 단위 테스트 |
| 2번 | Controller 입력 검증/응답 포맷 변경 | 슬라이스 테스트 (`@WebMvcTest`) |
| 3번 | 보안 규칙 자체가 변경 | security-focused 테스트 |
| 4번 | JPA 쿼리/매핑/인덱스 관련 변경 | 슬라이스 테스트 (`@DataJpaTest`) |
| 5번 | 트랜잭션 경계/여러 컴포넌트 협력 흐름 변경 | 통합 테스트 (`@SpringBootTest`) |

- `외부 API 연동 분기/재시도 정책 변경`은 위 4개 중 하나로 완전히 줄어들지 않는 **조합형 예외**다.
- 그래서 이 경우는 체크리스트에서 억지로 한 칸만 고르기보다, `분기 규칙은 단위 테스트` + `실제 연결은 통합 테스트 1개`로 읽으면 된다.

## 체크리스트 분기별 "잘못 고른 첫 테스트" 반례

초심자가 가장 자주 막히는 지점은 "틀린 테스트도 테스트니까 괜찮겠지"라는 감각이다. 아래 표는 **첫 삽을 잘못 뜬 짧은 반례 1개씩**만 붙여, 왜 더 싼 테스트부터 시작해야 하는지 바로 보이게 만든 것이다.

| 체크리스트 분기 | 추천 시작 | 잘못 고른 첫 테스트 반례 | 왜 잘못 고른 시작인가 |
|---|---|---|---|
| 계산식/검증 로직 변경 | 단위 테스트 | 할인율 계산만 바꿨는데 `@SpringBootTest`로 주문 생성 전체 플로우부터 띄운다. | 규칙 버그를 잡기 전에 DB, 빈 설정, 보안 같은 주변 요인에 먼저 막혀서 핵심 실패가 흐려진다. |
| Controller 입력 검증/응답 포맷 변경 | `@WebMvcTest` | 요청 JSON 필드 이름이 바뀌었는데 Service 단위 테스트만 써서 `createOrder()` 호출 여부만 본다. | HTTP 요청 바인딩, `@Valid`, 에러 응답 포맷은 Service 테스트로는 보이지 않는다. |
| JPA 쿼리/매핑/인덱스 관련 변경 | `@DataJpaTest` | 정렬 쿼리를 바꿨는데 Repository를 Mock 처리한 Service 테스트로 결과 리스트만 꾸며서 확인한다. | 실제 SQL, 정렬, 매핑 문제를 건드리지 못해서 쿼리가 틀려도 테스트가 초록으로 남는다. |
| 트랜잭션 경계/여러 컴포넌트 협력 흐름 변경 | `@SpringBootTest` | 주문 저장과 재고 차감을 한 트랜잭션으로 묶었는데 도메인 객체 단위 테스트만 추가한다. | 롤백, 트랜잭션 전파, 여러 빈 협력은 단위 테스트에서 재현되지 않아 "붙였을 때 깨지는" 버그를 놓친다. |

- 빠른 self-check: 테스트가 실패해도 "그래서 실제 변경이 틀렸는지" 바로 답이 안 나오면, 첫 테스트가 너무 넓거나 너무 좁은 경우가 많다.
- 추천 분기보다 비싼 테스트를 먼저 썼다면, 그 테스트를 지우기보다 **더 싼 테스트 1개를 앞에 추가**해서 실패 원인을 먼저 잠그는 편이 안전하다.

## before / after 한눈 비교

| 상태 | 코드 신호 | 결과 |
|---|---|---|
| before: 테스트 종류가 뒤섞임 | 작은 계산 변경에도 `@SpringBootTest`부터 작성 | 피드백이 느려지고 리팩터링 비용이 커진다 |
| after: 질문별 테스트 분리 | 규칙은 단위, 레이어 계약은 슬라이스, 핵심 경로만 통합/E2E로 검증 | 실패 원인 파악이 빨라지고 테스트 유지비가 낮아진다 |

## 핵심 개념

테스트는 코드가 의도대로 동작하는지 자동으로 확인하는 수단이다. 범위에 따라 세 단계로 나뉜다.

- **단위 테스트(Unit Test)** — 하나의 클래스나 메서드를 격리해서 검증한다. 빠르고 저렴하다.
- **통합 테스트(Integration Test)** — 여러 컴포넌트(DB, 서비스, 레포지토리)를 묶어서 검증한다. 느리지만 실제 협력을 확인한다.
- **E2E 테스트** — 실제 HTTP 요청을 보내 전체 흐름을 검증한다. 가장 느리고 비용이 크다.

입문자가 헷갈리는 포인트는 "외부 의존을 어떻게 처리하느냐"다. 단위 테스트에서는 실제 DB 대신 가짜 객체(Mock/Stub)를 쓰는 경우가 많다.

## 한눈에 보기

```
E2E         ▲ 적게
Integration ▌▌
Unit        ▌▌▌▌▌ 많이
```

| 종류 | 속도 | 신뢰도 | 권장 비율 |
|---|---|---|---|
| 단위 테스트 | 빠름 | 격리된 로직 검증 | 많이 |
| 통합 테스트 | 보통 | 협력 검증 | 적당히 |
| E2E 테스트 | 느림 | 전체 흐름 검증 | 소수 |

## 첫 테스트 선택표 (변경 1건 기준)

처음부터 완벽한 커버리지를 만들려 하지 말고, **"이번 변경에서 가장 먼저 깨질 만한 것 1개"**를 고르는 게 시작점이다.

| 이번 변경 | 첫 테스트로 시작할 것 | 이유 |
|---|---|---|
| 계산식/검증 로직 변경 (할인, 포인트, 상태 전이) | 단위 테스트 | 외부 의존 없이 규칙 자체를 가장 빠르게 검증할 수 있다. |
| Controller 입력 검증/응답 포맷 변경 | 슬라이스 테스트 (`@WebMvcTest`) | 웹 계층 계약(요청/응답/검증)을 DB 없이 확인할 수 있다. |
| 보안 규칙 자체 변경 (`401/403`, role, CSRF, filter chain) | security-focused 테스트 | MVC 계약과 보안 규칙을 분리해서, `401/403`이 보안 회귀인지 controller 계약 문제인지 더 빨리 가를 수 있다. |
| JPA 쿼리/매핑/인덱스 관련 변경 | 슬라이스 테스트 (`@DataJpaTest`) | 실제 영속 계층 동작을 좁은 범위로 검증할 수 있다. |
| 트랜잭션 경계/여러 컴포넌트 협력 흐름 변경 | 통합 테스트 (`@SpringBootTest`) | "붙였을 때" 깨지는 협력 문제를 조기에 잡는다. |
| 외부 API 연동 분기/재시도 정책 변경 | 단위 테스트 + 통합 테스트 1개 | 분기 로직은 단위로 빠르게, 실제 wiring은 통합으로 최소 확인한다. |

## 변경 유형 매핑 사례 3개 (before / after)

아래 3개는 실제 미션에서 자주 나오는 변경을, 위 선택표의 행과 1:1로 연결한 짧은 예시다.

| 변경 유형 (선택표 연결) | before: 자주 하는 시작 | after: 추천 시작 |
|---|---|---|
| 입력 검증 추가 (`Controller 입력 검증/응답 포맷 변경`) | `@SpringBootTest`로 주문 생성 전체 흐름을 띄운 뒤 `quantity=0`만 확인 | `@WebMvcTest`에서 `POST /orders`에 잘못된 JSON를 보내 `400`과 에러 필드만 고정 |
| JPA 쿼리 수정 (`JPA 쿼리/매핑/인덱스 관련 변경`) | 서비스 테스트에서 Mock Repository 반환값만 바꿔 쿼리 수정을 검증했다고 판단 | `@DataJpaTest`에서 테스트 데이터 저장 후 새 쿼리(`findRecentPaidOrders`) 결과 순서/건수를 확인 |
| 외부 API 재시도 정책 (`외부 API 연동 분기/재시도 정책 변경`) | 통합 테스트만 1개 두고 "2번 재시도 후 중단" 같은 분기 규칙을 코드 리뷰에 의존 | 단위 테스트로 retry 분기(예: `TIMEOUT`은 2회, `4xx`는 즉시 중단)를 먼저 고정하고, 통합 테스트 1개로 client wiring 확인 |

### 사례에서 바로 쓰는 30초 체크

- 입력 검증 변경인데 DB 준비 코드가 먼저 필요하면 시작 테스트가 과한 것이다.
- 쿼리 수정인데 Mock만으로 통과하면 실제 SQL/JPA 동작은 아직 검증되지 않은 상태다.
- 재시도 정책 변경인데 "어떤 예외를 몇 번 재시도하는지"가 단위 테스트 이름으로 안 보이면 분기 규칙이 잠겨 있지 않다.

## 외부 API 재시도 테스트는 이름이 정책 카드가 되어야 한다

멘탈 모델은 간단하다. **재시도 테스트 이름은 "정책 설명 한 줄"이어야 한다.**

즉 테스트 본문을 열기 전에, 이름만 보고도 "어떤 실패를 몇 번 재시도하고 언제 멈추는지"가 보여야 한다.

### Given-When-Then으로 바로 읽는 최소 규칙

| 구간 | 이름에 넣을 질문 | retry 정책 예시 |
|---|---|---|
| `Given` | 어떤 실패 조건인가? | `첫_호출이_TIMEOUT이면`, `응답이_400이면` |
| `When` | 어떤 요청을 보냈는가? | `결제를_요청하면`, `주문_동기화를_시도하면` |
| `Then` | 몇 번 재시도하고 어떻게 끝나는가? | `2번_재시도_후_성공한다`, `재시도하지_않고_실패를_반환한다` |

- `Given`에는 정책 분기를 가르는 실패 종류를 넣는다.
- `Then`에는 "성공/중단"만 쓰지 말고, **횟수나 중단 조건**까지 같이 적는다.
- 팀이 한글 메서드명을 쓰지 않아도 구조는 같다. 중요한 것은 Given-When-Then의 정보량이다.

### 바로 복붙할 수 있는 네이밍 예시

| 정책 | 이름이 약한 예 | 이름만 봐도 정책이 보이는 예 |
|---|---|---|
| timeout은 재시도 | `재시도한다` | `given_TIMEOUT이_1번_발생하면_when_결제를_요청하면_then_2번까지_재시도하고_성공한다` |
| 4xx는 즉시 중단 | `실패한다` | `given_400_BAD_REQUEST이면_when_결제를_요청하면_then_재시도하지_않고_실패를_반환한다` |
| 5xx는 최대 횟수 후 중단 | `최대_시도_후_중단한다` | `given_500_SERVER_ERROR가_계속되면_when_결제를_요청하면_then_총_3회_시도_후_중단한다` |

영문 스타일을 쓰는 팀이면 같은 내용을 아래처럼 적어도 된다.

```java
givenTimeoutOnFirstCall_whenChargeRequested_thenRetriesUpTo2TimesAndSucceeds()
givenBadRequest400_whenChargeRequested_thenDoesNotRetryAndReturnsFailure()
givenServerErrorContinues_whenChargeRequested_thenStopsAfterTotal3Attempts()
```

### 처음에 자주 헷갈리는 네이밍 포인트

- `2번 재시도`와 `총 3회 시도`는 다른 말이다. 팀에서 어느 표현을 기본으로 쓸지 먼저 정하고 이름에 일관되게 넣는다.
- `retryTemplate.execute`처럼 구현 도구 이름을 테스트 이름에 넣기보다, `TIMEOUT이면 2번 재시도`처럼 정책 문장을 넣는 편이 초심자에게 훨씬 잘 읽힌다.
- `예외가 나면 실패한다`는 이름은 너무 넓다. `TIMEOUT`, `429`, `5xx`처럼 분기 기준을 드러내야 리뷰 때 정책 누락을 빨리 찾는다.

## 외부 API 재시도 테스트는 이름이 정책 카드가 되어야 한다 (계속 2)

- retry 안전성 자체를 더 넓게 보려면 [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)에서 "언제 재시도가 위험해지는지"를 이어서 보면 된다.

## 실패 먼저 재현 -> 최소 테스트 1개 미니 시나리오

처음 테스트를 붙일 때는 "정답을 많이 쓰는 것"보다 **"지금 버그를 한 줄로 다시 깨지게 만들고, 그 장면만 잠그는 것"**이 더 중요하다.

| 변경 유형 | 실패 먼저 재현 | 최소 테스트 1개 |
|---|---|---|
| Controller 입력 검증 변경 | `POST /orders`에 `quantity=0`을 보내 봤더니 `201`이 나와서 잘못된 요청이 통과한다. | `@WebMvcTest` 1개로 `400`과 `quantity` 에러 필드만 고정한다. |
| JPA 쿼리 정렬 변경 | 최근 결제 주문이 먼저 보여야 하는데 `findRecentPaidOrders()`가 오래된 주문부터 반환한다. | `@DataJpaTest` 1개로 테스트 데이터를 2건 저장하고 결과 순서만 검증한다. |

## 시나리오 A. 입력 검증 변경

멘탈 모델은 단순하다. **HTTP 계약이 틀렸으면, 서버 전체를 띄우기 전에 요청 1개로 바로 실패를 다시 만든다.**

1. 실패 먼저 재현: `quantity=0` 요청을 보내 봤더니 `201 Created`가 내려온다.
2. 최소 테스트 1개: `@WebMvcTest`로 `400 Bad Request`와 `quantity` 필드 오류만 검증한다.
3. 그다음 수정: `@Valid`, `@Min(1)`, 에러 응답 포맷 중 실제 원인만 고친다.

```java
@WebMvcTest(OrderController.class)
@AutoConfigureMockMvc(addFilters = false)
class OrderControllerValidationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void 수량이_0이면_400과_quantity_필드_오류를_반환한다() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"menuId": 1, "quantity": 0}
                    """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.errors[0].field").value("quantity"));
    }
}
```

- 초심자 기준 첫 복붙은 `status + field`까지만 잠가도 충분하다.
- 에러 메시지까지 함께 고정하고 싶으면 아래 응답 예시와 assertion 1줄을 그대로 붙이면 된다.

## 복붙용 검증 실패 응답 예시

예를 들어 `@Min(1)`의 메시지를 `"수량은 1 이상이어야 합니다."`로 맞췄다면, 실패 응답은 보통 아래처럼 읽힌다.

```json
{
  "errors": [
    {
      "field": "quantity",
      "message": "수량은 1 이상이어야 합니다."
    }
  ]
}
```

이때 테스트는 `field`와 `message`를 바로 연결해서 읽으면 된다.

```java
mockMvc.perform(post("/orders")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
            {"menuId": 1, "quantity": 0}
            """))
    .andExpect(status().isBadRequest())
    .andExpect(jsonPath("$.errors[0].field").value("quantity"))
    .andExpect(jsonPath("$.errors[0].message").value("수량은 1 이상이어야 합니다."));
```

| 지금 고정할 것 | 추천 | 이유 |
|---|---|---|
| 필드 이름만 먼저 확인 | `$.errors[0].field` | 검증 실패가 어느 입력에서 났는지 가장 빨리 보인다. |
| 사용자에게 보여 줄 문구도 중요 | `$.errors[0].message` 추가 | 에러 응답 포맷과 메시지 회귀를 같이 막을 수 있다. |

- 실제 JSON 경로는 프로젝트 응답 포맷에 따라 `$.fieldErrors[0].field`처럼 다를 수 있다.
- 메시지는 기본 Bean Validation 문구를 그대로 쓰는 팀도 있으니, 문서 예시는 "field + message를 같이 잠그는 패턴"으로 이해하면 된다.

- 이 장면에서 DB 준비 코드가 먼저 필요하면 테스트 범위가 이미 커진 것이다.
- `401/403`이 먼저 나오면 검증 실패를 못 본 상태일 수 있으니 아래 `@WebMvcTest` 보안 섹션으로 바로 내려가면 된다.

## 시나리오 B. JPA 쿼리 정렬 변경

멘탈 모델은 이것이다. **쿼리가 틀렸으면 Mock 반환값이 아니라, 저장 후 조회 결과 순서로 실패를 다시 만든다.**

1. 실패 먼저 재현: 최근 주문이 먼저 보여야 하는데 정렬이 뒤집혀 오래된 주문이 앞에 나온다.
2. 최소 테스트 1개: `@DataJpaTest`에서 결제 완료 주문 2건을 저장하고 첫 번째 ID만 검증한다.
3. 그다음 수정: `ORDER BY`, 메서드 이름 파생 쿼리, 정렬 필드 매핑 중 실제 원인만 고친다.

```java
@DataJpaTest
class OrderRepositoryDataJpaTest {

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void 최근_결제_주문이_먼저_조회된다() {
        OrderEntity older = orderRepository.save(new OrderEntity("ORD-001", PAID, LocalDateTime.of(2026, 4, 20, 10, 0)));
        OrderEntity newer = orderRepository.save(new OrderEntity("ORD-002", PAID, LocalDateTime.of(2026, 4, 21, 10, 0)));

        List<OrderEntity> result = orderRepository.findRecentPaidOrders();

        assertThat(result.get(0).getId()).isEqualTo(newer.getId());
        assertThat(result.get(1).getId()).isEqualTo(older.getId());
    }
}
```

- 서비스 테스트에서 Mock Repository 결과만 바꾸면 정렬 SQL/JPA 문제는 아직 재현되지 않는다.
- H2와 운영 DB 차이가 의심되면, 여기서 더 파고들기보다 [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)를 먼저 보면 된다.

## `@DataJpaTest`에서 언제 `flush()`/`clear()`로 한 단계 올리나

초심자 기준 멘탈 모델은 간단하다. **`save()` 후 바로 검증해도 충분한 질문인지, 아니면 "진짜 DB에 반영된 뒤 다시 읽은 값"을 봐야 하는지**를 먼저 고르면 된다.

| 지금 확인하려는 것 | plain `@DataJpaTest`로 시작 | `flush()`/`clear()`까지 올릴 때 |
|---|---|---|
| 단건 저장, 기본 매핑, 파생 쿼리 조회 | 저장 후 바로 `findBy...`나 `count()`를 본다 | 보통 아직 필요 없다 |
| unique/FK/not null 같은 제약 조건이 언제 터지는지 | save만으로는 시점이 흐릴 수 있다 | `flush()`로 SQL을 당겨 본다 |
| bulk update 뒤 상태가 정말 바뀌었는지 | 같은 영속성 컨텍스트 착시가 남을 수 있다 | `clear()` 후 다시 조회한다 |
| 여러 건 저장 batch에서 "메모리 속 값"이 아니라 DB 재조회 결과를 말하고 싶은지 | count만 보면 초록인데도 질문이 남을 수 있다 | `flush()` 후 `clear()` 뒤 assertion 한다 |

- 한 줄 규칙: **저장 후 바로 읽는 테스트가 "같은 트랜잭션 안의 메모리 상태"를 보는지 헷갈리면 `flush()`/`clear()`를 붙인다.**
- `flush()`는 "SQL을 실제로 보내 보자", `clear()`는 "방금 들고 있던 엔티티를 내려놓고 다시 읽자"에 가깝다.
- batch insert, bulk update, stale state 착시를 더 짧게 복습하고 싶다면 [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)로 이어 가면 된다.

## 슬라이스 테스트 최소 템플릿 (복붙 시작점)

처음에는 "웹 계층 계약 확인"과 "JPA 매핑/쿼리 확인"을 분리해서 시작하면 된다.

| 목적 | 먼저 쓰는 어노테이션 | 기본 아이디어 |
|---|---|---|
| 요청/응답/검증 규칙 확인 | `@WebMvcTest` | 컨트롤러만 띄우고, 서비스는 mock으로 대체 |
| 리포지토리 쿼리/매핑 확인 | `@DataJpaTest` | JPA 관련 빈만 띄우고, 저장 후 조회 검증 |

## `@WebMvcTest` 최소 템플릿

```java
@WebMvcTest(OrderController.class)
class OrderControllerWebMvcTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PlaceOrderUseCase placeOrderUseCase;

    @Test
    void 주문_생성_요청시_201을_반환한다() throws Exception {
        given(placeOrderUseCase.place(any())).willReturn(new OrderId(1L));

        mockMvc.perform(post("/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"menuId": 1, "quantity": 2}
                    """))
            .andExpect(status().isCreated());
    }
}
```

## `@WebMvcTest`에서 `401`/`403`이 먼저 나올 때

처음에는 "컨트롤러 검증을 보려는데 입구의 보안 필터가 먼저 막았다"라고 이해하면 된다.

즉 `@WebMvcTest`에서 보고 싶은 것이 **Controller의 입력 검증/응답 포맷**인지, 아니면 **보안 규칙 자체**인지 먼저 나누면 덜 헷갈린다.

- 이 구분은 위 `첫 테스트 선택표`의 `Controller 입력 검증/응답 포맷 변경` 행과 `보안 규칙 자체가 변경` 행을 가르는 기준과 같다.

| 지금 확인하고 싶은 것 | 더 단순한 시작 | 왜 이 선택이 쉬운가 |
|---|---|---|
| `@Valid`, JSON 바인딩, 에러 응답 포맷 | `@AutoConfigureMockMvc(addFilters = false)` | 보안 필터를 잠시 빼고 controller 계약만 본다. |
| 인증된 사용자는 통과하고 익명 사용자는 막히는지 | 테스트 전용 security 설정 또는 security 통합 테스트 | `401`/`403` 의미를 보안 규칙과 함께 읽을 수 있다. |

- `401 Unauthorized`: 보통 인증이 없거나 실패했다는 뜻이다.
- `403 Forbidden`: 인증은 되었지만 권한이 부족하다는 뜻이다.
- 다만 `POST`/`PUT`/`DELETE` 테스트에서는 인증이 있어도 `with(csrf())`가 빠지면 `403`이 날 수 있다.
- 초급 단계에서는 보안이 주제가 아니면 `401/403` 해석에 시간을 쓰기보다, 먼저 필터를 빼고 controller 계약을 잠그는 편이 빠르다.

## 인증 주체가 필요한 `@WebMvcTest`의 가장 작은 시작점

처음에는 `@WithMockUser`를 "진짜 로그인"이 아니라 **테스트 안에 가짜 로그인 사용자를 하나 꽂아 넣는 가장 작은 패턴**으로 이해하면 된다.

| 지금 필요한 것 | 가장 작은 시작 |
|---|---|
| 보안이 주제가 아니고 입력 검증만 보고 싶다 | `addFilters = false` |
| 로그인한 사용자가 있어야 controller까지 들어간다 | `@WithMockUser` |
| 특정 권한이 있어야 통과한다 | `@WithMockUser(roles = "...")` |

- `@WithMockUser`는 security context에 인증된 사용자를 넣어 준다.
- 그래서 controller가 "익명 사용자는 막고, 로그인 사용자는 통과" 정도만 요구할 때 가장 빨리 시작할 수 있다.
- 다만 JWT 파싱, custom principal 매핑, 실제 인증 필터 동작까지 증명하는 도구는 아니다.

```java
@WebMvcTest(OrderController.class)
class OrderControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PlaceOrderUseCase placeOrderUseCase;

    @Test
    @WithMockUser(username = "jun", roles = "USER")
    void 로그인_사용자는_POST_요청을_보낼_수_있다() throws Exception {
        given(placeOrderUseCase.place(any())).willReturn(new OrderId(1L));

        mockMvc.perform(post("/orders")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"menuId": 1, "quantity": 2}
                    """))
            .andExpect(status().isCreated());
    }
}
```

- 이 예시는 "로그인한 사용자 1명만 있으면 controller까지 들어갈 수 있는가"를 보는 최소 패턴이다.
- `POST`이므로 `@WithMockUser`만으로는 부족할 수 있고, 보통 `with(csrf())`도 같이 넣는다.
- `403`이 계속 나오면 `CSRF 누락인가`와 `role이 맞는가`를 순서대로 가르면 된다.

## `@WithMockUser`를 먼저 쓰면 좋은 경우와 아닌 경우

| 상황 | 시작점 |
|---|---|
| `@AuthenticationPrincipal`, `Principal`, `@PreAuthorize` 때문에 익명 요청이 바로 막힌다 | `@WithMockUser`부터 |
| controller 입력 검증이 목표인데 보안 규칙은 이번 변경 범위가 아니다 | `addFilters = false`부터 |
| JWT claim, custom user details, 실제 filter chain 설정이 핵심이다 | security 통합 테스트 또는 테스트 전용 설정 |

짧게 말해, `@WithMockUser`는 **"인증된 사용자 한 명이 필요하다"**를 가장 싸게 만족시키는 시작점이다.
반대로 "실제 인증이 어떻게 해석되는가"가 질문이면 더 큰 보안 테스트로 올라가야 한다.

## `403`이 CSRF 때문인지 권한 때문인지 빠르게 가르는 최소 패턴

처음에는 `403`을 보면 "권한 부족"으로만 읽기 쉽지만, 쓰기 요청에서는 **CSRF 토큰 누락**도 같은 `403`으로 보일 수 있다.

| 같은 `403`이어도 먼저 볼 것 | 빠른 확인 방법 | 해석 |
|---|---|---|
| `POST`/`PUT`/`DELETE`인데 `with(csrf())`가 없다 | 같은 요청에 `with(csrf())`만 추가해 본다 | `403 -> 2xx/4xx(다른 기대 응답)`로 바뀌면 CSRF 누락 가능성이 크다. |
| `with(csrf())`를 넣어도 계속 `403`이다 | 인증/권한 설정(`@WithMockUser`, role, security config)을 본다 | 이때는 권한 규칙 때문에 막혔을 가능성이 더 크다. |

```java
@Test
void 주문_생성은_csrf가_없으면_403이고_넣으면_201을_볼_수_있다() throws Exception {
    given(placeOrderUseCase.place(any())).willReturn(new OrderId(1L));

    mockMvc.perform(post("/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .content("""
                {"menuId": 1, "quantity": 2}
                """))
        .andExpect(status().isForbidden());

    mockMvc.perform(post("/orders")
            .with(csrf())
            .contentType(MediaType.APPLICATION_JSON)
            .content("""
                {"menuId": 1, "quantity": 2}
                """))
        .andExpect(status().isCreated());
}
```

- 초급자 기준 빠른 해석: `with(csrf())` 추가만으로 응답이 바뀌면 "권한"보다 "토큰 누락"을 먼저 의심하면 된다.
- `GET`은 보통 CSRF 대상이 아니어서, 같은 패턴이 특히 `POST`/`PUT`/`DELETE`에서 자주 보인다.

## 보안 필터 때문에 초점이 흐릴 때 쓰는 최소 패턴

```java
@WebMvcTest(OrderController.class)
@AutoConfigureMockMvc(addFilters = false)
class OrderControllerValidationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PlaceOrderUseCase placeOrderUseCase;

    @Test
    void 수량이_0이면_보안_응답보다_400_검증_실패를_먼저_본다() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"menuId": 1, "quantity": 0}
                    """))
            .andExpect(status().isBadRequest());
    }
}
```

- 이 패턴은 "보안을 무시하고 운영 코드를 바꾸자"는 뜻이 아니다.
- 목적은 초심자가 `401/403`에 막혀 controller 검증 테스트 자체를 못 쓰는 상황을 줄이는 것이다.
- 이후 보안 규칙이 요구사항이면, 별도 security-focused 테스트에서 `401/403`을 다시 검증하면 된다.

## `addFilters=false` 대신 테스트 전용 보안 설정을 두는 경우

필터를 아예 끄기 싫다면, 테스트에서만 가장 단순한 보안 규칙을 주입해서 컨트롤러까지 도달시키는 방법도 있다.

```java
@WebMvcTest(OrderController.class)
@Import(TestSecurityConfig.class)
class OrderControllerSecurityFriendlyTest {

    @TestConfiguration
    static class TestSecurityConfig {

        @Bean
        SecurityFilterChain testFilterChain(HttpSecurity http) throws Exception {
            return http
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())
                .build();
        }
    }
}
```

- `addFilters=false`는 "필터 체인을 아예 빼고 controller만 본다"에 가깝다.
- 테스트 전용 보안 설정은 "필터 체인은 남기되, 지금 테스트에 필요한 최소 규칙만 둔다"에 가깝다.
- 초급자라면 먼저 `addFilters=false`로 시작하고, 보안과 MVC를 함께 봐야 할 때만 테스트 전용 설정으로 한 단계 올리면 충분하다.

## `@DataJpaTest` 최소 템플릿

```java
@DataJpaTest
class OrderRepositoryDataJpaTest {

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void 주문번호로_조회된다() {
        orderRepository.save(new OrderEntity("ORD-001"));

        Optional<OrderEntity> result = orderRepository.findByOrderNumber("ORD-001");

        assertThat(result).isPresent();
    }
}
```

## `@DataJpaTest`가 H2에서는 깨지는데 운영 DB 기준으로는 맞아 보일 때

처음에는 "JPA가 틀렸다"보다 **"지금 테스트 DB와 운영 DB가 같은 문법/타입/스키마를 쓰는가?"**를 먼저 묻는 편이 빠르다.

아래 중 하나면 [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)를 바로 열어 보면 된다.

- native query나 DB 전용 함수(`ILIKE`, `DATE_TRUNC`, `JSON_EXTRACT` 등)를 썼다
- 운영은 PostgreSQL/MySQL인데 테스트는 기본 H2다
- 운영은 Flyway/Liquibase로 스키마를 만들지만 테스트는 자동 생성에 기대고 있다

짧게 말해, `@DataJpaTest`는 좋은 첫 선택이지만 H2와 실제 DB가 다르면 "테스트 종류"보다 먼저 "검증 엔진이 맞는가"를 다시 봐야 할 수 있다.

## 처음에 자주 헷갈리는 점

- `@WebMvcTest`는 기본적으로 서비스/리포지토리를 안 띄운다. 필요한 협력은 `@MockBean`으로 채운다.
- `@WebMvcTest`에서 예상과 다르게 `401` 또는 `403`이 먼저 보이면, 컨트롤러보다 security filter chain이 먼저 응답을 만든 것일 수 있다.
- `@DataJpaTest`는 테스트마다 롤백된다. 테스트 간 데이터 공유를 기대하면 실패한다.
- 두 테스트가 느려지기 시작하면 `@SpringBootTest`로 올리기 전에, 먼저 "검증 목표가 레이어 계약인지 실제 wiring인지"를 다시 확인한다.

## 빠른 선택 규칙 (30초 버전)

- "순수 로직이 바뀌었나?" -> 단위 테스트부터.
- "스프링 레이어 계약이 바뀌었나?" -> 해당 슬라이스 테스트부터.
- "여러 의존을 실제로 붙여야 안심되나?" -> 통합 테스트 1개부터.
- 헷갈리면 단위 테스트 1개를 먼저 추가하고, 실패 원인이 경계(wiring) 쪽이면 슬라이스/통합으로 올린다.

## 상세 분해

**단위 테스트의 범위**

단위 테스트는 보통 외부 의존(DB, 외부 API)을 Mock으로 대체하고 순수 로직만 검증한다.

```java
@Test
void 주문_금액이_0원이면_예외() {
    OrderService service = new OrderService(mockRepository);
    assertThrows(InvalidOrderException.class,
        () -> service.create(new CreateOrderRequest(0)));
}
```

**테스트 더블(Test Double)**

- **Mock** — 호출 여부와 횟수를 검증한다. `verify(mock.send()).wasCalled(1)`.
- **Stub** — 특정 입력에 정해진 값을 반환한다. `when(repo.find(id)).thenReturn(order)`.
- **Fake** — 실제 동작을 단순하게 흉내낸다. 메모리 저장소 등.

입문 단계에서는 Mock과 Stub의 차이보다, "실제 의존을 교체해서 빠르게 테스트한다"는 개념을 먼저 잡으면 충분하다.

**통합 테스트 범위**

Spring에서 `@SpringBootTest`를 쓰면 전체 컨텍스트를 올려서 실제 DB와 함께 테스트할 수 있다. `@DataJpaTest`는 JPA 관련 빈만 올려 더 빠르다.

## 흔한 오해와 함정

- "테스트가 많으면 많을수록 좋다"는 오해가 있다. 테스트가 구현 세부에 강하게 묶이면 리팩터링할 때 테스트도 같이 고쳐야 해서 오히려 비용이 커진다. 인터페이스와 동작을 테스트하는 편이 낫다.
- `@SpringBootTest`를 단위 테스트처럼 쓰면 전체 컨텍스트 로딩 비용이 쌓여 빌드가 느려진다.
- Mock을 너무 많이 쓰면 실제 협력에서 발생하는 버그를 잡지 못한다. 핵심 통합 경로는 통합 테스트로 커버해야 한다.
- "통합 테스트가 더 현실적이니 처음부터 통합만 쓰자"는 선택도 흔한 실수다. 초급 단계에서는 **가장 싼 테스트 1개**(보통 단위/슬라이스)로 먼저 실패를 고정하고, 필요한 경우에만 통합 테스트를 추가하는 편이 유지비가 낮다.
- 입력 검증/쿼리 수정/재시도 정책처럼 변경 이유가 다른데 테스트 종류를 한 가지로 통일하면, 실패 원인이 어디인지 오히려 늦게 드러난다.

## 실무에서 쓰는 모습

대부분의 백엔드 프로젝트에서는 도메인/서비스 로직은 단위 테스트로 빠르게 커버하고, Repository나 외부 연동이 포함된 경로는 슬라이스 테스트(`@DataJpaTest`, `@WebMvcTest`)로 검증하며, 핵심 시나리오 2~3개만 `@SpringBootTest` E2E 테스트로 잡는 패턴이 흔하다.

## 더 깊이 가려면

- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md) — Spy, Stub, Mock, Fake의 정밀한 구분과 선택 기준
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) — 포트/어댑터 구조가 테스트 격리를 어떻게 도와주는지
- [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md) — controller slice에서 보안 wiring까지 언제 같이 볼지 경계를 더 자세히 설명

## 면접/시니어 질문 미리보기

- "단위 테스트와 통합 테스트를 어떻게 구분하나요?" — 외부 의존(DB, 네트워크)이 실제로 연결되는지 여부가 가장 실용적인 기준이다. 외부가 Mock이면 단위, 실제 연결이면 통합이다.
- "Mock을 쓰면 어떤 장단점이 있나요?" — 장점: 빠르고 격리된 검증 가능. 단점: 실제 의존 구현이 바뀌면 Mock이 현실을 반영하지 못해 거짓 통과가 생길 수 있다.
- "테스트가 많으면 리팩토링이 어려워지는 이유가 뭔가요?" — 테스트가 구현 내부(메서드 이름, 호출 순서)에 묶여 있으면 구현을 바꿀 때 테스트도 같이 바꿔야 한다. 동작(결과)을 테스트하면 이 문제가 줄어든다.

## 한 줄 정리

테스트는 단위·통합·E2E를 적절히 섞되, 많은 단위 테스트로 빠른 피드백을 잡고 소수의 통합 테스트로 실제 협력을 검증하는 것이 기본 전략이다.
