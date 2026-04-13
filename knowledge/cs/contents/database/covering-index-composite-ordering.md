# 커버링 인덱스와 복합 인덱스 컬럼 순서

> 신입 백엔드 개발자가 조회 성능과 인덱스 설계를 설명할 때 필요한 핵심 정리

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [복합 인덱스란](#복합-인덱스란)
- [왼쪽 접두어 규칙](#왼쪽-접두어-규칙)
- [커버링 인덱스란](#커버링-인덱스란)
- [컬럼 순서를 어떻게 정할까](#컬럼-순서를-어떻게-정할까)
- [SQL 예시](#sql-예시)
- [운영에서 확인할 것](#운영에서-확인할-것)
- [관련 문서](#관련-문서)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

조회가 느릴 때 가장 흔한 원인 중 하나는 인덱스가 있어도 **쿼리 패턴에 맞지 않게 설계된 것**이다.

특히 다음 두 가지를 같이 봐야 한다.

- 복합 인덱스의 컬럼 순서
- 커버링 인덱스가 가능한지 여부

이 둘을 이해하면 단순히 “인덱스를 걸었다”가 아니라, **어떤 SQL이 왜 빨라지는지** 설명할 수 있다.

---

## 복합 인덱스란

복합 인덱스는 여러 컬럼을 묶어서 만든 인덱스다.

예:

```sql
CREATE INDEX idx_order_member_status_created_at
ON orders (member_id, status, created_at);
```

이 인덱스는 단일 컬럼 인덱스보다 더 많은 조회 패턴을 지원할 수 있지만, 컬럼 순서가 중요하다.

---

## 왼쪽 접두어 규칙

복합 인덱스는 앞쪽 컬럼부터 활용되는 경우가 많다.

위 예시에서 보통 잘 활용되는 조건은 다음과 같다.

```sql
SELECT * FROM orders
WHERE member_id = 10;

SELECT * FROM orders
WHERE member_id = 10 AND status = 'PAID';

SELECT * FROM orders
WHERE member_id = 10 AND status = 'PAID' AND created_at >= '2026-04-01';
```

반대로 아래처럼 앞 컬럼이 빠지면 인덱스 활용도가 떨어질 수 있다.

```sql
SELECT * FROM orders
WHERE status = 'PAID';
```

즉 복합 인덱스는 “컬럼을 많이 넣을수록 좋다”가 아니라, **자주 쓰는 조건의 결합 순서**를 맞추는 것이 핵심이다.

---

## 커버링 인덱스란

커버링 인덱스는 **쿼리에 필요한 컬럼을 인덱스만으로 모두 읽을 수 있는 상태**를 말한다.

예를 들어 아래 쿼리를 보자.

```sql
SELECT member_id, status
FROM orders
WHERE member_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

만약 인덱스가 다음처럼 잡혀 있으면:

```sql
CREATE INDEX idx_orders_member_created_status
ON orders (member_id, created_at, status);
```

DB는 인덱스만 읽고 결과를 만들 수 있는 가능성이 커진다.

장점:

- 테이블 본문까지 가지 않아도 됨
- 랜덤 I/O를 줄일 수 있음
- pagination, 최근 목록 조회 같은 패턴에서 효과적일 수 있음

주의점:

- 인덱스가 커진다
- 쓰기 비용이 늘어난다
- 무조건 더 많은 컬럼을 넣는다고 좋은 것은 아니다

---

## 컬럼 순서를 어떻게 정할까

보통 다음 순서로 생각한다.

1. `WHERE`에서 자주 쓰는 동등 조건
2. 그다음 범위 조건
3. `ORDER BY`에 자주 쓰는 컬럼
4. 커버링이 필요하면 `SELECT`에 필요한 컬럼까지 검토

예:

```sql
SELECT id, member_id, status
FROM orders
WHERE member_id = 10
  AND status = 'PAID'
  AND created_at >= '2026-04-01'
ORDER BY created_at DESC
LIMIT 50;
```

이 경우는 보통 아래 같은 방향을 고려할 수 있다.

```sql
CREATE INDEX idx_orders_member_status_created_at
ON orders (member_id, status, created_at);
```

실무에서는 다음을 같이 확인한다.

- 실제 조회 조건이 무엇인지
- 정렬이 필요한지
- 페이지네이션이 offset인지 seek인지
- 조회만 빠르면 되는지, 쓰기 성능도 중요한지

---

## SQL 예시

### 예시 1. 최근 결제 주문 조회

```sql
SELECT id, member_id, status, created_at
FROM orders
WHERE member_id = 10
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

인덱스 후보:

```sql
CREATE INDEX idx_orders_member_status_created_at
ON orders (member_id, status, created_at DESC);
```

### 예시 2. 커버링 인덱스 확인

```sql
EXPLAIN
SELECT member_id, status, created_at
FROM orders
WHERE member_id = 10
  AND status = 'PAID';
```

확인 포인트:

- `type`이 범위 스캔인지
- `key`가 예상한 인덱스인지
- `Extra`에 `Using index`가 보이는지

### 예시 3. 잘못된 컬럼 순서

```sql
CREATE INDEX idx_orders_created_at_member_status
ON orders (created_at, member_id, status);
```

이렇게 만들면 `member_id` 중심 조회에는 덜 유리할 수 있다.
컬럼 순서는 “많이 쓰는 조건” 기준으로 정해야 한다.

---

## 운영에서 확인할 것

개발 단계에서 인덱스를 설계할 때는 아래를 같이 본다.

- `EXPLAIN` 결과
- 실제 슬로우 쿼리 로그
- 인덱스 크기
- 쓰기 트래픽 영향
- 동일 테이블의 다른 쿼리와 충돌 여부

특히 인덱스는 한 쿼리만 보고 만들면 위험하다.  
자주 쓰는 목록 조회는 좋아지지만, 전체 시스템에서는 쓰기 성능이 나빠질 수 있다.

---

## 관련 문서

- [인덱스와 실행 계획](./index-and-explain.md)
- [Offset vs Seek Pagination](./pagination-offset-vs-seek.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)

---

## 면접에서 자주 나오는 질문

### Q. 복합 인덱스에서 컬럼 순서가 왜 중요한가요?

- 왼쪽부터 활용되는 성질 때문에, 앞쪽 컬럼이 조회 패턴과 맞아야 인덱스 효율이 좋다.

### Q. 커버링 인덱스는 왜 빠른가요?

- 인덱스만 읽고 결과를 만들 수 있으면 테이블 본문 접근을 줄일 수 있기 때문이다.

### Q. 커버링 인덱스가 항상 좋은가요?

- 아니다.
- 조회는 빨라질 수 있지만 인덱스 크기와 쓰기 비용이 늘어난다.

### Q. 복합 인덱스를 만들 때 가장 먼저 보는 기준은 무엇인가요?

- 실제 `WHERE` 조건과 `ORDER BY` 패턴이다.
