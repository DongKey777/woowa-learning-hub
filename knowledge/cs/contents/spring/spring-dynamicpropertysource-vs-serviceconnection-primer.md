---
schema_version: 3
title: Spring DynamicPropertySource vs ServiceConnection Primer
concept_id: spring/dynamicpropertysource-vs-serviceconnection-primer
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 86
review_feedback_tags:
- dynamicpropertysource-vs-serviceconnection
- testcontainers-serviceconnection
- boot-testcontainers-property
- wiring
aliases:
- DynamicPropertySource vs ServiceConnection
- Testcontainers ServiceConnection
- Spring Boot Testcontainers property wiring
- ConnectionDetails
- GenericContainer service connection
- custom app property Testcontainers
- manual property wiring
intents:
- comparison
- definition
linked_paths:
- contents/spring/spring-testcontainers-boundary-strategy.md
- contents/spring/spring-test-property-override-boundaries-primer.md
- contents/spring/spring-testing-basics.md
- contents/spring/spring-boot-autoconfiguration-basics.md
expected_queries:
- @DynamicPropertySource와 @ServiceConnection은 Testcontainers에서 어떻게 달라?
- Spring Boot가 아는 DB나 Redis container는 @ServiceConnection만 쓰면 돼?
- custom app property에 container URL을 넣어야 하면 DynamicPropertySource가 필요한 이유는?
- GenericContainer에서는 ServiceConnection name과 manual property wiring 중 무엇을 골라?
contextual_chunk_prefix: |
  이 문서는 Testcontainers에서 @ServiceConnection과 @DynamicPropertySource의
  경계를 beginner 관점에서 비교한다. Boot auto-configuration이 소비하는
  ConnectionDetails, standard service connection, GenericContainer name hint,
  custom app property key/value 수동 wiring을 구분한다.
---
# Spring `@DynamicPropertySource` vs `@ServiceConnection`: Testcontainers에서 언제 수동 property wiring이 아직 필요한가

> 한 줄 요약: `@ServiceConnection`은 "Spring Boot가 아는 서비스 연결"을 자동으로 붙여 주는 더 짧은 방법이고, `@DynamicPropertySource`는 "내가 직접 어떤 key에 어떤 값을 넣을지"를 정하는 더 범용적인 방법이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Testcontainers를 쓸 때 `@DynamicPropertySource`와 `@ServiceConnection`의 경계를 beginner가 빠르게 고르는 **testing bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)
> - [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
> - [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](./spring-testing-basics.md)
> - [Spring Boot 자동 구성 기초: starter, 조건 평가, 내 코드와 프레임워크 코드의 경계](./spring-boot-autoconfiguration-basics.md)
> - 공식 기준: [Spring Boot Testcontainers - Service Connections / Dynamic Properties](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)
> - 공식 기준: [Spring Framework Testing - Dynamic Property Sources](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/dynamic-property-sources.html)

retrieval-anchor-keywords: dynamicpropertysource vs serviceconnection, spring service connection beginner, testcontainers service connection, spring boot testcontainers property wiring, manual property wiring still necessary, service connection vs dynamic property source, jdbcconnectiondetails, connection details override, genericcontainer service connection name, custom app property testcontainers, spring boot 3.1 service connection, spring dynamicpropertysource vs serviceconnection primer basics, spring dynamicpropertysource vs serviceconnection primer beginner, spring dynamicpropertysource vs serviceconnection primer intro, spring basics

## 핵심 개념

초보자 기준으로는 둘의 차이를 "누가 연결 정보를 해석하느냐"로 보면 가장 덜 헷갈린다.

```text
@ServiceConnection
= Spring Boot가 컨테이너를 보고 알아서 연결 정보 bean을 만든다

@DynamicPropertySource
= 내가 property key를 직접 적고 값을 직접 연결한다
```

그래서 첫 질문은 이것이다.

- 내 테스트 대상이 **Spring Boot가 이미 아는 DB/Redis/Kafka 같은 서비스**인가?
- 아니면 **내 앱의 custom property**까지 내가 직접 넣어야 하는가?

이 질문으로 대부분 갈린다.

---

## 1. 먼저 이 표로 고른다

| 질문 | 먼저 고를 것 | 이유 |
|---|---|---|
| Postgres, Redis, Kafka처럼 Boot가 잘 아는 서비스인가? | `@ServiceConnection` | boilerplate가 적고 자동 구성과 잘 맞는다 |
| 컨테이너 주소를 `app.partner.base-url` 같은 custom key에 넣어야 하나? | `@DynamicPropertySource` | 어떤 property key에 넣을지 직접 지정해야 한다 |
| 같은 컨테이너에서 JDBC URL 말고 bucket, topic, tenant id도 같이 넣어야 하나? | 둘 다 함께 | 연결 정보는 자동, 앱 고유 설정은 수동 |
| Boot auto-configuration이 아니라 내가 직접 만든 client bean이 `@Value`를 읽나? | `@DynamicPropertySource` 가능성이 큼 | `@ServiceConnection`은 connection details를 소비하는 auto-config가 있어야 빛난다 |
| `GenericContainer`라서 서비스 종류를 Boot가 바로 못 알아보나? | `@ServiceConnection(name=...)` 또는 `@DynamicPropertySource` | 자동 힌트가 필요하거나 아예 수동 연결이 더 단순할 수 있다 |

한 줄로 줄이면 이렇다.

- **Boot가 아는 표준 연결**: `@ServiceConnection`
- **내가 key를 직접 정해야 하는 연결**: `@DynamicPropertySource`

---

## 2. 둘을 한 장 표로 비교

| 항목 | `@ServiceConnection` | `@DynamicPropertySource` |
|---|---|---|
| mental model | "컨테이너를 서비스로 등록" | "property key/value를 수동 주입" |
| 주된 강점 | 코드가 짧다 | 범용성이 높다 |
| 잘 맞는 상황 | Boot auto-config가 소비하는 DB, Redis, Kafka, Neo4j 등 | custom URL, feature flag, bucket 이름, topic 이름, 임시 토큰 등 |
| 내가 적는 것 | 보통 annotation 하나 | property key 문자열과 값 supplier |
| 의존하는 것 | 해당 기술의 `ConnectionDetails`를 Boot가 지원해야 함 | Spring TestContext만 있으면 됨 |
| 흔한 한계 | custom app property까지 자동으로 넣어주지 않는다 | boilerplate가 늘고 오타 여지가 있다 |

여기서 중요한 포인트 하나:

`@ServiceConnection`은 본질적으로 **property를 대신 써 주는 기능**이라기보다, Boot auto-configuration이 읽는 **connection details bean**을 만들어 주는 기능에 가깝다.

즉 아래 둘은 겉으로 비슷해 보여도 사고방식이 다르다.

- `spring.datasource.url=...`를 내가 넣는다
- DataSource가 쓸 연결 정보를 Boot가 bean으로 만든다

---

## 3. `@ServiceConnection`이 잘 맞는 가장 쉬운 경우

PostgreSQL 같은 표준 DB를 붙이는 테스트라면 보통 `@ServiceConnection`이 가장 읽기 쉽다.

```java
@Testcontainers
@SpringBootTest
class MemberRepositoryTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16");
}
```

이 경우 beginner가 얻는 이점은 단순하다.

- `spring.datasource.url`
- `spring.datasource.username`
- `spring.datasource.password`

이런 key를 직접 다 적지 않아도 된다.

왜냐하면 Spring Boot가 container 정보를 보고 적절한 `ConnectionDetails`를 만들고, 관련 auto-configuration이 그 값을 사용하기 때문이다.

즉 "DB 연결" 자체가 목적이면 `@ServiceConnection`이 더 짧고 의도가 바로 보인다.

---

## 4. `@DynamicPropertySource`가 아직 필요한 대표 상황

### 1. custom app property를 넣어야 할 때

컨테이너가 떠도, 내 앱이 읽는 key가 Boot 표준 연결 key가 아닐 수 있다.

예를 들어 애플리케이션 코드가 이런 설정을 읽는다고 하자.

```text
app.payment.base-url
```

이 값은 `JdbcConnectionDetails` 같은 자동 연결 대상이 아니다.
그래서 직접 주입해야 한다.

```java
@Testcontainers
@SpringBootTest
class PaymentClientTest {

    @Container
    static GenericContainer<?> fakePayment =
            new GenericContainer<>("wiremock/wiremock:3.5.2")
                    .withExposedPorts(8080);

    @DynamicPropertySource
    static void paymentProperties(DynamicPropertyRegistry registry) {
        registry.add(
                "app.payment.base-url",
                () -> "http://" + fakePayment.getHost() + ":" + fakePayment.getMappedPort(8080)
        );
    }
}
```

이때 핵심은 "DB가 아니라 URL 문자열을 내 설정 key에 꽂는 문제"라는 점이다.
이런 경우는 `@ServiceConnection`보다 `@DynamicPropertySource`가 더 직접적이다.

### 2. Boot가 connection details를 만들어 주지 않는 경우

`@ServiceConnection`은 Spring Boot가 지원하는 서비스 연결일 때 가장 편하다.
반대로 지원 대상이 아니면 자동 연결이 되지 않는다.

이때는 보통 두 갈래다.

- service name 힌트만 주면 되는 경우: `@ServiceConnection(name = "...")`
- 아예 내 property key를 직접 넣는 편이 더 분명한 경우: `@DynamicPropertySource`

### 3. 연결 정보 말고 추가 설정도 같이 필요할 때

예를 들어 PostgreSQL 연결 자체는 자동으로 되더라도, 앱이 아래 같은 값을 따로 요구할 수 있다.

- `app.batch.schema`
- `app.storage.bucket`
- `app.kafka.order-topic`

이 값들은 서비스 연결 bean만으로는 해결되지 않는다.
그래서 실제 테스트에서는 두 방식을 함께 쓰는 경우가 많다.

## 4. `@DynamicPropertySource`가 아직 필요한 대표 상황 (계속 2)

```java
@Testcontainers
@SpringBootTest
class OrderFlowIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void appProperties(DynamicPropertyRegistry registry) {
        registry.add("app.batch.schema", () -> "order_test");
    }
}
```

### 4. 내 코드가 auto-config 대신 property를 직접 읽는 경우

애플리케이션이 `@ConfigurationProperties`, `@Value`, 수동 `WebClient` bean 설정으로 값을 직접 읽는다면, Boot의 service connection 자동 연결만으로는 원하는 곳까지 전달되지 않을 수 있다.

이때는 질문을 바꿔야 한다.

```text
내 클라이언트가 무엇을 읽는가?
```

- Boot connection details를 읽는 auto-config인가
- 아니면 내가 만든 custom property인가

두 번째라면 `@DynamicPropertySource`가 필요할 가능성이 크다.

---

## 5. 둘을 같이 쓰는 패턴이 오히려 정상이다

beginner가 자주 하는 오해는 이것이다.

```text
@ServiceConnection을 쓰면 DynamicPropertySource는 이제 완전히 안 쓴다
```

아니다. 실제로는 역할이 다르다.

- `@ServiceConnection`: 표준 서비스 연결 자동화
- `@DynamicPropertySource`: 그 밖의 런타임 설정 연결

그래서 아래 조합은 아주 흔하다.

| 상황 | 선택 |
|---|---|
| Postgres datasource만 필요 | `@ServiceConnection`만 |
| Redis 연결 + `app.cache.prefix` custom key 필요 | 둘 다 |
| Mock HTTP 서버 URL을 `app.partner.base-url`에 넣기 | `@DynamicPropertySource` 중심 |
| `GenericContainer` 기반 특수 서비스 | 상황 따라 `name` 힌트 또는 수동 property wiring |

---

## 6. `GenericContainer`에서 자주 헷갈리는 점

Spring Boot 공식 문서 기준으로 `GenericContainer`는 서비스 종류를 타입만 보고 바로 추론하기 어렵다.
특히 `@Bean` 메서드로 선언하면 image name을 조기에 확인하지 못하는 경우가 있어 `@ServiceConnection(name = "redis")` 같은 힌트가 필요할 수 있다.

즉 beginner 관점에서는 이렇게 기억하면 안전하다.

- `PostgreSQLContainer`, `Neo4jContainer`처럼 **타입이 분명한 컨테이너**는 `@ServiceConnection`이 잘 맞는다.
- `GenericContainer`는 자동 추론이 약할 수 있어 `name` 힌트가 필요하다.
- 그래도 내 앱의 custom property를 넣는 문제는 여전히 `@DynamicPropertySource` 쪽이다.

---

## 7. 흔한 오해

### 1. `@ServiceConnection`은 `@DynamicPropertySource`의 완전한 상위호환이다

아니다. 더 짧은 경우가 많지만, 범용성은 `@DynamicPropertySource`가 더 크다.

### 2. Testcontainers를 쓰면 항상 `@DynamicPropertySource`를 직접 작성해야 한다

아니다. Boot가 아는 서비스면 `@ServiceConnection`만으로 충분한 경우가 많다.

### 3. `@ServiceConnection`이 custom app property도 자동으로 채워 준다

아니다. 보통은 auto-configuration이 소비하는 연결 정보까지만 자동화한다.

### 4. 둘 중 하나만 골라야 한다

아니다. 표준 연결은 자동으로, 앱 고유 key는 수동으로 같이 쓰는 것이 자연스럽다.

---

## 8. 빠른 결정 규칙

1. 먼저 "이 값이 Boot 표준 서비스 연결인가, 내 앱 custom property인가"를 구분한다.
2. 표준 서비스 연결이면 `@ServiceConnection`부터 본다.
3. property key를 내가 직접 적어야 하면 `@DynamicPropertySource`를 쓴다.
4. DB/Redis 연결은 자동인데 추가 URL, bucket, topic, schema가 필요하면 둘을 함께 쓴다.
5. `GenericContainer`를 쓰는데 Boot가 서비스 종류를 모를 수 있으면 `name` 힌트 필요 여부를 점검한다.

---

## 꼬리질문

> Q: PostgreSQLContainer를 쓰는데 datasource key를 직접 안 적어도 되는 이유는?
> 의도: service connection의 역할 이해 확인
> 핵심: Boot가 connection details를 만들어 관련 auto-configuration에 전달하기 때문이다.

> Q: WireMock 컨테이너 주소를 `app.partner.base-url`에 넣어야 하면 무엇을 쓰나?
> 의도: custom property와 표준 연결 구분 확인
> 핵심: `@DynamicPropertySource`로 key를 직접 연결하는 편이 맞다.

> Q: `@ServiceConnection`을 썼는데도 `@DynamicPropertySource`를 같이 쓰는 이유는?
> 의도: 둘의 보완 관계 이해 확인
> 핵심: 표준 연결 자동화와 앱 고유 설정 주입은 별개이기 때문이다.

## 한 줄 정리

`@ServiceConnection`은 "Boot가 아는 서비스 연결을 자동으로 붙이는 도구", `@DynamicPropertySource`는 "내가 원하는 property key에 런타임 값을 직접 꽂는 도구"라서, **표준 연결은 자동으로 줄이고 custom 설정은 수동으로 보완한다**고 기억하면 된다.
