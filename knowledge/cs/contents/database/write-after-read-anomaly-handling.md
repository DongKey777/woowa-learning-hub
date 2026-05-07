---
schema_version: 3
title: Write-After-Read Anomaly Handling
concept_id: database/write-after-read-anomaly-handling
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- stale-read
- write-after-read
- consistency
- version-check
- conditional-update
aliases:
- write-after-read
- stale read
- read validate write
- read dependency
- recheck before write
- stale read before write
- write after stale replica read
- conditional update after read
- read dependency version token
- 최신 row 재검증
symptoms:
- replica나 cache에서 읽은 stale 값으로 business decision을 하고 write해 잘못된 상태 변경이 생길 수 있어
- read-after-write가 아니라 read 값을 근거로 write할 때 write 직전 재검증이 필요해
- retry 시 같은 결정을 그대로 다시 쓰지 말고 fresh read부터 다시 해야 해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/replica-read-routing-anomalies
- database/cache-replica-split-read-inconsistency
next_docs:
- database/transaction-retry-serialization-failure-patterns
- database/version-column-retry-walkthrough
- database/compare-and-set-version-columns
linked_paths:
- contents/database/replica-read-routing-anomalies.md
- contents/database/cache-replica-split-read-inconsistency.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/version-column-retry-walkthrough.md
- contents/database/compare-and-set-version-columns.md
confusable_with:
- database/replica-read-routing-anomalies
- database/monotonic-reads-session-guarantees
- database/version-column-retry-walkthrough
forbidden_neighbors: []
expected_queries:
- write-after-read anomaly는 stale read를 근거로 write할 때 어떤 문제가 생기는 거야?
- cache나 replica에서 읽은 값으로 승인 결정을 내리기 전에 write 직전 recheck가 필요한 이유는?
- read dependency version token을 저장하고 conditional update로 검증하는 패턴을 설명해줘
- write 실패 뒤 같은 결정을 다시 쓰면 안 되고 fresh read부터 다시 해야 하는 이유가 뭐야?
- read-after-write와 write-after-read consistency 문제는 방향이 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 write-after-read anomaly를 stale read, read dependency, recheck before write, conditional update, version token 관점으로 다루는 advanced playbook이다.
  stale read before write, write after stale replica read, read validate write 질문이 본 문서에 매핑된다.
---
# Write-After-Read Anomaly Handling

> 한 줄 요약: read를 근거로 write할 때는, 그 read가 이미 stale일 수 있다는 사실을 전제로 다시 검증해야 한다.

**난이도: 🔴 Advanced**

관련 문서: [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
retrieval-anchor-keywords: write-after-read, stale read, read validate write, read dependency, recheck before write

## 핵심 개념

Write-after-read anomaly는 읽은 값을 근거로 다시 쓰는 흐름에서, 읽기 시점이 stale이면 잘못된 write가 일어나는 문제다.  
이건 read-after-write와 반대 방향의 일관성 문제다.

왜 중요한가:

- 읽은 값에 따라 조건부 업데이트를 할 때 자주 생긴다
- replica나 cache를 읽고 write 결정을 내리면 잘못된 판단이 가능하다
- “읽었을 때 맞았는데 왜 쓰고 나니 틀렸지?”가 운영에서 자주 나온다

핵심은 읽기 결과를 진실로 믿기 전에 **쓰기 직전 다시 확인**해야 한다는 점이다.

## 깊이 들어가기

### 1. 왜 문제가 생기나

전형적인 흐름은 다음과 같다.

1. 상태를 읽는다
2. 읽은 값으로 비즈니스 결정을 한다
3. 그 값을 근거로 write한다

문제는 1번이 stale일 수 있다는 점이다.

- cache가 오래됨
- replica lag가 있음
- 다른 트랜잭션이 그 사이 값을 바꿈

### 2. recheck before write

가장 단순한 방어는 write 직전에 다시 검증하는 것이다.

- version token 재확인
- 최신 row 다시 읽기
- 조건부 update 사용
- 비즈니스 불변식 재검증

즉 read는 힌트일 뿐, write는 최종 검증을 거쳐야 한다.

### 3. read dependency를 저장하라

읽은 값이 write의 근거라면, 그 근거의 version을 같이 저장하는 편이 안전하다.

- 어떤 version을 보고 결정을 했는지
- write 시점에 그 version이 아직 유효한지

이렇게 해야 stale read에 의한 잘못된 결정을 줄일 수 있다.

### 4. write-after-read와 retry

write 실패가 났을 때 무조건 같은 결정을 다시 쓰면 안 된다.  
read를 다시 하고, 필요하면 결정 자체를 바꿔야 한다.

## 실전 시나리오

### 시나리오 1: 재고를 보고 주문 생성

재고를 읽고 주문을 만들었는데, 그 사이 재고가 줄었을 수 있다.  
write 전에 다시 검증하지 않으면 초과 주문이 생긴다.

### 시나리오 2: 권한을 보고 작업 승인

권한 정보를 읽고 승인했는데, 실제 write 시점에는 권한이 취소됐을 수 있다.  
이때 read dependency를 다시 확인해야 한다.

### 시나리오 3: cache를 보고 정책 저장

옛 정책을 읽고 새 정책을 저장하면, 최신 변경을 덮어쓸 수 있다.  
version check가 필요하다.

## 코드로 보기

```java
OrderSnapshot snapshot = readCurrentOrThrow(orderId);
if (snapshot.getVersion() != expectedVersion) {
    throw new ConcurrentModificationException();
}
saveWithVersion(orderId, snapshot.getVersion());
```

```sql
UPDATE stock
SET amount = amount - 1,
    version = version + 1
WHERE sku = 'SKU-1'
  AND version = 12
  AND amount > 0;
```

write-after-read 문제는 read를 믿는 순간 시작되므로, **write 직전 재검증이 핵심 방어선**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| read once then write | 단순하다 | stale read 위험 | 거의 없음 |
| recheck before write | 안전하다 | 추가 read가 필요하다 | 대부분의 상태 변경 |
| conditional update | 짧고 강하다 | SQL로 표현해야 한다 | 카운터/재고 |
| version dependency tracking | 정교하다 | 복잡하다 | 중요 워크플로우 |

## 꼬리질문

> Q: write-after-read anomaly는 왜 위험한가요?
> 의도: 읽은 값이 stale일 수 있다는 점을 아는지 확인
> 핵심: 잘못된 read를 근거로 잘못된 write를 하기 때문이다

> Q: write 직전에 다시 확인해야 하는 이유는 무엇인가요?
> 의도: 최종 검증의 필요성을 아는지 확인
> 핵심: read 시점과 write 시점 사이에 상태가 바뀔 수 있다

> Q: conditional update가 왜 도움이 되나요?
> 의도: 저장 시점 충돌 감지를 이해하는지 확인
> 핵심: version이나 조건이 맞을 때만 write되기 때문이다

## 한 줄 정리

Write-after-read anomaly는 stale read를 근거로 잘못된 write를 하는 문제이고, write 직전 재검증이나 조건부 update로 막아야 한다.
