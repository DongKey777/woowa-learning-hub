# 느린 쿼리 분석 플레이북

> 한 줄 요약: 느린 쿼리는 인덱스 하나로 고치는 문제가 아니라, 재현과 계측으로 병목을 분리해 가는 문제다.

**난이도: 🔴 Advanced**

관련 문서:

- [인덱스와 실행 계획](./index-and-explain.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [트랜잭션 실전 시나리오](./transaction-case-studies.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Multi-Tenant Statistics Skew, Plan Drift, and Query Isolation](./multi-tenant-stats-skew-plan-isolation.md)

retrieval-anchor-keywords: slow query playbook, explain triage, explain analyze, explain symptom route, type all, key null, possible_keys empty, key_len, filtered, rows estimate wrong, rows examined high, explain analyze actual rows mismatch, using filesort, using temporary, plan drift, tenant stats skew, index not used, order by limit slow, connection pool starvation, lock wait, latch contention, api slow but db fast, app vs db bottleneck, backend performance debugging, 느린 쿼리 점검 순서, 실행 계획 트리아지

---

## 핵심 개념

느린 쿼리를 볼 때 가장 흔한 실수는 “인덱스를 추가하면 되겠지”라고 바로 결론 내리는 것이다.  
실제로는 다음 순서가 더 중요하다.

1. 어떤 쿼리가 느린지 특정한다.
2. 느린 지점을 재현한다.
3. 실행 계획과 실제 실행 시간을 비교한다.
4. DB 내부 병목인지, connection pool인지, 네트워크인지 분리한다.
5. 고친 뒤 다시 측정한다.

이 문서는 그 순서를 반복 가능하게 만드는 플레이북이다.

---

## 깊이 들어가기

### 1. 먼저 “느리다”를 숫자로 정의한다

감각으로는 안 된다.

- 평균인지 p95인지 p99인지
- 특정 API인지 전체 트래픽인지
- 어떤 시간대에 느린지

먼저 정의해야 한다.

### 2. slow query log부터 확인한다

MySQL 계열에서는 slow query log가 출발점이 될 수 있다.

```sql
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'log_queries_not_using_indexes';
```

운영에서는 로그를 켜는 것 자체가 비용이 될 수 있으므로, 무턱대고 장시간 켜지 말고 범위와 기간을 정한다.

### 3. 실행 계획을 본다

`EXPLAIN`은 기본이고, 가능하면 `EXPLAIN ANALYZE`까지 본다.

```sql
EXPLAIN ANALYZE
SELECT id, status, created_at
FROM orders
WHERE user_id = 12345
ORDER BY created_at DESC
LIMIT 20;
```

여기서 봐야 할 포인트:

- `type`이 full scan인지
- `rows` 추정치가 큰지
- `Using filesort`가 있는지
- `Using temporary`가 있는지
- 실제 row와 추정 row가 얼마나 다른지

### 4. 인덱스 문제인지 확인한다

아래 질문을 순서대로 본다.

- 조건이 sargable 한가
- 복합 인덱스의 컬럼 순서가 맞는가
- 선택도가 충분한가
- 커버링 인덱스가 가능한가
- 쿼리가 인덱스를 실제로 선택하는가

예를 들어 다음 쿼리는 인덱스를 잘 타기 쉽다.

```sql
SELECT id, status
FROM orders
WHERE user_id = 12345
  AND created_at >= '2026-01-01'
ORDER BY created_at DESC
LIMIT 20;
```

하지만 아래는 성능이 떨어질 수 있다.

```sql
SELECT *
FROM orders
WHERE DATE(created_at) = '2026-01-01';
```

### 5. DB가 아니라 connection pool이 병목일 수 있다

쿼리 자체는 빠른데 서비스가 느리다면, 커넥션 점유 시간을 봐야 한다.

```text
DB query time < 20ms
API latency > 500ms
```

이런 경우는 다음을 의심한다.

- 트랜잭션이 너무 길다
- 외부 API 호출이 트랜잭션 안에 들어 있다
- 커넥션 풀 대기 시간이 길다
- 배치 작업이 커넥션을 오래 잡고 있다

### 6. 캐시와 데이터 분포도 본다

운영에서는 캐시 미스나 데이터 skew가 쿼리를 느리게 만든다.

- 특정 user_id만 유독 큰가
- hot key가 몰리는가
- 통계가 오래돼 optimizer가 잘못된 계획을 고르는가
- 특정 tenant 하나가 전체 분포를 흔들고 있지는 않은가

필요하면 `ANALYZE TABLE` 같은 통계 갱신도 검토해야 한다.

---

## 실전 시나리오

### 시나리오 1: 배포 후 갑자기 p95가 튄다

증상:

- 특정 목록 API가 느려짐
- DB CPU가 올라감
- scan 비율이 높아짐

원인 후보:

- 조건절이 바뀌어 인덱스를 못 탐
- 새 정렬 조건이 추가됨
- 통계가 오래되어 잘못된 실행 계획이 나옴

### 시나리오 2: 로컬에서는 빠른데 운영에서만 느리다

대개 다음 중 하나다.

- 데이터량 차이
- cold cache
- real index selectivity 차이
- concurrent load

로컬에서 재현이 안 되면 운영과 같은 데이터 분포와 실행 계획을 봐야 한다.

### 시나리오 3: 쿼리는 빠른데 서비스는 느리다

이 경우는 종종 DB가 문제가 아니다.

- connection pool 대기
- N+1
- 트랜잭션 경계 과대
- 네트워크 지연

즉 SQL만 보면 안 된다.

---

## 코드로 보기

### 진단 순서 예시

```sql
-- 1) 슬로우 쿼리 후보 찾기
SHOW FULL PROCESSLIST;

-- 2) 실행 계획 확인
EXPLAIN
SELECT ...

-- 3) 통계 갱신 여부 확인
ANALYZE TABLE orders;

-- 4) 인덱스 강제 비교(임시 진단용)
SELECT ...
FROM orders FORCE INDEX (idx_user_created_at)
WHERE user_id = 12345
ORDER BY created_at DESC
LIMIT 20;
```

### 디버깅용 관찰 항목

```text
query text
bind parameter values
execution time
rows examined
rows sent
lock wait time
connection wait time
replica lag
tenant_id / tenant tier
```

이 정보가 있어야 “느림”을 하나의 원인으로 착각하지 않는다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 인덱스 추가 | 읽기 개선이 빠르다 | 쓰기 비용이 늘어난다 | 명확한 조회 패턴이 있을 때 |
| 쿼리 재작성 | 구조를 바로잡을 수 있다 | 코드 영향 범위가 있다 | sargable 개선이 가능할 때 |
| 캐시 추가 | 지연을 크게 줄일 수 있다 | 정합성 관리가 어렵다 | 읽기 집중 워크로드일 때 |
| 배치/비동기화 | 피크를 낮춘다 | 복잡도가 올라간다 | 즉시 응답이 필수가 아닐 때 |
| 통계/플랜 튜닝 | 적은 변경으로 개선 가능 | 지속성이 낮을 수 있다 | optimizer 오판이 원인일 때 |

핵심은 “빠르게 만드는 방법”과 “계속 빠르게 유지되는 방법”을 구분하는 것이다.

---

## 꼬리질문

> Q: 인덱스를 추가했는데 왜 더 느려질 수 있나?
> 의도: 쓰기 비용, 옵티마이저 선택, 통계 문제 이해 확인
> 핵심: 인덱스는 공짜가 아니고, DB가 실제로 선택하지 않을 수도 있다

> Q: 쿼리 시간은 짧은데 API가 느리면 어디를 보나?
> 의도: DB 외 병목 분리 능력 확인
> 핵심: connection pool, 트랜잭션 경계, 네트워크, 애플리케이션 로직

> Q: 운영에서 실험적으로 인덱스를 검증하는 안전한 방법은?
> 의도: 검증과 롤백 감각 확인
> 핵심: 샘플 데이터, 복제본, FORCE INDEX 비교, 피크 시간 외 검증

---

## 한 줄 정리

느린 쿼리는 SQL 한 줄을 고치는 문제가 아니라, 재현 가능하게 원인을 분리하고 가장 작은 변경으로 병목을 제거하는 문제다.
