---
schema_version: 3
title: Monotonic Reads and Session Guarantees
concept_id: database/monotonic-reads-session-guarantees
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- session-consistency
- replica-routing
- monotonic-read
- consistency-token
aliases:
- monotonic reads
- monotonic read
- session guarantees
- session consistency
- read goes backward
- saw newer then older
- sticky session read
- session watermark
- 읽기가 뒤로 감
- 새로고침했더니 옛값이 다시 보여요
symptoms:
- 같은 세션에서 한 번 최신 값을 본 뒤 새로고침이나 다음 화면에서 더 오래된 값이 다시 보여
- replica routing이 요청마다 바뀌면서 사용자가 saw newer then older 현상을 겪고 있어
- read-your-writes는 일부 지켰지만 세션이 이미 관측한 version보다 뒤로 떨어지는 문제가 남아 있어
intents:
- troubleshooting
- deep_dive
prerequisites:
- database/replica-lag-read-after-write-strategies
- database/read-your-writes-session-pinning
next_docs:
- database/client-consistency-tokens
- database/causal-consistency-intuition
- database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide
linked_paths:
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-read-routing-anomalies.md
- contents/database/client-consistency-tokens.md
- contents/database/causal-consistency-intuition.md
- contents/database/read-after-write-routing-decision-guide.md
- contents/database/replica-lag-observability-routing-slo.md
- contents/database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide.md
confusable_with:
- database/read-your-writes-session-pinning
- database/causal-consistency-intuition
- database/client-consistency-tokens
forbidden_neighbors: []
expected_queries:
- 같은 세션에서 최신 값을 봤다가 다시 옛값을 보는 건 어떤 consistency 문제야?
- monotonic read와 read-your-writes를 replica routing 관점에서 비교해줘
- session watermark나 version token으로 읽기가 뒤로 가지 않게 만드는 방법을 알려줘
- saw newer then older 문제가 replica lag만 작으면 해결되는지 설명해줘
- 결제나 권한 화면에서 session guarantee를 어디까지 강하게 걸어야 해?
contextual_chunk_prefix: |
  이 문서는 monotonic reads, session guarantees, session watermark, sticky replica routing으로 같은 사용자 세션의 읽기가 뒤로 가지 않게 만드는 advanced symptom router다.
  새로고침 후 옛값, saw newer then older, read goes backward, session consistency 질문이 본 문서에 매핑된다.
---
# Monotonic Reads와 Session Guarantees

> 한 줄 요약: 한 세션 안에서는 시간이 뒤로 가지 않아야 하고, 그 약속을 지키려면 읽기 라우팅이 “가장 최근에 본 값”을 기억해야 한다.

**난이도: 🔴 Advanced**

관련 문서: [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Client Consistency Tokens](./client-consistency-tokens.md), [Causal Consistency Intuition](./causal-consistency-intuition.md)
retrieval-anchor-keywords: monotonic reads, monotonic read, session guarantees, session guarantee, session consistency, session-consistent reads, read goes backward, saw newer then older, same session sees older data, refresh shows older value again, sticky read, sticky session read, version token, session watermark, causal consistency, monotonic read broken, 세션 일관성, 읽기가 뒤로 감, 방금 본 값보다 옛값, 새로고침했더니 더 옛값

## 증상별 바로 가기

- `write는 성공했는데 바로 안 보인다`, `save succeeded but old value returned`처럼 freshness 자체가 아직 확보되지 않았으면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)와 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)부터 본다.
- `한 번 최신을 본 뒤 다시 옛값을 본다`, `saw newer then older`, `refresh shows older value again`처럼 같은 세션의 읽기가 뒤로 가면 이 문서에서 monotonic read와 session guarantee를 본다.
- 서버 sticky session만으로 부족하고 탭/디바이스를 넘겨 같은 최신선을 운반해야 하면 [Client Consistency Tokens](./client-consistency-tokens.md)으로 이어 간다.
- `원인보다 결과를 먼저 본다`, `comment visible before post`처럼 의미 순서까지 지켜야 하면 [Causal Consistency Intuition](./causal-consistency-intuition.md)을 같이 본다.

## 핵심 개념

Monotonic read는 같은 사용자가 연속해서 읽을 때, 더 과거의 상태를 다시 보지 않도록 하는 보장이다.

freshness entry 문서들이 "최신 write가 한 번이라도 보이느냐"를 다룬다면, monotonic read는 그다음 단계인 "한 번 본 최신선보다 뒤로 다시 떨어지지 않느냐"를 다룬다.

왜 중요한가:

- 사용자는 새로고침할수록 오래된 상태를 다시 보는 일을 이상하게 느낀다
- replica routing이 바뀌면 같은 세션에서도 관측 시간이 뒤집힐 수 있다
- read-your-writes보다 더 넓은 의미로, “읽기의 시간이 되돌아가지 않게” 만드는 게 핵심이다

session guarantee는 단일 쿼리의 정확성보다, **한 사용자 흐름의 관측 순서**를 지키는 문제다.

## 깊이 들어가기

### 1. monotonic read가 깨지는 이유

다음 상황은 흔하다.

- 첫 요청은 replica A를 읽는다
- 두 번째 요청은 replica B를 읽는다
- B가 A보다 조금 더 뒤처져 있다

그러면 사용자는 같은 화면에서 이전에 봤던 값보다 더 오래된 값을 다시 본다.

이 문제는 lag가 크지 않아도 발생한다.  
핵심은 “늦은 replica”가 아니라 **서로 다른 replica 간 시간축이 다르다**는 점이다.

### 2. session guarantee가 필요한 곳

monotonic read는 다음 경로에서 특히 중요하다.

- 프로필 수정 후 목록/상세 이동
- 관리자 상태 전이 후 재조회
- 장바구니나 결제 상태처럼 순서가 중요한 화면

이 경로에서는 단순 확장성보다 사용자 관측의 일관성이 더 중요하다.

### 3. 구현 방식

대표적인 구현은 다음과 같다.

- 세션이 본 최소 version/LSN/GTID를 기억한다
- replica가 그 version 이상인지 확인한다
- 부족하면 primary나 더 앞선 replica로 보낸다

이 방식은 read-your-writes보다 조금 넓다.  
내가 쓴 것만 보는 게 아니라, **내가 이미 본 미래보다 뒤로 가지 않는 것**이 목표다.
세션 메모리 대신 이 기준선을 클라이언트가 들고 다니게 하면 [Client Consistency Tokens](./client-consistency-tokens.md) 패턴이 된다.

### 4. 어디까지 강하게 할 것인가

모든 조회에 monotonic guarantee를 넣을 필요는 없다.

- 검색 결과 목록은 약한 일관성으로도 충분할 수 있다
- 결제/주문/권한 경로는 강하게 가져가야 한다
- 관리자와 운영자 화면은 더 보수적이어야 한다

즉 consistency는 전역 정책이 아니라 경로별 정책이다.

## 실전 시나리오

### 시나리오 1: 상태가 왔다 갔다 한다

사용자가 주문 상태를 `PAID`로 본 뒤 새로고침했는데 `PENDING`으로 돌아간다.  
이건 단순 lag보다 monotonic read 실패다.

### 시나리오 2: 같은 세션에서 페이지가 뒤집힌다

목록 페이지 1과 페이지 2가 서로 다른 replica를 타면, 정렬 결과가 뒤섞여 보일 수 있다.  
이때는 세션 단위 라우팅이 필요하다.

### 시나리오 3: 장애 후 다시 옛 상태를 본다

failover 직후 토폴로지가 바뀌면서 읽기 기준점이 흔들리면, 사용자는 시간을 거슬러 올라간 것처럼 느낀다.

## 코드로 보기

```java
class SessionReadContext {
    private long minSeenVersion;

    void observe(long version) {
        if (version > minSeenVersion) {
            minSeenVersion = version;
        }
    }

    boolean canReadFrom(long replicaVersion) {
        return replicaVersion >= minSeenVersion;
    }
}
```

```sql
-- version column이나 commit token을 사용해 라우팅 기준을 만들 수 있다
SELECT id, status, version
FROM orders
WHERE id = 9001;
```

monotonic read의 핵심은 “최신을 본다”가 아니라, **한 세션 안에서 더 과거로 되돌아가지 않는다**는 점이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무작위 replica 읽기 | 확장성이 좋다 | 시간 역행이 생길 수 있다 | 조회 위주 |
| 세션 version pinning | 관측 순서가 안정적이다 | 라우팅이 복잡해진다 | 상태 전이 경로 |
| primary fallback | 가장 안전하다 | primary 부하가 늘어난다 | 결제, 권한, 운영 화면 |
| causal token 기반 라우팅 | 정교하다 | 인프라 요구가 높다 | 대규모 시스템 |

## 꼬리질문

> Q: monotonic read는 read-your-writes와 어떻게 다른가요?
> 의도: 세션 보장 종류를 구분하는지 확인
> 핵심: read-your-writes는 내가 쓴 것을 보는 것이고, monotonic read는 내가 본 것보다 뒤로 가지 않는 것이다

> Q: 왜 replica lag이 작아도 monotonic read가 깨질 수 있나요?
> 의도: 라우팅 전환 문제를 아는지 확인
> 핵심: 서로 다른 replica의 관측 시점이 다를 수 있다

> Q: 모든 API에 session guarantee를 넣어야 하나요?
> 의도: 경로별 consistency 설계를 이해하는지 확인
> 핵심: 중요한 경로에만 강하게 적용하는 것이 보통 더 현실적이다

## 한 줄 정리

Monotonic read는 한 세션의 시간이 뒤로 가지 않게 하는 보장이고, 그 약속은 replica 라우팅이 세션의 관측 버전을 기억할 때만 유지된다.
