---
schema_version: 3
title: Failover Visibility Window, Topology Cache, and Freshness Playbook
concept_id: database/failover-visibility-window-topology-cache-playbook
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- failover-visibility-window
- topology-cache-invalidation
- freshness-fence-after-promotion
aliases:
- failover visibility window
- topology cache invalidation
- stale endpoint read
- promotion visibility
- freshness fence
- failover read consistency
- topology version mismatch
- failover cache bust
- old dns after promotion
- visibility window
symptoms:
- failover 완료 후에도 topology cache, DNS TTL, connection pool 때문에 옛 DB나 cache를 읽는 요청이 남아 있어
- promotion 이후 일정 시간 primary pinning이나 freshness fence를 둬야 하는지 판단해야 해
- stale read forensic에서 요청이 본 topology version, endpoint, cache hit 여부를 추적해야 해
intents:
- troubleshooting
- design
prerequisites:
- database/failover-promotion-read-divergence
- database/primary-switch-write-fencing
next_docs:
- database/commit-horizon-after-failover-verification
- database/read-repair-reconciliation-after-failover
- database/read-after-write-routing-decision-guide
linked_paths:
- contents/database/replica-lag-observability-routing-slo.md
- contents/database/failover-promotion-read-divergence.md
- contents/database/primary-switch-write-fencing.md
- contents/database/replication-failover-split-brain.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/commit-horizon-after-failover-verification.md
- contents/database/read-repair-reconciliation-after-failover.md
- contents/database/read-after-write-routing-decision-guide.md
- contents/database/read-your-writes-session-pinning.md
confusable_with:
- database/failover-promotion-read-divergence
- database/replica-lag-observability-routing-slo
- database/commit-horizon-after-failover-verification
forbidden_neighbors: []
expected_queries:
- failover visibility window를 줄이려면 topology cache invalidation과 primary pinning을 어떤 순서로 해야 해?
- failover 후 some pods old some new 상태에서 stale endpoint read를 어떻게 forensic해?
- promotion 이후 freshness fence나 consistency token을 잠깐 강하게 거는 이유는 뭐야?
- DB failover event와 cache invalidation event가 분리되면 어떤 stale read가 생겨?
- failover stale read가 replication lag인지 topology version mismatch인지 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 failover 뒤 topology cache, DNS TTL, connection pool, cache invalidation, freshness fence가 어긋나는 visibility window를 줄이는 advanced playbook이다.
  failover visibility window, topology cache invalidation, stale endpoint read, freshness fence 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# Failover Visibility Window, Topology Cache, and Freshness Playbook

> 한 줄 요약: failover 후 사용자가 겪는 "어떤 화면은 새 값, 어떤 화면은 옛 값" 문제는 복제 자체보다 topology cache, read routing, freshness fence가 한동안 제각각 움직이는 visibility window에서 생긴다.

**난이도: 🔴 Advanced**

관련 문서:

- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)
- [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md)
- [Primary Switch와 Write Fencing](./primary-switch-write-fencing.md)
- [Replication Failover and Split Brain](./replication-failover-split-brain.md)
- [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)
- [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md)
- [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)

retrieval-anchor-keywords: failover visibility window, topology cache invalidation, stale endpoint read, promotion visibility, freshness fence, failover read consistency, post promotion stale reads, failover freshness, topology version mismatch, some pods old some new, new primary but old cache, old dns after promotion, old primary still serving reads, topology cache stale, failover cache bust, promotion freshness incident

## 빠른 증상 라우팅

| 보이는 증상 | 먼저 볼 문서 | 이유 |
|---|---|---|
| promotion 직후 read authority가 왜 둘로 갈라지는지 개념부터 잡아야 한다 | [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md) | old primary / new primary / stale replica가 함께 읽히는 구조를 설명한다 |
| failover와 무관한 steady-state lag metric, routing threshold, fallback SLO를 설계해야 한다 | [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md) | visibility window 전 단계의 관측/정책 문제다 |
| `some pods old some new`, `topology cache stale`, `DNS TTL after promotion`처럼 지금 invalidation과 pinning 순서를 정해야 한다 | 이 문서 | failover 이후 freshness incident의 실전 액션 순서를 담고 있다 |
| 최근 write가 stale한 게 아니라 새 primary에 실제로 없는지 확인해야 한다 | [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md) | visibility window와 write loss를 구분해야 한다 |

## 핵심 개념

failover는 control plane에서는 한 순간처럼 보인다.

- new primary promoted
- old primary fenced
- traffic switched

하지만 사용자 관점에서는 한동안 여러 경로가 다른 현실을 볼 수 있다.

- app connection pool
- topology cache
- DNS / service discovery TTL
- session pinning state
- stale cache entries

이 과도기를 visibility window라고 볼 수 있다.  
즉 failover 운영의 마지막 과제는 승격이 아니라, **읽기 현실을 다시 하나로 모으는 것**이다.

## 깊이 들어가기

### 1. visibility window는 "DB 전환 완료" 이후에도 남는다

control plane이 전환 완료를 선언해도:

- 일부 애플리케이션 인스턴스는 old endpoint를 유지
- 일부 클라이언트는 old DNS를 참조
- 일부 cache는 pre-failover 값을 계속 반환

할 수 있다.

그래서 failover 완료 시점과 사용자 일관성 회복 시점은 다를 수 있다.

### 2. topology cache invalidation이 늦으면 read divergence가 길어진다

특히 내부 라우터/ORM/connection pool이 topology를 캐시하면:

- write는 새 primary로 가는데
- 일부 read는 old node나 lagging replica로 갈 수 있다

이건 단순 lag가 아니라, **authoritative source에 대한 합의가 늦는 문제**다.

### 3. freshness fence를 두면 전환 직후를 더 안전하게 지날 수 있다

전환 직후 일정 기간:

- 모두 primary pinning
- consistency token/epoch 기반 최소 freshness 보장
- stale endpoint reject

같은 보수적 fence를 두면 visibility window를 짧게 만들 수 있다.

핵심은 평시 최적화보다, 전환 직후 **잠깐 더 보수적으로 읽는 것**이다.

### 4. cache invalidation과 failover event는 분리되면 안 된다

운영에서 자주 놓치는 점:

- DB failover event는 갔는데
- cache/topology invalidation event는 늦거나 누락

이러면 old DB를 안 읽어도 old cache가 계속 남는다.

즉 failover 후 visibility 안정화에는:

- DB fencing
- topology refresh
- cache invalidation

이 같이 움직여야 한다.

### 5. forensic 관점에서는 "그 요청이 어느 topology version을 봤나"가 중요하다

사용자 stale read를 분석할 때 필요한 것:

- failover timestamp
- app instance topology version
- chosen DB endpoint
- cache hit 여부
- session consistency state

이 정보가 없으면 "replication lag인가?"라는 잘못된 질문만 반복하게 된다.

반대로 이 telemetry를 봤는데 topology version은 갈라져 있고 lag metric은 멀쩡하다면, 이 이슈는 [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)의 threshold 조정보다 이 playbook의 invalidation / fence / pinning 순서를 먼저 손봐야 한다.

### 6. reconciliation은 visibility window가 끝난 뒤의 cleanup이다

visibility window 동안 stale read가 있었더라도, 이후에는:

- cache refresh
- read repair
- projection reconciliation

으로 수습할 수 있다.

즉 visibility window를 줄이는 것이 1차 목표이고, 남은 잔여 불일치는 reconciliation이 맡는다.

## 실전 시나리오

### 시나리오 1. failover 후 모바일과 관리자 화면이 다른 값 표시

원인:

- 모바일 API는 새 topology
- 관리자 화면은 old topology cache

대응:

- forced topology invalidation
- 짧은 primary pinning window

### 시나리오 2. old primary는 fenced됐는데 stale read가 계속 남음

원인:

- DB가 아니라 application cache가 old value를 유지

대응:

- failover event와 cache bust 묶기

### 시나리오 3. 사용자는 한 번만 stale read를 경험

이 경우는 reconciliation보다 visibility window telemetry가 더 중요하다.  
왜냐하면 재현은 어렵고, 라우팅 버전 추적이 핵심 단서이기 때문이다.

## 코드로 보기

```java
class TopologySnapshot {
    long version;
    String primaryEndpoint;
}

void onFailover(FailoverEvent event) {
    topologyCache.invalidate();
    cacheNamespace.bump("db-topology");
}
```

```text
post-failover safety window
1. fence old primary writes
2. invalidate topology cache
3. invalidate stale read caches
4. temporarily pin reads to new primary
5. relax to normal routing after stabilization
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 즉시 normal routing 복귀 | 부하가 적다 | stale read window가 길어질 수 있다 | 가벼운 서비스 |
| short primary pinning fence | visibility를 빠르게 안정화한다 | primary 부하가 증가한다 | failover 직후 |
| aggressive topology invalidation | divergence를 줄인다 | refresh storm이 생길 수 있다 | 중요한 관리/결제 데이터 |
| cache namespace bump | stale cache 제거가 명확하다 | 캐시 hit rate가 일시 하락한다 | failover event 대응 |

## 꼬리질문

> Q: failover 후 stale read가 남는 이유가 꼭 replication lag인가요?
> 의도: topology/cache/routing 문제를 구분하는지 확인
> 핵심: 아니다. topology cache와 stale cache가 더 직접 원인일 수 있다

> Q: visibility window를 줄이려면 무엇이 가장 중요하나요?
> 의도: control plane과 read path를 함께 보는지 확인
> 핵심: topology invalidation, cache invalidation, 짧은 freshness fence를 같이 적용해야 한다

> Q: reconciliation은 언제 필요한가요?
> 의도: visibility 완화와 사후 정리를 분리하는지 확인
> 핵심: visibility window 이후에도 남은 stale projection이나 cache를 정리할 때 필요하다

## 한 줄 정리

failover visibility 문제의 핵심은 복제 지연보다, 여러 read 경로가 서로 다른 topology 버전을 보는 과도기와 그것을 얼마나 빨리 invalidation/fence로 줄이느냐에 있다.
