# HikariCP 튜닝

> 한 줄 요약: HikariCP는 크게 잡는다고 빨라지지 않는다. DB 용량, 트랜잭션 길이, 커넥션 점유 시간을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
> - [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
> - [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
> - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
> - [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
> - [Spring Bean 생명주기와 스코프 함정](../spring/spring-bean-lifecycle-scope-traps.md)
> - [Spring Routing DataSource Read/Write Transaction Boundaries](../spring/spring-routing-datasource-read-write-transaction-boundaries.md)

> retrieval-anchor-keywords: hikaricp, hikari connection pool, hikari datasource, maximumPoolSize, hikari max pool size, maximum pool size too high, maximum pool size too low, minimumIdle, connectionTimeout, hikari connection timeout, getConnection timeout, borrow timeout, acquire timeout, connection acquisition timeout, connection is not available, request timed out after, pool timeout is not query timeout, maxLifetime, leakDetectionThreshold, connection leak detection triggered, apparent connection leak detected, leak detection false positive, keepaliveTime, connection pool exhaustion, pool exhausted, connection pool starvation, threads awaiting connection, waiting for connection, active connections high idle zero, db max connections, long transaction, external call in transaction, spring datasource pool tuning, 커넥션 풀 고갈, 커넥션 누수 의심, hikari 설정

## 이 문서 다음에 보면 좋은 문서

- pool size보다 먼저 transaction boundary를 어떻게 잘라야 하는지 보려면 [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)로 이어 가는 편이 정확하다.
- 증상이 실제로 DB lock/latch 경합인지, 아니면 풀 고갈인지 분리하려면 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)과 [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)을 같이 본다.
- `connectionTimeout`이 query timeout인지, borrow/acquire timeout인지 헷갈리면 [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)로 timeout ownership을 바로잡는 편이 빠르다.
- Spring에서 read/write routing과 커넥션 획득 시점까지 함께 보려면 [Spring Routing DataSource Read/Write Transaction Boundaries](../spring/spring-routing-datasource-read-write-transaction-boundaries.md)가 바로 연결된다.

---

## 핵심 개념

HikariCP는 Java/Spring 백엔드에서 가장 흔한 DB connection pool이다. 핵심은 단순하다.

1. 커넥션 생성 비용을 줄인다
2. DB 연결 수를 통제한다
3. 커넥션을 오래 잡고 있는 병목을 드러낸다

많은 팀이 `maximumPoolSize`만 크게 조정하고 끝내는데, 그건 절반만 보는 것이다. 실제 병목은 트랜잭션 길이, 쿼리 시간, 외부 I/O, DB max connection 수와 같이 봐야 한다.

---

## 운영 검색 alias 빠른 매핑

운영에서 들어오는 검색어는 설정 이름, 에러 문자열, 증상 표현이 섞여 있다. 아래 네 묶음은 같은 축으로 읽는 편이 정확하다.

| 검색 alias cluster | 여기서 먼저 확인할 해석 | 같이 보면 좋은 문서 |
|---|---|---|
| `maximumPoolSize`, `max pool size`, `pool size too high`, `db max connections` | pool size는 단독 숫자가 아니라 `인스턴스 수 x pool size`와 DB safe concurrency 예산으로 읽어야 한다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| `connectionTimeout`, `getConnection timeout`, `borrow timeout`, `acquire timeout`, `Connection is not available, request timed out after ...` | 이 값은 query 실행 시간 제한이 아니라 `getConnection()` borrow 대기 한도다 | [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md) |
| `leakDetectionThreshold`, `connection leak detection triggered`, `apparent connection leak detected`, `leak detection false positive` | leak detection은 "반환 누락 확정"이 아니라 "너무 오래 점유된 connection" 경보다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| `pool exhaustion`, `pool exhausted`, `threads awaiting connection`, `waiting for connection`, `active=... idle=0` | pool 고갈은 원인보다 1차 증상인 경우가 많아서 long transaction, lock wait, external I/O inside tx를 같이 봐야 한다 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

---

## 깊이 들어가기

### 1. 풀 크기는 DB와 함께 정한다

대략적인 출발점은 이런 사고다.

```text
app instance 수 x pool size <= DB가 감당 가능한 연결 수
```

여기서 중요한 것은 애플리케이션 인스턴스가 여러 개라는 점이다.

- instance 1개당 30 connection
- instance 8개면 240 connection

이렇게 쌓이면 DB `max_connections`를 쉽게 넘긴다.

### 2. 중요한 설정은 최대 크기만이 아니다

자주 보는 설정:

- `maximumPoolSize`
- `minimumIdle`
- `connectionTimeout`
- `idleTimeout`
- `maxLifetime`
- `leakDetectionThreshold`
- `keepaliveTime`

각 설정은 다른 문제를 푼다.

- `maximumPoolSize`: 동시 커넥션 상한
- `connectionTimeout`: 대기할 수 있는 최대 시간
- `maxLifetime`: 오래된 커넥션 교체
- `leakDetectionThreshold`: 커넥션 반환 누락 탐지

#### `maximumPoolSize`는 성능 스위치가 아니라 동시성 예산이다

`maximumPoolSize`를 올리는 것은 앱 thread를 더 쓰는 일이 아니라 DB에 동시에 밀어 넣는 작업 수를 늘리는 일이다.

- pool을 20에서 80으로 키워도 connection hold time이 그대로면 saturation 시점만 조금 뒤로 밀린다.
- 여러 인스턴스, 배치 worker, admin job이 같이 붙는 환경이면 `instance 수 x maximumPoolSize`를 총량으로 본다.
- `maximumPoolSize` 부족처럼 보여도 실제 원인은 lock wait, 긴 트랜잭션, 외부 I/O inside tx인 경우가 더 많다.

#### `connectionTimeout`은 query timeout이 아니라 borrow timeout이다

이 값은 `getConnection()`에서 얼마나 기다릴지를 뜻한다.

- 이미 빌려 간 connection에서 실행 중인 query를 직접 끊어 주지 않는다.
- 짧게 두면 pool saturation을 빨리 surface하지만, burst에도 빨리 실패한다.
- 길게 두면 실패는 늦어지지만 request backlog와 응답 tail이 더 조용히 커질 수 있다.

즉 "`connectionTimeout`을 줄였는데 왜 느린 query는 그대로냐"는 질문은 자연스럽다. query/statement timeout과 pool borrow timeout의 소유자가 다르기 때문이다.

#### `leakDetectionThreshold`는 "누수 확정"이 아니라 "오래 점유됨" 경보다

leak detection 로그가 떴다고 곧바로 `close()` 누락으로 결론내리면 오판하기 쉽다.

- 진짜 누수일 수도 있다.
- 하지만 긴 쿼리, lock wait, 대량 batch commit, 트랜잭션 안 외부 호출도 같은 경보를 낼 수 있다.
- stack trace를 볼 때는 "어디서 안 돌아왔는가"보다 "왜 이 코드가 오래 connection을 잡았는가"를 같이 본다.

### 3. 커넥션은 오래 쥐고 있을수록 위험하다

다음 코드는 흔한 실수다.

```java
@Transactional
public void placeOrder() {
    orderRepository.save(order);
    paymentClient.pay(order); // 외부 호출
    shippingClient.reserve(order);
}
```

이 패턴은 DB 커넥션을 잡은 채 네트워크를 기다릴 수 있다. 그러면 쿼리가 느린 게 아니라, 커넥션이 묶이는 것이다.

### 4. HikariCP는 문제를 숨기기보다 드러낸다

풀 크기를 무작정 키우면 대기열은 잠깐 줄 수 있지만, DB가 버티지 못하면 전체 지연이 더 커진다.

즉 HikariCP는 다음을 보여준다.

- 요청이 커넥션을 얼마나 오래 잡는가
- DB가 실제로 처리 가능한 동시성이 얼마인가
- 긴 트랜잭션이 있는가

---

## 실전 시나리오

### 시나리오 1: `Connection is not available` 폭증

증상:

- 로그에 `Connection is not available, request timed out after ...`가 찍힘
- 앱 CPU는 낮은데 요청이 밀림
- DB는 바쁘지 않아 보여도 풀은 고갈됨
- Hikari metrics에서 `threads awaiting connection`이 늘거나 `active ~= maximumPoolSize`, `idle = 0`으로 붙어 있음

원인:

- 긴 트랜잭션
- 외부 API 호출을 DB 트랜잭션 안에 넣음
- 배치 작업이 너무 많은 커넥션을 점유함

대응:

- 트랜잭션 범위를 줄인다
- 외부 호출을 트랜잭션 밖으로 뺀다
- batch size를 조절한다
- Hikari metrics와 DB process list를 같이 본다

### 시나리오 2: 풀을 늘렸는데 더 느려짐

풀을 20에서 80으로 키웠더니 잠깐 좋아졌다가 전체 p99가 더 나빠질 수 있다. 이유는 DB 자체의 동시성 처리 능력을 넘어서기 때문이다.

교훈:

- 풀은 큐잉 지연을 숨길 수 있지만, 병목을 없애지 못한다
- DB가 한 번에 처리할 수 있는 작업 수는 무한하지 않다

### 시나리오 3: leak detection이 진짜 누수를 잡아냄

테스트 환경에서 `leakDetectionThreshold`를 낮춰두면 반환하지 않은 커넥션을 빨리 찾을 수 있다.

하지만 너무 낮으면 정상적인 긴 쿼리도 누수처럼 보일 수 있다.

로그를 이렇게 읽는 편이 안전하다.

- `connection leak detection triggered`는 "이 connection이 너무 오래 반환되지 않았다"는 뜻이지, 곧바로 영구 누수를 증명하지는 않는다.
- `apparent connection leak detected`처럼 보여도 stack trace가 long transaction, 외부 API call, lock wait를 가리키면 점유 시간 문제일 수 있다.
- 진짜 누수인지 보려면 같은 stack이 반복되는지, 요청 종료 후에도 return이 없는지, pool active 수가 계속 내려오지 않는지를 같이 본다.

### 시나리오 4: `connectionTimeout`을 줄였는데 query hang은 그대로다

증상:

- `getConnection()` 실패는 빨라졌는데 느린 query 자체는 그대로다
- 팀이 "pool timeout을 줄였는데 왜 socket hang이 안 끊기지?"라고 묻는다

해석:

- `connectionTimeout`은 borrow wait budget이다
- 이미 실행 중인 query timeout, lock wait timeout, driver/socket timeout은 다른 층이다
- 그래서 acquire timeout만 줄이면 pool exhaustion은 빨리 surface돼도 query ownership은 그대로 남는다

대응:

- acquire wait와 query execution wait를 분리해서 본다
- request timeout, statement timeout, driver/network timeout과 pool timeout을 같은 말로 부르지 않는다
- timeout ownership이 헷갈리면 [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)까지 같이 본다

---

## 코드로 보기

### Spring Boot 설정 예시

```yaml
spring:
  datasource:
    url: jdbc:mysql://db.example.com:3306/app
    username: app
    password: secret
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 3000
      idle-timeout: 600000
      max-lifetime: 1800000
      leak-detection-threshold: 2000
      keepalive-time: 300000
```

### 풀 크기 감각

```text
적정 pool size ≈ (DB가 처리 가능한 동시 작업 수) - (안전 여유)
```

정확한 숫자보다 중요한 것은, 여러 인스턴스와 배치 작업을 합산해서 보는 것이다.

### 트랜잭션 외부 호출 분리 예시

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(Order.from(command));
    outboxService.publishOrderCreated(order.getId());
}

public void sendPayment(Order order) {
    paymentClient.pay(order); // DB 트랜잭션 밖
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 pool | 순간 처리량이 늘어날 수 있다 | DB/락/스케줄링 비용이 커질 수 있다 | DB가 여유 있을 때만 |
| 작은 pool | DB를 보호한다 | 대기열이 커질 수 있다 | 안정성이 더 중요할 때 |
| 짧은 connectionTimeout | 장애를 빨리 드러낸다 | 일시적 burst에 민감하다 | SLA가 명확할 때 |
| leak detection 활성화 | 반환 누락을 빨리 찾는다 | 긴 쿼리와 혼동될 수 있다 | 테스트/스테이징 |
| keepalive 조정 | 유휴 커넥션 끊김을 줄인다 | 과하면 불필요한 트래픽이 늘어난다 | 네트워크가 불안정할 때 |

핵심은 풀 튜닝이 아니라 **점유 시간 튜닝**이다.

---

## 꼬리질문

> Q: pool size를 무작정 크게 하면 안 되는 이유는 뭔가요?
> 의도: 연결 수와 DB 처리량의 관계 이해 여부 확인
> 핵심: 풀은 대기열을 줄일 수 있지만 DB의 처리 한계를 넘기면 더 느려진다

> Q: HikariCP 설정 중 가장 먼저 봐야 하는 것은 무엇인가요?
> 의도: 단일 파라미터 집착 여부 확인
> 핵심: maximumPoolSize보다 커넥션 점유 시간과 트랜잭션 경계를 먼저 본다

> Q: leak detection은 왜 운영에 그대로 켜두기 어려운가요?
> 의도: 운영 비용 인식 확인
> 핵심: 긴 쿼리/배치가 누수처럼 오탐될 수 있다

---

## 한 줄 정리

HikariCP는 커넥션 수를 늘리는 도구가 아니라, DB 연결 점유를 통제해서 병목을 드러내는 도구다.
