---
schema_version: 3
title: 'Connection pool 고갈 — 누수 / 긴 트랜잭션 / N+1 / 풀 사이즈 어디에 원인이 있나'
concept_id: database/connection-pool-starvation-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
aliases:
- connection pool 고갈
- HikariCP timeout
- DB connection leak
- 커넥션 풀 부족
- pool exhausted symptom
intents:
- symptom
- troubleshooting
symptoms:
- 'HikariPool: Connection is not available, request timed out after 30000ms 에러가 반복된다'
- '평소엔 멀쩡하다가 트래픽이 늘면 응답 시간이 급격히 늘어난다'
- 'CPU/DB 부하는 낮은데 API 응답이 느려지고 timeout이 발생한다'
linked_paths:
- contents/database/connection-pool-basics.md
- contents/database/hikari-connection-pool-tuning.md
- contents/database/transaction-locking-connection-pool-primer.md
forbidden_neighbors:
- contents/database/pool-timeout-term-matching-card.md
expected_queries:
- HikariCP timed out 에러가 나는데 원인을 어떻게 찾아?
- connection pool이 고갈되는 진짜 원인을 어떻게 진단해?
- 커넥션 풀 사이즈를 늘리면 해결되는 거야?
- pool exhausted가 떴는데 어디부터 봐야 해?
---

# Connection pool 고갈 — 누수 / 긴 트랜잭션 / N+1 / 풀 사이즈 어디에 원인이 있나

> 한 줄 요약: *"Connection is not available"* 메시지는 *원인이 아니라 증상*이다. 풀 사이즈 자체보다 *커넥션이 너무 오래 잡혀 있다는 사실*이 먼저고, 그 이유는 (1) leak 미반환, (2) 트랜잭션이 외부 호출로 길어짐, (3) N+1로 한 요청이 100개를 빌림, (4) 진짜로 풀이 작음 — 순서대로 진단한다.

**난이도: 🟡 Intermediate**

**증상 분기**: connection pool / HikariCP

관련 문서:

- [Connection Pool 기초](./connection-pool-basics.md) — 일반 개념
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md) — 파라미터 디테일
- [Transaction + Locking + Connection Pool Primer](./transaction-locking-connection-pool-primer.md) — 세 가지가 얽힌 모양

## 어떤 증상에서 이 문서를 펴는가

학습자/주니어가 다음 중 하나를 본다:

- *"HikariPool-1 - Connection is not available, request timed out after 30000ms"* (가장 흔함)
- *"평소엔 100ms이던 API가 트래픽 살짝 늘면 30초로 폭주."* — *latency cliff*
- *"DB CPU는 5%, 앱 CPU도 낮은데 응답은 안 옴."*

세 증상 모두 *pool exhaustion*의 동일한 모양 — *커넥션을 빌리려는 요청이 풀에서 대기*하고 있다.

본능적으로 *"풀 사이즈를 20에서 50으로"* 늘리려는 충동이 든다. 하지만 *진짜 원인*이 풀 사이즈인 경우는 드물다. 진단 순서대로 좁힌다.

## 원인 분기 (확률 높은 순)

### 분기 1 — Connection Leak (커넥션 미반환)

가장 자주 발생한다. JdbcTemplate/JPA 사용 시는 잘 안 일어나지만, *직접 Connection을 들고 다니는 코드*가 있으면 위험.

```java
public List<Item> findItems() {
    Connection conn = dataSource.getConnection();   // ❌ try-with-resources 없음
    PreparedStatement ps = conn.prepareStatement(...);
    ResultSet rs = ps.executeQuery();
    // ... 예외 발생 시 conn.close() 호출 안 됨
}
```

**진단**:

- HikariCP `leakDetectionThreshold` 옵션을 *활성화* (예: 10초)
- 누수 발생 시 *스택 트레이스가 로그*에 찍힌다 (*"Connection leak detection triggered"*)

**해결**:

- *try-with-resources* 또는 *JdbcTemplate/JPA*로 마이그레이션
- 직접 빌리는 코드는 *반환 책임을 명시*

### 분기 2 — 트랜잭션이 외부 I/O를 포함

```java
@Transactional
public void create(...) {
    repository.save(...);                       // 커넥션 빌림 (트랜잭션 시작)
    httpClient.notify(externalApi);             // ❌ 외부 호출 (수 초)
    auditService.log(...);
}
```

`@Transactional`은 *메소드 진입 시 커넥션을 빌리고 커밋까지 잡는다*. 안에서 *외부 HTTP 호출*이 있으면 *그 호출 시간만큼* 커넥션이 묶인다. 외부 API가 1초 걸리면 *1 RPS = 1 커넥션 전속*.

**진단**:

- 느린 요청의 *스택 트레이스 샘플링* — `RestTemplate.execute` / `WebClient.block` 같은 외부 I/O가 트랜잭션 안에 있는지
- DB 쿼리 시간 vs 메소드 실행 시간 *gap*이 큰지

**해결**:

- 외부 호출은 *트랜잭션 밖*으로 (`@TransactionalEventListener(AFTER_COMMIT)` 또는 큐 발행)
- *짧은 트랜잭션 → 외부 호출 → 짧은 트랜잭션* 분리

### 분기 3 — N+1 쿼리

한 요청이 *N+1 쿼리*를 날리면 *N+1 번 커넥션을 빌린다*. 100개 아이템 조회에 *주문 정보 조인*을 lazy로 하면 *101번* 빌리고 반환을 반복한다. 풀 작은 환경에서는 *경합* 폭발.

```java
List<Order> orders = orderRepository.findAll();        // 1 쿼리
for (Order o : orders) {
    o.getItems().size();                                // N 쿼리 (lazy)
}
```

**진단**:

- 쿼리 로깅 활성화 (`logging.level.org.hibernate.SQL=DEBUG`)
- 한 요청에 *예상보다 많은* SELECT 발행 여부

**해결**:

- *fetch join* 또는 *@EntityGraph*
- *batch fetch size* 설정
- DTO projection으로 *필요한 컬럼만*

### 분기 4 — DB Lock 대기로 트랜잭션이 길어짐

다른 트랜잭션이 *같은 row를 잡고 있어* 내가 락 대기 중일 수 있다. 락 대기 = *커넥션은 잡혀있고 DB는 일을 안 함*.

**진단**:

- DB 측 `SHOW PROCESSLIST` (MySQL) 또는 `pg_stat_activity` (Postgres)에서 *waiting* 상태 트랜잭션
- *lock_wait_timeout* 발생 빈도

**해결**:

- 트랜잭션 *짧게* + 락 대상을 *마지막에* 만지기
- 인덱스 최적화 (full table scan으로 lock 범위 폭발 방지)

### 분기 5 — 진짜 풀 사이즈 부족

위 4분기를 모두 점검해 *문제 없음*이면 그제야 풀 사이즈를 본다. 일반 가이드:

```
pool_size = (CPU 코어 수 * 2) + 디스크 수
```

(HikariCP 권장식, *대부분 10~30 사이*에 들어옴)

100개로 늘려도 *DB 측이 동시 100개 처리 가능*해야 의미 있다. *DB 한도*가 50이면 앱 풀 100은 *경합을 DB로 옮길 뿐*.

**해결**:

- *DB max_connections*와 *앱 풀 합계*를 함께 본다
- 여러 앱 인스턴스의 *합산 풀*이 DB 한도를 안 넘는지

## 분기 체크리스트

- [ ] HikariCP `leakDetectionThreshold` 로그에 *leak 스택 트레이스*가 있는가? (있으면 분기 1)
- [ ] 트랜잭션 안에 *외부 I/O*가 있는가? (있으면 분기 2)
- [ ] 한 요청에 *N+1 쿼리*가 발생하는가? (Hibernate 로그) (있으면 분기 3)
- [ ] DB 측에 *락 대기 트랜잭션*이 자주 보이는가? (있으면 분기 4)
- [ ] 위 모두 아니고 *RPS 실측치 / 평균 응답시간*으로 *최소 풀 사이즈*를 계산했는가? (분기 5)

## 흔한 함정

### 함정 — *풀 사이즈만 늘려서 해결*

분기 1~4 중 하나가 살아있으면 *풀을 늘려도 시간문제*. 단지 *고갈 시점이 늦춰질 뿐*. 더 나쁘게는 DB 측 부담이 늘어 *전체 시스템*이 더 흔들린다.

### 함정 — Pool 사이즈 = max threads

서블릿 컨테이너 thread 수와 풀 사이즈를 *같게* 설정하면 *모든 thread가 커넥션 대기 가능*. 일부 thread가 *커넥션 없이 동작 가능한 작업*을 처리하도록 분리해 두는 게 안전.

## 다음 문서

- 더 큰 그림: [Connection Pool 기초](./connection-pool-basics.md)
- HikariCP 파라미터 튜닝: [HikariCP Tuning](./hikari-connection-pool-tuning.md)
- 트랜잭션 + 락 + 풀이 얽힌 모양: [Transaction + Locking + Pool Primer](./transaction-locking-connection-pool-primer.md)
- Pool 메트릭과 Lock 대기의 분기: [Pool Metrics + Lock Wait Timeout Mini Bridge](./pool-metrics-lock-wait-timeout-mini-bridge.md)
