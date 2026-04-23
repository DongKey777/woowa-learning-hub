# Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지

> 한 줄 요약: Spring 테스트는 전체 컨텍스트를 로드하는 `@SpringBootTest`와 특정 레이어만 로드하는 슬라이스 테스트(`@WebMvcTest`, `@DataJpaTest`)로 나뉘며, 슬라이스 테스트가 더 빠르고 집중적이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring @Transactional 기초](./spring-transactional-basics.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring testing basics, 스프링 테스트 처음, springboottest 입문, webmvctest 뭐예요, datajpatest 입문, 슬라이스 테스트 입문, mockmvc 입문, @mockbean 입문, spring 단위 테스트 vs 통합 테스트, spring test 빠르게 하는 법, spring test 컨텍스트 로드 느린 이유, mockito spring 입문

## 핵심 개념

Spring 테스트는 "얼마나 많은 컨텍스트를 로드하느냐"에 따라 크게 두 종류로 나뉜다.

- **통합 테스트(`@SpringBootTest`)**: 애플리케이션 전체 컨텍스트를 로드한다. 실제 동작과 가장 가깝지만 느리다.
- **슬라이스 테스트**: 특정 레이어만 로드한다. `@WebMvcTest`는 웹 레이어만, `@DataJpaTest`는 JPA 레이어만 로드해 빠르다.

입문자가 처음 접할 때는 `@SpringBootTest`로 모든 것을 테스트하려 하는데, 테스트 숫자가 늘어나면 빌드 시간이 급격히 느려진다.

## 한눈에 보기

| 애노테이션 | 로드 범위 | 주요 용도 |
|---|---|---|
| `@SpringBootTest` | 전체 컨텍스트 | 통합 테스트, E2E |
| `@WebMvcTest` | 웹 레이어(Controller, Filter 등) | 컨트롤러 단위 테스트 |
| `@DataJpaTest` | JPA 레이어(Repository, Datasource) | 레포지토리 단위 테스트 |
| 순수 단위 테스트 | Spring 컨텍스트 없음 | Service 로직 테스트 |

## 상세 분해

- **`@WebMvcTest`**: `@Controller`, `@ControllerAdvice`, `Filter` 등 웹 레이어 Bean만 로드한다. `@Service`, `@Repository`는 로드되지 않으므로 `@MockBean`으로 대체해야 한다.
- **`@DataJpaTest`**: 인메모리 DB(H2)와 JPA 관련 Bean만 로드한다. 각 테스트는 기본적으로 롤백된다.
- **`@MockBean`**: Spring 컨텍스트 안에 Mock 객체를 Bean으로 등록한다. `@WebMvcTest`에서 Service를 모킹할 때 사용한다.
- **`MockMvc`**: 실제 HTTP 서버 없이 컨트롤러를 테스트하는 도구. `perform(get("/api/members"))` 형태로 요청을 시뮬레이션한다.
- **순수 단위 테스트**: Spring 컨텍스트 없이 JUnit + Mockito만으로 Service 로직을 테스트한다. 가장 빠르고 컨텍스트 로드 비용이 없다.

## 흔한 오해와 함정

**오해 1: `@SpringBootTest`로 모든 테스트를 작성해야 정확하다**
Spring 컨텍스트 로드 시간이 수초씩 걸린다. 테스트가 수십 개를 넘으면 빌드가 수분 단위로 느려진다. Service 로직은 순수 단위 테스트로, 컨트롤러는 `@WebMvcTest`로 분리하는 것이 좋다.

**오해 2: `@DataJpaTest`에서 롤백되니 DB 상태를 신뢰하기 어렵다**
테스트 격리가 오히려 장점이다. 각 테스트가 독립적으로 실행되어 순서 의존성이 없어진다.

**오해 3: `@MockBean`과 Mockito의 `@Mock`은 같다**
`@Mock`은 Spring 컨텍스트 밖에서 사용하는 Mockito 애노테이션이고, `@MockBean`은 Spring 컨텍스트 안에 Mock을 Bean으로 등록한다. 슬라이스 테스트에서 컨텍스트 안에 Mock이 필요하면 `@MockBean`을 써야 한다.

## 실무에서 쓰는 모습

`@WebMvcTest`로 컨트롤러를 테스트하는 기본 패턴이다.

```java
@WebMvcTest(MemberController.class)
class MemberControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean  MemberService memberService;

    @Test
    void 회원_조회_성공() throws Exception {
        given(memberService.findById(1L))
            .willReturn(new MemberResponse(1L, "test@example.com"));

        mockMvc.perform(get("/api/members/1"))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.email").value("test@example.com"));
    }
}
```

`MemberService`는 `@MockBean`으로 대체하고, 실제 HTTP 요청 없이 컨트롤러 로직만 테스트한다.

## 더 깊이 가려면

- 슬라이스 테스트에서 컨텍스트 캐시가 어떻게 재사용되는지는 [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)에서 이어서 본다.
- `@DataJpaTest`에서 롤백과 플러시 타이밍 때문에 발생하는 함정은 [Spring @Transactional 기초](./spring-transactional-basics.md)와 연결지어 보면 좋다.

## 면접/시니어 질문 미리보기

> Q: `@WebMvcTest`와 `@SpringBootTest`의 차이를 설명하면?
> 의도: 테스트 레이어 분리 이해 확인
> 핵심: `@WebMvcTest`는 웹 레이어만 로드해 빠르고, `@SpringBootTest`는 전체 컨텍스트를 로드해 통합 테스트에 쓴다.

> Q: `@MockBean`을 왜 쓰나? Mockito `@Mock`으로는 안 되나?
> 의도: Spring 컨텍스트와 Mockito의 관계 이해
> 핵심: `@WebMvcTest`처럼 Spring 컨텍스트가 필요한 테스트에서는 Mock이 Bean으로 등록되어야 하므로 `@MockBean`을 써야 한다.

> Q: 단위 테스트와 통합 테스트를 어떻게 구분해 작성하나?
> 의도: 테스트 전략 이해
> 핵심: 외부 의존 없이 로직만 검증하면 단위 테스트(Spring 없이), 레이어 간 연동을 검증하면 슬라이스 테스트, 전체 흐름을 검증하면 통합 테스트를 쓴다.

## 한 줄 정리

Spring 테스트는 `@SpringBootTest`로 전체를 검증하는 통합 테스트와 `@WebMvcTest`, `@DataJpaTest` 같은 슬라이스 테스트로 나뉘며, 레이어별로 분리할수록 빌드가 빠르고 테스트 목적이 명확해진다.
