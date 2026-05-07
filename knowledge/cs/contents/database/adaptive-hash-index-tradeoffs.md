---
schema_version: 3
title: Adaptive Hash Index Trade-offs
concept_id: database/adaptive-hash-index-tradeoffs
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- adaptive-hash-index
- innodb-internals
- point-lookup
- latch-contention
aliases:
- adaptive hash index
- AHI
- innodb_adaptive_hash_index
- innodb adaptive hash index
- hash lookup acceleration
- latch contention AHI
- buffer pool point lookup
- adaptive hash index tradeoffs
- InnoDB AHI
- 반복 point lookup
symptoms:
- AHI를 사용자가 만드는 hash index처럼 오해해 schema/index 설계 대체물로 본다
- 반복 point lookup에는 도움이 되지만 쓰기-heavy나 scan-heavy workload에서 유지 비용과 latch contention이 커진다
- 재시작 직후와 warm-up 이후 성능 차이를 buffer pool과 AHI hot set 변화로 설명하지 못한다
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- database/innodb-buffer-pool-internals
- database/index-and-explain
next_docs:
- database/btree-latch-contention-hot-pages
- database/slow-query-analysis-playbook
- database/covering-index-vs-index-only-scan
linked_paths:
- contents/database/innodb-buffer-pool-internals.md
- contents/database/index-and-explain.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/btree-latch-contention-hot-pages.md
confusable_with:
- database/index-basics
- database/covering-index-vs-index-only-scan
- database/btree-latch-contention-hot-pages
- database/innodb-buffer-pool-internals
forbidden_neighbors: []
expected_queries:
- InnoDB Adaptive Hash Index는 사용자가 만드는 해시 인덱스가 아니라 내부 point lookup 가속 장치야?
- AHI가 반복 key lookup에는 좋지만 write-heavy나 scan-heavy workload에서 경합을 키울 수 있는 이유가 뭐야?
- innodb_adaptive_hash_index를 끄거나 켜는 실험은 언제 진단용으로만 써야 해?
- AHI와 buffer pool warm-up 때문에 재시작 직후와 평시 성능이 달라지는 이유를 설명해줘
- AHI는 인덱스 설계를 대체하지 않고 잘 설계된 B+Tree path를 보조한다는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Adaptive Hash Index Trade-offs deep dive로, InnoDB AHI가 반복 point lookup의
  B+Tree traversal을 내부적으로 가속할 수 있지만 buffer pool hot set, write/scan workload, latch contention에 따라
  성능이 불안정해질 수 있음을 설명한다.
---
# Adaptive Hash Index Trade-offs

> 한 줄 요약: AHI는 반복 조회를 빠르게 만들 수 있지만, 경합과 예측 불가능성을 함께 사오는 내부 가속 장치다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: adaptive hash index, AHI, innodb_adaptive_hash_index, hash lookup, latch contention, hot pages, buffer pool, point lookup

## 핵심 개념

- 관련 문서:
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)

Adaptive Hash Index(AHI)는 InnoDB가 자주 반복되는 B+Tree 탐색 패턴을 내부적으로 더 빠르게 찾기 위해 쓰는 메커니즘이다.  
중요한 점은 이것이 "사용자가 만드는 해시 인덱스"가 아니라, 엔진이 자동으로 관리하는 가속 장치라는 점이다.

AHI의 존재 이유는 단순하다.

- 같은 경로로 반복 조회되는 point lookup을 빠르게 하고
- B+Tree 상단 탐색 비용을 줄이며
- 핫 페이지에서의 탐색 지연을 낮춘다

하지만 이 장치는 늘 좋은 것이 아니다.

- 패턴이 자주 바뀌면 효율이 떨어진다
- 쓰기와 스캔이 많으면 유지 비용이 생긴다
- 내부 경합이 커지면 오히려 병목이 된다

## 깊이 들어가기

### 1. AHI는 어떻게 도움이 되는가

일반적인 B+Tree 탐색은 루트에서 리프까지 내려간다.  
반복되는 검색 조건이 많으면 이 경로를 매번 다시 걷는 비용이 쌓인다.

AHI는 이 반복 경로를 내부적으로 더 짧게 만들 수 있다.  
그래서 다음과 같은 패턴에서 체감이 좋다.

- 같은 PK/unique key lookup이 반복된다
- 특정 tenant의 작은 범위를 계속 읽는다
- 핫셋이 안정적이다

### 2. 왜 쓰기-heavy 워크로드에서는 불리할 수 있는가

AHI는 한 번 만들어 놓고 끝나는 구조가 아니다.  
버퍼 풀 페이지가 바뀌거나 access pattern이 달라지면 내부 엔트리도 계속 관리되어야 한다.

그래서 쓰기 비중이 커지면 다음이 문제 된다.

- AHI 유지/갱신 비용
- 관련 경합
- 패턴 변화로 인한 낮은 적중률

### 3. 스캔-heavy 워크로드에서는 기대보다 못할 수 있다

대량 range scan이나 배치성 조회는 "같은 경로 반복"보다 "넓은 범위 소모"가 많다.  
이 경우 AHI의 장점은 줄고, 내부 캐시 오염이나 경합만 남을 수 있다.

### 4. AHI는 인덱스 설계를 대체하지 않는다

가장 중요한 함정은 이것이다.

- AHI가 빠르니 인덱스를 대충 둬도 된다고 생각하면 안 된다
- AHI는 잘 설계된 인덱스를 더 빠르게 보조하는 장치다
- 쿼리 패턴이 바뀌면 AHI보다 인덱스 재설계가 먼저다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `adaptive hash index`
- `AHI`
- `innodb_adaptive_hash_index`
- `latch contention`
- `point lookup`
- `hot pages`
- `buffer pool`

## 실전 시나리오

### 시나리오 1. 로그인/세션/tenant lookup이 매우 잦다

같은 키로 반복 조회가 많으면 AHI가 꽤 유리할 수 있다.  
특히 작은 핫셋을 자주 찍는 API에서는 인덱스 상단 탐색 비용이 눈에 띈다.

### 시나리오 2. 배치가 시작되자 p99가 튄다

배치가 range scan과 업데이트를 섞어 실행하면, AHI 적중률이 떨어지고 유지 비용이 늘어날 수 있다.  
이때는 AHI를 끄는 것보다, 쿼리 경로와 스캔 범위를 먼저 본다.

### 시나리오 3. 장애 직후와 평시의 특성이 다르다

AHI는 버퍼 풀과 강하게 연결된 내부 구조라서, 핫셋이 바뀌면 체감도 달라진다.  
재시작 직후와 워밍업 후의 성능 차이가 큰 이유를 버퍼 풀과 함께 봐야 한다.

## 코드로 보기

### 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_adaptive_hash_index';
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
```

### 메모리 사용 관찰

```sql
SELECT EVENT_NAME, CURRENT_NUMBER_OF_BYTES_USED
FROM performance_schema.memory_summary_global_by_event_name
WHERE EVENT_NAME = 'memory/innodb/adaptive hash index';
```

### 온오프 비교 실험

```sql
SET GLOBAL innodb_adaptive_hash_index = OFF;

EXPLAIN ANALYZE
SELECT id, status
FROM orders
WHERE user_id = 1001
  AND id = 900001;

SET GLOBAL innodb_adaptive_hash_index = ON;
```

이런 비교는 임시 진단용으로만 써야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| AHI 활성화 | 반복 point lookup이 빨라질 수 있다 | 경합과 예측 불안정이 생긴다 | 핫셋이 안정적일 때 |
| AHI 비활성화 | 내부 경합을 줄일 수 있다 | 반복 조회에서 손해를 볼 수 있다 | 스캔/쓰기 비중이 높을 때 |
| 인덱스 재설계 | 근본 해결이 가능하다 | DDL과 검증 비용이 든다 | 패턴이 바뀌었을 때 |
| 워크로드 분리 | 효과가 크다 | 운영 구조가 복잡해진다 | OLTP와 배치가 섞일 때 |

핵심은 AHI를 믿을지 말지가 아니라, **반복 조회 패턴이 진짜 안정적인지**를 보는 것이다.

## 꼬리질문

> Q: AHI는 왜 만능이 아닌가요?
> 의도: 내부 캐시/가속 구조를 절대화하지 않는지 확인
> 핵심: 패턴이 바뀌면 적중률이 떨어지고 유지 비용이 생긴다

> Q: AHI가 도움이 되는 대표 패턴은 무엇인가요?
> 의도: point lookup과 range scan을 구분하는지 확인
> 핵심: 반복적인 키 조회와 작은 핫셋 탐색이다

> Q: AHI를 끄면 무조건 손해인가요?
> 의도: 성능 장치를 이분법적으로 보지 않는지 확인
> 핵심: 경합이 줄어 전체 시스템이 안정될 수 있다

## 한 줄 정리

Adaptive Hash Index는 반복 탐색을 더 빠르게 할 수 있지만, 경합과 적중률 변동을 함께 관리해야 하는 선택적 가속 장치다.
