---
schema_version: 3
title: Monotonic Write Guarantees
concept_id: database/monotonic-write-guarantees
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- monotonic-write
- write-ordering
- sequence-gate
- session-consistency
aliases:
- monotonic write
- monotonic writes
- write ordering
- session write order
- sequence gate
- fencing epoch
- retry reorders writes
- 늦은 요청이 최신 값을 덮어요
- 쓰기 순서가 뒤집혀요
symptoms:
- 같은 세션에서 뒤에 보낸 변경이 먼저 반영되고 늦은 retry가 최신 값을 덮어쓰고 있어
- 상태 전이 API에서 PENDING APPROVED REJECTED 같은 write order가 뒤집혀 비즈니스 흐름이 깨져
- profile이나 setting update가 거의 동시에 들어올 때 오래된 요청이 최신 변경을 원복해
intents:
- deep_dive
- design
prerequisites:
- database/monotonic-reads-session-guarantees
- database/read-your-writes-session-pinning
next_docs:
- database/client-consistency-tokens
- database/causal-consistency-intuition
- database/compare-and-set-version-columns
linked_paths:
- contents/database/monotonic-reads-session-guarantees.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-read-routing-anomalies.md
- contents/database/client-consistency-tokens.md
- contents/database/causal-consistency-intuition.md
- contents/database/compare-and-set-version-columns.md
- contents/database/application-level-fencing-token-propagation.md
confusable_with:
- database/read-your-writes-session-pinning
- database/compare-and-set-version-columns
- database/application-level-fencing-token-propagation
forbidden_neighbors: []
expected_queries:
- monotonic write는 read-your-writes와 무엇이 다르고 어떤 API에 필요해?
- timeout retry가 늦게 도착해서 최신 변경을 덮는 문제를 sequence gate로 막는 법을 알려줘
- 상태 전이 API에서 write ordering을 지키려면 어떤 token이나 fencing이 필요해?
- 같은 사용자 세션의 profile update 순서가 뒤집히는 현상을 어떻게 설계로 막아?
- monotonic write 보장이 필요한 경로와 필요 없는 경로를 구분해줘
contextual_chunk_prefix: |
  이 문서는 monotonic write, session write order, sequence gate, fencing epoch으로 같은 세션의 쓰기 순서가 뒤집히지 않게 하는 advanced deep dive다.
  늦은 retry가 최신 값을 덮음, write ordering 역전, 상태 전이 순서 보장 질문이 본 문서에 매핑된다.
---
# Monotonic Write Guarantees

> 한 줄 요약: monotonic write는 같은 세션의 쓰기가 순서대로 반영된다는 약속이고, 라우팅이 뒤집히면 이 약속이 쉽게 깨진다.

**난이도: 🔴 Advanced**

관련 문서: [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)
retrieval-anchor-keywords: monotonic write, session order, write ordering, causal consistency, write routing

## 핵심 개념

Monotonic write는 한 세션에서 발생한 write가 순서를 거꾸로 보이지 않도록 하는 보장이다.  
즉, 뒤에 발생한 write가 앞선 write보다 먼저 보이거나, 앞선 write를 덮어써서 사라지는 일이 없어야 한다.

왜 중요한가:

- 프로필 수정, 상태 전이, 권한 변경이 순서대로 적용되어야 한다
- write가 여러 경로를 타면 순서가 바뀔 수 있다
- 읽기 일관성보다 쓰기 순서가 먼저 무너지면 재현이 더 어렵다

monotonic write는 단순히 “잘 저장됐다”보다, **저장 순서가 세션 관점에서 유지되는가**를 묻는다.

## 깊이 들어가기

### 1. write 순서가 왜 뒤집히는가

다음 상황을 생각하면 된다.

- 같은 사용자 세션에서 update A, update B가 발생
- B는 빠른 경로로 반영
- A는 네트워크 지연이나 재시도로 더 늦게 도착

이때 늦은 A가 B를 덮어쓰면 순서가 뒤집힌다.

### 2. 왜 read-after-write와 다르지 않은가

read-your-writes는 내가 쓴 것을 보는 문제다.  
monotonic write는 내가 쓴 것들의 **서로 간 순서**를 지키는 문제다.

둘은 비슷해 보이지만, write ordering이 흔들리면 read route를 고쳐도 해결되지 않는다.

### 3. 구현 방식

- 세션별 write sequence number
- 단조 증가하는 fencing epoch
- 최신 sequence만 accept하는 write gate
- reorder 가능성이 있는 경로는 serialize

핵심은 늦은 write가 최신 write를 덮지 못하게 하는 것이다.

### 4. 어떤 경로에서 필요한가

- 상태 전이 API
- profile/settings update
- 권한/멤버십 수정
- 작업 순서가 중요한 workflow

즉 최신성보다 **순서 보장**이 중요한 곳이다.

## 실전 시나리오

### 시나리오 1: 이름 변경 후 다시 원복됨

두 요청이 같은 세션에서 거의 동시에 날아가면, 늦은 요청이 앞선 요청을 덮을 수 있다.  
순서 토큰이 없으면 뒤집힘을 막기 어렵다.

### 시나리오 2: 상태 전이 역전

`PENDING -> APPROVED -> REJECTED` 같은 요청이 reorder되면, 비즈니스 흐름이 이상해진다.

### 시나리오 3: retry가 순서를 깨뜨림

timeout 재시도가 원래 요청보다 늦게 처리되면 이전 변경을 덮을 수 있다.

## 코드로 보기

```java
class WriteSession {
    private long sequence;

    long nextSequence() {
        return ++sequence;
    }
}

boolean acceptWrite(long incomingSequence, long lastAcceptedSequence) {
    return incomingSequence > lastAcceptedSequence;
}
```

```sql
UPDATE user_profile
SET nickname = 'kim2',
    write_seq = 12
WHERE id = 10
  AND write_seq < 12;
```

monotonic write는 “최신 값”이 아니라, **쓰기 순서의 단조성**을 지키는 장치다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무순서 write | 단순하다 | 순서 역전 위험 | 중요하지 않은 로그성 데이터 |
| sequence gate | 순서를 지킨다 | 상태 관리가 필요하다 | 상태 전이 API |
| primary pinning | 구현이 쉽다 | 실패 시 fallback이 느리다 | 중요한 세션 |
| full serialization | 가장 안전하다 | 비용이 크다 | 소수의 핵심 경로 |

## 꼬리질문

> Q: monotonic write와 read-your-writes는 어떻게 다른가요?
> 의도: write 순서와 read 관측을 분리해서 아는지 확인
> 핵심: read-your-writes는 내가 쓴 것을 보는 것이고, monotonic write는 쓰기 순서를 지키는 것이다

> Q: 왜 retry가 write ordering을 깨나요?
> 의도: 늦은 재시도가 최신 write를 덮는 문제를 아는지 확인
> 핵심: 늦게 도착한 오래된 요청이 더 늦은 변경을 덮을 수 있다

> Q: 순서 토큰만 있으면 충분한가요?
> 의도: 경로 전체 일관성의 필요를 아는지 확인
> 핵심: 라우팅과 상태 저장이 함께 따라야 한다

## 한 줄 정리

Monotonic write는 세션 내 write 순서가 뒤집히지 않게 하는 보장이며, 늦은 요청이 최신 변경을 덮지 못하도록 sequence gate나 fencing이 필요하다.
