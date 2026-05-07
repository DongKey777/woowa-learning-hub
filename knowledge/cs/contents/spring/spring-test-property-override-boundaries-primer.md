---
schema_version: 3
title: Spring Test Property Override Boundaries Primer
concept_id: spring/test-property-override-boundaries-primer
canonical: true
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 75
review_feedback_tags:
- test-property-override
- boundaries
- springboottest-properties
- testpropertysource
aliases:
- @SpringBootTest properties
- @TestPropertySource
- @DynamicPropertySource
- test property override
- context cache property key
- dynamic test property
intents:
- comparison
- troubleshooting
linked_paths:
- contents/spring/spring-property-source-precedence-quick-guide.md
- contents/spring/spring-dynamicpropertysource-vs-serviceconnection-primer.md
- contents/spring/spring-test-context-cache-split-triage-guide.md
- contents/spring/spring-test-slices-context-caching.md
- contents/spring/spring-multidocument-yaml-on-profile-primer.md
confusable_with:
- spring/property-source-precedence-quick-guide
- spring/dynamicpropertysource-vs-serviceconnection-primer
- spring/test-context-cache-split-triage-guide
expected_queries:
- @SpringBootTest(properties) @TestPropertySource @DynamicPropertySource 차이는 뭐야?
- 테스트에서 설정 값을 덮어쓸 때 어떤 도구를 골라야 해?
- DynamicPropertySource는 실행 중 계산되는 값이라 context cache에 어떤 영향을 줘?
- test property override가 Spring test context cache를 갈라놓을 수 있어?
contextual_chunk_prefix: |
  이 문서는 Spring test property override를 @SpringBootTest(properties) 상수,
  @TestPropertySource 공유 설정 묶음, @DynamicPropertySource 실행 중 계산되는 값으로 나누는
  chooser다. property precedence와 context cache key 영향을 함께 설명한다.
---
# Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache

> 한 줄 요약: 셋 다 테스트에서 설정을 덮어쓰는 도구지만, `properties`는 "이 테스트 클래스에 바로 적는 상수", `@TestPropertySource`는 "공유 가능한 테스트용 설정 묶음", `@DynamicPropertySource`는 "실행 중에 계산되는 값"으로 나누면 대부분의 혼란이 정리된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, 그리고 context cache 영향을 한 번에 가르는 **beginner testing primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [Spring `@ActiveProfiles` vs test override primer: `application-test.yml`, `@TestPropertySource`, annotation `properties`](./spring-activeprofiles-vs-test-overrides-primer.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)
- [Spring `@DynamicPropertySource` vs `@ServiceConnection`: Testcontainers에서 언제 수동 property wiring이 아직 필요한가](./spring-dynamicpropertysource-vs-serviceconnection-primer.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)

retrieval-anchor-keywords: spring test property override, springboottest properties precedence, @springboottest(properties), properties attribute on your tests, testpropertysource precedence, testpropertysource file vs inline, dynamicpropertysource precedence, dynamicpropertysource testcontainers, dynamicpropertysource dirtiescontext, spring test property source cache, spring context cache property override, test property cache split, test property source exact strings cache key, test property override beginner, spring test configuration beginner

## 핵심 개념

초보자 기준으로는 세 annotation을 "우선순위 암기"보다 **값이 어디서 오느냐**로 먼저 나누는 편이 쉽다.

```text
1. @SpringBootTest(properties = ...) = 이 테스트 클래스 위에 포스트잇으로 상수 하나 붙이기
2. @TestPropertySource = 테스트용 설정 파일이나 설정 묶음을 올리기
3. @DynamicPropertySource = 실행하고 나서 알게 되는 값을 꽂기
4. context cache = 같은 레시피면 재사용, 레시피가 달라지면 새 컨텍스트
```

즉 같은 key를 덮어쓴다는 점은 비슷하지만, 경계는 다르다.

- `@SpringBootTest(properties)`는 가장 짧은 local override다.
- `@TestPropertySource`는 파일 기반 또는 여러 key를 묶는 공유 override다.
- `@DynamicPropertySource`는 container port, 임시 URL처럼 런타임에 계산되는 override다.

이 문서에서는 `@SpringBootTest(properties)`를 중심으로 설명하지만, 같은 `properties` 속성은 `@WebMvcTest`, `@DataJpaTest` 같은 slice test에도 같은 감각으로 적용된다.

---

## 1. 먼저 이 표로 고른다

| 질문 | 먼저 고를 도구 | 이유 |
|---|---|---|
| 이 클래스에서만 고정값 1~2개 바꾸면 되나? | `@SpringBootTest(properties)` | 가장 짧고 읽기 쉽다 |
| 여러 key를 한 번에 묶거나 파일로 공유해야 하나? | `@TestPropertySource` | inline 묶음과 파일 위치 둘 다 지원한다 |
| 포트, URL, 비밀번호처럼 실행 후에 값이 정해지나? | `@DynamicPropertySource` | `Supplier`로 런타임 값을 넣을 수 있다 |
| 캐시 재사용까지 신경 써야 하나? | 세 도구 모두 가능, 하지만 구성을 흔들지 말아야 한다 | 설정이 달라지면 새 컨텍스트를 만들 가능성이 커진다 |

한 줄로 줄이면 이렇게 기억하면 된다.

- 상수 몇 개: `properties`
- 테스트 설정 묶음: `@TestPropertySource`
- 런타임 값: `@DynamicPropertySource`

---

## 2. 세 annotation을 한 장 표로 분리

| 도구 | 값의 출처 | 잘 맞는 상황 | 덜 맞는 상황 | context cache 감각 |
|---|---|---|---|---|
| `@SpringBootTest(properties = ...)` | annotation 안의 문자열 상수 | 테스트 클래스 하나에서 flag, timeout, base URL 같은 고정값 몇 개를 바꿀 때 | key가 많거나 여러 클래스가 같은 설정을 공유해야 할 때 | 테스트마다 `properties` 구성이 달라지기 시작하면 재사용 기대가 떨어진다 |
| `@TestPropertySource` | properties 파일 위치 또는 inline properties 묶음 | 여러 key를 같이 관리하거나 같은 테스트 설정을 재사용할 때 | 실행 시점에 포트/URL이 바뀌는 값 | 파일/inline 선언이 같을수록 재사용이 쉽다 |
| `@DynamicPropertySource` | static method가 등록한 `Supplier` 값 | Testcontainers, 임베디드 서버, 임시 포트처럼 런타임에 값이 정해질 때 | 고정값 몇 개를 억지로 동적으로 만들 때 | dynamic property 구성도 cache key에 영향을 주며, base class 상속 구조에서는 `@DirtiesContext`가 필요할 수 있다 |

핵심 차이는 "누가 이 값을 알고 있느냐"다.

- 컴파일할 때 이미 아는 값이면 `properties`
- 테스트 자원 파일로 정리할 값이면 `@TestPropertySource`
- 테스트가 시작돼야 알 수 있는 값이면 `@DynamicPropertySource`

---

## 3. 같은 목적을 서로 다른 방식으로 해 보기

### 1. 테스트 클래스 하나에서 고정 flag만 끄기

```java
@SpringBootTest(properties = "spring.cache.type=none")
class OrderServiceTest {
}
```

이 경우는 `properties`가 가장 읽기 쉽다.
"이 테스트만 캐시를 끄고 싶다"가 annotation 한 줄에 바로 보이기 때문이다.

### 2. 여러 key를 묶어 재사용하기

```java
@SpringBootTest
@TestPropertySource(locations = "/partner-client-test.properties")
class PartnerClientTest {
}
```

또는 inline으로 여러 개를 같이 둘 수도 있다.

```java
@SpringBootTest
@TestPropertySource(properties = {
        "partner.base-url = http://localhost:8089",
        "partner.timeout = 2s",
        "partner.retry.enabled = false"
})
class PartnerClientTest {
}
```

이 경우는 "테스트용 설정 묶음"이라는 의도가 더 잘 드러난다.
특히 key가 많아질수록 `properties` 속성 하나에 몰아넣는 것보다 `@TestPropertySource` 쪽이 관리하기 쉽다.

### 3. 컨테이너 포트를 datasource URL에 연결하기

```java
@Testcontainers
@SpringBootTest
class MemberRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

이 경우는 테스트가 뜨기 전에는 실제 포트를 모르므로 `@DynamicPropertySource`가 맞다.
고정 문자열을 억지로 맞추는 문제가 아니라, **실행하고 나서 알게 되는 값**을 넣는 문제이기 때문이다.

---

## 4. 우선순위는 이 정도만 기억하면 충분하다

beginner 기준으로는 아래 mental model이면 대부분의 충돌을 빠르게 가를 수 있다.

```text
application.yml / profile / env var / command-line
        < test annotation properties
        < @TestPropertySource
        < @DynamicPropertySource
```

즉 셋 다 일반 애플리케이션 설정보다 위에 올라오는 **테스트 전용 override**다.

여기서 자주 놓치는 두 가지는 따로 기억하면 좋다.

| 착시 | 실제로는 |
|---|---|
| `@SpringBootTest(properties)`와 `@TestPropertySource`는 완전히 같은 도구다 | 아니다. 둘 다 test override지만, 하나는 클래스 로컬 상수, 다른 하나는 파일/묶음 지향이다 |
| `@TestPropertySource`와 `@DynamicPropertySource`는 아무거나 써도 된다 | 아니다. `@DynamicPropertySource`는 런타임 값이 필요할 때 쓰는 도구다 |

또 하나 더 중요하다.

- `@TestPropertySource(properties = ...)`의 inline 값은 그 annotation의 `locations` 파일 값보다 우선한다.
- `@DynamicPropertySource`는 `@TestPropertySource`보다 더 높은 우선순위에서 값을 덮을 수 있다.

그래서 같은 key를 여러 곳에 적어 놓고 "왜 파일 값이 안 먹지?"라고 느끼면, 우선 file/env보다 **더 위에 있는 test override가 있는지**부터 보면 된다.

---

## 5. context cache에서는 무엇이 갈리나

Spring TestContext는 "완전히 같은 설정 레시피"일 때 컨텍스트를 재사용한다.
즉 property override 방식이 달라지면 테스트 자체는 비슷해 보여도 새 컨텍스트가 뜰 수 있다.

### 1. `@TestPropertySource`는 문자열 모양까지 cache에 영향을 준다

이 부분은 beginner가 가장 쉽게 놓친다.

```java
@TestPropertySource(properties = "timezone = GMT")
```

```java
@TestPropertySource(properties = "timezone=GMT")
```

논리상 같은 뜻처럼 보여도, Spring 문서 기준으로는 **exact string**이 context cache key 판단에 사용된다.
그래서 팀 안에서 공백 스타일이 섞이면 불필요하게 캐시가 쪼개질 수 있다.

### 2. `properties`를 테스트마다 조금씩 바꾸면 재사용이 줄어든다

```java
@SpringBootTest(properties = "app.feature-x.enabled=false")
class ATest {
}

@SpringBootTest(properties = "app.feature-x.enabled=true")
class BTest {
}
```

둘은 테스트 의도는 비슷해 보여도, 컨텍스트 입장에서는 같은 레시피가 아니다.
이런 클래스가 많아질수록 "값 하나만 다른 full context"가 여러 벌 생기기 쉽다.

그래서 고정값 몇 개를 건드릴 때도 질문이 필요하다.

- 정말 이 클래스만 달라야 하나?
- 아니면 공통 테스트 설정으로 묶는 편이 나은가?

### 3. `@DynamicPropertySource`는 "메서드는 같지만 값은 달라지는" 상황이 함정이다

특히 base test class에 `@DynamicPropertySource`를 두고, 하위 클래스마다 다른 컨테이너 값을 쓰는 구조에서 헷갈리기 쉽다.

```java
abstract class BaseDatabaseTest {

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        // 하위 클래스마다 다른 컨테이너 값을 쓰는 상황을 가정
    }
}
```

Spring 문서도 이 경우를 따로 경고한다.
상위 클래스의 dynamic property가 하위 클래스마다 다른 값을 만들어야 한다면, 각 하위 클래스가 올바른 컨텍스트를 받도록 `@DirtiesContext`가 필요할 수 있다.

즉 `@DynamicPropertySource`는 단순히 "동적이라서 편하다"가 아니라, **캐시와 상속까지 같이 생각해야 하는 도구**다.

---

## 6. 흔한 오해

### 1. 값만 덮어쓰면 되니 늘 `@DynamicPropertySource`를 쓰면 된다

아니다. 고정값이라면 `properties`나 `@TestPropertySource`가 더 단순하고 읽기 쉽다.

### 2. `@TestPropertySource`는 파일 전용이다

아니다. `locations` 파일도 되고 `properties` inline도 된다.

### 3. `@SpringBootTest(properties)`는 작으니 cache에 거의 영향이 없다

아니다. 테스트 클래스마다 구성이 달라지면 컨텍스트 재사용이 어려워질 수 있다.

### 4. Testcontainers를 쓰면 무조건 `@DirtiesContext`도 같이 붙여야 한다

그건 아니다. 다만 같은 상위 dynamic property 구성을 상속하면서 실제 값이 하위 클래스마다 달라지는 구조면 `@DirtiesContext`가 필요할 수 있다.

---

## 7. 30초 선택 가이드

1. 이 테스트 클래스에서만 고정값 1~2개 바꾸면 되면 `@SpringBootTest(properties)`부터 본다.
2. 여러 key를 같이 쓰거나 파일로 공유해야 하면 `@TestPropertySource`로 올린다.
3. 포트, URL, 자격 증명처럼 실행 후에 값이 정해지면 `@DynamicPropertySource`를 쓴다.
4. 테스트가 느려졌다면 값 그 자체보다 "테스트마다 다른 override 조합이 cache를 쪼갰는가"를 본다.
5. base class의 `@DynamicPropertySource`를 하위 클래스가 서로 다른 값으로 공유한다면 `@DirtiesContext` 필요 여부를 점검한다.

---

## 한 줄 정리

`@SpringBootTest(properties)`는 "이 클래스의 고정 메모", `@TestPropertySource`는 "공유 가능한 테스트 설정 묶음", `@DynamicPropertySource`는 "실행 후에 채워 넣는 값"으로 보면 되고, 셋 중 무엇을 택하든 **context cache가 같은 레시피를 보는지**까지 같이 생각해야 테스트 속도와 안정성이 유지된다.
