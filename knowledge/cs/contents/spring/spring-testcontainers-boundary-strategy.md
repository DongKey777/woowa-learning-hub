# Spring Testcontainers Boundary Strategy

> 한 줄 요약: Testcontainers는 "실제와 비슷한 테스트"를 쉽게 만들지만, 어떤 경계까지 컨테이너로 올리고 어떤 부분은 slice/mock으로 남길지 결정해야 테스트가 느려지지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
> - [Spring `@DynamicPropertySource` vs `@ServiceConnection`: Testcontainers에서 언제 수동 property wiring이 아직 필요한가](./spring-dynamicpropertysource-vs-serviceconnection-primer.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

retrieval-anchor-keywords: Testcontainers, integration test, boundary strategy, docker container, ephemeral dependency, reusable container, slice test, full integration test, dynamic property source

## 핵심 개념

Testcontainers는 테스트에서 외부 의존성을 실제에 가깝게 띄워 주는 도구다.

좋은 점은 분명하다.

- DB, Kafka, Redis 같은 의존성을 실제처럼 다룰 수 있다
- 로컬/CI 환경 차이를 줄일 수 있다
- "내 코드만 되는 테스트"를 줄일 수 있다

하지만 컨테이너를 너무 많이 올리면 테스트는 금방 느려진다.

그래서 중요한 질문은 "Testcontainers를 쓸까 말까"가 아니라, **어떤 경계까지 containerized integration으로 검증할까**다.

## 깊이 들어가기

### 1. Testcontainers는 외부 의존성을 현실화한다

```java
@Testcontainers
@SpringBootTest
class OrderIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");
}
```

이 방식은 실제 DB와 유사한 동작을 확인하는 데 좋다.

- SQL 방언 차이
- 락/트랜잭션 경계
- 인덱스와 제약 조건
- 마이그레이션 스크립트

### 2. 모든 테스트를 full integration으로 만들 필요는 없다

Testcontainers를 무조건 모든 테스트에 붙이면 느려진다.

그래서 보통 경계를 나눈다.

- slice test: controller, repository, serializer 단위
- container test: DB, broker, cache 같은 외부 경계
- full integration test: 핵심 플로우만

이 문맥은 [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)과 같이 봐야 한다.

### 3. 컨테이너를 어디에 둘지 정해야 한다

Testcontainers 경계는 보통 다음 중 하나다.

- repository layer만 container로 검증
- service layer까지 포함하되 외부 API는 mock
- end-to-end 핵심 시나리오만 container로 검증

모든 걸 실제로 올리면 좋아 보이지만, 속도와 유지보수 비용이 급격히 오른다.

### 4. DynamicPropertySource로 런타임 주소를 주입한다

컨테이너는 실행 시점에 host/port가 정해지므로, Spring 테스트에 동적으로 주입해야 한다.

```java
@DynamicPropertySource
static void overrideProps(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
}
```

이 패턴이 없으면 테스트는 실제 컨테이너를 띄워도 앱 설정이 그 주소를 못 본다.

### 5. 재사용 가능한 컨테이너와 격리 사이의 균형을 봐야 한다

컨테이너 재사용은 빠르지만, 상태 오염 위험이 있다.

반대로 매번 새로 띄우면 느리지만, 깨끗하다.

운영 전략은 보통 다음과 같다.

- 로컬 개발: 재사용 우선
- CI: 격리 우선
- flakey test 조사: 깨끗한 컨테이너 우선

## 실전 시나리오

### 시나리오 1: 테스트는 통과하는데 운영 DB에서는 실패한다

대개 다음 원인이 있다.

- H2 같은 in-memory DB와 실제 DB 방언 차이
- 제약 조건이 다르다
- 트랜잭션 락 동작이 다르다

이때 Testcontainers는 in-memory 대신 실제 DB를 쓰게 해 차이를 줄여 준다.

### 시나리오 2: 컨테이너 테스트가 너무 느리다

원인 후보:

- 너무 많은 컨테이너를 띄운다
- 매 테스트마다 context를 새로 올린다
- full integration test가 너무 많다

대응:

- slice test와 container test를 분리한다
- 컨테이너를 static fixture로 관리한다
- 느린 시나리오는 소수만 남긴다

### 시나리오 3: CI에서는 잘 되는데 로컬에서 깨진다

흔한 이유는 포트 충돌, 네트워크, 환경 변수 차이다.

Testcontainers는 이런 차이를 줄이지만, 테스트가 외부 상태를 너무 많이 공유하면 여전히 불안정할 수 있다.

### 시나리오 4: outbox/queue 같은 비동기 경로를 테스트하고 싶다

이 경우는 단순 unit test보다 container 기반 통합 테스트가 더 적합할 수 있다.

- 실제 DB
- 실제 broker
- 실제 relay worker

이 조합은 [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)와 잘 맞는다.

## 코드로 보기

### PostgreSQL container

```java
@Testcontainers
@SpringBootTest
class ProductRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

### slice + container 혼합 전략

```java
@DataJpaTest
class ProductRepositorySliceTest {
}
```

```java
@SpringBootTest
class ProductFlowIntegrationTest {
}
```

### 실제 브로커와 함께 테스트하는 예

```java
@Testcontainers
class OutboxRelayIntegrationTest {

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.6.0")
    );
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| unit test + mock | 빠르다 | 현실성이 낮다 | 순수 로직 |
| slice test | 경계가 좁고 빠르다 | 외부 의존성은 못 본다 | 레이어 계약 |
| Testcontainers | 실제와 가깝다 | 느리고 운영 비용이 있다 | DB, broker, cache 검증 |
| full end-to-end | 가장 현실적이다 | 가장 비싸다 | 핵심 비즈니스 플로우 |

핵심은 Testcontainers를 쓰는지보다, **테스트 피라미드의 어디에 두는가**다.

## 꼬리질문

> Q: Testcontainers와 `@DataJpaTest`는 어떻게 같이 쓸 수 있는가?
> 의도: slice와 container 결합 이해 확인
> 핵심: slice 범위 안에서 실제 DB를 붙일 수 있다.

> Q: 컨테이너 테스트가 느려지는 가장 흔한 이유는 무엇인가?
> 의도: 비용 구조 이해 확인
> 핵심: 너무 많은 full context와 너무 많은 컨테이너다.

> Q: `DynamicPropertySource`는 왜 필요한가?
> 의도: 런타임 설정 주입 이해 확인
> 핵심: 컨테이너 주소가 실행 시점에 정해지기 때문이다.

> Q: H2만 쓰면 안 되는 경우는 언제인가?
> 의도: 현실 DB 차이 이해 확인
> 핵심: 락, 제약, SQL 방언, 트랜잭션 차이가 중요한 경우다.

## 한 줄 정리

Testcontainers는 실제 의존성을 테스트로 끌어오지만, slice와 full integration의 경계를 정하지 않으면 테스트가 느리고 비싸진다.
