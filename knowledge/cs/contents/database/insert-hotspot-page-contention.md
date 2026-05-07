---
schema_version: 3
title: Insert Hotspot Page Contention
concept_id: database/insert-hotspot-page-contention
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- insert-hotspot-page-contention
- last-leaf-page-latch
- auto-increment-hotspot
aliases:
- insert hotspot
- last leaf page
- page contention
- auto-increment hotspot
- clustered index insert
- page split
- latch contention
- hot page
- insert page hotspot
- 마지막 leaf page 경합
symptoms:
- 증가형 PK나 시간순 key에 insert가 몰려 마지막 leaf page latch contention이 병목처럼 보여
- row lock이 아닌 page latch와 page split 비용 때문에 append-only 테이블 insert TPS가 평평해지고 있어
- random PK로 hotspot을 줄이면 locality와 page split 비용이 어떻게 바뀌는지 판단해야 해
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- database/btree-latch-contention-hot-pages
- database/page-split-merge-fill-factor
next_docs:
- database/hot-update-secondary-index-churn
- database/secondary-index-maintenance-statistics-skew
- database/clustered-index-locality
linked_paths:
- contents/database/btree-latch-contention-hot-pages.md
- contents/database/clustered-index-locality.md
- contents/database/page-split-merge-fill-factor.md
- contents/database/secondary-index-maintenance-cost-analyze-skew.md
- contents/database/hot-update-secondary-index-churn.md
- contents/database/hot-row-contention-counter-sharding.md
confusable_with:
- database/btree-latch-contention-hot-pages
- database/page-split-merge-fill-factor
- database/hot-update-secondary-index-churn
forbidden_neighbors: []
expected_queries:
- auto-increment PK insert가 많으면 왜 마지막 leaf page가 hot page가 될 수 있어?
- insert hotspot은 row lock이 아니라 page latch와 page split 병목이라는 뜻이야?
- append-only 로그 테이블인데도 last leaf page contention 때문에 느릴 수 있어?
- random PK는 insert hotspot을 줄이지만 locality와 page split 비용을 왜 늘릴 수 있어?
- shard_id를 primary key 앞에 넣으면 insert 위치 분산과 읽기 복잡도가 어떻게 바뀌어?
contextual_chunk_prefix: |
  이 문서는 증가형 PK나 시간순 key insert가 마지막 B-Tree leaf page에 몰려 page latch, page split, hot page contention을 만드는 원리를 설명하는 advanced deep dive다.
  insert hotspot, auto-increment hotspot, last leaf page, page contention 같은 자연어 질문이 본 문서에 매핑된다.
---
# Insert Hotspot Page Contention

> 한 줄 요약: insert hotspot은 row 하나가 아니라 마지막 leaf page 하나에 쓰기가 몰리면서 page latch와 split 비용을 터뜨리는 현상이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: insert hotspot, last leaf page, page contention, auto-increment hotspot, clustered index insert, page split, latch contention, hot page

## 핵심 개념

- 관련 문서:
  - [B-Tree Latch Contention and Hot Pages](./btree-latch-contention-hot-pages.md)
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [Page Split, Merge, and Fill Factor](./page-split-merge-fill-factor.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)

insert hotspot은 쓰기가 특정 위치에 몰릴 때 생긴다.  
가장 흔한 예는 증가형 PK나 시간순 정렬 키가 테이블의 끝 페이지에만 insert를 계속 만들 때다.

핵심은 다음이다.

- 한 row가 뜨거운 게 아니라 page 끝이 뜨겁다
- row lock보다 page latch와 split 비용이 먼저 보일 수 있다
- 쓰기량이 늘수록 마지막 page가 병목이 된다

## 깊이 들어가기

### 1. 왜 마지막 leaf page가 뜨거워지는가

증가형 PK는 대체로 가장 큰 키 값 뒤에 계속 insert된다.  
그 결과 새로운 row가 항상 비슷한 page 근처에 쌓인다.

이 패턴은:

- cache locality는 좋을 수 있지만
- 경합은 한곳에 몰린다

즉 locality와 hotspot은 늘 같이 움직이지 않는다.

### 2. auto-increment hotspot

auto-increment는 구현상 단순하고 조회에도 편리하지만, 동시 insert가 많으면 마지막 page와 관련된 경합이 커질 수 있다.  
큰 테이블, 높은 TPS, 짧은 트랜잭션이 겹치면 더 도드라진다.

### 3. 랜덤 PK는 hotspot을 줄이나

랜덤 PK는 마지막 page 집중은 줄일 수 있지만, 대신 page split과 locality 저하를 부를 수 있다.  
즉 hotspot을 옮기는 대신 다른 비용을 치른다.

### 4. hotspot은 secondary index도 부를 수 있다

insert가 많으면 clustered index만이 아니라 secondary index leaf에도 쓰기가 몰린다.  
그래서 실제 병목은 여러 page에서 함께 나타날 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `insert hotspot`
- `last leaf page`
- `page contention`
- `auto-increment hotspot`
- `clustered index insert`
- `hot page`

## 실전 시나리오

### 시나리오 1. 새 주문이 몰리면 TPS가 평평해진다

주문 테이블의 PK가 시간순 증가형이면, 최근 insert가 끝 페이지에 몰리면서 경합이 생길 수 있다.  
이때는 row lock이 아니라 page-level hotspot을 의심해야 한다.

### 시나리오 2. 로그 테이블에 append만 하는데도 느리다

append-only처럼 보여도 마지막 page는 계속 바뀐다.  
page split과 latch contention이 반복되면 생각보다 빨리 병목이 온다.

### 시나리오 3. shard를 나누자 성능이 나아졌다

쓰기 위치를 여러 shard로 분산하면 한 page에 몰리는 insert hotspot을 줄일 수 있다.  
대신 읽기 합산과 운영 복잡도는 늘어난다.

## 코드로 보기

### 증가형 PK 예시

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL
);
```

### 경합 완화 아이디어

```sql
CREATE TABLE orders_shard (
  shard_id INT NOT NULL,
  id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (shard_id, id)
);
```

### 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 증가형 PK | 단순하고 locality가 좋다 | hot page가 생길 수 있다 | 일반 OLTP |
| 랜덤 PK | 쓰기 위치가 분산된다 | page split과 locality 손실이 있다 | hotspot 완화가 더 중요할 때 |
| shard 분산 | 경합을 크게 줄인다 | 조회/집계가 복잡해진다 | 고TPS insert |

핵심은 insert hotspot을 row 문제가 아니라 **page 끝으로 쓰기가 몰리는 구조 문제**로 보는 것이다.

## 꼬리질문

> Q: insert hotspot은 왜 생기나요?
> 의도: page-level 경합 원인을 아는지 확인
> 핵심: 쓰기가 한쪽 leaf page 끝에 집중되기 때문이다

> Q: auto-increment PK가 항상 나쁜가요?
> 의도: locality와 hotspot trade-off를 아는지 확인
> 핵심: 단순하지만 hotspot을 만들 수 있다

> Q: hotspot을 줄이려면 무엇부터 보나요?
> 의도: PK와 shard 설계를 연결하는지 확인
> 핵심: 쓰기 위치 분산, shard, PK 구조다

## 한 줄 정리

insert hotspot은 증가형 쓰기가 같은 leaf page에 몰려 생기는 page-level 병목이고, PK 분산이나 shard로 완화할 수 있다.
