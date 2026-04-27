# Spring Test Slices와 Context Caching

> 한 줄 요약: Spring 테스트는 "많이 돌리는 것"보다, 어떤 컨텍스트를 얼마나 작게 재사용할지 설계하는 문제가 더 중요하다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
> - [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
> - [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
> - [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
> - [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
> - [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)

retrieval-anchor-keywords: test slice, context cache, WebMvcTest, DataJpaTest, SpringBootTest, SpringBootTest properties, TestPropertySource, DynamicPropertySource, test property override, test property cache split, MockBean, DirtiesContext, TestEntityManager, flush clear test, test boundary, test configuration

---

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

### 2. Context Caching은 왜 중요한가

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

### 3. Slice와 Full Context의 경계

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `@WebMvcTest` | 빠르고 좁다 | 서비스/리포지토리 흐름은 못 본다 | controller contract 확인 |
| `@DataJpaTest` | repository 검증에 좋다 | 웹/보안/서비스 흐름은 못 본다 | query, mapping, transaction 확인 |
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

### 시나리오 3: Security가 붙은 컨트롤러 테스트가 너무 복잡하다

`@WebMvcTest`에 `Spring Security`가 섞이면 인증/인가 필터 설정이 추가된다.
이때 실제 인증이 필요한지, 아니면 `@WithMockUser`로 충분한지 구분해야 한다.

이 주제는 [Spring Security 아키텍처](./spring-security-architecture.md)와 같이 보면 이해가 빠르다.

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

## 꼬리질문

> Q: `@WebMvcTest`와 `@SpringBootTest`의 가장 큰 차이는 무엇인가?
> 의도: 테스트 범위와 컨텍스트 비용 구분 확인
> 핵심: 슬라이스는 레이어 계약, 풀 컨텍스트는 통합 검증

> Q: `@DirtiesContext`를 남발하면 왜 느려지는가?
> 의도: 컨텍스트 캐싱 이해 확인
> 핵심: 캐시를 의도적으로 버리기 때문이다

> Q: `@MockBean`이 많아지면 어떤 문제가 생기는가?
> 의도: 테스트 설계의 응집도 확인
> 핵심: 구현 세부사항에 테스트가 묶인다

> Q: Security가 붙은 MVC 테스트는 왜 어려워지기 쉬운가?
> 의도: 필터 체인과 테스트 경계 이해 확인
> 핵심: 인증/인가 필터가 컨텍스트에 개입하기 때문이다

---

## 한 줄 정리

Spring 테스트는 무엇을 검증할지보다, 어떤 컨텍스트를 얼마나 재사용할지를 먼저 설계해야 빨라지고 안정적이다.
