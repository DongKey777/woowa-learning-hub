# Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지

> 한 줄 요약: Spring 테스트는 "애플리케이션을 어디까지 켤지"를 고르는 문제라서, 처음에는 `@SpringBootTest` 하나로 밀기보다 `@WebMvcTest`, `@DataJpaTest` 같은 슬라이스를 먼저 구분하면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring `@ActiveProfiles` vs test override primer: `application-test.yml`, `@TestPropertySource`, annotation `properties`](./spring-activeprofiles-vs-test-overrides-primer.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring testing basics, spring test beginner, springboottest basics, webmvctest basics, datajpatest basics, slice test basics, spring test too slow, service bean not found test, mockmvc basics, mockbean basics, spring test what is, spring test 처음, spring test 헷갈려, spring test 뭐부터

## 먼저 mental model 한 줄

처음에는 테스트를 "로직 확인"보다 **Spring을 어디까지 켤지 정하는 문제**로 보면 된다.

- `@SpringBootTest`: 앱 전체를 크게 켠다.
- `@WebMvcTest`: 컨트롤러 주변만 켠다.
- `@DataJpaTest`: repository/JPA 주변만 켠다.
- 순수 단위 테스트: Spring 자체를 안 켠다.

입문자가 자주 하는 실수는 "`일단 전부 켜면 정확하겠지`"라고 생각하는 것이다. 하지만 그러면 느려지고, "`service bean not found`", "`왜 이 테스트만 DB까지 떠요?`" 같은 혼란이 같이 커진다.

## 한눈에 보기

| 애노테이션 | 로드 범위 | 주요 용도 |
|---|---|---|
| `@SpringBootTest` | 전체 컨텍스트 | 통합 테스트, E2E |
| `@WebMvcTest` | 웹 레이어(Controller, Filter 등) | 컨트롤러 단위 테스트 |
| `@DataJpaTest` | JPA 레이어(Repository, Datasource) | 레포지토리 단위 테스트 |
| 순수 단위 테스트 | Spring 컨텍스트 없음 | Service 로직 테스트 |

## 처음엔 테스트를 2가지 질문으로 고른다

처음에는 annotation 이름보다 "`무엇을 검증하나`"와 "`Spring을 어디까지 켜야 하나`" 두 질문만 잡으면 된다.

| 먼저 답할 질문 | 예시 답 | 자연스러운 시작점 |
|---|---|---|
| 지금 보는 건 웹 계약인가, DB 매핑인가, 계산 로직인가? | "`응답 코드와 JSON`", "`쿼리와 엔티티`", "`할인 계산`" | `@WebMvcTest`, `@DataJpaTest`, 순수 단위 테스트 |
| 여러 레이어 wiring과 실제 트랜잭션까지 같이 봐야 하나? | "`controller -> service -> repository`를 한 번에 붙여 보고 싶어요" | `@SpringBootTest` |

짧게 외우면 "`무엇을 확인하나`가 먼저고, `얼마나 크게 켜나`가 그다음"이다.

## 실패 문장을 먼저 번역하면 덜 헷갈린다

처음에는 "`테스트가 안 돼요`"를 한 덩어리로 보기 쉽다. 하지만 beginner 단계에서는 실패 문장을 아래처럼 번역하면 출발점이 훨씬 빨라진다.

| 지금 바로 보이는 말 | 먼저 자를 축 | 먼저 읽을 문서 |
|---|---|---|
| "`@WebMvcTest`인데 service bean not found예요" | slice 경계 | [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md) |
| "`@Transactional`이 안 먹는 것 같아요`" | 프록시 경계 | [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md) |
| "`POST /orders`가 controller 전에 400 나요`" | 요청 바인딩/파이프라인 | [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md) |
| "`어제보다 테스트가 3배 느려졌어요`" | context 재사용 | [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md) |

한 줄로 줄이면:

- "`무엇을 띄웠나`"는 test slice 질문이다.
- "`어떻게 호출됐나`"는 프록시 질문이다.
- "`어디서 실패했나`"는 요청 파이프라인 질문이다.

## 처음엔 `POST /orders` 한 장면으로 고르면 쉽다

같은 주문 기능도 "무엇을 확인하느냐"에 따라 테스트 시작점이 달라진다.

| 내가 지금 확인할 것 | 먼저 고를 테스트 | 왜 이 테스트가 맞나 |
|---|---|---|
| `POST /orders`가 `201 Created`와 JSON을 잘 주는가 | `@WebMvcTest` | URL 매핑, `@RequestBody`, 응답 바디처럼 웹 계약만 본다 |
| 주문 저장 쿼리와 엔티티 매핑이 맞는가 | `@DataJpaTest` | repository, JPA, rollback 경계만 좁게 본다 |
| 주문 생성 service의 할인 계산이 맞는가 | 순수 단위 테스트 | Spring 없이 계산 규칙만 가장 빠르게 검증한다 |
| 컨트롤러 -> service -> repository wiring과 트랜잭션까지 한 번에 붙는가 | `@SpringBootTest` | 여러 레이어 연결과 실제 Bean 구성을 같이 본다 |

초급자 기준 mental model은 이것이면 충분하다.

- 웹 계약이면 `@WebMvcTest`
- DB/JPA면 `@DataJpaTest`
- 계산 로직이면 순수 단위 테스트
- "진짜로 다 같이 붙는가"를 볼 때만 `@SpringBootTest`

## 같은 `OrderService`라도 테스트마다 역할이 다르다

처음 많이 헷갈리는 지점은 "`OrderService`라는 이름이 같으니 어느 테스트에서나 같은 객체겠지"라고 보는 것이다. 실제로는 같은 주문 예제라도 테스트가 무엇을 확인하느냐에 따라 `OrderService`가 **진짜 Bean일 수도 있고, Mock일 수도 있고, 아예 없을 수도 있다.**

| 내가 고른 테스트 | `OrderService`는 보통 무엇인가 | 초급자용 한 줄 |
|---|---|---|
| `@WebMvcTest(OrderController.class)` | `@MockBean`으로 넣은 가짜 Bean | controller가 service를 "어떻게 호출하는지"만 본다 |
| `@DataJpaTest` | 보통 아예 없다 | service 없이 repository/JPA만 본다 |
| `@SpringBootTest` | 실제 Spring Bean | wiring, 트랜잭션, 설정까지 같이 본다 |
| 순수 단위 테스트 | 개발자가 직접 만든 mock/stub 의존성 | Spring 없이 service 로직만 본다 |

짧은 concrete example 하나로 보면 아래처럼 구분하면 된다.

- "`POST /orders`가 201과 JSON을 주는지만 보겠다" -> `@WebMvcTest` + `@MockBean OrderService`
- "`OrderRepository.save()`와 매핑이 맞는지만 보겠다" -> `@DataJpaTest`
- "`주문 생성 service가 재고 차감, 저장, 트랜잭션까지 실제로 붙는가`" -> `@SpringBootTest`

그래서 "`왜 어떤 테스트에서는 service bean not found가 나고, 어떤 테스트에서는 진짜 service가 돌아가죠?`"라는 질문은 scan이 오락가락해서가 아니라, **테스트가 일부러 보는 범위를 다르게 잘랐기 때문**인 경우가 많다.

## 슬라이스는 새 구조가 아니라 보는 창이다

초급자가 자주 헷갈리는 포인트는 "`@WebMvcTest`와 `@DataJpaTest`가 runtime 구조에도 따로 존재하나?`"라는 느낌이다. 하지만 slice는 운영 코드의 새 레이어가 아니라, **한 요청에서 어느 부분만 확대해서 볼지 정하는 테스트 창**에 가깝다.

| 지금 보는 창 | 주로 확대하는 runtime 질문 | 같이 섞지 말아야 할 것 |
|---|---|---|
| `@WebMvcTest` | URL 매핑, JSON, 검증/바인딩, 예외 응답 | service 트랜잭션 동작까지 한 번에 확인하려는 기대 |
| `@DataJpaTest` | repository 쿼리, 엔티티 매핑, flush/rollback 감각 | controller 요청 흐름과 HTTP 응답 문제 |
| `@SpringBootTest` | controller-service-repository wiring 전체 | 느린데도 이유 없이 기본값처럼 쓰는 습관 |

짧게 외우면 "`slice는 무엇을 줄여서 볼지`, `@Transactional`은 어디를 묶을지`"다. 둘 다 같은 주문 기능을 보더라도 질문 축이 다르다.

## 처음 막히는 질문부터 고르기

| 지금 보이는 증상 | 먼저 고를 테스트 | 왜 이쪽이 먼저인가 |
|---|---|---|
| "컨트롤러 응답 JSON만 보고 싶은데 전체 앱이 너무 느려요" | `@WebMvcTest` | 요청 매핑, 바인딩, 응답 형식만 빠르게 볼 수 있다 |
| "`@WebMvcTest`인데 service bean not found가 나요" | `@WebMvcTest` + `@MockBean` | 웹 슬라이스는 service를 기본으로 안 올리는 것이 정상이다 |
| "쿼리나 엔티티 매핑만 확인하고 싶어요" | `@DataJpaTest` | JPA 경계만 켜서 repository 검증에 집중한다 |
| "`commit` 뒤 이벤트/후처리까지 같이 확인하고 싶어요" | `@SpringBootTest` | rollback 기본값인 slice보다 실제 commit 경계를 보는 질문에 가깝다 |
| "트랜잭션, 보안, 설정까지 한 번에 붙는지 봐야 해요" | `@SpringBootTest` | 여러 레이어 wiring을 같이 보는 통합 검증이기 때문이다 |
| "service 계산 로직만 확인하면 돼요" | 순수 단위 테스트 | Spring 없이 가장 빠르게 실패 원인을 좁힌다 |

## 자주 하는 오해를 먼저 끊기

처음엔 "`테스트가 실패했다`"를 한 문제로 보지만, 실제로는 질문 종류가 다르다.

| 흔한 말 | 실제로 먼저 자를 축 | 바로 떠올릴 기준 |
|---|---|---|
| "`@WebMvcTest`인데 왜 service bean not found가 나요?" | slice 경계 | scan 고장보다 "웹만 띄웠다"를 먼저 본다 |
| "`@DataJpaTest`인데 트랜잭션이 롤백돼서 저장이 안 된 것 같아요" | 테스트 기본 롤백 | 실패보다 격리 목적이 먼저다 |
| "`처음이라 그냥 @SpringBootTest 하나로 다 보면 안 돼요?`" | 비용과 목적 | 정확성보다 느림과 원인 혼합이 먼저 커진다 |
| "`@Transactional`이 안 먹는 것도 테스트 종류 문제예요?`" | 테스트 범위 vs 프록시 경계 | 테스트 종류와 프록시 우회 문제를 분리해서 본다 |

특히 마지막 줄이 많이 섞인다.

- `@WebMvcTest`에서 service Bean이 없다는 것은 대개 **슬라이스 경계 문제**다.
- `@Transactional`이 안 먹는 것은 대개 **프록시 경계 문제**다.
- 둘 다 "`안 된다`"로 보이지만, 하나는 "무엇을 띄웠나", 다른 하나는 "어떻게 호출했나"를 보는 질문이다.
- controller 전에 `400`이 나는 것은 테스트 종류보다 **바인딩/요청 파이프라인 문제**일 수 있다.

## 레이어별로 이렇게 읽으면 된다

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

**오해 4: `@WebMvcTest`가 service를 못 찾으면 scan이 깨진 것이다**
보통은 scan 실패가 아니라 slice 경계가 원래 좁기 때문이다. 이때는 component scan보다 "내가 controller 계약만 보려는가"를 먼저 확인하는 편이 맞다.

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

## `service bean not found`와 `@Transactional` 혼동 20초 분기

처음엔 둘 다 service 쪽에서 터져 보여서 같은 문제처럼 느껴진다. 하지만 보는 위치가 다르다.

| 증상 | 먼저 볼 문서 | 왜 이쪽이 먼저인가 |
|---|---|---|
| `@WebMvcTest`에서 `NoSuchBeanDefinitionException`, `service bean not found` | [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md) | 슬라이스가 service를 안 올리는 것이 정상인 경우가 많다 |
| `@SpringBootTest`나 실제 앱에서는 service가 있는데 `@Transactional`만 안 먹음 | [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md) | Bean 존재 여부보다 `this.method()`/`private`/프록시 경계를 먼저 봐야 한다 |
| "`assertSame`은 맞는데 트랜잭션 동작이 이상해요" | [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md) | identity 확인과 transaction behavior 확인은 다른 테스트 질문이다 |

## 요청 흐름과 같이 붙여 보기

테스트 선택이 잘 안 되면 "실패가 요청 흐름의 어디에서 나는가"로 다시 잘라 보면 된다.

- URL 매핑, `@RequestBody`, JSON 응답이 헷갈리면 [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md)와 같이 본다.
- repository save/find, rollback, flush가 헷갈리면 [`@Transactional 기초`](./spring-transactional-basics.md)와 같이 본다.
- mock이 많아져서 테스트가 구현 세부사항에 묶이면 [`테스트 전략과 테스트 더블`](../software-engineering/testing-strategy-and-test-doubles.md)로 넘어간다.

## 더 깊이 가려면

- 슬라이스 테스트에서 컨텍스트 캐시가 어떻게 재사용되는지는 [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)에서 이어서 본다.
- "`왜 `@WebMvcTest`에서 service/repository가 안 보여요?`"가 핵심 질문이면 [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)를 먼저 본다.
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

Spring 테스트는 "앱 전체를 켤지, 웹만 켤지, JPA만 켤지, 아예 Spring을 끌지"를 먼저 고르는 문제라서, 처음에는 `@SpringBootTest` 하나로 밀기보다 슬라이스 경계를 먼저 나누는 편이 훨씬 덜 헷갈린다.
