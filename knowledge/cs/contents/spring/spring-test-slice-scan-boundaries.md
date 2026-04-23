# Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다

> 한 줄 요약: `@SpringBootTest`는 애플리케이션 실제 경계에서 시작하지만, `@WebMvcTest`와 `@DataJpaTest`는 미리 잘라 둔 slice에서 시작하므로 같은 package에 있어도 service/repository가 자동으로 보이지 않으며, custom `@Import`/`@TestConfiguration`은 그 경계를 명시적으로 바꾸는 버튼이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 **test slice scan boundary beginner primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
> - [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
> - [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)
> - [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

retrieval-anchor-keywords: test slice scan boundary, spring test slice beginner, WebMvcTest scan, WebMvcTest service not found, DataJpaTest scan, DataJpaTest service bean not found, SpringBootTest full context, test configuration boundary, TestConfiguration component scan, Import in slice test, slice vs full context, controller slice, repository slice, test slice misunderstanding

## 이 문서 다음에 보면 좋은 문서

- 테스트 컨텍스트를 얼마나 재사용할지까지 이어서 보려면 [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)으로 넘어간다.
- `@Import`, `@TestConfiguration`, security/filter 설정이 slice를 어떻게 새게 만드는지 더 깊게 보려면 [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)을 본다.
- service/controller는 뜨는데 entity/repository 쪽에서만 깨지면 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)로 넘어가 JPA 전용 경계를 따로 본다.
- `@DataJpaTest` 자체는 맞는데 flush/clear/rollback 착시가 섞이면 [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)까지 이어서 본다.

---

## 핵심 개념

테스트에서 사람들이 말하는 "scan"은 보통 두 가지를 섞어 말한다.

1. 어떤 package를 기준으로 bean/entity/repository를 찾는가
2. 어떤 종류의 bean만 후보로 허용하는가

`@SpringBootTest`와 test slice의 가장 큰 차이는 둘 다 다르다는 점이다.

| 테스트 형태 | 시작점 | 자동으로 들어오는 것 | 자동으로 빠지는 것 | 경계가 바뀌는 순간 |
|---|---|---|---|---|
| `@SpringBootTest` | 애플리케이션의 `@SpringBootApplication` / `@SpringBootConfiguration` | 보통 controller, service, repository, entity, 대부분의 auto-configuration | 테스트 전용 helper bean | `classes`, profile, exclude, test property로 앱 경계를 바꿀 때 |
| `@WebMvcTest` | MVC slice + 선택한 controller 중심 | controller, controller advice, converter, JSON/MVC 지원 bean, 일부 filter/security 지원 | service, repository, 일반 `@Component` | `@Import`, `@TestConfiguration`, custom filter/security config를 얹을 때 |
| `@DataJpaTest` | JPA slice | entity, repository, JPA infra, transaction test support | controller, service, web/security bean | `@Import`, auditing config, custom JPA scan 설정을 얹을 때 |
| slice + custom config | 원래 slice 위에 명시적으로 올린 추가 설정 | import한 bean, 또는 그 설정이 다시 scan한 bean | 여전히 full app 전체는 아님 | `@ComponentScan`, `@EnableJpaRepositories`, `@EntityScan`을 test config에 넣을 때 |

핵심은 간단하다.

- `@SpringBootTest`는 **애플리케이션 실제 시작점**에 가깝다.
- `@WebMvcTest`, `@DataJpaTest`는 **미리 잘라 둔 탐색 경계**에서 시작한다.
- custom test config는 **원래 경계를 복원하는 버튼이 아니라, 새로운 구멍을 내는 버튼**이다.

---

## 먼저 이 오해부터 버린다

| 흔한 오해 | 실제 동작 |
|---|---|
| `@WebMvcTest`도 controller와 service가 같은 package면 service를 찾는다 | 아니다. MVC slice는 service/repository를 기본 후보에서 제외한다 |
| `@DataJpaTest`는 repository가 필요하니 service도 같이 올린다 | 아니다. JPA slice는 entity/repository/JPA infra 중심이다 |
| nested `@TestConfiguration`을 붙이면 slice가 full context처럼 변한다 | 아니다. 거기서 선언한 bean만 추가된다. 단, 그 안에 `@ComponentScan`을 넣으면 이야기가 달라진다 |
| `@Import(AppConfig.class)`는 bean 하나만 더하는 안전한 동작이다 | 아니다. imported config가 다른 config나 scan을 끌고 오면 slice 경계가 생각보다 크게 넓어진다 |
| full `@SpringBootTest`에서 통과하니 slice에서도 같은 bean이 보여야 한다 | 아니다. slice는 의도적으로 빠진 영역이 있다 |

---

## `@SpringBootTest`는 왜 기준점인가

기본 `@SpringBootTest`는 보통 실제 애플리케이션과 가장 비슷한 컨텍스트를 띄운다.

- `@SpringBootApplication`이 정한 component scan 경계를 따른다
- Boot auto-configuration이 전체 애플리케이션 시나리오를 기준으로 적용된다
- controller, service, repository, entity가 한 번에 wiring될 수 있다

즉 full test에서 보이던 bean이 slice test에서 안 보이면, 보통 "package가 틀렸다"보다 먼저 **테스트 종류가 경계를 잘랐는지**를 의심해야 한다.

```java
@SpringBootTest
class OrderApplicationTest {

    @Autowired OrderController orderController;
    @Autowired OrderService orderService;
    @Autowired OrderRepository orderRepository;
}
```

이 그림은 애플리케이션 전체 wiring 검증에는 맞지만, controller 계약 하나만 보기에는 무겁다.

---

## `@WebMvcTest`는 package 전체를 다시 scan하지 않는다

`@WebMvcTest`를 처음 쓰면 가장 많이 하는 오해가 이것이다.

> "controller가 같은 패키지에 있으니 service도 같이 보이겠지"

실제로는 그렇지 않다.

`@WebMvcTest`는 "웹 계층에 필요한 후보만 남긴 테스트 컨텍스트"다.  
즉 package가 같아도 아래는 기본으로 들어오지 않는다.

- `@Service`
- `@Repository`
- 일반 `@Component`
- 데이터베이스/메시징/외부 클라이언트 wiring

반대로 이런 것은 slice 안에서 자주 남는다.

- 선택한 `@Controller`
- `@ControllerAdvice`
- `Converter`, `GenericConverter`
- `HandlerMethodArgumentResolver`
- JSON/MVC 설정
- 경우에 따라 filter/security 관련 web bean

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;

    // 직접 구현체가 자동 주입되길 기대하면 안 된다.
    @MockBean OrderService orderService;
}
```

즉 `@WebMvcTest`에서 service가 안 보이는 것은 scan 실패라기보다 **원래 slice 경계가 그렇게 설계된 것**이다.

---

## `@DataJpaTest`는 JPA 쪽만 보는 별도 경계다

`@DataJpaTest`도 full context를 반쯤 줄인 것이 아니다.

이 테스트는 보통 아래를 검증하려고 만든다.

- entity 매핑
- repository query
- JPA 설정
- 트랜잭션 안의 persistence context 동작

그래서 기본적으로 기대할 수 있는 것은 이쪽이다.

- `@Entity`
- Spring Data repository
- JPA 관련 infrastructure
- 테스트용 transaction support

반대로 기대하면 안 되는 것은 이쪽이다.

- controller
- service
- security/web layer
- 애플리케이션 전체 business wiring

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository orderRepository;

    // service는 자동으로 보이지 않는 것이 정상이다.
    // @Autowired OrderService orderService;
}
```

여기서 더 헷갈리는 지점은, `@DataJpaTest`의 "scan"은 component scan 하나로 끝나지 않는다는 점이다.  
entity discovery와 repository discovery는 JPA 전용 경계를 따르므로, 이 축이 더 궁금하면 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)로 이어서 보는 편이 빠르다.

---

## custom `@Import` / `@TestConfiguration`은 경계를 넓히기도 하고, 그냥 구멍만 뚫기도 한다

여기가 실무에서 가장 자주 오해되는 부분이다.

### 1. 좁게 bean 하나만 추가하는 경우

이런 형태는 slice의 의도를 비교적 잘 유지한다.

```java
@WebMvcTest(OrderController.class)
@Import(OrderControllerTest.TestClockConfig.class)
class OrderControllerTest {

    @TestConfiguration
    static class TestClockConfig {
        @Bean
        Clock testClock() {
            return Clock.systemUTC();
        }
    }
}
```

이 경우 `Clock`만 추가된 것이다.  
애플리케이션 전체를 다시 scan한 것이 아니다.

### 2. imported config가 다시 scan을 시작하는 경우

이때부터 slice 경계가 새기 시작한다.

```java
@WebMvcTest(OrderController.class)
@Import(AppTestConfig.class)
class OrderControllerTest {
}

@TestConfiguration
@ComponentScan("com.example.order")
class AppTestConfig {
}
```

이 설정은 helper bean 하나만 더한 게 아니라, test config가 다시 package scan을 시작한다.  
그러면 controller test에 service, repository, 다른 component가 들어오기 시작할 수 있다.

같은 문제는 JPA slice에서도 생긴다.

- `@EnableJpaRepositories`를 test config에 다시 넣는다
- `@EntityScan` 범위를 넓힌다
- 운영용 config를 통째로 `@Import`한다

이런 순간 `@DataJpaTest`는 단순 repository test가 아니라 **무슨 경계인지 설명하기 어려운 partial integration test**가 되기 쉽다.

### 3. 중요한 차이 하나

`@Import` 자체가 위험한 것이 아니라, **무엇을 import하느냐**가 중요하다.

- test support bean만 선언한 config: 비교적 안전
- 운영용 app config, broad `@ComponentScan`, 다른 infra config를 품은 config: 경계 leak 위험 큼

즉 custom config의 질문은 항상 이것이어야 한다.

> 이 설정은 bean 하나를 보강하는가, 아니면 테스트가 원래 제외하던 레이어를 다시 끌어오는가?

---

## 왜 "같은 package인데 안 보이지?"가 자꾸 나오나

full `@SpringBootTest`에 익숙하면 package 구조만 보고 이렇게 추론하기 쉽다.

```text
com.example.order
  ├── OrderController
  ├── OrderService
  └── OrderRepository
```

하지만 slice에서는 package보다 먼저 **허용된 bean 종류**가 작동한다.

- `@WebMvcTest`는 "order package 전체"가 아니라 "그중 web 관련 후보"
- `@DataJpaTest`는 "order package 전체"가 아니라 "그중 JPA 관련 후보"

즉 slice에서는 package가 맞아도 bean 종류가 다르면 제외될 수 있다.

이 점이 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)과 다른 부분이다.  
component scan 문서는 "base package 자체가 틀린 경우"를 다루고, 이 문서는 **base package가 맞아도 slice filter가 일부를 의도적으로 빼는 경우**를 다룬다.

---

## 실전 분기표

### 시나리오 1: `@WebMvcTest`에서 service 주입이 안 된다

가장 먼저 드는 결론은 "scan이 고장 났다"가 아니다.

- 정상적인 slice 동작인지 본다
- controller 계약만 보면 되는 테스트라면 mock/stub으로 유지한다
- 진짜 service wiring까지 봐야 하면 `@SpringBootTest` 또는 더 넓은 integration test로 올린다

### 시나리오 2: `@DataJpaTest`에서 auditing bean이나 converter가 없다

- repository/JPA 계약에 필요한 최소 bean만 `@Import`할지
- 그 bean이 사실 service/web/security까지 끌고 오는 운영 config인지
- 계속 import를 늘려야 하는 상황이면 full integration test가 더 맞는지

를 순서대로 본다.

### 시나리오 3: nested `@TestConfiguration`을 추가했더니 갑자기 DB bean까지 보인다

`@TestConfiguration` 자체보다 그 안의 `@ComponentScan`, `@Import`, 혹은 imported config의 하위 graph를 의심해야 한다.

### 시나리오 4: full `@SpringBootTest`는 통과하지만 slice만 깨진다

보통 slice가 부족한 것이 아니라, **검증하려는 경계와 테스트 타입이 안 맞는 것**이다.

---

## 선택 기준을 짧게 정리하면

| 지금 검증하려는 것 | 우선 선택 | 이유 |
|---|---|---|
| controller request/response 계약 | `@WebMvcTest` | web layer만 좁게 검증한다 |
| repository query/매핑/JPA 동작 | `@DataJpaTest` | JPA 경계를 빠르게 검증한다 |
| controller + service + repository + security wiring 전체 | `@SpringBootTest` | slice를 억지로 넓히는 것보다 경계가 정직하다 |
| slice에 작은 helper bean 하나 | nested `@TestConfiguration` / 좁은 `@Import` | 경계를 크게 흐리지 않고 부족분만 채운다 |
| slice에 운영용 config 여러 개를 계속 import해야 함 | 테스트 타입 재선정 | 이미 slice보다 full integration이 더 맞을 수 있다 |

---

## 꼬리질문

> Q: `@WebMvcTest`에서 service가 안 보이는 이유는 package가 달라서인가?
> 의도: slice filter와 package boundary 차이 구분 확인
> 핵심: 꼭 그렇지 않다. 같은 package여도 MVC slice가 service를 기본 후보에서 제외할 수 있다.

> Q: nested `@TestConfiguration`을 붙이면 왜 full `@SpringBootTest`가 되지 않는가?
> 의도: custom test config 역할 확인
> 핵심: 선언한 bean만 추가할 뿐이며, broad scan이나 운영 config import를 하지 않는 한 전체 앱을 다시 올리지 않는다.

> Q: `@Import`가 붙은 slice test가 언제 위험해지는가?
> 의도: boundary leak 징후 확인
> 핵심: imported config가 다른 config, broad scan, infra wiring을 같이 끌고 올 때다.

> Q: slice에 필요한 bean이 계속 늘어나면 어떻게 판단해야 하는가?
> 의도: test type 선택 기준 확인
> 핵심: 보강이 아니라 여러 레이어 wiring 검증이 목적이라면 `@SpringBootTest`가 더 정직하다.

---

## 한 줄 정리

test slice의 핵심은 "애플리케이션을 조금만 띄운다"가 아니라, **무엇을 후보로 볼지 미리 잘라 둔 경계에서 시작한다**는 데 있고, custom test config는 그 경계를 조용히 바꿀 수 있는 수동 스위치다.
