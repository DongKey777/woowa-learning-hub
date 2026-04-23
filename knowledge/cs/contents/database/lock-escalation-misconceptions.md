# Lock Escalation Misconceptions

> 한 줄 요약: lock escalation은 모든 DB에서 같은 방식으로 일어나지 않으며, row lock이 늘어난다고 자동으로 테이블 락으로 바뀐다고 생각하면 운영 판단이 틀어진다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md), [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md), [Savepoint Rollback, Lock Retention, and Escalation Edge Cases](./savepoint-lock-retention-edge-cases.md)
retrieval-anchor-keywords: lock escalation, table lock, row lock, lock granularity, escalation misconception, savepoint lock retention

## 핵심 개념

Lock escalation은 많은 row lock을 잡을 때 더 큰 단위의 lock으로 바뀌는 현상을 말한다.  
하지만 이 개념을 모든 DB에 똑같이 적용하면 오해가 생긴다.

왜 중요한가:

- “row가 많으니 곧 테이블 락이 걸릴 것”이라고 단정하면 원인을 잘못 본다
- 실제 문제는 escalation보다 경합, 범위 락, MDL, 쿼리 패턴일 수 있다
- DB마다 lock 정책이 달라서, 잘못된 일반화는 장애 대응을 흐린다

즉 lock escalation은 종종 설명용 비유로 쓰이지만, **실제 현상은 DB마다 다르다**.

## 깊이 들어가기

### 1. 왜 오해가 생기나

운영에서는 “갑자기 전체가 멈췄다”는 관측만 있고, 내부 락 계층은 보이지 않는다.  
그래서 사람들은 row lock이 늘면 자동으로 테이블 락으로 바뀐다고 생각하기 쉽다.

하지만 실제 원인은 보통 다음 중 하나다.

- 많은 row를 오래 잠금
- gap/next-key lock 범위 확대
- metadata lock 대기
- 느린 쿼리로 인한 lock hold time 증가

### 2. 어떤 DB는 escalation이 있고 어떤 DB는 약하다

lock escalation은 엔진별로 다르게 동작한다.  
따라서 “무조건 테이블 락으로 상승한다”는 식으로 외우면 위험하다.

운영자가 봐야 할 것은 escalation이라는 단어보다:

- 실제 어떤 lock이 잡혔는지
- 대기 중인 세션이 무엇인지
- 범위가 넓어진 이유가 무엇인지

### 3. escalation보다 더 자주 보는 문제

- full scan 때문에 row lock이 많이 걸림
- 인덱스가 없어 범위가 넓어짐
- DDL이 MDL 때문에 막힘
- 장기 트랜잭션이 lock을 오래 유지함

실무에서는 escalation보다 이런 패턴이 더 흔하다.

### 4. 대응 전략

- 필요한 row만 건드리도록 쿼리를 고친다
- chunk 단위로 나눈다
- 트랜잭션을 짧게 유지한다
- MDL과 row lock을 구분해 본다

## 실전 시나리오

### 시나리오 1: row를 많이 건드렸더니 테이블 전체가 느려짐

진짜 원인이 lock escalation이 아닐 수 있다.  
인덱스 미스나 장기 트랜잭션이 더 큰 원인일 수 있다.

### 시나리오 2: 대량 업데이트 후 DDL까지 막힘

row lock과 MDL을 혼동하면 원인을 잘못 찾는다.  
DDL이 막힌 건 escalation이 아니라 metadata lock일 수 있다.

### 시나리오 3: 일부 쿼리만 느린데 전체가 죽은 것처럼 보임

범위 lock이나 hot range가 문제인데, escalation으로 오해하는 경우가 많다.

## 코드로 보기

```sql
-- 대량 row lock이 걸리는 패턴
START TRANSACTION;
UPDATE orders
SET status = 'ARCHIVED'
WHERE created_at < '2025-01-01';
COMMIT;
```

```sql
-- 먼저 확인할 것
SHOW PROCESSLIST;
SELECT * FROM performance_schema.metadata_locks;
```

lock escalation을 떠올리기 전에, **정말 escalation인지, 아니면 MDL/범위 lock/장기 트랜잭션인지** 먼저 봐야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| row-level focus | 세밀하다 | 락 수가 많다 | OLTP |
| larger lock assumption | 이해가 쉽다 | 오판하기 쉽다 | 설명용 |
| chunked processing | 부담이 줄어든다 | 구현이 복잡하다 | 대량 작업 |
| direct DDL/UPDATE | 단순하다 | 영향 범위가 커질 수 있다 | 작은 테이블 |

## 꼬리질문

> Q: row lock이 많아지면 항상 테이블 락으로 바뀌나요?
> 의도: lock escalation을 DB 보편 규칙으로 오해하는지 확인
> 핵심: 아니다, DB마다 다르고 실제 원인은 다른 경우가 많다

> Q: 대량 작업이 느릴 때 무엇부터 봐야 하나요?
> 의도: escalation보다 관측부터 하는지 확인
> 핵심: lock 종류, MDL, 트랜잭션 길이, 인덱스를 본다

> Q: MDL과 lock escalation은 같은 건가요?
> 의도: lock 계층을 구분하는지 확인
> 핵심: 아니다, MDL은 테이블 정의 보호이고 escalation은 락 granularity 변화다

## 한 줄 정리

Lock escalation은 DB마다 다르고, 실제 운영 문제는 종종 범위 락, MDL, 장기 트랜잭션이 더 큰 원인이다.
