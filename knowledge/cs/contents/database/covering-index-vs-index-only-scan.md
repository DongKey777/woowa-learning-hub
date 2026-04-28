# Covering Index vs Index-Only Scan

> 한 줄 요약: 커버링 인덱스는 "인덱스만으로 답을 만들 수 있는 설계"이고, index-only scan은 "실제로 테이블 본문을 안 읽고 끝나는 실행"이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: covering index, index-only scan, using index, using index vs index only scan, mysql using index vs postgresql index only scan, visibility map, heap fetches, heap fetches not zero, MVCC visibility, covering index but still heap fetches, covering index but still reads table, why heap fetches remain, using index but still table lookup, secondary index lookup, EXPLAIN ANALYZE, postgresql cluster vs index only scan, postgresql cluster physical row order, cluster does not mean index only scan, cluster 한번 하면 계속 정렬되나요, postgresql cluster 헷갈림, physical row order index only scan, 커버링 인덱스와 index only scan 차이, using index 의미

## 증상별 바로 가기

- `Using index`와 `Index Only Scan`을 같은 뜻으로 읽고 있거나, MySQL `Extra`와 PostgreSQL plan node를 같은 신호로 해석하고 있다면 이 문서에서 용어부터 분리한다.
- `covering index를 만들었는데 PostgreSQL에서 Heap Fetches가 남는다`, `visibility map 때문에 heap/table를 다시 읽는다` 같은 follow-up이면 먼저 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)에서 초급 멘탈모델을 잡고, 그다음 이 문서에서 MVCC visibility와 vacuum 상태를 함께 본다.
- PostgreSQL `CLUSTER`, `Index Only Scan`, physical row order를 한 덩어리로 헷갈리고 있다면 먼저 [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)의 비교표로 저장 구조 층을 분리한 뒤 이 문서를 읽는다.
- `Using index`는 보이는데도 읽기 p95가 그대로이거나, 컬럼을 더 넣은 뒤 write가 무거워졌다면 [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md)으로 이동한다.
- `Using filesort`, `ORDER BY ... LIMIT`, left-prefix 문제가 먼저면 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)로 돌아가서 인덱스 shape부터 다시 잡는다.

## 핵심 개념

- 관련 문서:
  - [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
  - [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md)
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
  - [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md)

커버링 인덱스와 index-only scan은 비슷하게 들리지만, 같은 문장이 아니다.

- 커버링 인덱스는 쿼리에 필요한 컬럼이 인덱스 안에 모두 들어 있는 상태를 뜻한다.
- index-only scan은 실행 엔진이 실제로 heap/table 본문을 읽지 않고 끝내는 실행 경로를 뜻한다.

즉, 커버링 인덱스는 설계이고 index-only scan은 실행 결과다.

이 차이를 모르면 "인덱스는 다 같은 거 아닌가?"라는 착각에 빠진다.

## 초급자용 30초 구분

PostgreSQL에서 아래 셋을 같은 층으로 묶으면 거의 항상 헷갈린다.

| 헷갈리는 말 | 실제로 답하는 질문 | 안전한 첫 문장 |
|------|------|------|
| covering index | "이 쿼리에 필요한 컬럼이 인덱스에 다 있나?" | 컬럼 구성에 대한 설계 이야기다 |
| `Index Only Scan` | "이번 실행에서 heap을 안 읽고 끝내려는 경로를 탔나?" | 실행 계획 이름이다 |
| `CLUSTER` / physical row order | "table heap row를 어떤 순서로 다시 써 뒀나?" | 저장 배치나 maintenance 이야기다 |

짧게 말하면 이렇다.

- covering index: 인덱스 안에 무엇을 넣었는가
- `Index Only Scan`: 그 인덱스로 이번 실행을 어떻게 끝냈는가
- `CLUSTER`: heap row 순서를 한 번 어떻게 정리했는가

즉 `CLUSTER`는 row 배치 쪽 이야기이고, `Index Only Scan`은 heap 생략 실행 이야기다. 이름에 `index`가 같이 보여도 같은 버튼이 아니다.

## 깊이 들어가기

### 1. MySQL InnoDB에서 커버링 인덱스가 빠른 이유

InnoDB secondary index의 leaf에는 인덱스 키와 primary key가 들어 있다.  
쿼리가 필요한 컬럼을 모두 secondary index에서 해결할 수 있으면, 테이블 본문으로 내려가는 추가 탐색을 줄일 수 있다.

예를 들어:

```sql
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

여기서 필요한 컬럼이 인덱스에 다 들어 있으면 `Using index`가 나타날 수 있다.  
이건 테이블 접근을 줄인다는 의미에서 매우 중요하다.
다만 커버링을 위해 컬럼을 계속 추가하면 leaf entry 폭이 커지고, write path와 cache residency 비용도 같이 늘어난다.

### 2. PostgreSQL index-only scan은 visibility 확인이 핵심이다

PostgreSQL은 단순히 컬럼이 인덱스에 있다는 이유만으로 테이블 본문을 완전히 건너뛰지 않는다.  
MVCC 때문에 해당 heap tuple이 현재 스냅샷에서 보이는지 확인해야 하고, 이때 visibility map이 중요하다.

핵심은 이렇다.

- page가 all-visible이면 heap 방문을 생략할 가능성이 커진다
- vacuum이 덜 됐거나 page가 아직 visible로 표시되지 않으면 heap fetch가 다시 생긴다

그래서 PostgreSQL에서 index-only scan은 "이론상 가능"과 "실제로 heap fetch 0"이 다르다.

### 3. 같은 "인덱스만 읽는다"라도 엔진마다 조건이 다르다

실무에서는 아래처럼 구분하면 안전하다.

| 관점 | MySQL InnoDB | PostgreSQL |
|------|------|------|
| 용어 | `Using index`가 커버링 인덱스 신호 | `Index Only Scan` 실행 경로 |
| 핵심 조건 | 필요한 컬럼이 모두 인덱스에 있어야 함 | 인덱스 + visibility map + heap fetch 최소화 |
| MVCC 영향 | 읽기 경로에 따라 추가 확인 비용이 남을 수 있음 | heap visibility 확인이 핵심 병목이 될 수 있음 |

### 4. 설계와 실행은 같지 않다

커버링 인덱스를 설계했다고 해서 항상 index-only scan이 되는 것은 아니다.

- 쿼리에 `SELECT *`가 있으면 깨진다
- 함수나 계산식이 들어가면 필요한 컬럼이 늘어난다
- MVCC/visibility 확인 때문에 heap 접근이 생길 수 있다
- 옵티마이저가 더 싸다고 판단하면 다른 경로를 고를 수 있다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `covering index`
- `index-only scan`
- `Using index`
- `visibility map`
- `heap fetches`
- `MVCC visibility`
- `EXPLAIN ANALYZE`

## 실전 시나리오

### 시나리오 1. MySQL에서는 빨라졌는데 PostgreSQL에서는 덜 빨라 보인다

같은 API라도 엔진이 다르면 실행 경로가 다르다.  
MySQL에서는 커버링 인덱스로 테이블 접근을 줄였는데, PostgreSQL에서는 visibility 확인 때문에 heap fetch가 남을 수 있다.

### 시나리오 2. 인덱스를 추가했는데도 `SELECT *` 때문에 효과가 없다

조회 API에서 필요한 컬럼이 조금이라도 늘어나면 커버링이 깨질 수 있다.  
특히 목록 API는 처음엔 작아 보여도 나중에 DTO가 커지면서 테이블 본문을 다시 읽게 되는 일이 많다.

### 시나리오 3. vacuum이 밀리면 index-only scan 효과가 떨어진다

PostgreSQL에서 index-only scan을 기대했는데 heap fetch가 계속 보인다면, vacuum과 visibility map 상태를 먼저 봐야 한다.  
쿼리만 고쳐서는 안 되는 경우가 많다.

## 코드로 보기

### MySQL 예시

```sql
CREATE INDEX idx_orders_user_status_created_at
ON orders (user_id, status, created_at);

EXPLAIN
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 10
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

확인 포인트:

- `Extra`에 `Using index`가 보이는지
- `type`이 불필요하게 넓지 않은지

### PostgreSQL 예시

```sql
CREATE INDEX idx_orders_user_status_created_at
ON orders (user_id, status, created_at);

EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 10
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

확인 포인트:

- `Index Only Scan`인지
- `Heap Fetches`가 얼마나 있는지
- `BUFFERS`에서 heap read가 남는지

### visibility를 개선하는 쪽

```sql
VACUUM (ANALYZE) orders;
```

이 작업은 커버링 인덱스를 만드는 것과 다른 층의 최적화다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 커버링 인덱스 추가 | 테이블 접근을 줄인다 | 인덱스 크기와 쓰기 비용이 늘어난다 | 목록/검색 API가 반복될 때 |
| index-only scan 기대 | 읽기 비용을 크게 줄일 수 있다 | visibility 조건이 맞아야 한다 | PostgreSQL + vacuum 상태가 좋을 때 |
| `SELECT *` 유지 | 코드 변경이 적다 | 커버링이 깨진다 | 개발 초기, 임시 도구 |
| 필요한 컬럼만 명시 | 실행 계획이 좋아진다 | DTO/쿼리 관리가 더 필요하다 | 운영 API |

핵심은 "인덱스에 컬럼이 있느냐"보다, **실제로 heap/table 본문을 얼마나 안 읽게 되는가**다.

## 꼬리질문

> Q: 커버링 인덱스와 index-only scan은 같은 말인가요?
> 의도: 설계와 실행 경로를 구분하는지 확인
> 핵심: 커버링 인덱스는 설계이고, index-only scan은 실행 결과다

> Q: PostgreSQL에서 index-only scan이 있어도 heap fetch가 생기는 이유는 무엇인가요?
> 의도: MVCC visibility와 visibility map 이해 여부 확인
> 핵심: 모든 heap page가 all-visible로 표시된 상태가 아니기 때문이다

> Q: MySQL에서 `Using index`가 보이면 항상 최고 성능인가요?
> 의도: 실행 계획 신호를 절대화하지 않는지 확인
> 핵심: 인덱스만 읽어도 정렬, 범위, 통계, 다른 병목은 남을 수 있다

## 한 줄 정리

커버링 인덱스는 테이블 본문을 덜 읽게 만드는 설계이고, index-only scan은 그 설계가 실제 실행에서 테이블 접근을 얼마나 없앴는지를 보여주는 결과다.
