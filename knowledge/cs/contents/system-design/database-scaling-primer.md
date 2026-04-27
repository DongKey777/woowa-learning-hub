# Database Scaling Primer

> 한 줄 요약: 초보자가 "DB가 느리다"에서 바로 sharding으로 뛰지 않고, index -> primary/replica -> read-write split -> partitioning -> sharding 순서로 어떤 문제를 푸는지 잡는 입문 문서다.

retrieval-anchor-keywords: database scaling primer, primary replica basics, read write split, indexing basics, query tuning before sharding, read scaling, write scaling, replica lag, read after write, primary fallback, session stickiness, strong read consistency, partitioning vs sharding, shard key basics, hot partition detection

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Shard Key Selection Basics](./shard-key-selection-basics.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)
- [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)
- [인덱스와 실행 계획](../database/index-and-explain.md)
- [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)
- [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
- [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)

---

## 핵심 개념

DB 확장은 보통 "서버를 여러 대 붙이면 끝"이 아니다.
초보자가 가장 많이 헷갈리는 지점은 **읽기 문제, 쓰기 문제, 쿼리 문제, 데이터 크기 문제를 한 단어로 다 `스케일링`이라고 부른다**는 점이다.

실전에서는 보통 아래 순서로 생각한다.

1. 느린 쿼리와 인덱스를 먼저 본다.
2. 같은 읽기가 너무 많으면 cache나 replica로 읽기를 줄인다.
3. primary/replica를 붙였다면 read-write split와 stale read 대응을 같이 설계한다.
4. 큰 테이블 관리가 어려우면 partitioning을 검토한다.
5. 그래도 단일 primary의 write, storage, 운영 한계가 오면 sharding을 검토한다.

즉, sharding은 출발점이 아니라 **여러 쉬운 레버를 다 쓴 뒤에도 한계가 남을 때 들어오는 마지막 축**에 가깝다.

대표 흐름을 아주 단순하게 그리면 아래와 같다.

```text
Client
  -> App
      -> cache
      -> primary (write)
      -> replica (read)

테이블이 너무 커지면:
  -> partitioning

단일 DB 자체가 한계면:
  -> sharding
```

---

## 깊이 들어가기

### 1. 먼저 읽기 병목인지 쓰기 병목인지 구분한다

같은 "DB가 느리다"여도 실제 원인은 다르다.

| 증상 | 먼저 보는 것 | 이유 |
|---|---|---|
| 특정 API 한두 개만 느리다 | query, index, EXPLAIN | 한 개의 나쁜 쿼리는 replica를 늘려도 계속 비싸다 |
| 조회 QPS가 전체적으로 높다 | cache, primary/replica | 같은 읽기를 분산하거나 재사용하면 된다 |
| 쓰기 QPS가 높고 primary CPU/IO가 꽉 찬다 | schema, index 비용, batch/write path | replica는 write 병목을 직접 해결하지 못한다 |
| 오래된 데이터 때문에 테이블이 너무 크다 | partitioning | pruning, retention, archive가 쉬워진다 |
| 단일 DB 용량/쓰기/운영 한계가 명확하다 | sharding | 데이터 자체를 여러 DB로 나눠야 한다 |

핵심은 이거다.

- 읽기 병목인데 sharding부터 가면 너무 비싸다.
- 쿼리 병목인데 replica부터 붙이면 비효율을 복제하는 셈이다.
- 관리 문제인데 sharding으로 가면 운영 복잡도만 급증한다.

### 2. Primary / Replica는 무엇을 해결하나

primary/replica는 같은 데이터를 여러 DB 서버에 복제하는 구조다.

| 역할 | 주 책임 | 초보자 관점의 핵심 |
|---|---|---|
| Primary | write 처리, commit 기준점 | 보통 source of truth가 된다 |
| Replica | primary 데이터를 복제해 read 처리 | read 부하를 분산하지만 최신성이 늦을 수 있다 |

이 구조가 주는 장점:

- read를 여러 replica로 분산할 수 있다
- 장애 대비용 복제본을 둘 수 있다
- 분석성 조회나 목록 조회를 primary에서 떼어낼 수 있다

하지만 primary/replica는 만능이 아니다.

- replica가 많아도 write는 여전히 primary가 받는다
- replication lag 때문에 replica는 최신값이 늦을 수 있다
- failover가 일어나면 topology 변경, promotion, routing 변경이 같이 따라온다

즉, primary/replica는 **읽기 확장 + 가용성 레버**이지, write 확장 레버는 아니다.

### 3. Read-Write Split는 구조보다 라우팅 문제다

primary/replica를 두면 보통 write는 primary로, read는 replica로 보내고 싶어진다.
이걸 read-write split라고 부른다.

```text
POST /orders      -> primary
GET /products     -> replica
GET /orders/123   -> 경우에 따라 primary fallback
```

## 깊이 들어가기 (계속 2)

이때 초보자가 놓치기 쉬운 점은 `split`의 본질이 DB 구조가 아니라 **라우팅 정책**이라는 것이다.

대표 정책:

- 일반 목록/검색/통계성 조회는 replica
- 주문 직후 상세 조회처럼 최신성이 중요한 요청은 primary
- 최근 write가 있었던 세션만 일정 시간 primary
- 아주 중요한 경로만 read-your-writes를 보장

가장 흔한 함정은 stale read다.

- 방금 저장했는데 목록에 안 보인다
- 상태를 바꿨는데 관리자 화면이 예전 값을 보여 준다
- 결제 직후 주문 상태가 아직 `PENDING`처럼 보인다

이 문제는 "replica가 이상하다"보다, 보통 **lag를 허용한 경로에 강한 일관성 기대를 실수로 얹은 것**에 가깝다.

### 4. 인덱싱은 replica보다 먼저 보는 경우가 많다

느린 쿼리 하나가 DB를 태우는 상황이라면, replica를 추가하는 것보다 인덱스를 먼저 보는 편이 훨씬 싸고 효과적일 때가 많다.

왜냐하면:

- 인덱스는 쿼리 1회당 비용을 줄인다
- replica는 같은 비싼 쿼리를 여러 대에 나눠 실행할 뿐이다

예를 들어 `orders` 테이블 500만 건에서 아래 쿼리가 자주 돈다고 하자.

```sql
SELECT *
FROM orders
WHERE user_id = ?
ORDER BY created_at DESC
LIMIT 20;
```

여기서 적절한 인덱스가 없으면 DB는 넓은 범위를 훑을 수 있다.
반대로 `(user_id, created_at)` 같은 인덱스가 맞게 잡히면, 같은 쿼리를 primary와 replica 모두 훨씬 싸게 처리할 수 있다.

초보자 기준의 실전 원칙:

- 느린 API가 있다면 먼저 `EXPLAIN`을 본다
- 조회 조건, 정렬, 조인 순서에 맞는 인덱스를 고민한다
- 인덱스가 많아질수록 write 비용도 오른다는 점을 같이 본다

즉, replica는 용량 레버이고 인덱스는 효율 레버다.
효율 문제를 먼저 해결하지 않으면 용량 문제도 금방 다시 터진다.

### 5. Partitioning은 "한 DB 안에서 정리"가 먼저다

partitioning은 보통 **하나의 큰 테이블을 기준에 따라 나눠 관리하는 방식**이다.
여전히 하나의 논리적 DB 안에 머무는 경우가 많다.

자주 쓰는 상황:

- 시간 기반 데이터가 계속 쌓인다
- 최근 30일 데이터만 자주 읽는다
- 오래된 데이터는 archive하거나 쉽게 drop하고 싶다
- 쿼리가 항상 특정 key나 기간을 포함한다

예:

- 월별 `events_2026_04`
- 날짜 range partition
- tenant tier별 partition

partitioning이 주는 이점:

- partition pruning으로 읽는 범위를 줄일 수 있다
- retention 작업이 쉬워진다
- vacuum, compaction, backup 단위를 더 잘게 다룰 수 있다

하지만 partitioning이 자동으로 해결하지 않는 것도 분명하다.

## 깊이 들어가기 (계속 3)

- 단일 primary write 한계가 그대로일 수 있다
- partition key 선택이 나쁘면 특정 partition만 뜨거워질 수 있다
- cross-partition query는 여전히 비쌀 수 있다

즉, partitioning은 자주 **운영성과 데이터 수명주기 관리**를 개선하는 레버다.
sharding보다 먼저 검토되는 이유도 여기에 있다.

### 6. Sharding은 단일 DB 경계를 넘는 순간이다

sharding은 데이터를 여러 독립 DB나 cluster에 나눠 저장하는 방식이다.
replication이 "같은 데이터 복제"라면, sharding은 "데이터 자체를 분할 보관"한다.

보통 이런 순간에 검토한다.

- 단일 primary의 write throughput이 한계다
- storage 크기 자체가 한 DB 장비/cluster에 부담이다
- tenant별로 부하 편차가 커서 독립적으로 떼어내고 싶다
- blast radius를 tenant/shard 단위로 줄이고 싶다

대표적인 shard key 예:

- `user_id`
- `tenant_id`
- 지역/국가
- 해시 기반 key range

이때 `user_id`나 `tenant_id`가 눈에 잘 띈다고 바로 확정하면 안 된다.
실제 query shape, skew, hot partition 조기 신호를 같이 보는 기준은 [Shard Key Selection Basics](./shard-key-selection-basics.md)에서 따로 정리한다.

하지만 sharding 비용은 훨씬 크다.

- cross-shard join과 transaction이 어려워진다
- shard key를 잘못 잡으면 hot shard가 생긴다
- resharding과 data move가 큰 프로젝트가 된다
- 운영 도구, migration, backup, observability가 전부 복잡해진다

그래서 좋은 질문은 "언제 sharding할까?"보다
"**정말 단일 DB 한계가 맞는가, 아니면 index/replica/partitioning으로 더 버틸 수 있는가**?"다.

### 7. 헷갈리기 쉬운 세 개를 한 번에 구분하기

| 개념 | 무엇을 나누나 | 주 목적 | 아직 남는 문제 |
|---|---|---|---|
| Replication | 같은 데이터를 복제 | read 확장, 가용성 | lag, stale read, write 병목 |
| Partitioning | 큰 테이블을 한 DB 안에서 분할 | pruning, retention, 관리성 | 단일 primary 한계는 남을 수 있음 |
| Sharding | 전체 데이터를 여러 DB로 분할 | write/storage 수평 확장, blast radius 분리 | cross-shard complexity, rebalancing |

이 표만 머리에 남겨도 면접이나 설계 대화에서 훨씬 덜 헷갈린다.

### 8. 보통은 이런 순서로 커진다

주문 서비스가 커지는 과정을 단순화하면 아래와 같다.

## 깊이 들어가기 (계속 4)

1. 초기에는 단일 primary만 둔다.
2. 주문 목록이 느려져 `(user_id, created_at)` 같은 인덱스를 보강한다.
3. 조회가 계속 늘면 replica를 추가해 목록/상세 일부를 분산한다.
4. 주문 직후 화면은 primary fallback으로 read-after-write를 보완한다.
5. `order_events`가 너무 커지면 월별 partitioning으로 pruning과 retention을 개선한다.
6. 특정 대형 tenant 때문에 단일 primary write가 한계면 tenant_id 기준 sharding을 검토한다.

여기서 중요한 감각은 **매 단계마다 문제 종류가 달라진다**는 점이다.

- 초기: query efficiency
- 중기: read capacity
- 그다음: consistency-aware routing
- 더 나중: data lifecycle
- 마지막: single-node or single-cluster ceiling

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 먼저 보는가 |
|---|---|---|---|
| 인덱스 최적화 | 가장 싸고 효과가 큰 경우가 많다 | write 비용과 저장 공간이 늘 수 있다 | 특정 쿼리가 느릴 때 |
| Primary / Replica | read 확장과 장애 대비가 가능하다 | lag와 failover 운영이 필요하다 | 읽기 비중이 높을 때 |
| Read-Write Split | 읽기 경로를 더 적극적으로 분산한다 | stale read 대응과 라우팅 정책이 복잡하다 | consistency class를 구분할 수 있을 때 |
| Partitioning | 큰 테이블 관리와 pruning이 쉬워진다 | key 설계와 cross-partition 접근을 조심해야 한다 | 시간축/retention/대용량 테이블이 문제일 때 |
| Sharding | write와 storage를 수평으로 확장할 수 있다 | 애플리케이션과 운영 복잡도가 가장 크다 | 단일 DB 한계가 명확할 때 |

## 꼬리질문

> Q: replica를 붙이면 write도 같이 빨라지나요?
> 의도: replication이 푸는 문제의 범위 이해 확인
> 핵심: 아니다. replica는 주로 read 확장과 가용성에 도움을 주고, write는 대개 primary가 계속 담당한다.

> Q: read-write split을 했는데 방금 저장한 데이터가 안 보이면 무엇을 의심하나요?
> 의도: lag와 read-after-write trade-off 이해 확인
> 핵심: replica lag와 라우팅 정책을 먼저 본다. 중요 경로는 primary fallback이나 session stickiness가 필요할 수 있다.

> Q: partitioning과 sharding은 왜 다른가요?
> 의도: 데이터 분할의 층위 구분 확인
> 핵심: partitioning은 보통 한 DB 내부의 정리 문제고, sharding은 여러 DB에 데이터를 분산하는 구조 문제다.

> Q: 언제 sharding이 현실적인가요?
> 의도: "무조건 빨리 shard" 오해 교정
> 핵심: query/index/cache/replica/partitioning을 봤는데도 단일 DB의 write, storage, blast radius 한계가 남을 때다.

## 한 줄 정리

DB scaling은 대개 `인덱스 -> replica와 라우팅 -> partitioning -> sharding` 순서로 커지고, 뒤로 갈수록 해결 범위는 커지지만 시스템 복잡도도 훨씬 빨리 증가한다.
