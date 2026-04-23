# Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks

> 한 줄 요약: slice test는 작게 유지될 때 가치가 있는데, `@Import`, `@TestConfiguration`, custom filter/security 설정을 무심코 얹으면 빠른 단위 계약 검증이 아니라 느리고 왜곡된 준통합 테스트가 되기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
> - [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)

retrieval-anchor-keywords: test slice leak, WebMvcTest import, TestConfiguration, slice boundary, DataJpaTest import, test context customization, webmvctest security, test support bean, context cache split

## 핵심 개념

slice test의 목적은 애플리케이션 전체를 올리지 않고, 특정 레이어 계약만 빠르게 검증하는 것이다.

하지만 아래를 무심코 추가하면 slice의 의미가 쉽게 흐려진다.

- `@Import`
- `@TestConfiguration`
- custom `SecurityFilterChain`
- custom resolver / converter / advice
- 테스트마다 다른 property / mock 조합

즉 slice test의 함정은 "부족해서 안 되는 것"만이 아니라, **너무 많이 끌어와서 무엇을 검증하는지 모호해지는 것**이다.

## 깊이 들어가기

### 1. slice는 애초에 curated context다

`@WebMvcTest`, `@DataJpaTest`, `@JsonTest` 같은 slice는 필요한 auto-configuration만 일부 올린다.

즉 slice는 단순히 Bean 수가 적은 게 아니라, **의도적으로 제외된 영역이 있는 컨텍스트**다.

그래서 문제가 생겼을 때 질문은 보통 둘 중 하나다.

- 이 Bean이 원래 slice 범위에 있어야 하는가
- 아니면 내가 slice 경계를 넓혀 버린 것인가

이걸 구분하지 않으면 테스트는 빠르게 복잡해진다.

### 2. `@Import`는 필요한 Bean만 들여오는 동시에 경계를 쉽게 새게 만든다

예를 들어 `@WebMvcTest`에서 custom argument resolver 하나가 필요해서 설정 클래스를 import했다고 해 보자.

그 설정 클래스가 아래를 함께 참조하면 문제가 커진다.

- service bean
- repository bean
- security config 전체
- 외부 클라이언트 설정

그 순간 slice는 controller 계약 검증이 아니라, 잘려 있어야 할 레이어 의존성을 억지로 끌고 들어오는 테스트가 된다.

즉 `@Import`는 강력하지만, **지원 Bean 하나만 가져오는 도구가 아니라 설정 그래프 전체를 당겨오는 지점**이 될 수 있다.

### 3. `@TestConfiguration`은 좁고 안정적으로 유지해야 한다

`@TestConfiguration`은 slice에 부족한 테스트 전용 Bean을 보강할 때 유용하다.

하지만 아래 패턴은 위험하다.

- component scan 사용
- 환경마다 달라지는 동적 Bean 생성
- 테스트마다 조금씩 다른 nested config 정의

이런 구성이 많아질수록 context cache가 잘게 쪼개지고, 테스트 의미도 흐려진다.

좋은 방향은 보통 이렇다.

- 테스트 지원 Bean만 최소로 둔다
- 외부 시스템 stub은 명시적으로 만든다
- 재사용 가능한 구성은 가능한 한 안정적으로 공유한다

### 4. `@WebMvcTest`에서 security와 filter는 "포함 여부"를 먼저 정해야 한다

웹 슬라이스에서 자주 생기는 혼란은 "보안이 왜 붙지?" 혹은 "보안이 왜 빠지지?"다.

핵심은 테스트 계약을 먼저 정하는 것이다.

- controller serialization / validation만 볼 것인가
- 인증/인가 정책도 계약에 포함할 것인가

전자는 `@WithMockUser` 없이 최소 MVC 경계만 검증할 수도 있다.
후자는 최소한의 `SecurityFilterChain`이나 필요한 설정만 가져와야 한다.

중요한 건 무작정 필터를 끄거나 전부 켜는 게 아니라, **무엇을 이 테스트에서 보려는지 명시하는 것**이다.

### 5. `@DataJpaTest`도 slice leakage가 생긴다

JPA 슬라이스는 repository와 매핑 검증에 좋지만, 다음 요소가 있으면 경계가 흔들릴 수 있다.

- auditing
- custom converter
- entity listener
- database-specific function
- migration script 전제

이 경우는 필요한 테스트 지원을 좁게 import할지, 아니면 Testcontainers를 붙인 더 넓은 통합 테스트로 올릴지 선택해야 한다.

즉 slice 부족분을 끝없이 때우는 것보다, **애초에 검증 경계를 다시 정하는 것**이 더 낫다.

### 6. slice boundary leak는 속도뿐 아니라 신뢰도 문제다

경계가 애매해지면 다음이 동시에 나빠진다.

- 테스트가 느려진다
- 실패 원인이 불분명해진다
- 리팩터링 시 깨지는 범위가 넓어진다
- 운영에서 필요한 필터/설정이 테스트에선 빠지기도 한다

즉 "일단 되게 만들자" 식 import/test config 누적은 생산성 문제가 아니라, **테스트 계약을 약하게 만드는 구조적 문제**다.

## 실전 시나리오

### 시나리오 1: `@WebMvcTest`에 설정 하나 import했더니 갑자기 DB Bean을 찾는다

import한 설정이 service/repository/infra 설정을 함께 끌고 들어왔을 가능성이 높다.

이건 controller slice가 아니라 애매한 partial integration test로 변한 신호다.

### 시나리오 2: `@WebMvcTest`는 통과하는데 실제 서비스에서는 보안 버그가 난다

테스트에서 필터 체인을 완전히 빼 버렸거나, 필요한 security 설정이 누락됐을 수 있다.

slice에서 보안을 제외했다면 의도적으로 제외한 것인지 문서화해야 한다.

### 시나리오 3: `@DataJpaTest`가 auditing bean이 없다고 깨진다

필요한 auditing 지원만 좁게 import할지, 아예 더 넓은 통합 테스트로 올릴지 판단해야 한다.

무심코 애플리케이션 전체 설정을 가져오면 slice가 쉽게 무너진다.

### 시나리오 4: 테스트마다 다른 `@TestConfiguration` 때문에 갑자기 전체 테스트가 느려진다

설정이 조금씩 달라져 context cache가 쪼개졌을 가능성이 높다.

이건 한 테스트의 로직 문제가 아니라 테스트 지원 구성이 불안정하다는 신호다.

## 코드로 보기

### 필요한 지원 Bean만 좁게 추가

```java
@WebMvcTest(OrderController.class)
@Import(OrderControllerTest.WebTestSupportConfig.class)
class OrderControllerTest {

    @TestConfiguration
    static class WebTestSupportConfig {
        @Bean
        Clock testClock() {
            return Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
        }
    }
}
```

### security를 계약에 포함시키는 최소 예

```java
@WebMvcTest(AdminController.class)
@Import(AdminWebSecurityTestConfig.class)
class AdminControllerTest {

    @Test
    @WithMockUser(roles = "ADMIN")
    void 관리자만_접근한다() {
    }
}
```

### JPA slice에서 필요한 지원만 보강

```java
@DataJpaTest
@Import(JpaAuditingTestConfig.class)
class OrderRepositoryTest {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 순수 slice 유지 | 빠르고 실패 원인이 좁다 | 실제 운영 설정 일부는 못 본다 | 레이어 계약 검증 |
| 최소 `@Import` / `@TestConfiguration` | 부족한 지원만 보강할 수 있다 | 경계가 새기 시작하면 금방 복잡해진다 | 명확한 보조 Bean이 필요할 때 |
| 많은 설정을 import한 slice | 당장 테스트를 통과시키기 쉽다 | 느리고 왜곡된 준통합 테스트가 된다 | 가급적 피한다 |
| `@SpringBootTest` / Testcontainers로 승격 | 실제와 가깝다 | 느리고 비싸다 | slice보다 넓은 wiring 검증이 진짜 필요할 때 |

핵심은 slice test를 "작은 SpringBootTest"가 아니라, **제외된 영역까지 포함해 경계가 명확한 계약 테스트**로 보는 것이다.

## 꼬리질문

> Q: `@Import`가 slice test에서 특히 위험한 이유는 무엇인가?
> 의도: 설정 그래프 확장 위험 이해 확인
> 핵심: 필요한 Bean 하나가 아니라 관련 설정 그래프 전체를 끌고 들어올 수 있기 때문이다.

> Q: `@TestConfiguration`은 어떤 방향으로 유지하는 것이 좋은가?
> 의도: 테스트 지원 구성 안정성 확인
> 핵심: 좁고 재사용 가능하며, component scan 없이 명시적인 지원 Bean만 둔다.

> Q: `@WebMvcTest`에서 security를 끄는 것과 포함하는 것 중 무엇이 정답인가?
> 의도: 테스트 계약 사고 확인
> 핵심: 정답은 없고, 이 테스트가 보안까지 계약으로 볼지 먼저 정해야 한다.

> Q: slice boundary leak가 단순 성능 문제만은 아닌 이유는 무엇인가?
> 의도: 테스트 신뢰도 관점 확인
> 핵심: 무엇을 검증하는지 모호해져 실패 원인과 리팩터링 비용도 나빠진다.

## 한 줄 정리

slice test의 품질은 얼마나 많이 mock했는지가 아니라, `@Import`와 `@TestConfiguration`이 그 slice의 경계를 얼마나 조용히 새게 만들지 통제했는지에 달려 있다.
