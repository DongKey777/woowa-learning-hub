---
schema_version: 3
title: Page Directory and Record Layout Intuition
concept_id: database/page-directory-and-record-layout-intuition
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- innodb-page
- record-layout
- btree
- storage-internals
aliases:
- page directory
- record layout
- infimum supremum
- heap number
- page slots
- InnoDB page structure
- next record pointer
- page directory slots
- InnoDB page 내부 구조
- record header layout
symptoms:
- InnoDB page를 단순한 16KB 바이트 덩어리로 보고 record header와 page directory가 만드는 내부 탐색 구조를 놓치고 있어
- page split, latch contention, clustered locality를 설명하려면 page 내부 record layout과 directory slot 감각이 필요해
- infimum, supremum, heap number, next record 같은 storage internals 용어를 연결해서 이해해야 해
intents:
- deep_dive
- definition
prerequisites:
- database/clustered-index-locality
- database/bptree-vs-lsm-tree
next_docs:
- database/page-split-merge-fill-factor
- database/btree-latch-contention-hot-pages
- database/innodb-buffer-pool-internals
linked_paths:
- contents/database/clustered-index-locality.md
- contents/database/btree-latch-contention-hot-pages.md
- contents/database/page-split-merge-fill-factor.md
- contents/database/bptree-vs-lsm-tree.md
- contents/database/innodb-buffer-pool-internals.md
confusable_with:
- database/page-split-merge-fill-factor
- database/btree-latch-contention-hot-pages
- database/clustered-index-locality
forbidden_neighbors: []
expected_queries:
- InnoDB page directory와 record layout은 page 내부에서 무엇을 해?
- infimum과 supremum record가 page boundary에서 왜 필요한지 설명해줘
- page 내부 record header와 next pointer가 B-tree 탐색과 어떤 관련이 있어?
- page split이 비싼 이유를 page directory 재배치와 연결해서 알려줘
- hot page latch contention을 이해하려면 왜 page structure를 알아야 해?
contextual_chunk_prefix: |
  이 문서는 InnoDB page directory, record header, infimum, supremum, heap number, next record pointer가 page 내부 검색 구조를 만드는 원리를 다루는 advanced deep dive다.
  InnoDB page 내부 구조, page directory slots, record layout 질문이 본 문서에 매핑된다.
---
# Page Directory and Record Layout Intuition

> 한 줄 요약: InnoDB page는 그냥 데이터 덩어리가 아니라, record header와 page directory가 함께 작동하는 작은 검색 구조다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: page directory, record layout, infimum supremum, next record, heap number, page slots, InnoDB page structure

## 핵심 개념

- 관련 문서:
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [B-Tree Latch Contention and Hot Pages](./btree-latch-contention-hot-pages.md)
  - [Page Split, Merge, and Fill Factor](./page-split-merge-fill-factor.md)

InnoDB page는 16KB 덩어리 하나가 아니라, 그 안에 record와 directory가 정렬된 구조다.  
이걸 이해하면 B-Tree가 왜 page 단위로 움직이는지 감이 온다.

핵심은 다음이다.

- record는 page 안에서 연결 리스트처럼 이어진다
- page directory는 빠른 탐색을 돕는 슬롯 집합이다
- infimum/supremum은 page 경계를 표시한다

## 깊이 들어가기

### 1. record layout은 왜 중요한가

row는 page 안에 순서대로 저장되지만, 단순히 바이트 덩어리로만 있지 않다.  
record header가 있고, next pointer가 있고, offset이 있다.

이 구조 덕분에:

- page 내 순차 탐색이 가능하고
- slot directory로 빠르게 위치를 찾을 수 있다

### 2. page directory는 무엇을 하는가

page directory는 page 안 record의 위치를 가리키는 슬롯 목록이다.  
완전한 배열도 아니고, 완전한 링크드 리스트도 아니다.

이 구조가 의미하는 것:

- page 내 검색을 빠르게 한다
- binary-like 탐색 감각을 준다
- record가 많아져도 빠른 접근을 돕는다

### 3. infimum과 supremum

page에는 경계 역할을 하는 가상의 record가 있다.

- infimum: 가장 작은 경계
- supremum: 가장 큰 경계

이들은 실제 데이터라기보다 page 구조를 안정적으로 유지하는 장치다.

### 4. 왜 이걸 알아야 하나

page split, latch contention, buffer pool miss를 설명하려면 page 내부 구조 감각이 필요하다.  
이걸 알아야 "왜 page 단위로 병목이 생기는지"를 이해할 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `page directory`
- `record layout`
- `infimum supremum`
- `heap number`
- `page slots`
- `InnoDB page structure`

## 실전 시나리오

### 시나리오 1. page split이 왜 비싼지 감이 안 온다

page 안 record와 directory를 재배치해야 하기 때문이다.  
단순히 "공간이 부족해서 나눈다"보다 구조 재배치 비용을 봐야 한다.

### 시나리오 2. hot page가 왜 병목인지 이해하고 싶다

page 안 구조를 보호하려고 latch가 걸리고, record와 directory가 함께 움직이기 때문이다.  
그래서 같은 page를 동시에 건드리면 내부 경합이 생긴다.

### 시나리오 3. clustered index가 왜 물리 locality와 연결되는지 보고 싶다

같은 page 안에 인접 record가 모이기 때문에, page directory와 record layout이 locality를 만든다.

## 코드로 보기

### page 구조를 직접 보는 도구 감각

```sql
SHOW ENGINE INNODB STATUS\G
```

### 정렬된 insert 예시

```sql
INSERT INTO orders (id, user_id, status, created_at)
VALUES (1001, 1, 'PAID', NOW());
```

### page 구조를 의식한 설계

```sql
CREATE INDEX idx_orders_user_created_at
ON orders (user_id, created_at);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| page directory 활용 | page 내 탐색이 빠르다 | 구조가 복잡하다 | InnoDB 기본 |
| 단순 리스트 구조 | 구현이 쉽다 | 탐색이 느리다 | 내부 자료구조 비교 |

핵심은 page를 바이트 덩어리로 보지 말고, **record와 directory가 함께 움직이는 검색 구조**로 보는 것이다.

## 꼬리질문

> Q: page directory는 무엇을 하나요?
> 의도: page 내부 탐색 구조 이해 여부 확인
> 핵심: page 내 record 위치를 빠르게 찾도록 돕는다

> Q: infimum/supremum은 왜 있나요?
> 의도: page 경계 sentinel 개념을 아는지 확인
> 핵심: page 구조를 안정적으로 만들기 위해서다

> Q: record layout을 왜 알아야 하나요?
> 의도: page split과 latch 병목 이해 여부 확인
> 핵심: page-level 성능 문제를 설명할 수 있기 때문이다

## 한 줄 정리

page directory와 record layout은 InnoDB page 내부의 탐색과 경계를 담당하는 구조라, B-Tree 병목을 이해하려면 반드시 알아야 한다.
