---
schema_version: 3
title: Read-Ahead False Positives and Buffer Pool Pollution
concept_id: database/read-ahead-false-positives-buffer-pollution
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- read-ahead
- buffer-pool
- cache-pollution
- storage-internals
aliases:
- read-ahead false positives
- buffer pool pollution
- prefetch miss
- sequential scan heuristic
- false positive prefetch
- hot set eviction
- random read ahead
- read ahead 오판
- 버퍼 풀 오염
- hot page eviction
symptoms:
- read-ahead heuristic이 곧 쓰지 않을 page를 미리 읽어 hot working set을 buffer pool에서 밀어내고 있어
- 짧은 range scan이나 중간에 끊기는 batch가 false positive prefetch를 반복해 OLTP latency를 흔들고 있어
- read-ahead를 버그로 보거나 무조건 이득으로 보고 접근 패턴과 cache pollution tradeoff를 놓치고 있어
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/read-ahead-sequential-scan-behavior
- database/innodb-buffer-pool-internals
next_docs:
- database/buffer-pool-read-ahead-eviction-interaction
- database/read-ahead-sequential-scan-behavior
- database/clustered-index-locality
linked_paths:
- contents/database/read-ahead-sequential-scan-behavior.md
- contents/database/buffer-pool-read-ahead-eviction-interaction.md
- contents/database/innodb-buffer-pool-internals.md
- contents/database/clustered-index-locality.md
confusable_with:
- database/read-ahead-sequential-scan-behavior
- database/buffer-pool-read-ahead-eviction-interaction
- database/innodb-buffer-pool-internals
forbidden_neighbors: []
expected_queries:
- read-ahead false positive는 왜 buffer pool pollution과 hot page eviction을 만들까?
- 짧은 range scan이나 중간에 끊기는 batch가 false positive prefetch를 늘리는 이유를 설명해줘
- read-ahead heuristic이 틀렸을 때 디스크 읽기 낭비와 cache pollution이 함께 생기는 흐름을 알려줘
- OLTP hot set이 analytics scan 뒤 밀리는 상황을 read-ahead 관점으로 해석해줘
- read-ahead false positive를 완전히 없애기보다 비용을 낮추는 쪽이 현실적인 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 InnoDB read-ahead false positives가 곧 쓰지 않을 page를 prefetch해 buffer pool pollution, hot set eviction, cache miss를 만드는 advanced deep dive다.
  read ahead 오판, 버퍼 풀 오염, hot page eviction 질문이 본 문서에 매핑된다.
---
# Read-Ahead False Positives and Buffer Pool Pollution

> 한 줄 요약: read-ahead false positive는 "미리 읽었는데 곧 안 쓰는" page를 대량으로 끌어와 buffer pool을 오염시키는 현상이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: read-ahead false positives, buffer pool pollution, prefetch miss, sequential scan heuristic, false positive prefetch, hot set eviction, random read ahead

## 핵심 개념

- 관련 문서:
  - [Read Ahead and Sequential Scan Behavior](./read-ahead-sequential-scan-behavior.md)
  - [Buffer Pool Read-Ahead and Eviction Interaction](./buffer-pool-read-ahead-eviction-interaction.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)

read-ahead false positive는 DB가 "곧 필요할 것"이라고 예상한 page가 실제로는 별로 쓰이지 않는 상황이다.  
이런 오판이 반복되면 buffer pool은 쓸모 없는 page로 채워지고, hot page가 밀린다.

핵심은 다음이다.

- read-ahead는 heuristic이다
- heuristic은 틀릴 수 있다
- 틀리면 cache pollution이 된다

## 깊이 들어가기

### 1. false positive는 왜 생기나

DB는 접근 패턴을 보고 다음 page를 미리 읽는다.  
하지만 다음 page를 실제로 읽지 않는다면 그건 false positive다.

대표 원인:

- scan이 중간에 끊김
- range 조건이 생각보다 짧음
- 읽기 패턴이 순차적이지 않음
- join/aggregation 중간에 페이지를 덜 쓰게 됨

### 2. 왜 버퍼 풀 오염이 되나

미리 읽은 page는 buffer pool 공간을 차지한다.  
곧바로 쓰이지 않으면 LRU에서 머물다가, 나중에 더 중요한 page를 밀어낸다.

즉 false positive는:

- 디스크 읽기 낭비
- 메모리 오염
- hot page eviction

을 함께 만든다.

### 3. false positive를 더 악화시키는 패턴

- 짧은 pagination을 장기로 예측
- range scan이 자주 끊기는 API
- 분석성 쿼리와 OLTP가 한 DB에 섞임
- 잘못된 인덱스 순서로 인해 scan이 분산됨

### 4. false positive는 완전히 없앨 수 없다

read-ahead는 heuristic이므로 어느 정도 오판은 허용해야 한다.  
중요한 것은 오판의 비용을 감당 가능한 수준으로 낮추는 것이다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `read-ahead false positives`
- `buffer pool pollution`
- `false positive prefetch`
- `hot set eviction`
- `random read ahead`

## 실전 시나리오

### 시나리오 1. 부분 범위 조회가 많다

최근 1시간 데이터를 읽는 줄 알았는데 실제로는 몇 페이지 읽고 끝나는 패턴이면, read-ahead는 곧바로 쓰이지 않는 page를 끌어올 수 있다.

### 시나리오 2. 배치가 scan을 중간에 끊는다

쿼리가 마지막까지 page를 소비하지 않으면 prefetch된 page는 그대로 남는다.  
이후 OLTP가 그 자리를 정리해야 한다.

### 시나리오 3. scan 최적화가 다른 API를 느리게 만든다

분석성 쿼리를 위해 read-ahead를 믿었는데, 결과적으로 hot set이 밀리면 OLTP latency가 나빠질 수 있다.

## 코드로 보기

### false positive를 유발할 수 있는 짧은 range

```sql
EXPLAIN
SELECT id
FROM orders
WHERE created_at >= '2026-04-08 10:00:00'
  AND created_at <  '2026-04-08 10:05:00';
```

### 상태 확인

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
```

### 패턴 점검

```sql
SELECT COUNT(*)
FROM orders
WHERE user_id = 1001;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| read-ahead 유지 | scan이 빠를 수 있다 | false positive pollution이 생길 수 있다 | 순차성이 높을 때 |
| read-ahead 보수화 | pollution을 줄인다 | scan이 느려질 수 있다 | OLTP 중심 |
| 쿼리/인덱스 재설계 | heuristic 의존도를 줄인다 | 설계 변경이 필요하다 | false positive가 잦을 때 |

핵심은 false positive를 "버그"가 아니라 **heuristic의 비용**으로 보고, 그 비용이 크면 접근 패턴을 바꾸는 것이다.

## 꼬리질문

> Q: read-ahead false positive는 왜 문제가 되나요?
> 의도: heuristic 오판의 비용을 아는지 확인
> 핵심: 쓰이지 않을 page가 buffer pool을 오염시키기 때문이다

> Q: false positive를 완전히 없앨 수 있나요?
> 의도: heuristic의 한계를 이해하는지 확인
> 핵심: 완전 제거보다는 비용을 낮추는 쪽이 현실적이다

> Q: 어떤 패턴이 false positive를 늘리나요?
> 의도: scan 중단과 짧은 range의 영향을 아는지 확인
> 핵심: 순차성이 약하고 중간에 끊기는 패턴이다

## 한 줄 정리

read-ahead false positive는 곧 쓰지 않을 page를 미리 읽어 buffer pool을 오염시키는 heuristic 오판이고, 반복되면 hot page eviction을 유발한다.
