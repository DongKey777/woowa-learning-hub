---
schema_version: 3
title: Spring Multiple Transaction Managers and Qualifier Boundaries
concept_id: spring/multiple-transaction-managers-qualifier-boundaries
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- multiple-transaction-managers
- qualifier-boundaries
- platformtransactionmanager
- transactionmanager-qualifier
aliases:
- multiple transaction managers
- PlatformTransactionManager
- transactionManager qualifier
- @Transactional transactionManager
- chained transaction
- mixed persistence
- local transaction
- multiple datasource transaction
intents:
- troubleshooting
- design
symptoms:
- transaction manager bean이 여러 개인데 @Transactional이 어떤 manager를 쓰는지 불명확하다.
- JPA repository와 JdbcTemplate이 서로 다른 transaction boundary에서 실행된다.
- 한 저장소는 commit되고 다른 저장소는 rollback되어 distributed transaction처럼 기대한 흐름이 깨진다.
linked_paths:
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-transaction-debugging-playbook.md
- contents/spring/spring-transaction-synchronization-aftercommit-pitfalls.md
- contents/spring/spring-delivery-reliability-retryable-resilience4j-outbox-relay.md
- contents/spring/spring-boot-autoconfiguration.md
expected_queries:
- Spring에서 transaction manager가 여러 개면 @Transactional은 무엇을 선택해?
- @Transactional(transactionManager = ...)는 언제 명시해야 해?
- JPA와 JDBC가 다른 transaction manager를 쓰면 어떤 문제가 생겨?
- 다중 DataSource에서 transaction boundary와 qualifier를 어떻게 설계해?
contextual_chunk_prefix: |
  이 문서는 multiple PlatformTransactionManager 환경에서 @Transactional의
  transactionManager qualifier, @Primary/default 선택, JPA/JDBC/multiple datasource,
  local transaction, chained transaction expectation, outbox 대안을 진단하는 playbook이다.
---
# Spring Multiple Transaction Managers and Qualifier Boundaries

> 한 줄 요약: transaction manager가 여러 개면 `@Transactional`의 경계는 더 이상 자동이 아니며, qualifier와 proxy boundary를 정확히 맞춰야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)

retrieval-anchor-keywords: multiple transaction managers, PlatformTransactionManager, qualifier, TransactionManager, @Transactional transactionManager, chained transaction, mixed persistence, local transaction

## 핵심 개념

하나의 애플리케이션이 하나의 transaction manager만 쓰는 것은 흔한가?

꼭 그렇지는 않다.

- JPA와 JDBC를 함께 쓸 수 있다
- DB와 메시지 오프셋을 따로 다룰 수 있다
- 다중 데이터소스를 가질 수 있다

이때 `@Transactional`은 어느 manager를 쓸지 명확하지 않으면 엉뚱한 경계를 잡을 수 있다.

## 깊이 들어가기

### 1. `PlatformTransactionManager`가 핵심 계약이다

각 persistence 기술은 transaction manager 구현을 가진다.

- JPA transaction manager
- JDBC transaction manager
- custom manager

### 2. 기본 선택이 항상 의도와 같지는 않다

transaction manager bean이 여러 개면 기본 bean, primary, qualifier 관계를 확인해야 한다.

### 3. `@Transactional`에도 manager를 지정할 수 있다

```java
@Transactional(transactionManager = "orderTxManager")
public void placeOrder() {
    ...
}
```

이렇게 해야 실제로 어느 저장소를 제어하는지 명확해진다.

### 4. 서로 다른 저장소를 한 메서드에서 다루면 경계가 흐려진다

JPA와 JDBC를 섞거나, DB와 Kafka를 같은 트랜잭션처럼 다루면 정합성 모델이 복잡해진다.

이 문맥은 [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)와 같이 보면 좋다.

### 5. qualifier는 선택이 아니라 계약이다

bean 이름과 qualifier가 명확하지 않으면 사고가 난다.

- 어느 repository가 어느 manager를 쓰는가
- 어느 서비스가 어느 datasource를 쓰는가

## 실전 시나리오

### 시나리오 1: JPA repository와 JDBC template이 다른 tx를 쓴다

각각의 transaction manager가 다르면 서로 다른 경계를 잡는다.

### 시나리오 2: 기본 tx manager를 바꿨더니 일부 서비스만 깨진다

기존 `@Transactional`이 암묵적으로 다른 manager를 사용했을 수 있다.

### 시나리오 3: 한 DB는 커밋되고 다른 DB는 롤백된다

distributed transaction이 없는 상태에서 다중 manager를 섞은 전형적 결과다.

### 시나리오 4: `REQUIRES_NEW`와 다중 manager가 같이 들어간다

부분 커밋과 분리 커밋이 겹쳐 추적이 어려워진다.

## 코드로 보기

### multiple managers

```java
@Configuration
public class TxConfig {

    @Bean
    @Primary
    public PlatformTransactionManager jpaTxManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }

    @Bean(name = "jdbcTxManager")
    public PlatformTransactionManager jdbcTxManager(DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}
```

### explicit manager selection

```java
@Service
public class LedgerService {

    @Transactional(transactionManager = "jdbcTxManager")
    public void writeLedger() {
    }
}
```

### mixed service

```java
@Service
public class MixedService {

    private final OrderRepository orderRepository;
    private final JdbcTemplate jdbcTemplate;
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 tx manager | 단순하다 | 기술 선택이 제한된다 | 단일 persistence |
| 다중 tx manager | 유연하다 | 경계가 복잡하다 | 복수 datasource |
| qualifier 명시 | 의도가 분명하다 | 설정이 늘어난다 | 운영 안정성이 중요할 때 |
| 암묵적 기본 manager | 코드가 짧다 | 오해를 부른다 | 아주 작은 시스템 |

핵심은 tx manager를 여러 개 두는 것보다, **어떤 메서드가 어느 manager를 소유하는지**를 명확히 하는 것이다.

## 꼬리질문

> Q: transaction manager가 여러 개일 때 왜 qualifier가 중요한가?
> 의도: 경계 선택 이해 확인
> 핵심: 어떤 저장소를 제어하는지 명시해야 하기 때문이다.

> Q: 다중 transaction manager에서 가장 흔한 버그는 무엇인가?
> 의도: 경계 혼동 이해 확인
> 핵심: 의도와 다른 manager가 선택되는 것이다.

> Q: JPA와 JDBC를 섞을 때 왜 조심해야 하는가?
> 의도: 저장소 일관성 이해 확인
> 핵심: 서로 다른 tx boundary가 생길 수 있다.

> Q: 기본 manager와 `@Transactional(transactionManager=...)`의 차이는 무엇인가?
> 의도: explicit contract 이해 확인
> 핵심: 전자는 암묵, 후자는 명시다.

## 한 줄 정리

Transaction manager가 여러 개면 `@Transactional`은 자동으로 맞지 않으므로 qualifier로 경계를 명시해야 한다.
