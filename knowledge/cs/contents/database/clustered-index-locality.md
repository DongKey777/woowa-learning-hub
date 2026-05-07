---
schema_version: 3
title: Clustered Index Locality
concept_id: database/clustered-index-locality
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- clustered-index
- primary-key-locality
- secondary-index-lookup
- page-split
aliases:
- clustered index
- clustered index locality
- primary key locality
- leaf page locality
- page split locality
- secondary index lookup
- physical clustering
- random I/O
- clustered PK locality
- 클러스터드 인덱스 locality
symptoms:
- InnoDB primary key를 단순 식별자로만 보고 테이블 물리 배치와 range scan locality를 결정한다는 점을 놓친다
- UUID 같은 random PK로 page split과 locality 저하가 생기는데 secondary index 문제로만 진단한다
- secondary index는 있어도 본문 row 접근이 흩어져 buffer pool miss와 random I/O가 남는다
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- database/index-and-explain
- database/covering-index-composite-ordering
next_docs:
- database/clustered-primary-key-update-cost
- database/btree-latch-contention-hot-pages
- database/page-split-merge-fill-factor
linked_paths:
- contents/database/index-and-explain.md
- contents/database/covering-index-composite-ordering.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/innodb-buffer-pool-internals.md
- contents/database/clustered-primary-key-update-cost.md
- contents/database/page-split-merge-fill-factor.md
confusable_with:
- database/index-basics
- database/covering-index-vs-index-only-scan
- database/clustered-primary-key-update-cost
- database/btree-latch-contention-hot-pages
forbidden_neighbors: []
expected_queries:
- InnoDB clustered index는 primary key 순서가 테이블 물리 locality를 결정한다는 뜻이야?
- UUID random PK를 쓰면 page split, buffer pool miss, range scan locality가 왜 나빠질 수 있어?
- secondary index lookup 후 primary key로 본문 row를 찾는 비용이 clustered locality에 따라 달라지는 이유가 뭐야?
- monotonic PK는 locality에는 좋지만 hot page를 만들 수 있다는 trade-off를 설명해줘
- clustered index를 단순 PK가 아니라 physical layout decision으로 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Clustered Index Locality deep dive로, InnoDB primary key가 clustered index leaf에 row를 배치해
  physical locality, page split, range scan, secondary index back-to-primary lookup, random I/O 비용을 결정한다는
  기준을 설명한다.
---
# Clustered Index Locality

> 한 줄 요약: clustered index는 PK 순서로 데이터가 물리적으로 가까워지게 만들어, point lookup과 범위 조회의 locality를 결정한다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: clustered index, primary key locality, leaf page locality, page split, secondary index lookup, physical clustering, range scan, random I/O

## 핵심 개념

- 관련 문서:
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
  - [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)

InnoDB에서 clustered index는 단순한 인덱스가 아니라 **테이블 자체의 정렬 축**이다.  
즉 PK가 곧 데이터의 물리적 배치 방식에 영향을 준다.

이게 중요한 이유는 다음 때문이다.

- 같은 PK 근처 row는 같은 page에 모이기 쉽다
- 범위 조회가 더 자연스럽다
- secondary index lookup 후 primary key로 본문을 찾는 비용이 locality에 따라 달라진다

## 깊이 들어가기

### 1. clustered index는 무엇을 클러스터링하는가

InnoDB의 primary key leaf는 단순 포인터가 아니라 실제 row 데이터를 담는다.  
그래서 PK 순서가 곧 데이터 페이지 배치에 큰 영향을 준다.

결과적으로:

- PK 증가형은 append 패턴과 잘 맞는다
- 랜덤 PK는 page split과 분산을 늘릴 수 있다
- 범위 조회는 같은 leaf page를 연속적으로 읽기 쉬워진다

### 2. locality가 좋으면 왜 빨라지나

locality가 좋다는 건 근처 데이터를 함께 읽는다는 뜻이다.

- buffer pool hit 가능성이 높아진다
- disk seek가 줄어든다
- range scan이 효율적이다

반대로 locality가 나쁘면:

- page miss가 늘고
- 랜덤 I/O가 증가하고
- page split이 잦아질 수 있다

### 3. secondary index는 locality를 우회하지 못한다

secondary index는 결국 primary key로 본문을 찾는다.  
따라서 secondary index가 잘 설계되어 있어도 clustered locality가 나쁘면 본문 접근 비용이 남는다.

### 4. PK 선택이 사실상 물리 배치 설계다

UUID 같은 랜덤 PK는 분산 장점이 있어 보이지만, InnoDB에서는 page split과 locality 저하를 부를 수 있다.  
반면 monotonic PK는 locality에 유리하지만 hot spot을 만들 수 있다.

즉 PK는 단순 식별자가 아니라 **쓰기 패턴과 페이지 구조를 같이 정하는 결정**이다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `clustered index`
- `primary key locality`
- `page split`
- `random I/O`
- `range scan`
- `secondary index lookup`

## 실전 시나리오

### 시나리오 1. PK가 UUID로 바뀌고 나서 insert가 흔들린다

랜덤 PK는 페이지 끝에만 쓰는 형태가 아니어서 split과 재배치가 늘 수 있다.  
이때는 PK 설계가 테이블의 locality를 깨고 있는지 봐야 한다.

### 시나리오 2. 최근 주문 조회는 빠른데 오래된 주문 조회가 튄다

PK 순서가 생성 시점과 맞으면 최근 데이터는 잘 붙어 있지만, 오래된 범위는 buffer pool에서 밀려날 수 있다.  
hot/cold 데이터 경계와도 연결된다.

### 시나리오 3. secondary index는 있는데 본문 조회가 계속 많다

조회 조건이 secondary index에만 맞고 본문 row는 랜덤하게 흩어져 있으면 locality 이득이 줄어든다.  
이 경우 covering index나 PK 재설계가 필요할 수 있다.

## 코드로 보기

### PK가 locality에 미치는 예시

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  INDEX idx_orders_user_created_at (user_id, created_at)
);
```

### 범위 조회

```sql
EXPLAIN
SELECT *
FROM orders
WHERE id BETWEEN 100000 AND 100500;
```

### page split 감각 확인

```sql
SHOW ENGINE INNODB STATUS\G
```

### locality를 고려한 설계 감각

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= '2026-04-01'
ORDER BY id;
```

PK와 access pattern이 얼마나 맞는지 생각해 본다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| monotonic PK | locality가 좋다 | hot spot이 생길 수 있다 | OLTP 중심 |
| random PK | 분산이 좋다 | page split과 locality 저하 | 분산 식별자 우선일 때 |
| covering index 추가 | 본문 접근을 줄인다 | index size와 write cost 증가 | 반복 목록 조회 |
| PK 재설계 | 구조를 바로잡을 수 있다 | 대규모 migration이 필요하다 | 장기적으로 locality가 중요할 때 |

핵심은 clustered index를 "그냥 PK 저장 방식"이 아니라 **물리 locality를 결정하는 축**으로 보는 것이다.

## 꼬리질문

> Q: clustered index가 왜 locality에 중요한가요?
> 의도: PK와 물리 배치 관계를 이해하는지 확인
> 핵심: PK 순서가 데이터 페이지 정렬에 직접 영향을 준다

> Q: UUID PK가 왜 문제될 수 있나요?
> 의도: 랜덤 쓰기와 page split의 관계 확인
> 핵심: 데이터가 흩어져 page split과 랜덤 I/O가 늘 수 있다

> Q: secondary index만 좋으면 충분하지 않나요?
> 의도: 본문 접근 비용을 무시하지 않는지 확인
> 핵심: 결국 primary key로 본문을 찾아야 한다

## 한 줄 정리

clustered index는 PK 순서로 데이터가 모이는 방식이라, locality가 좋으면 읽기와 쓰기 모두 유리하지만 PK 설계가 곧 물리 배치 설계가 된다.
