---
schema_version: 3
title: B+Tree vs LSM-Tree
concept_id: database/bptree-vs-lsm-tree
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- btree-vs-lsm
- storage-engine
- read-write-amplification
- compaction
aliases:
- b+tree vs lsm tree
- btree vs lsm
- b tree vs lsm
- b+ tree
- lsm tree
- lsm-tree
- write optimized storage engine
- compaction sstable memtable
- read amplification write amplification
- 범위 조회 인덱스
symptoms:
- 인덱스는 전부 B-Tree라고 생각해 write-heavy storage engine의 compaction/read amplification 비용을 놓친다
- LSM이 쓰기에 강하다는 말만 보고 range scan, compaction, space amplification 운영 비용을 보지 않는다
- OLTP point/range lookup과 event/log write burst를 같은 storage trade-off로 판단한다
intents:
- comparison
- deep_dive
- design
prerequisites:
- database/index-and-explain
- database/clustered-index-locality
next_docs:
- database/btree-latch-contention-hot-pages
- data-structure/lsm-friendly-index-structures
- database/query-tuning-checklist
linked_paths:
- contents/database/index-and-explain.md
- contents/database/clustered-index-locality.md
- contents/database/btree-latch-contention-hot-pages.md
- contents/database/mvcc-replication-sharding.md
- contents/data-structure/lsm-friendly-index-structures.md
- contents/database/query-tuning-checklist.md
confusable_with:
- database/index-basics
- database/clustered-index-locality
- database/btree-latch-contention-hot-pages
- data-structure/lsm-friendly-index-structures
forbidden_neighbors: []
expected_queries:
- B+Tree와 LSM-Tree는 read, range scan, write throughput, compaction 비용 기준으로 어떻게 달라?
- LSM Tree가 쓰기에 강하지만 read amplification과 compaction p99를 관리해야 하는 이유가 뭐야?
- OLTP 주문 테이블처럼 범위 조회가 많으면 B+Tree가 운영하기 쉬운 이유를 설명해줘
- RocksDB LevelDB 같은 LSM 계열에서 memtable SSTable flush compaction이 어떤 trade-off를 만드는지 알려줘
- B-Tree index basics에서 storage engine trade-off로 넘어갈 때 어떤 문서를 보면 돼?
contextual_chunk_prefix: |
  이 문서는 B+Tree vs LSM-Tree chooser로, B+Tree의 point lookup/range scan locality와
  LSM-Tree의 write buffering, memtable/SSTable flush, compaction, read/write/space amplification을 비교해
  workload별 storage engine trade-off를 설명한다.
---
# B+Tree vs LSM-Tree

> 한 줄 요약: B+Tree는 읽기와 범위 조회에 강한 범용 인덱스이고, LSM-Tree는 쓰기 처리량을 높이는 대신 컴팩션과 읽기 증폭 비용을 함께 관리해야 하는 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인덱스와 실행 계획](./index-and-explain.md)
> - [Clustered Index Locality](./clustered-index-locality.md)
> - [B-Tree Latch Contention and Hot Pages](./btree-latch-contention-hot-pages.md)
> - [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
> - [LSM-Friendly Index Structures](../data-structure/lsm-friendly-index-structures.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)

> retrieval-anchor-keywords: b+tree vs lsm tree, btree vs lsm, b tree vs lsm, b+ tree, lsm tree, lsm-tree, write optimized storage engine, write heavy vs read heavy, compaction, sstable, memtable, flush, range scan, read amplification, write amplification, space amplification, rocksdb, leveldb, innodb, oltp index tradeoff, 범위 조회 인덱스, 쓰기 최적화 저장소

## 이 문서 다음에 보면 좋은 문서

- B+Tree 쪽에서 PK 정렬과 page locality 비용까지 이어서 보려면 [Clustered Index Locality](./clustered-index-locality.md)가 바로 붙는다.
- LSM이 실제로 memtable, sparse index, Bloom filter를 어떻게 조합하는지 자료구조 관점으로 보려면 [LSM-Friendly Index Structures](../data-structure/lsm-friendly-index-structures.md)를 같이 본다.
- 실제 SQL/EXPLAIN 문맥에서 B+Tree 인덱스 감각을 먼저 고정하고 싶다면 [인덱스와 실행 계획](./index-and-explain.md)으로 돌아가면 된다.

---

## 핵심 개념

B+Tree와 LSM-Tree는 둘 다 “빠르게 찾기 위한 자료구조”지만, 최적화하는 방향이 다르다.

- B+Tree는 디스크 페이지를 계층적으로 탐색하면서 **읽기와 범위 조회**를 안정적으로 빠르게 만든다.
- LSM-Tree는 메모리에서 먼저 쓰고, 나중에 디스크로 정리하면서 **쓰기 처리량**을 크게 높인다.

실무에서 중요한 건 “무엇이 더 좋냐”가 아니라 다음이다.

- OLTP에서 읽기와 쓰기 비율이 어떤가
- 범위 조회가 많은가, 단건 조회가 많은가
- 장비가 SSD인가 HDD인가
- 쓰기 폭주를 흡수해야 하는가
- compaction 비용을 운영팀이 감당할 수 있는가

### 한 줄로 구분하면

- B+Tree: “찾기”와 “범위 훑기”가 강한 구조
- LSM-Tree: “많이 쓰고 나중에 정리”하는 구조

`인덱스`를 말할 때 보통 떠올리는 것은 B+Tree다.  
반면 Cassandra, LevelDB, RocksDB 계열은 LSM-Tree 계열의 사고방식을 자주 쓴다.

> B+Tree 인덱스의 기본 감각은 [인덱스와 실행 계획](./index-and-explain.md)에서 이어서 보면 좋다.

---

## 깊이 들어가기

### 1. B+Tree는 왜 읽기에 강한가

B+Tree는 루트에서 리프까지 내려가며 값을 찾는다.  
중요한 점은 실제 데이터 위치가 리프 쪽에 있고, 리프 노드가 정렬되어 있다는 것이다.

그래서:

- `=` 조건 조회가 빠르다
- `BETWEEN`, `>=`, `<=` 같은 범위 조회가 좋다
- 정렬된 리프를 순차적으로 따라가며 스캔할 수 있다

즉 B+Tree는 “한 건을 빨리 찾는 것”뿐 아니라 **옆의 값까지 계속 읽는 것**에 유리하다.

### 2. LSM-Tree는 왜 쓰기에 강한가

LSM-Tree(Log-Structured Merge Tree)는 기본적으로 쓰기를 바로 디스크의 정렬된 구조에 밀어 넣지 않는다.

전형적인 흐름은 이렇다.

1. write는 먼저 메모리 구조에 들어간다.
2. 일정 크기가 되면 immutable file로 flush된다.
3. 백그라운드 compaction이 여러 파일을 정리한다.

이 구조의 장점은:

- 작은 쓰기를 모아서 처리할 수 있다
- 랜덤 쓰기 비용을 줄일 수 있다
- 높은 write throughput을 낼 수 있다

하지만 공짜가 아니다.

- flush와 compaction이 백그라운드에서 계속 돈다
- 같은 key를 여러 레이어에서 확인해야 할 수 있다
- tombstone과 중복 버전이 생긴다

### 3. 읽기/쓰기 증폭의 차이

#### Write amplification

한 번 쓴 데이터를 실제로는 여러 번 다시 쓰는 정도다.

- B+Tree는 page split, page merge, redo/undo 같은 비용이 있다
- LSM-Tree는 flush와 compaction 때문에 같은 데이터가 여러 번 이동한다

#### Read amplification

한 번 읽으려는 요청이 내부적으로 얼마나 많은 페이지나 파일을 보게 되는가다.

- B+Tree는 보통 루트→리프 경로가 짧아 읽기 증폭이 낮은 편이다
- LSM-Tree는 여러 SSTable과 레벨을 확인해야 해서 읽기 증폭이 커질 수 있다

#### Space amplification

디스크에 중복 데이터가 얼마나 쌓이는가다.

- B+Tree는 page split의 오버헤드가 있다
- LSM-Tree는 compaction 전 중복 버전과 tombstone이 남는다

### 4. Range scan은 왜 차이가 큰가

범위 조회는 OLTP에서 생각보다 자주 나온다.

예:

```sql
SELECT * 
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-02'
ORDER BY created_at;
```

B+Tree는 리프 노드가 정렬되어 있어서 이런 패턴에 강하다.  
한 번 위치를 찾은 뒤에는 옆 레코드를 계속 따라가면 된다.

LSM-Tree는 key 정렬 자체는 유지하지만, 데이터가 여러 SSTable에 흩어져 있을 수 있다.  
그래서 범위 조회가 많으면:

- 여러 파일을 확인해야 하고
- merge 과정이 필요하고
- compaction 상태에 따라 성능 편차가 커질 수 있다

즉 범위 조회가 중요한 서비스일수록 B+Tree가 운영하기 편하다.

### 5. SSD와 HDD에서는 감각이 달라진다

#### HDD

HDD는 랜덤 I/O가 비싸다.  
그래서 순차 쓰기 패턴이 강한 LSM-Tree가 유리해질 수 있다.

#### SSD

SSD는 랜덤 접근 비용이 HDD보다 훨씬 낮다.  
그래서 B+Tree의 랜덤 읽기/쓰기 패턴도 실무에서 충분히 감당 가능하다.

하지만 SSD라고 해서 LSM-Tree가 자동으로 우위가 되는 건 아니다.

- compaction이 너무 무거우면 쓰기 지연이 튈 수 있다
- read amplification이 커지면 p95/p99가 흔들릴 수 있다

즉 장비가 SSD로 바뀌면 “LSM이 무조건 좋다”가 아니라, **읽기/쓰기 패턴의 균형을 다시 봐야 한다**가 맞다.

### 6. OLTP 팀이 왜 이걸 알아야 하나

OLTP 팀에서 이 주제가 중요한 이유는 단순하다.

- 인덱스 설계가 사실상 B+Tree 사고방식 위에 있다
- write-heavy 서비스는 compaction 비용을 놓치면 장애가 난다
- range scan이 많으면 storage 구조가 곧 latency가 된다
- replication, backup, migration 때 storage amplification이 운영비로 이어진다

특히 아래 상황에서는 반드시 의식해야 한다.

- 주문, 결제, 재고 같은 트랜잭션성 데이터
- 최신 상태를 자주 갱신하는 테이블
- 날짜 범위 조회가 많은 로그성 테이블
- 쓰기 폭주가 오는 이벤트성 테이블

---

## 실전 시나리오

### 시나리오 1: 주문 테이블 조회는 빠른데 쓰기가 흔들린다

주문 서비스에서 `order_id` 단건 조회는 충분히 빠르지만, 초당 수천 건 insert/update가 들어오면 병목이 생긴다.

점검 포인트:

- 인덱스 page split이 잦은가
- 트랜잭션이 너무 길어 page latch가 늘어나는가
- 쓰기 경합이 특정 key에 몰리는가

이 경우 B+Tree 기반 DB에서는:

- 복합 인덱스 재설계
- 트랜잭션 경계 축소
- hot key 분산

같은 대응이 먼저다.

### 시나리오 2: 로그 적재는 빠른데 조회가 느리다

이벤트 로그처럼 쓰기량이 많고 조회는 나중에 하는 시스템은 LSM-Tree 사고방식이 잘 맞는다.

하지만 운영 중에 다음 문제가 생긴다.

- compaction backlog
- tombstone 누적
- 특정 범위 조회 지연 증가

이 경우 “쓰기 빠르니 끝”이 아니라, compaction 설정과 retention 정책까지 함께 봐야 한다.

### 시나리오 3: 날짜 범위 조회가 많은 서비스

예:

```sql
SELECT user_id, total_amount
FROM daily_sales
WHERE sale_date BETWEEN '2026-04-01' AND '2026-04-30'
ORDER BY sale_date, user_id;
```

이런 쿼리는 B+Tree 계열 인덱스가 자연스럽다.  
LSM 계열에서는 여러 파일을 건너뛰며 읽을 가능성이 커서, 범위가 넓을수록 비용이 올라간다.

### 시나리오 4: 복제본은 있는데 복제 지연이 크다

Replication이 붙은 환경에서는 storage 구조뿐 아니라 write amplification이 replica lag에도 영향을 준다.

느린 compaction이나 page split이 누적되면:

- primary write latency 상승
- replication lag 증가
- 읽기 분산 효과 감소

그래서 storage 구조 선택은 단독 문제가 아니라 운영 문제다.

---

## 코드로 보기

### 1. B+Tree 감각을 SQL로 보기

```sql
CREATE INDEX idx_orders_created_at ON orders (created_at, id);

SELECT id, created_at
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-02'
ORDER BY created_at, id
LIMIT 100;
```

이 패턴은:

- 범위 조건
- 정렬
- 페이징

이 한 번에 맞물릴 때 B+Tree의 장점이 잘 드러난다.

### 2. LSM-Tree의 flush/compaction 감각을 의사코드로 보기

```text
write(key, value):
  memtable.put(key, value)
  if memtable.isFull():
      flush(memtable -> sstable)
      schedule_compaction()

read(key):
  check memtable
  check immutable memtables
  check sstable levels from newest to oldest
```

핵심은 `read`가 단일 구조 하나만 보는 게 아니라는 점이다.  
여러 레이어를 훑을수록 read amplification이 커진다.

### 3. compaction이 튀는 상황의 감각

```text
ingest_rate > compaction_rate
  -> sstable files accumulate
  -> read amplification rises
  -> disk usage grows
  -> p99 latency worsens
```

이건 단순 저장 문제처럼 보여도 결국 서비스 지연 문제다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| B+Tree | 범위 조회와 단건 조회가 안정적이다 | 랜덤 쓰기와 page split 비용이 있다 | OLTP, 인덱스 중심 설계 |
| LSM-Tree | 쓰기 처리량이 높다 | compaction과 read amplification을 관리해야 한다 | write-heavy, 로그성 워크로드 |
| SSD + B+Tree | 범용성이 높고 운영이 익숙하다 | 초고쓰기량에서는 병목이 될 수 있다 | 일반적인 백엔드 서비스 |
| HDD + LSM-Tree | 순차 쓰기 패턴에 잘 맞는다 | 읽기와 compaction 설계가 중요하다 | 대용량 적재, 일부 저장소 엔진 |

판단 기준은 다음 순서가 실용적이다.

1. 읽기/쓰기 비율이 어떤가
2. 범위 조회가 많은가
3. p95/p99 지연이 중요한가
4. 저장 비용보다 운영 단순성이 중요한가
5. compaction/backfill을 감당할 팀 역량이 있는가

OLTP 팀은 보통 “쓰기만 빠른 구조”보다 **예측 가능한 지연과 운영 단순성**을 더 중요하게 본다.

---

## 꼬리질문

> Q: B+Tree와 B-Tree는 같은 건가요?
> 의도: 정확한 용어와 리프 정렬 구조 이해 여부 확인
> 핵심: 엄밀히는 다르며, DB 인덱스는 보통 B+Tree 특성을 가진다

> Q: LSM-Tree가 쓰기에 강한데 왜 모든 DB가 LSM-Tree를 쓰지 않나요?
> 의도: read amplification, compaction, range scan 비용을 아는가
> 핵심: 읽기와 운영 복잡도 비용이 커질 수 있다

> Q: range scan이 많으면 왜 B+Tree가 유리한가요?
> 의도: 리프 정렬과 순차 접근 감각 확인
> 핵심: 범위 시작점을 찾은 뒤 이웃 키를 따라가면 되기 때문이다

> Q: SSD면 LSM-Tree의 장점이 사라지나요?
> 의도: 스토리지 특성과 알고리즘 선택을 구분하는지 확인
> 핵심: SSD에서도 write amplification과 compaction 비용은 남는다

> Q: OLTP 팀이 storage 구조를 왜 알아야 하나요?
> 의도: 운영과 설계의 연결 여부 확인
> 핵심: 인덱스, latency, replication lag, batch 처리에 직접 영향을 주기 때문이다

---

## 한 줄 정리

B+Tree는 읽기와 범위 조회에 강한 기본 선택이고, LSM-Tree는 쓰기량을 흡수하는 데 강하지만 compaction과 read amplification까지 같이 운영할 수 있어야 쓸 수 있다.
