---
schema_version: 3
title: Replica Lag and Read-after-write Strategies
concept_id: database/replica-lag-read-after-write-strategies
canonical: false
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
aliases:
- replica lag
- read-after-write
- stale read after write
- primary fallback
- read replica delay
intents:
- deep_dive
linked_paths:
- contents/database/read-your-writes-session-pinning.md
- contents/system-design/read-after-write-routing-primer.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/system-design/post-write-stale-dashboard-primer.md
- contents/database/replica-lag-observability-routing-slo.md
forbidden_neighbors:
- contents/security/session-cookie-jwt-basics.md
expected_queries:
- replica lag 때문에 write 직후 read가 stale하면 어떻게 설계해?
- 저장 직후 조회가 안 보일 때 replica lag와 cache 문제를 어떻게 나눠?
- read-after-write 전략에서 primary fallback은 언제 써?
- insert succeeded but select misses row면 어떤 freshness 문서를 봐야 해?
---

# Replica Lag and Read-after-write Strategies

> 한 줄 요약: replica를 붙인 뒤 "방금 쓴 데이터가 안 보인다"는 문제는 설계가 아니라 전파 지연을 다루는 방식의 문제다.

**난이도: 🔴 Advanced**

> 관련 문서: [MVCC, Replication, Sharding](./mvcc-replication-sharding.md), [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md), [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md), [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md), [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md), [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)
retrieval-anchor-keywords: replica lag, read after write, read-after-write, stale read after write, primary fallback, session stickiness, version routing, replication delay, stale read incident, old data after write, saved but still old data, save succeeded but old value returned, write succeeded read is stale, insert succeeded but select misses row, created row not visible yet, just wrote but cannot read, read own write missing, read replica delay, freshness after write, cache invalidation vs replica lag, cache miss stale replica, mixed stale source, stale cache or replica, 방금 저장했는데 옛값, 저장 직후 조회 안 보임, 생성 직후 데이터 안 보임

## 증상별 바로 가기

- `write는 성공했는데 바로 조회하면 안 보인다`, `save succeeded but old value returned`처럼 write 직후 freshness 자체가 문제면 이 문서에서 replica lag, primary fallback, version routing부터 본다.
- `cache miss 뒤에만 옛값`, `cache invalidation vs replica lag`, `캐시와 리플리카가 서로 다른 값을 준다`처럼 stale source 자체를 먼저 가려야 하면 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)로 바로 이동한다.
- `내가 방금 바꾼 값이 내 세션에서만 바로 보여야 한다`, `refresh after edit shows old value`처럼 세션 보장이 핵심이면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 바로 이동한다.
- `새로고침할 때마다 최신/옛값이 번갈아 보인다`, `retry changed the result`처럼 라우팅 흔들림이 보이면 [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)을 먼저 본다.

## 핵심 개념

primary/replica 구조에서는 쓰기와 읽기가 다른 서버로 갈 수 있다.  
이때 replica lag 때문에 read-after-write 일관성이 깨질 수 있다.

왜 중요한가:

- 주문 직후 상세 조회가 옛 데이터를 보여줄 수 있다
- 재고/결제/권한 변경처럼 즉시 반영이 필요한 화면이 있다
- replica는 읽기 확장을 주지만 일관성 비용을 숨긴다

중요한 점은 사용자 stale read가 항상 replica lag 그 자체를 뜻하지는 않는다는 것이다.
실제 질문은 `old data after write`, `방금 저장했는데 옛값`, `write는 성공했는데 조회는 예전 데이터`처럼 더 자연어에 가깝게 들어오는 경우가 많다.
실제 lag, routing, cache, session consistency를 같이 봐야 한다.

특히 cache-first + replica fallback 구조에서는 pure lag incident인지, cache invalidation 이후 stale replica를 다시 채운 incident인지 먼저 갈라야 한다.
그 분기점이 애매하면 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)로 넘어가 stale source split부터 확인하는 편이 빠르다.

## 깊이 들어가기

### 1. lag가 생기는 이유

복제는 완전히 동기적이지 않은 경우가 많다.

- binlog apply 지연
- 네트워크 지연
- replica I/O/SQL thread 지연
- 긴 트랜잭션 블로킹

### 2. read-after-write 전략

대표적인 전략:

- write 후 일정 시간 primary 읽기
- 세션 sticky
- version token 기반 재조회
- 중요 경로만 강한 일관성 유지

### 3. 언제 replica를 믿을 수 없는가

- 결제 직후 조회
- 상태 전이 직후 화면
- 멱등성 키 검증 직후

## 실전 시나리오

### 시나리오 1: 주문 성공 직후 주문 목록에 없다

replica lag가 원인일 수 있다.  
이 경우 주문 생성 직후는 primary, 그 후는 replica로 분기한다.

### 시나리오 2: 관리자 페이지에서 상태 변경이 늦게 보인다

관리 화면은 보통 강한 일관성이 더 중요하다.

## 코드로 보기

```text
write path -> primary
read path -> replica

하지만 최근 write가 있었으면:
  -> primary fallback
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| replica read | 확장성 좋음 | lag 문제 | 조회 위주 |
| primary read on recent write | 일관성 높음 | 라우팅 복잡 | 주문/결제 |
| session stickiness | 구현 단순 | 분산 부하 감소 | 사용자 단위 일관성 |
| version-based routing | 정교함 | 저장/판정 비용 | 대규모 서비스 |

## 꼬리질문

> Q: replica를 썼는데 왜 최신 데이터가 안 보이는가?
> 의도: 복제 지연 이해 여부 확인
> 핵심: 읽기 확장은 일관성 비용을 가져온다.

> Q: read-after-write를 보장하려면 어떤 전략이 현실적인가?
> 의도: 운영 가능한 일관성 설계 이해 여부 확인
> 핵심: primary fallback, sticky session, version routing.

## 한 줄 정리

replica lag는 읽기 확장과 즉시 일관성의 trade-off이며, read-after-write가 중요한 경로는 라우팅을 따로 설계해야 한다.
