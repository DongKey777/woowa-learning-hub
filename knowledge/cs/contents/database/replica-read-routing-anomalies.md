---
schema_version: 3
title: Replica Read Routing Anomalies and Session Consistency
concept_id: database/replica-read-routing-anomalies
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 92
mission_ids: []
review_feedback_tags:
- replica-routing
- session-consistency
- monotonic-read
- read-after-write
- failover
aliases:
- replica read routing anomaly
- read routing anomaly
- inconsistent replica read
- different replica different results
- stale read after retry
- monotonic read broken
- read goes backward
- refresh old then new
- session affinity
- GTID based routing
symptoms:
- 새로고침할 때마다 어떤 때는 최신값이고 어떤 때는 옛값이 보여
- timeout 재시도 후 같은 조회가 다른 replica로 가면서 결과가 뒤로 돌아가
- 페이지네이션 중간에 replica가 바뀌어 중복이나 누락이 생겨
- write 직후 세션 안에서 read-after-write나 monotonic read를 보장해야 해
- failover 직후 topology cache가 낡아 old primary나 stale replica를 읽는 것 같아
intents:
- symptom
- troubleshooting
- design
prerequisites:
- database/replica-lag-read-after-write-strategies
- database/monotonic-reads-session-guarantees
next_docs:
- database/read-your-writes-session-pinning
- database/monotonic-reads-session-guarantees
- database/failover-promotion-read-divergence
linked_paths:
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/monotonic-reads-session-guarantees.md
- contents/database/causal-consistency-intuition.md
- contents/database/failover-promotion-read-divergence.md
- contents/database/failover-visibility-window-topology-cache-playbook.md
- contents/database/replication-failover-split-brain.md
confusable_with:
- database/replica-lag-observability-routing-slo
- database/read-your-writes-session-pinning
- database/failover-promotion-read-divergence
forbidden_neighbors: []
expected_queries:
- replica lag는 낮은데 새로고침할 때 값이 old new로 번갈아 보이면 무엇을 의심해야 해?
- retry나 connection pool 재선택 때문에 다른 replica를 읽으면 monotonic read가 왜 깨져?
- write 직후 내 세션에서는 primary pinning이나 GTID routing을 언제 써야 해?
- 페이지네이션이 replica A와 B를 번갈아 읽으면 중복 누락이 생기는 이유가 뭐야?
- failover 이후 topology cache가 낡아서 stale primary를 읽는 증상과 일반 lag 증상을 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 replica read routing anomaly, session consistency, read-after-write, monotonic read, GTID/LSN routing을 stale read 증상별로 설명하는 advanced symptom router다.
  새로고침 old/new 반복, retry returns older data, connection pool replica switch, session affinity 질문이 본 문서에 매핑된다.
---
# Replica Read Routing Anomalies와 세션 일관성

> 한 줄 요약: replica lag만 막아서는 부족하고, 요청이 어떤 replica로 흘러가느냐 자체가 일관성을 깨뜨릴 수 있다.

**난이도: 🔴 Advanced**

관련 문서: [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md), [Causal Consistency Intuition](./causal-consistency-intuition.md), [Failover Promotion Read Divergence](./failover-promotion-read-divergence.md), [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md)
retrieval-anchor-keywords: replica read routing anomaly, replica routing anomaly, read routing anomaly, different replica different results, stale read after retry, refresh shows old then new, value flips between refreshes, inconsistent replica read, session consistency, monotonic read broken, read goes backward, sometimes old sometimes new, retry returns older data, pagination duplicates across replicas, pagination missing rows across replicas, connection pool replica switch, topology cache stale, failover read divergence, session affinity, causal consistency, GTID, 새로고침할 때마다 값 달라짐, 어떤 때는 최신 어떤 때는 옛값, 재시도 후 결과 바뀜, 페이지네이션 중복 누락

## 증상별 바로 가기

- `어떤 때는 최신, 어떤 때는 옛값`, `refresh shows old then new`, `retry returns older data`처럼 요청마다 결과가 흔들리면 이 문서에서 replica selection, retry path, topology cache 문제를 먼저 본다.
- `write 직후 최신성이 안 맞는다`가 핵심이면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)에서 lag budget과 primary fallback을 먼저 본다.
- `내가 쓴 값이 내 세션에서 유지돼야 한다`가 핵심이면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 바로 간다.
- failover 직후 promotion, topology cache, stale primary 의심이면 [Failover Promotion Read Divergence](./failover-promotion-read-divergence.md)와 [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md)을 이어 본다.

## 핵심 개념

replica를 읽기 분산에 쓰면 좋은 점이 많지만, 라우팅이 조금만 흔들려도 사용자는 “방금 바꾼 값이 사라졌다”고 느낀다.

왜 중요한가:

- 같은 요청 흐름인데도 어떤 때는 최신값, 어떤 때는 옛값이 보인다
- retry나 connection pool 재선택만으로도 읽기 대상이 바뀔 수 있다
- failover 직후에는 replica와 primary 사이의 시간축이 어긋난다

이 문서의 초점은 단순 lag가 아니라, **어떤 요청을 어떤 서버로 보내느냐**다.

## 깊이 들어가기

### 1. lag보다 무서운 라우팅 흔들림

대표적인 실수는 “replica는 좀 늦을 수 있다”까지만 생각하는 것이다.

실제로는 다음이 더 위험하다.

- 같은 HTTP 요청 안에서 서로 다른 replica를 본다
- write 직후 retry가 다른 서버로 간다
- connection pool이 새 커넥션을 뽑으며 다른 replica를 고른다
- failover 후에도 앱이 이전 토폴로지를 잠시 믿는다

이런 상황에서는 lag가 작아도 읽기 결과가 뒤집힌다.

### 2. 세션 일관성이 왜 필요한가

사용자가 한 번 쓴 변화는 적어도 그 세션 안에서는 계속 보여야 한다.

- 내 프로필 수정 후 새로고침하면 바로 보여야 한다
- 결제 상태가 `PAID`로 바뀌었으면 다시 읽을 때도 보여야 한다
- 관리자 화면은 특히 monotonic read가 중요하다

즉 “읽기 분산”이 아니라 **세션 단위 causality**를 지켜야 한다.

### 3. 어떤 신호로 라우팅해야 하는가

실무에서는 보통 다음 중 하나를 쓴다.

- 최근 write가 있었는지
- 그 세션이 본 최소 GTID/LSN이 무엇인지
- primary fallback이 필요한 경로인지
- user/session sticky를 얼마 동안 유지할지

핵심은 “서버가 최신인가”보다 “내가 본 결과보다 뒤로 가지 않는가”다.

### 4. 왜 failover와도 엮이는가

primary가 바뀌면 라우팅 규칙도 같이 바뀐다.

- 옛 primary에 쓰던 토큰이 새 primary에서는 무효일 수 있다
- replica promotion 직후 캐시된 topology가 틀릴 수 있다
- 읽기 요청이 잠깐 과거 노드를 타면 데이터가 사라진 것처럼 보인다

## 실전 시나리오

### 시나리오 1: 프로필 수정 직후 새로고침하면 옛 이름이 보임

lag가 작아도, 재조회가 다른 replica로 가면 결과가 뒤집힌다.  
이 경우 최근 write 세션은 primary로 pinning해야 한다.

### 시나리오 2: 페이지네이션 중간에 데이터가 앞뒤로 튐

1페이지는 replica A, 2페이지는 replica B를 읽으면 정렬 기준이 달라질 수 있다.  
사용자는 “중복이 보인다” 또는 “몇 개가 사라졌다”고 느낀다.

### 시나리오 3: retry가 다른 replica로 가면서 관측이 바뀜

일시적 timeout 후 재시도하면, 같은 쿼리라도 다른 노드를 보고 전혀 다른 결과를 얻을 수 있다.  
이건 단순 오류가 아니라 라우팅 정책의 결함이다.

## 코드로 보기

```java
// 최근 write가 있었으면 같은 세션 동안 primary에 고정한다.
class ReadRouter {
    DataSource route(SessionContext ctx) {
        if (ctx.hasRecentWrite()) {
            return primaryDataSource;
        }
        if (!ctx.isReplicaSafe()) {
            return primaryDataSource;
        }
        return replicaPool.pick(ctx.sessionId());
    }
}
```

```sql
-- GTID 기반으로 replica가 특정 시점까지 따라왔는지 확인하는 패턴
SELECT WAIT_FOR_EXECUTED_GTID_SET('uuid:1-12345', 1);
SELECT * FROM users WHERE id = 10;
```

라우팅의 핵심은 “느린 replica를 피하자”가 아니라, **관측한 causality를 유지하자**다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무작위 replica 읽기 | 부하 분산이 쉽다 | 세션 일관성이 깨지기 쉽다 | 최신성이 덜 중요한 조회 |
| 최근 write는 primary pinning | read-after-write가 안정적이다 | primary 부하가 늘어난다 | 결제, 프로필, 관리 화면 |
| GTID/LSN 기반 라우팅 | causality를 정교하게 다룬다 | 구현이 복잡하다 | 중요한 데이터 경로 |
| sticky session | 구현이 단순하다 | 부하 분산 효율이 떨어진다 | 사용자 세션 중심 서비스 |

## 꼬리질문

> Q: replica lag을 막았는데도 왜 옛 데이터가 보이나요?
> 의도: 라우팅 자체가 일관성을 깨뜨릴 수 있음을 아는지 확인
> 핵심: 같은 요청이 다른 replica를 타면 결과가 뒤집힐 수 있다

> Q: read-after-write를 보장하려면 무엇을 봐야 하나요?
> 의도: lag 외에 causality 기반 판정을 아는지 확인
> 핵심: 최근 write, GTID/LSN, 세션 pinning이 중요하다

> Q: replica 읽기와 failover를 같이 쓰면 왜 더 복잡한가요?
> 의도: topology 변경 시 라우팅 안정성 이해 여부 확인
> 핵심: 노드 역할과 토폴로지가 바뀌면서 이전 가정이 깨진다

## 한 줄 정리

Replica 읽기는 lag 관리만으로는 부족하고, 세션 단위로 어느 노드를 읽는지까지 제어해야 read-after-write와 monotonic read를 지킬 수 있다.
