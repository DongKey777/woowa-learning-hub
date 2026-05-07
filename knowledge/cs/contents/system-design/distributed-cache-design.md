---
schema_version: 3
title: 분산 캐시 설계
concept_id: system-design/distributed-cache-design
canonical: true
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- distributed-cache-consistency
- hot-key-cache-stampede
- cache-capacity-failure-planning
aliases:
- distributed cache design
- 분산 캐시 설계
- cache-aside write-through write-behind
- hot key cache
- TTL jitter single-flight
- consistent hashing cache
- cache rebalancing
- local cache vs distributed cache
symptoms:
- 분산 캐시를 단일 메모리 캐시를 여러 대로 늘린 것 정도로 이해하고 있어
- cache-aside, write-through, write-behind를 쓰기/읽기 책임 기준으로 구분하지 못하고 있어
- hot key, stampede, rebalancing, eviction이 DB 보호와 어떻게 연결되는지 헷갈려
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- system-design/cache-invalidation-patterns-primer
- system-design/back-of-envelope-estimation
- system-design/caching-vs-read-replica-primer
next_docs:
- system-design/cache-admission-policy-design
- system-design/shard-rebalancing-partition-relocation-design
- system-design/cell-based-architecture-blast-radius-isolation-design
- system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design
linked_paths:
- contents/system-design/cache-invalidation-patterns-primer.md
- contents/system-design/system-design-framework.md
- contents/system-design/caching-vs-read-replica-primer.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/rate-limiter-design.md
- contents/database/index-and-explain.md
- contents/database/mvcc-replication-sharding.md
- contents/network/cache-control-practical.md
- contents/system-design/shard-rebalancing-partition-relocation-design.md
- contents/system-design/cell-based-architecture-blast-radius-isolation-design.md
- contents/system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design.md
confusable_with:
- system-design/cache-invalidation-patterns-primer
- system-design/caching-vs-read-replica-primer
- system-design/cdn-basics
- database/mvcc-replication-sharding
forbidden_neighbors: []
expected_queries:
- 분산 캐시는 local cache나 CDN cache와 무엇이 달라?
- cache-aside, write-through, write-behind는 어떤 읽기 쓰기 tradeoff가 있어?
- hot key와 cache stampede는 분산 캐시 설계에서 어떻게 막아?
- consistent hashing만으로 cache rebalancing 문제가 끝나지 않는 이유는 뭐야?
- 캐시 장애가 DB 장애로 번지지 않게 어떤 보호 장치를 둬야 해?
contextual_chunk_prefix: |
  이 문서는 distributed cache design deep dive로, shared cache cluster, cache-aside/write-through/write-behind, consistent hashing, hot key, stampede, eviction, fallback, cache miss metrics를 다룬다.
  분산 캐시 설계, local cache vs distributed cache, cache stampede, TTL jitter, single-flight, cache rebalancing 같은 자연어 질문이 본 문서에 매핑된다.
---
# 분산 캐시 설계

> 한 줄 요약: 단일 메모리 캐시를 넘어, 여러 노드에 캐시를 나누고 일관성과 성능을 동시에 관리하는 설계다.

retrieval-anchor-keywords: distributed cache, cache-aside, write-through, write-behind, cache invalidation, hot key, stampede, admission policy, TTL jitter, local cache, distributed cache, cache rebalancing, shard relocation, cell isolation, cache prefill, receiver warmup

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [인덱스와 실행 계획](../database/index-and-explain.md)
> - [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)
> - [Cache-Control 실전](../network/cache-control-practical.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)

---

처음 배우는 단계라면 `cache invalidation`, `TTL`, `write-through`, `delete-on-write`의 큰 그림을 먼저 [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)에서 잡고 다시 내려오는 편이 안전하다.

## 핵심 개념

분산 캐시는 "메모리 캐시를 여러 대로 늘린 것"이 아니다.  
실제로는 다음 문제를 동시에 풀어야 한다.

- 읽기 지연을 줄인다.
- 캐시 노드를 늘려 수평 확장을 한다.
- 캐시와 원본 데이터 사이의 일관성을 관리한다.
- hot key와 stampede를 막는다.
- 장애가 나도 전체 시스템이 무너지지 않게 한다.

분산 캐시를 설계할 때 가장 먼저 묻는 질문은 "무엇을 캐시할 것인가"가 아니라, **어떤 읽기 패턴을 숨기고 어떤 쓰기 비용을 감당할 것인가**다.

실무에서는 캐시가 단순 데이터 저장소가 아니라, 다음의 "빠른 스냅샷" 역할도 한다.

- feature flag snapshot
- config snapshot
- authz policy snapshot
- rate limit quota snapshot
- search ranking warm cache
- session lookup cache

이 관점은 [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md), [Config Distribution System 설계](./config-distribution-system-design.md), [Edge Authorization Service 설계](./edge-authorization-service-design.md), [Rate Limit Config Service 설계](./rate-limit-config-service-design.md), [Session Store Design at Scale](./session-store-design-at-scale.md)와 같이 보면 더 잘 보인다.

### 주 사용처

- 반복 조회가 많은 프로필/설정 데이터
- 조인 비용이 큰 읽기 경로
- DB 병목을 흡수해야 하는 상세 페이지
- 계산 결과가 비싼 파생 데이터

---

## 깊이 들어가기

### 1. 캐시 배치 방식

대표적인 배치 전략은 다음과 같다.

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Client-side cache | 가장 빠르다 | 무효화가 어렵다 | 매우 제한된 내부 도구 |
| Local cache | 네트워크 없이 빠르다 | 인스턴스 간 불일치가 생긴다 | 단일 노드 최적화 |
| Distributed cache | 여러 서버가 공유한다 | 네트워크와 일관성 비용이 있다 | 일반적인 서비스 |
| CDN/edge cache | 사용자와 가장 가깝다 | 동적 데이터 반영이 어렵다 | 정적/반정적 콘텐츠 |

실무에서는 local cache와 distributed cache를 같이 쓰는 경우가 많다.  
예를 들어 local cache로 초단기 hot path를 줄이고, distributed cache로 공통 데이터를 공유한다.

### 2. 샤딩과 일관성

캐시가 커지면 한 노드에 다 넣을 수 없다.  
보통 consistent hashing으로 key를 여러 노드에 분산한다.

핵심은 노드 수가 바뀌어도 key 이동을 최소화하는 것이다.

```text
key -> hash(key) -> ring -> nearest node
```

노드 추가/장애 시 영향 범위를 줄이지만, 다음 문제는 여전히 남는다.

- 특정 key가 너무 뜨거우면 한 노드에 몰린다.
- 노드 장애 시 cache miss가 급증한다.
- 리밸런싱이 순간적으로 DB를 두드린다.

즉, 해시 분배와 실제 shard relocation은 다른 문제다. metadata만 바꾸는 것과 상태를 warm-up하며 옮기는 것은 운영 난이도가 다르다.

### 3. 캐시 패턴

가장 자주 쓰는 패턴은 아래 셋이다.

#### Cache-aside

애플리케이션이 캐시를 먼저 보고, 없으면 DB에서 읽어 캐시에 채운다.

- 장점: 단순하고 많이 쓰인다.
- 단점: 무효화와 stampede 관리가 필요하다.

#### Write-through

쓰기 시 캐시와 DB를 같이 갱신한다.

- 장점: 읽기 일관성이 좋다.
- 단점: 쓰기 지연이 늘어난다.

#### Write-behind

캐시에 먼저 쓰고 DB는 나중에 반영한다.

- 장점: 빠르다.
- 단점: 장애 시 데이터 유실 위험이 있다.

실무에서는 대부분 cache-aside를 기본으로 두고, 중요한 경로만 write-through 혹은 별도 동기화를 고려한다.

### 4. 캐시 무효화

분산 캐시의 진짜 난제는 무효화다.

대표 전략:

- TTL로 자연 만료시킨다.
- 쓰기 시 해당 key를 삭제한다.
- 이벤트 기반으로 연관 key를 함께 갱신한다.
- 버전 키를 바꿔 새 값을 읽게 한다.

예를 들어 사용자 프로필이 바뀌면:

```text
user:123:profile
user:123:profile:v2
```

버전 키는 단순하지만, 오래된 키가 계속 남을 수 있다.  
삭제 기반 무효화는 깔끔하지만 race condition을 조심해야 한다.

### 5. Cache Stampede

많은 요청이 동시에 만료된 key를 보고 DB로 몰리는 현상이다.

대응책:

- jitter를 섞어 TTL을 분산한다.
- single-flight / request coalescing을 쓴다.
- stale-while-revalidate를 적용한다.
- hot key는 미리 warm-up한다.

캐시가 깨질 때 시스템이 버티는지 보는 것이 설계의 핵심이다.

### 6. Eviction과 용량 계획

메모리는 무한하지 않다.  
보통 다음 정책을 조합한다.

- `LRU`: 최근에 안 쓴 것을 내보낸다.
- `LFU`: 자주 안 쓴 것을 내보낸다.
- `TTL`: 오래된 것을 내보낸다.

실제 시스템에서는 key 크기와 접근 패턴이 제각각이라 하나의 정책만으로는 부족하다.  
중요한 것은 "어떤 데이터를 절대로 쫓아내면 안 되는가"를 정하는 일이다.

### 7. 실패와 복구

분산 캐시의 장애는 곧바로 DB 압박으로 이어질 수 있다.

자주 보는 시나리오:

- 캐시 전체 장애로 DB가 급격히 느려진다.
- 리밸런싱 순간에 DB로 트래픽이 몰린다.
- hot key 한 개가 특정 노드를 죽인다.
- 캐시 클러스터는 살아있지만 네트워크 지연으로 사실상 무용지물이 된다.

따라서 운영 관점에서는 다음을 준비해야 한다.

- fallback 정책
- DB 보호용 rate limit
- cache miss 메트릭
- hit ratio, eviction, latency, error rate

### 8. 캐시를 어디에 쓰고 어디에 쓰지 말아야 하나

캐시는 성능을 올리지만, 모든 문제를 해결하지는 않는다.

- 써야 하는 곳: 자주 조회되는 설정, 권한 스냅샷, 검색 결과 일부, 프로필, hot leaderboard
- 조심해야 하는 곳: 금전 상태, 강한 정합성이 필요한 결제 원장, 순서가 중요한 단일 writer state

특히 다음 경로는 캐시를 넣을 때 정책을 더 엄격히 봐야 한다.

- [Edge Authorization Service 설계](./edge-authorization-service-design.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)
- [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)

### 9. admission과 warmup

캐시가 가득 차면 그냥 LRU로만 밀어내면 중요한 key가 사라질 수 있다.

- admission policy를 둔다
- TTL jitter로 만료를 분산한다
- pre-warm로 핫셋을 미리 올린다
- negative cache로 없는 값을 짧게 기억한다

이건 특히 다음 시스템에서 중요하다.

- [Search 시스템 설계](./search-system-design.md)
- [Document Search / Ranking Platform 설계](./document-search-ranking-platform-design.md)
- [Recommendation / Feed Ranking Architecture](./recommendation-feed-ranking-architecture.md)
- [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
- [Distributed Scheduler 설계](./distributed-scheduler-design.md)

---

## 실전 시나리오

### 시나리오 1: 사용자 프로필 조회

프로필은 읽기 비중이 높고, 변경은 상대적으로 적다.

설계:

- cache-aside
- TTL 5분
- 프로필 수정 시 key 삭제
- miss 시 DB 조회 후 캐시 적재

주의점:

- 프로필 수정 직후 읽기 일관성이 중요하면 TTL만 믿으면 안 된다.
- 삭제와 재적재 사이 race를 고려해야 한다.

### 시나리오 2: 상세 페이지 hot key

특정 상품/게시글 하나가 바이럴이 되면 단일 key에 트래픽이 몰린다.

대응:

- local cache 추가
- stale 허용 범위 정의
- pre-warming
- 요청 coalescing

### 시나리오 3: 멀티 리전

리전이 나뉘면 중앙 캐시 하나로 끝나지 않는다.

결정해야 할 것:

- 리전별 캐시를 둘 것인가
- 전역 일관성을 얼마나 포기할 것인가
- miss가 다른 리전 DB를 때리지 않게 할 것인가

이 경우 캐시는 성능 도구이면서 동시에 복제 전략의 일부가 된다.

### 시나리오 4: 제어 평면 스냅샷

문제:

- flag, config, quota, authz policy를 매 요청마다 원본 저장소에서 읽으면 느리다

대응:

- snapshot cache를 쓴다
- versioned invalidation을 둔다
- critical action만 synchronous check를 유지한다

이 패턴은 [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md), [Config Distribution System 설계](./config-distribution-system-design.md), [Edge Authorization Service 설계](./edge-authorization-service-design.md), [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)에서 반복된다.

---

## 코드로 보기

### 1. cache-aside 의사코드

```pseudo
function getUserProfile(userId):
    cacheKey = "user:" + userId + ":profile"
    value = cache.get(cacheKey)
    if value != null:
        return value

    value = db.selectUserProfile(userId)
    if value != null:
        cache.set(cacheKey, value, ttl=300s)
    return value
```

### 2. stampede 방지 아이디어

```java
public Profile getProfile(long userId) {
    String key = "user:" + userId + ":profile";
    return cache.get(key, () -> {
        synchronized (lockFor(key)) {
            Profile cached = cache.peek(key);
            if (cached != null) {
                return cached;
            }
            Profile profile = repository.findProfile(userId);
            cache.put(key, profile, Duration.ofMinutes(5));
            return profile;
        }
    });
}
```

실제 구현에서는 분산 락, single-flight, request coalescing 중 하나를 선택한다.

### 3. TTL jitter

```java
Duration baseTtl = Duration.ofMinutes(5);
Duration jitter = Duration.ofSeconds(ThreadLocalRandom.current().nextInt(0, 30));
Duration ttl = baseTtl.plus(jitter);
```

TTL이 동시에 만료되는 것을 막는 간단한 장치다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Local cache | 가장 빠름 | 인스턴스 간 불일치 | 초단기 hot path |
| Distributed cache | 공유 가능 | 네트워크 비용 | 일반적인 서비스 |
| TTL 기반 무효화 | 구현이 단순 | stale 데이터 가능 | 읽기 중심, 허용 가능한 지연 |
| 이벤트 기반 무효화 | 정확도가 높다 | 운영 복잡도 증가 | 정합성이 중요한 데이터 |
| Write-through | 읽기 일관성 좋음 | 쓰기 지연 증가 | 중요한 설정/상태 |

분산 캐시는 "빨라지는 대신 복잡해지는 것"을 받아들이는 설계다.  
어떤 데이터는 캐시하면 안 되고, 어떤 데이터는 무효화 비용 때문에 캐시를 억제해야 한다.

### 실전 체크리스트

캐시를 넣기 전에 아래 질문에 답할 수 있어야 한다.

1. TTL이 얼마나 stale을 허용하는가
2. invalidation source of truth는 어디인가
3. stampede가 생기면 누가 막는가
4. hot key를 어떻게 찾고 분산하는가
5. cache miss가 downstream을 죽이지 않는가
6. multi-region에서 cache key가 충돌하지 않는가

이 체크는 [Session Store Design at Scale](./session-store-design-at-scale.md), [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md), [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md), [Knowledge Search / RAG Platform 설계](./knowledge-search-rag-platform-design.md)와 잘 연결된다.

---

## 꼬리질문

> Q: 캐시를 넣으면 왜 더 복잡해지나요?
> 의도: 성능 개선이 항상 단순화가 아님을 아는지 확인
> 핵심: 무효화, stale read, stampede, 장애 전파가 새로 생긴다

> Q: TTL만 있으면 무효화가 충분한가요?
> 의도: 캐시 일관성 모델 이해 확인
> 핵심: 허용 가능한 stale 범위가 작으면 이벤트 기반 갱신이 필요하다

> Q: hot key를 어떻게 찾나요?
> 의도: 운영 지표 감각 확인
> 핵심: key별 hit/miss, latency, per-key QPS, eviction 로그를 본다

---

## 한 줄 정리

분산 캐시는 단순 메모리 확장이 아니라, 읽기 성능과 일관성, 장애 복구, hot key 관리까지 함께 설계해야 하는 시스템이다.
