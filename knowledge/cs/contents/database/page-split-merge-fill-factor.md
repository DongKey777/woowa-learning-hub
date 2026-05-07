---
schema_version: 3
title: Page Split, Merge, and Fill Factor
concept_id: database/page-split-merge-fill-factor
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- page-split
- fill-factor
- btree
- fragmentation
aliases:
- page split
- page merge
- fill factor
- B+Tree fragmentation
- leaf page split
- insert hotspot page split
- fanout
- page fullness
- UUID 인덱스 쓰기 비용
- delete해도 공간이 안 줄어요
symptoms:
- random insert나 wide index 때문에 leaf page split, redo, latch contention, fragmentation이 늘고 있어
- delete 후 공간이 바로 줄지 않아 page merge와 fragmentation 회수 비용을 이해해야 해
- fill factor와 key design이 split 빈도, fanout, buffer pool pressure에 미치는 영향을 설명해야 해
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/bptree-vs-lsm-tree
- database/page-directory-and-record-layout-intuition
next_docs:
- database/insert-hotspot-page-contention
- database/secondary-index-maintenance-statistics-skew
- database/innodb-buffer-pool-internals
linked_paths:
- contents/database/bptree-vs-lsm-tree.md
- contents/database/clustered-index-locality.md
- contents/database/secondary-index-maintenance-cost-analyze-skew.md
- contents/database/innodb-buffer-pool-internals.md
- contents/database/page-directory-and-record-layout-intuition.md
- contents/database/insert-hotspot-page-contention.md
confusable_with:
- database/page-directory-and-record-layout-intuition
- database/insert-hotspot-page-contention
- database/clustered-index-locality
forbidden_neighbors: []
expected_queries:
- B+Tree page split이 왜 redo와 latch contention, fragmentation 비용을 만들까?
- fill factor는 random insert와 append-heavy workload에서 어떻게 다르게 봐야 해?
- delete를 많이 해도 table이나 index 공간이 바로 줄지 않는 이유가 뭐야?
- UUID 같은 random key 인덱스가 page split을 자주 만드는 과정을 설명해줘
- page merge를 너무 적극적으로 하면 왜 split merge 반복 비용이 생길 수 있어?
contextual_chunk_prefix: |
  이 문서는 B+Tree page split, page merge, fill factor, fragmentation, fanout을 write amplification과 storage locality 관점에서 다루는 advanced deep dive다.
  UUID 인덱스 쓰기 비용, delete해도 공간이 안 줄어요, page split 비용 질문이 본 문서에 매핑된다.
---
# Page Split, Merge, and Fill Factor

> 한 줄 요약: page split은 B+Tree가 성장하는 방식이지만, 너무 자주 일어나면 쓰기 비용과 fragmentation이 운영 문제로 바뀐다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: page split, page merge, fill factor, B+Tree fragmentation, leaf page, insert hotspot, fanout, page fullness

## 핵심 개념

- 관련 문서:
  - [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)

B+Tree는 고정 크기 page 위에 키를 정렬해서 저장한다.  
그래서 page가 꽉 차면 나누고, 너무 비면 합친다.

이 두 동작이 바로 page split과 page merge다.

- split은 insert가 들어올 자리를 만들기 위해 페이지를 둘로 나눈다
- merge는 삭제 후 너무 비어진 페이지를 합쳐 공간을 회수한다
- fill factor는 이 과정에서 어느 정도 여유를 남길지에 대한 감각이다

## 깊이 들어가기

### 1. page split은 왜 비싼가

page split은 단순한 메모리 복사가 아니다.  
페이지의 절반을 새 페이지로 옮기고, parent node도 갱신해야 한다.

이때 비용:

- 추가 page write
- redo/undo 증가
- latch 경합
- buffer pool 오염

특히 insert가 한쪽 끝에 몰리거나, 랜덤 키가 많이 들어오면 split이 더 자주 발생할 수 있다.

### 2. page merge는 왜 항상 일어나지 않나

delete가 생겼다고 바로 merge하는 것도 아니다.  
과도한 merge/split 반복은 더 나쁜 비용을 만들 수 있어서, DB는 보통 신중하게 합친다.

즉:

- 너무 자주 split되면 fragmentation이 증가
- 너무 자주 merge되면 재배치 비용이 증가

### 3. fill factor는 왜 중요한가

fill factor는 페이지를 꽉 채워두는 대신 일정 여유를 두는 관점이다.  
예상 insert 패턴이 있으면 약간 비워 두는 편이 나을 수 있다.

실무 감각:

- 랜덤 insert가 많으면 여유 공간이 도움이 될 수 있다
- 순차 append가 많으면 여유보다 locality가 더 중요할 수 있다
- 삭제가 많은 테이블은 merge 비용까지 같이 본다

### 4. index 폭과 split 빈도는 연결된다

키가 길어질수록 한 page에 담기는 엔트리 수가 줄어든다.  
즉 fanout이 줄고, split이 더 자주 일어날 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `page split`
- `page merge`
- `fill factor`
- `fragmentation`
- `leaf page`
- `fanout`
- `page fullness`

## 실전 시나리오

### 시나리오 1. UUID 인덱스를 추가하자마자 쓰기가 무거워진다

랜덤 키는 leaf page의 끝에만 insert되지 않아서 split이 잦아질 수 있다.  
그 결과 page churn과 redo가 함께 늘어난다.

### 시나리오 2. 오래된 데이터를 지웠는데 공간이 바로 줄지 않는다

삭제가 page merge로 즉시 이어지지 않으면 공간은 당장 회수되지 않는다.  
그래서 테이블/인덱스가 "지운 만큼 바로 작아질 것"이라고 기대하면 안 된다.

### 시나리오 3. insert hotspot이 생긴다

시간순 PK처럼 한쪽 끝에만 쓰기가 몰리면 특정 leaf page가 자주 바뀐다.  
이건 page split보다 latch 경쟁이 더 크게 보일 수도 있다.

## 코드로 보기

### 인덱스 생성 예시

```sql
CREATE TABLE logs (
  id BIGINT PRIMARY KEY,
  created_at DATETIME NOT NULL,
  level VARCHAR(20) NOT NULL,
  message TEXT NOT NULL,
  INDEX idx_logs_created_at (created_at)
);
```

### 관찰 포인트

```sql
SHOW ENGINE INNODB STATUS\G
```

### split 유발 패턴 감각

```sql
INSERT INTO logs (id, created_at, level, message)
VALUES (900001, NOW(), 'INFO', 'test');
```

insert 패턴이 인덱스 순서와 어떻게 맞는지 본다.

### 공간 회수 감각

```sql
OPTIMIZE TABLE logs;
```

이건 page merge와 fragmentation 해소를 직접 체감하는 데 도움이 된다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 높은 fill factor | page 낭비가 적다 | split이 빨리 올 수 있다 | append 중심 |
| 낮은 fill factor | insert 여유가 생긴다 | 공간 효율이 떨어진다 | 랜덤 insert/갱신 |
| merge 적극화 | 공간 회수에 유리 | 재배치 비용이 있다 | 삭제 비중이 높을 때 |
| PK/인덱스 재설계 | split 원인을 줄인다 | migration이 필요할 수 있다 | 장기 구조 개선 |

핵심은 page split을 "DB의 정상 성장"으로 보되, 그 빈도와 비용을 운영 가능하게 관리하는 것이다.

## 꼬리질문

> Q: page split이 왜 비싼가요?
> 의도: B+Tree 재배치 비용 이해 여부 확인
> 핵심: 페이지 절반 이동과 parent 갱신이 필요하다

> Q: fill factor는 왜 조절하나요?
> 의도: insert 여유와 공간 효율의 균형 이해 여부 확인
> 핵심: 앞으로 들어올 쓰기를 대비해 공간을 남기는 개념이다

> Q: delete를 해도 바로 공간이 안 줄어드는 이유는?
> 의도: merge가 즉시 일어나지 않는다는 점 이해 확인
> 핵심: split/merge는 비용이 큰 구조적 작업이기 때문이다

## 한 줄 정리

page split과 merge는 B+Tree의 자연스러운 성장/정리 방식이지만, fill factor와 키 설계가 나쁘면 그 비용이 곧 성능 문제로 드러난다.
