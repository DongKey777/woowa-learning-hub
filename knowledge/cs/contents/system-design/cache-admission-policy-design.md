---
schema_version: 3
title: Cache Admission Policy 설계
concept_id: system-design/cache-admission-policy-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- cache admission
- cache warming
- hotset
- LFU
aliases:
- cache admission
- cache warming
- hotset
- LFU
- TinyLFU
- negative caching
- eviction policy
- recency
- frequency
- cache pollution
- Cache Admission Policy 설계
- cache admission policy design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/distributed-cache-design.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/search-system-design.md
- contents/system-design/document-search-ranking-platform-design.md
- contents/system-design/tenant-aware-search-architecture-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/feature-flag-control-plane-design.md
- contents/system-design/edge-authorization-service-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Cache Admission Policy 설계 설계 핵심을 설명해줘
- cache admission가 왜 필요한지 알려줘
- Cache Admission Policy 설계 실무 트레이드오프는 뭐야?
- cache admission 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Cache Admission Policy 설계를 다루는 deep_dive 문서다. cache admission policy는 무엇을 캐시에 넣을지 결정해 핫셋을 지키고, 무의미한 항목이 캐시를 오염시키지 못하게 하는 설계다. 검색 질의가 cache admission, cache warming, hotset, LFU처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Cache Admission Policy 설계

> 한 줄 요약: cache admission policy는 무엇을 캐시에 넣을지 결정해 핫셋을 지키고, 무의미한 항목이 캐시를 오염시키지 못하게 하는 설계다.

retrieval-anchor-keywords: cache admission, cache warming, hotset, LFU, TinyLFU, negative caching, eviction policy, recency, frequency, cache pollution

**난이도: 🔴 Advanced**

> 관련 문서:
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Search 시스템 설계](./search-system-design.md)
> - [Document Search / Ranking Platform 설계](./document-search-ranking-platform-design.md)
> - [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)

## 핵심 개념

캐시는 넣는 것보다 "무엇을 안 넣을지"가 더 중요하다.  
실전에서는 다음을 함께 다뤄야 한다.

- 자주 쓰는 항목만 넣는다
- 너무 큰 항목은 제외한다
- ephemeral noise를 걸러낸다
- 핫셋을 보호한다
- eviction과 admission을 분리한다

즉, admission policy는 캐시 오염을 막는 첫 방어선이다.

## 깊이 들어가기

### 1. admission과 eviction은 다르다

- admission: 캐시에 들어올 자격을 판단
- eviction: 이미 들어온 항목을 내보냄

이 둘을 분리해야 정책이 선명해진다.

### 2. Capacity Estimation

예:

- 캐시 100GB
- key 수가 수억 개
- 대부분은 한 번만 조회

그럼 모든 요청을 캐시에 넣는 것은 낭비다.  
핫셋과 long tail을 분리해야 한다.

봐야 할 숫자:

- key frequency
- object size
- hit ratio
- miss penalty
- admission reject rate

### 3. 정책 후보

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| LRU | 단순하다 | scan-heavy workload에 약하다 | 일반적인 캐시 |
| LFU | 자주 쓰는 항목을 지킨다 | 구현이 복잡해질 수 있다 | 핫셋 보호 |
| TinyLFU | admission에 강하다 | 설계가 복잡하다 | 대규모 캐시 |
| Size-aware admission | 큰 객체를 제어한다 | 튜닝이 필요하다 | 객체 크기 편차가 클 때 |
| Negative cache | 없는 값을 짧게 기억한다 | stale negative 가능성 | lookup-heavy service |

### 4. admission decision

새 항목을 넣기 전에 묻는 질문:

- 최근에 몇 번이나 봤는가
- 크기가 큰가
- 이 key가 hot path에 속하는가
- miss penalty가 큰가

### 5. warmup

정책이 없으면 cold start가 크게 보인다.

- 배포 직후 프리워밍
- 인기 key 사전 적재
- TTL jitter와 함께 만료 분산

이 부분은 [Distributed Cache 설계](./distributed-cache-design.md)와 [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)와 연결된다.

### 6. negative caching

없는 값도 잠깐 기억할 수 있다.

- 없는 문서
- 없는 사용자
- 없는 토큰

단, 너무 오래 기억하면 새로 생긴 데이터가 보이지 않는 문제가 생긴다.

### 7. tenant / policy aware admission

모든 key를 똑같이 보면 안 된다.

- tenant별 quota
- search result cache
- session cache
- authz snapshot cache

이 부분은 [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md), [Edge Authorization Service 설계](./edge-authorization-service-design.md), [Session Store Design at Scale](./session-store-design-at-scale.md)와 같이 보면 좋다.

## 실전 시나리오

### 시나리오 1: 바이럴 상품

문제:

- 한 상품이 갑자기 폭발적으로 조회된다

해결:

- frequency-aware admission
- pre-warm
- TTL 관리

### 시나리오 2: 검색 결과 캐시

문제:

- 긴 꼬리 query가 캐시를 오염시킨다

해결:

- top query만 admit
- negative cache 짧게 유지

### 시나리오 3: 세션/권한 스냅샷

문제:

- 모든 세션 스냅샷을 넣으면 메모리가 부족하다

해결:

- session hotset 우선
- policy snapshot versioning

## 코드로 보기

```pseudo
function admit(key, stats):
  if stats.frequency < threshold:
    return false
  if stats.size > maxSize and not highValue(key):
    return false
  return true

function get(key):
  value = cache.lookup(key)
  if value != null:
    return value
  value = loadSource()
  if admit(key, observe(key)):
    cache.put(key, value)
  return value
```

```java
public boolean shouldAdmit(CacheEntry entry) {
    return admissionPolicy.admit(entry.key(), entry.frequency(), entry.size());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Blind cache-aside | 쉽다 | cache pollution 위험 | 작은 서비스 |
| Frequency-aware admission | 핫셋을 지킨다 | 튜닝이 필요하다 | 실서비스 |
| Size-aware admission | 큰 객체를 제어 | 계산이 복잡 | 편차가 큰 데이터 |
| Negative caching | miss 폭주를 줄인다 | stale negative 위험 | lookup-heavy |
| Warmup-heavy | cold start가 적다 | 운영이 늘어난다 | 대형 배포 |

핵심은 cache admission policy가 eviction보다 앞에 있는 **캐시 오염 방지 장치**라는 점이다.

## 꼬리질문

> Q: admission과 eviction의 차이는 무엇인가요?
> 의도: 넣을지 말지와 빼는지의 차이를 아는지 확인
> 핵심: admission은 신규 유입 제어, eviction은 내부 정리다.

> Q: 왜 frequency를 보나요?
> 의도: hotset과 long tail 분리를 이해하는지 확인
> 핵심: 자주 쓰는 항목을 지키기 위해서다.

> Q: negative cache는 언제 쓰나요?
> 의도: lookup-heavy workload 감각 확인
> 핵심: 없는 값을 반복 조회할 때 miss 폭주를 막는다.

> Q: warmup은 왜 필요한가요?
> 의도: cold start와 preloading 이해 확인
> 핵심: 배포 직후 캐시 미스를 줄이기 위해서다.

## 한 줄 정리

Cache admission policy는 캐시에 들어오는 항목을 걸러 핫셋을 보호하고, 캐시 오염과 cold start를 줄이는 운영 장치다.

