# Spring Test Slices와 Context Caching

> 한 줄 요약: 이 문서는 "`왜 테스트가 갑자기 느려졌지?`" 단계에서 slice와 context cache를 같이 보는 follow-up이고, 처음 테스트를 고르는 단계라면 먼저 beginner primer로 내려가는 편이 안전하다.

**난이도: 🟡 Intermediate**

관련 문서:
- [카테고리 README](./README.md)
- [Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
- [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
- [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)

retrieval-anchor-keywords: test slice, context cache, webmvctest, datajpatest, springboottest, spring test slow, 왜 테스트 느려요, 처음 배우는데 test slice, context cache 뭐예요, slice test cache split, springboottest properties, testpropertysource, dynamicpropertysource, test property override, dirtiescontext

---

## 먼저 이 문서로 오기 전 체크

처음 Spring 테스트를 고르는 단계라면 이 문서보다 아래 두 문서가 먼저다.

- "`처음이라 `@SpringBootTest` / `@WebMvcTest` / `@DataJpaTest` 차이부터 헷갈려요`" -> [Spring 테스트 기초](./spring-testing-basics.md)
- "`service bean not found`가 scan 문제인지 slice 경계 문제인지 모르겠어요`" -> [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)

이 문서는 그 다음 단계, 즉 "**테스트 종류는 대충 골랐는데 왜 느리고 왜 캐시가 자꾸 갈라지지?**"를 보는 문서다.

## 먼저 잡는 mental model

처음에는 캐시 구현 디테일보다 아래 한 줄로 보면 된다.

> mental model: slice는 "얼마나 적게 띄울까"를 정하는 선택이고, context cache는 "한 번 띄운 걸 몇 번 다시 쓸까"를 정하는 선택이다.

같은 `POST /orders` 테스트라도 질문이 다르면 보는 축이 달라진다.

| 지금 막힌 말 | 먼저 보는 축 | 먼저 읽을 문서 |
|---|---|---|
| "`/orders` 응답 코드만 빨리 보고 싶어요" | 테스트 범위 선택 | [Spring 테스트 기초](./spring-testing-basics.md) |
| "`service bean not found`가 나요" | slice 경계 확인 | [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md) |
| "`어제보다 테스트가 3배 느려졌어요`" | context 재사용 여부 | 이 문서 |
| "`JSON` 모양이나 외부 API client 헤더만 보고 싶어요" | 더 좁은 계약 slice | [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md) |

## 핵심 개념

Spring 테스트의 핵심은 두 가지다.

1. 어떤 범위의 Spring `ApplicationContext`를 올릴 것인가
2. 그 컨텍스트를 얼마나 재사용할 것인가

테스트가 느려지는 이유는 대개 테스트 로직 자체보다, **매번 거대한 컨텍스트를 새로 만드는 비용** 때문이다.

`Test Slice`는 전체 애플리케이션을 다 올리지 않고, 필요한 레이어만 잘라서 테스트하는 방식이다.

- `@WebMvcTest`: MVC 컨트롤러 계층 중심
- `@DataJpaTest`: JPA/Repository 계층 중심
- `@JsonTest`: JSON serialization 중심
- `@SpringBootTest`: 거의 전체 컨텍스트

이 문서를 읽어야 하는 이유는 명확하다.
테스트가 느리고, 불안정하고, 리팩터링에 약하다면 단순히 mock을 늘릴 문제가 아니라, **컨텍스트 구성 자체를 재설계해야 하기 때문**이다.

## 20초 분기: 지금 문제는 slice 선택인가, cache 분열인가

아래처럼 나누면 glossary처럼 읽지 않고 바로 출발점을 고를 수 있다.

| 보이는 증상 | 더 가까운 원인 | 다음 행동 |
|---|---|---|
| "`@WebMvcTest`인데 service bean이 없어요" | 원래 slice에 없는 Bean을 기대함 | [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)로 이동 |
| "`@SpringBootTest`가 여기저기 늘면서 CI가 느려졌어요" | full context 남용 | slice로 줄일 수 있는 테스트를 먼저 분리 |
| 테스트 로직은 비슷한데 클래스마다 시작 시간이 길다 | 같은 컨텍스트를 재사용하지 못함 | property, mock, `@DirtiesContext` 차이를 비교 |
| JSON 직렬화나 outbound client만 검증하면 되는데 테스트가 무겁다 | slice가 너무 넓음 | [`@JsonTest` / `@RestClientTest`](./spring-jsontest-restclienttest-slice-boundaries.md)로 축소 |

---

## 깊이 들어가기

### 1. Test Slice는 무엇을 줄이는가

Slice 테스트는 보통 아래 비용을 줄인다.

- Bean 수
- Auto-configuration 범위
- 데이터베이스 연결 수
- 웹 서버 기동 비용

예를 들어 `@WebMvcTest`는 Controller 관련 빈만 올리고, 서비스는 `@MockBean`으로 대체하는 식이다.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    OrderService orderService;

    @Test
    void 주문_조회() throws Exception {
        when(orderService.findOrder(1L)).thenReturn(new OrderDto(1L, "PAID"));

        mockMvc.perform(get("/orders/1"))
            .andExpect(status().isOk());
    }
}
```

## Context Caching은 왜 중요한가

Spring Test는 비슷한 설정의 `ApplicationContext`를 캐시한다.
즉, 테스트 클래스마다 무조건 다시 올리는 것이 아니라, 컨텍스트 구성이 같으면 재사용할 수 있다.

문제는 아래와 같은 상황에서 캐시가 깨진다는 점이다.

- `@MockBean` 구성이 테스트마다 다름
- `@SpringBootTest(properties = ...)` 값이 테스트마다 다름
- `@TestPropertySource` file/inline 구성이 테스트마다 다름
- `@DynamicPropertySource` 값이 달라짐
- `@DirtiesContext`를 남발함
- 불필요한 `@SpringBootTest`를 여러 곳에서 씀

결과적으로 테스트는 논리적으로 비슷한데, 컨텍스트는 매번 새로 뜬다.

짧게 기억하면 아래 표면 충분하다.

| 느려지는 이유 | 초급자용 해석 |
|---|---|
| slice를 너무 크게 골랐다 | 처음부터 큰 앱을 매번 띄운다 |
| 같은 slice라도 속성이 자꾸 달라진다 | 재사용 가능한 컨텍스트가 매번 다른 것으로 판정된다 |
| `@DirtiesContext`를 자주 쓴다 | 일부러 캐시를 버린다 |

## Slice와 Full Context의 경계

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `@WebMvcTest` | 빠르고 좁다 | 서비스/리포지토리 흐름은 못 본다 | controller contract 확인 |
| `@DataJpaTest` | repository 검증에 좋다 | 웹/보안/서비스 흐름은 못 본다 | query, mapping, transaction 확인 |
| `@JsonTest` / `@RestClientTest` | payload / outbound client 계약만 더 좁게 본다 | 애플리케이션 전체 흐름은 못 본다 | JSON shape, 외부 HTTP adapter 확인 |
| `@SpringBootTest` | 현실과 가장 가깝다 | 느리고 무겁다 | end-to-end-like integration |

핵심은 “`@SpringBootTest`를 쓰지 말라”가 아니라, **슬라이스로 충분한데 전체 컨텍스트를 올리는 습관을 줄이라**는 것이다.

---

## 실전 시나리오

### 시나리오 1: 테스트가 갑자기 3배 느려졌다

원인 후보:

- 새로운 `@SpringBootTest`가 추가됨
- 컨텍스트 캐시가 깨지는 `@MockBean`이 늘어남
- embedded DB가 매 테스트마다 새로 뜸

대응 순서:

1. 어떤 테스트가 full context인지 확인한다.
2. `@WebMvcTest` / `@DataJpaTest`로 줄일 수 있는지 본다.
3. `@DirtiesContext`가 필요한지 재검토한다.

### 시나리오 2: `@MockBean`을 많이 쓰다 보니 리팩터링이 무서워졌다

테스트가 구현 세부사항에 묶이면, 클래스 이름만 바꿔도 테스트가 흔들린다.
이 경우 mock 자체보다, **테스트의 경계가 잘못 잡힌 것**일 가능성이 크다.

짧게 말하면 "`mock이 많다`"는 현상보다 "`원래 좁아야 할 테스트가 이미 너무 많은 Bean을 기대한다`"가 더 근본 원인일 수 있다.

### 시나리오 3: 보안, 필터, custom config까지 섞이며 slice가 커졌다

이 시점부터는 단순 캐시 문서보다 "원래 slice 경계를 누가 넓혔는가"를 따로 보는 편이 빠르다.

- `@Import`, `@TestConfiguration`이 섞였으면 [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
- "`원래 `@WebMvcTest`에 service가 없어야 하는 거였나?`"가 헷갈리면 [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)
- 보안 필터 체인이 핵심이면 [Spring Security 아키텍처](./spring-security-architecture.md)

---

## 코드로 보기

### WebMvcTest

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    OrderQueryService orderQueryService;
}
```

### DataJpaTest

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired
    OrderRepository orderRepository;

    @Test
    void 주문을_저장하고_조회한다() {
        Order saved = orderRepository.save(new Order("PAID"));
        assertThat(orderRepository.findById(saved.getId())).isPresent();
    }
}
```

### Context 재사용을 깨는 예

```java
@SpringBootTest
class ATest {
}

@SpringBootTest
class BTest {
}
```

겉보기에는 같아 보여도, 설정이 조금씩 다르면 캐시가 쪼개진다.
특히 테스트마다 다른 property, mock, profile을 넣는 습관이 있으면 컨텍스트 재사용이 잘 안 된다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 선택 기준 |
|---|---|---|---|
| Slice test | 빠르다, 실패 원인이 좁다 | 전체 흐름을 다 못 본다 | 특정 레이어 계약 검증 |
| Full context test | 실제와 가깝다 | 느리고 비싸다 | 여러 계층 통합 검증 |
| `@DirtiesContext` | 상태 오염을 강하게 끊는다 | 캐시를 깨서 느려진다 | 정말 컨텍스트 상태가 바뀌는 경우 |
| `@MockBean` | 의존성 격리가 쉽다 | 과하면 리팩터링 내성이 떨어진다 | 외부 협력자를 통제할 때 |

핵심은 테스트 수를 줄이는 것이 아니라, **컨텍스트 비용이 반복되지 않게 만드는 것**이다.

---

## 다음 질문은 다른 문서로 넘긴다

> Q: `@WebMvcTest`와 `@SpringBootTest`의 가장 큰 차이는 무엇인가?
> 의도: 테스트 범위와 컨텍스트 비용 구분 확인
> 핵심: 슬라이스는 레이어 계약, 풀 컨텍스트는 통합 검증

> Q: `@DirtiesContext`를 남발하면 왜 느려지는가?
> 의도: 컨텍스트 캐싱 이해 확인
> 핵심: 캐시를 의도적으로 버리기 때문이다

> Q: `@MockBean`이 많아지면 어떤 문제가 생기는가?
> 의도: 테스트 설계의 응집도 확인
> 핵심: 구현 세부사항에 테스트가 묶인다

- "`처음이라 어떤 테스트 annotation을 고를지 모르겠어요`" -> [Spring 테스트 기초](./spring-testing-basics.md)
- "`property override가 cache를 왜 쪼개죠?`" -> [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
- "`slice에 뭘 import했더니 갑자기 무거워졌어요`" -> [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
- "`JSON` 필드명이나 외부 API client 요청만 검증하고 싶은데 너무 무거워요`" -> [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)

---

## 한 줄 정리

Spring 테스트는 무엇을 검증할지보다, 어떤 컨텍스트를 얼마나 재사용할지를 먼저 설계해야 빨라지고 안정적이다.
