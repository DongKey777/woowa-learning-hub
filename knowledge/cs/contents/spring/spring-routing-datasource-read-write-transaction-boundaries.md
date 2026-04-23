# Spring Routing DataSource Read/Write Transaction Boundaries

> 한 줄 요약: Spring의 read/write routing은 lookup key를 고르는 문제보다, 트랜잭션에서 실제 커넥션이 언제 획득되는지와 read-after-write 일관성을 어떻게 보장할지의 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)
> - [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [Replica Read Routing Anomalies](../database/replica-read-routing-anomalies.md)
> - [Replica Lag Read-After-Write Strategies](../database/replica-lag-read-after-write-strategies.md)

retrieval-anchor-keywords: AbstractRoutingDataSource, read write split, read replica routing, transaction readOnly routing, LazyConnectionDataSourceProxy, read after write, routing datasource, replica lag, writer pinning, inner readOnly writer pool, readOnly routing confusion, requires new reader route, writer pool confusion

## 핵심 개념

Spring에서 read/write 분리를 붙일 때 가장 흔한 오해는 아래다.

- `@Transactional(readOnly = true)`면 자동으로 replica로 가겠지
- routing datasource만 만들면 나머지는 알아서 안전하겠지
- read-only 트랜잭션이면 일관성 문제도 같이 해결되겠지

실제로는 그렇지 않다.

read/write routing에서 핵심 질문은 세 가지다.

1. lookup key를 어떤 기준으로 고를 것인가
2. 그 기준이 **커넥션 획득 시점**에 이미 확정돼 있는가
3. replica lag 상황에서 read-after-write를 어떻게 보장할 것인가

즉 이 주제는 단순 datasource wiring이 아니라, **트랜잭션 경계와 일관성 계약**의 문제다.

## 깊이 들어가기

### 1. route는 커넥션을 고를 때 결정된다

`AbstractRoutingDataSource`는 대개 `determineCurrentLookupKey()`로 현재 lookup key를 고른다.

중요한 점은 이 판단이 "메서드 선언" 시점이 아니라, **실제 커넥션을 가져오는 시점**에 의미를 가진다는 것이다.

따라서 다음이 아주 중요하다.

- 트랜잭션이 이미 시작됐는가
- read-only 플래그가 설정됐는가
- 커넥션이 너무 일찍 잡히지 않았는가

한 번 writer 커넥션이 잡힌 뒤에는, 나중에 lookup key를 바꿔도 같은 트랜잭션 안에서는 바뀌지 않는 경우가 많다.

### 2. `readOnly`는 routing 힌트일 뿐, 일관성 보장은 아니다

많은 구현이 아래처럼 현재 트랜잭션의 read-only 여부를 보고 route를 정한다.

```java
public class ReplicationRoutingDataSource extends AbstractRoutingDataSource {

    @Override
    protected Object determineCurrentLookupKey() {
        return TransactionSynchronizationManager.isCurrentTransactionReadOnly()
            ? "reader"
            : "writer";
    }
}
```

이 방식은 유용하지만, 어디까지나 힌트다.

`readOnly = true`는 다음을 뜻하지 않는다.

- replica가 최신 데이터라는 보장
- 쓰기 직후 조회가 반드시 같은 값을 본다는 보장
- JPA flush/connection timing이 언제나 이상적으로 맞는다는 보장

즉 routing 판단과 consistency 보장은 별개의 계층이다.

### 3. 커넥션 획득 시점을 늦추는 것이 중요할 수 있다

실전에서는 커넥션이 생각보다 일찍 잡히면 routing 의도가 무너진다.

예를 들어 다음 상황이 있다.

- 트랜잭션 시작과 함께 커넥션이 선점된다
- JPA/Hibernate가 특정 작업에서 일찍 connection을 요청한다
- OSIV나 초기화 로직이 서비스 경계 밖에서 늦은 조회를 만든다

이럴 때 `LazyConnectionDataSourceProxy`는 물리 커넥션 획득을 실제 SQL 시점까지 늦춰 routing 의도를 보존하는 데 도움이 될 수 있다.

핵심은 routing 클래스 자체보다, **커넥션 acquisition timing**이다.

### 4. read-after-write는 replica routing만으로 해결되지 않는다

같은 요청 안에서 쓰기 후 바로 읽으면, 비즈니스는 보통 최신 값을 기대한다.

하지만 read-only 메서드가 replica로 가면 아래 문제가 생길 수 있다.

- 방금 쓴 데이터가 아직 replica에 반영되지 않음
- 카운트/집계가 직전 쓰기를 반영하지 않음
- 사용자 입장에서 "저장했는데 조회에 안 보임" 현상 발생

이 문제는 DB 복제 지연의 영역이다.

해결 전략은 보통 아래 중 하나다.

- 같은 유스케이스 안에서는 writer pinning
- 일정 시간 read-after-write를 writer로 강제
- consistency token / fence 기반 라우팅
- UX 차원에서 eventual consistency를 명시

즉 `@Transactional(readOnly = true)` 하나로 해결되는 문제가 아니다.

### 5. 전파와 내부 호출이 routing 기대를 바꾼다

예를 들어 outer method가 write transaction이라면, inner read-only method는 같은 트랜잭션에 합류할 수 있다.

그 경우 기대는 종종 아래처럼 바뀐다.

- 코드 선언: inner는 `readOnly = true`
- 실제 실행: 이미 writer transaction / writer connection을 공유

반대로 `REQUIRES_NEW`로 분리하면 새 트랜잭션에서 reader route가 선택될 수 있다.

즉 routing은 메서드 선언만 보면 안 되고, **실제 전파 결과**를 봐야 한다.

### 6. OSIV와 lazy loading이 route를 흐릴 수 있다

service 경계에서는 writer로 읽고 썼다고 생각했는데, 뷰 렌더링이나 직렬화 시점의 lazy loading이 나중에 추가 조회를 만들 수 있다.

이 경우 route가 예기치 않게 달라지거나, 아예 트랜잭션 경계 밖에서 조회가 일어날 수 있다.

그래서 read/write routing은 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)와도 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 저장 직후 상세 조회가 빈 값처럼 보인다

write는 writer에 반영됐지만, 후속 조회가 reader로 라우팅되어 replica lag를 맞았을 수 있다.

이건 routing 성공이 아니라 **일관성 계약 실패**다.

### 시나리오 2: inner method에 `readOnly = true`를 붙였는데도 writer pool이 사용된다

outer write transaction에 합류했을 가능성이 높다.

즉 선언적 read-only와 실제 connection route가 다를 수 있다.

### 시나리오 3: read-only 서비스인데 writer로만 간다

원인 후보:

- connection이 너무 일찍 잡힌다
- `LazyConnectionDataSourceProxy`가 없다
- transaction이 없는 시점에 라우팅 기준이 비어 있다

### 시나리오 4: 운영에서는 stale read가 터지는데 로컬에서는 재현이 안 된다

로컬 단일 DB에서는 replica lag가 없어서 routing anomaly가 숨는다.

이 경우는 Testcontainers나 복제 환경에 더 가까운 통합 테스트가 필요할 수 있다.

## 코드로 보기

### routing datasource

```java
public class ReplicationRoutingDataSource extends AbstractRoutingDataSource {

    @Override
    protected Object determineCurrentLookupKey() {
        return TransactionSynchronizationManager.isCurrentTransactionReadOnly()
            ? "reader"
            : "writer";
    }
}
```

### lazy proxy로 물리 커넥션 획득 지연

```java
@Bean
public DataSource dataSource(
        @Qualifier("writerDataSource") DataSource writerDataSource,
        @Qualifier("readerDataSource") DataSource readerDataSource) {
    ReplicationRoutingDataSource routing = new ReplicationRoutingDataSource();
    routing.setTargetDataSources(Map.of(
        "writer", writerDataSource,
        "reader", readerDataSource
    ));
    routing.setDefaultTargetDataSource(writerDataSource);
    routing.afterPropertiesSet();
    return new LazyConnectionDataSourceProxy(routing);
}
```

### 최신성이 중요한 읽기는 writer pinning

```java
@Transactional
public OrderDetail placeAndRead(Long id) {
    orderService.place(id);
    return orderQueryService.readFromPrimary(id);
}
```

### 일반 조회는 read-only route 후보

```java
@Transactional(readOnly = true)
public OrderSummary findSummary(Long id) {
    return orderQueryRepository.findSummary(id);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| writer 단일 사용 | 가장 단순하고 일관성이 높다 | 읽기 확장성이 낮다 | 규모가 작거나 최신성이 매우 중요할 때 |
| read-only 기반 reader routing | 구현이 비교적 단순하다 | stale read와 timing 이슈가 생긴다 | 조회 부하가 크고 eventual consistency를 감수할 때 |
| writer pinning 혼합 전략 | 중요한 유스케이스 일관성을 지킨다 | 라우팅 규칙이 복잡해진다 | write 직후 read가 중요한 서비스 |
| consistency token 기반 라우팅 | 제어력이 높다 | 구현과 운영 비용이 크다 | 고트래픽, 다중 리전, 강한 UX 일관성 요구 |

핵심은 routing datasource를 "DB 두 개 연결"이 아니라, **connection timing + transaction propagation + replica consistency를 함께 다루는 설계**로 보는 것이다.

## 꼬리질문

> Q: `@Transactional(readOnly = true)`만으로 reader routing이 항상 보장되지 않는 이유는 무엇인가?
> 의도: 선언과 실제 connection 획득 구분 확인
> 핵심: route는 실제 커넥션 획득 시점과 전파 결과에 좌우된다.

> Q: `LazyConnectionDataSourceProxy`가 왜 중요한가?
> 의도: connection timing 이해 확인
> 핵심: 물리 커넥션 획득을 늦춰 routing 판단이 더 정확한 시점에 이뤄지게 돕는다.

> Q: read-after-write 문제는 왜 Spring routing만으로 해결되지 않는가?
> 의도: DB 복제 지연과 앱 계층 경계 구분 확인
> 핵심: replica lag는 DB consistency 문제이기 때문이다.

> Q: outer write transaction 안의 inner read-only 메서드는 왜 여전히 writer를 탈 수 있는가?
> 의도: 전파와 route 관계 이해 확인
> 핵심: 같은 트랜잭션에 합류하면 기존 writer connection을 공유할 수 있다.

## 한 줄 정리

Spring의 read/write routing에서 진짜 핵심은 lookup key 자체보다, 커넥션 획득 시점과 전파 결과를 기준으로 어떤 일관성 계약을 지킬지 결정하는 것이다.
