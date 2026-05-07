---
schema_version: 3
title: Cache Acceptance Rules for Causal Reads
concept_id: system-design/cache-acceptance-rules-for-causal-reads
canonical: false
category: system-design
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- cache acceptance rules for causal reads
- cache acceptance causal reads
- causal read cache hit check
- causal token cache hit miss refill
aliases:
- cache acceptance rules for causal reads
- cache acceptance causal reads
- causal read cache hit check
- causal token cache hit miss refill
- cache hit accept rule causal token
- cache miss causal routing
- cache refill causal guard
- required watermark cache acceptance
- notification token cache check
- watermark-aware cache hit reject
- stale cache after notification click
- effect before cause cache bridge
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/token-propagation-through-bff-and-gateway.md
- contents/system-design/causal-consistency-notification-primer.md
- contents/system-design/notification-causal-token-walkthrough.md
- contents/system-design/watermark-metadata-persistence-basics.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
- contents/system-design/rejected-hit-observability-primer.md
- contents/system-design/outbox-watermark-token-primer.md
- contents/system-design/caching-vs-read-replica-primer.md
- contents/system-design/read-after-write-routing-primer.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Cache Acceptance Rules for Causal Reads 설계 핵심을 설명해줘
- cache acceptance rules for causal reads가 왜 필요한지 알려줘
- Cache Acceptance Rules for Causal Reads 실무 트레이드오프는 뭐야?
- cache acceptance rules for causal reads 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Cache Acceptance Rules for Causal Reads를 다루는 deep_dive 문서다. causal read에서 cache는 "값이 있나?"보다 "이 causal token이 요구하는 기준선을 만족하나?"를 먼저 물어야 하고, 그 질문은 hit, miss, refill 세 단계에서 같아야 한다. 검색 질의가 cache acceptance rules for causal reads, cache acceptance causal reads, causal read cache hit check, causal token cache hit miss refill처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Cache Acceptance Rules for Causal Reads

> 한 줄 요약: causal read에서 cache는 "값이 있나?"보다 "이 causal token이 요구하는 기준선을 만족하나?"를 먼저 물어야 하고, 그 질문은 hit, miss, refill 세 단계에서 같아야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Token Propagation Through BFF and Gateway](./token-propagation-through-bff-and-gateway.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [system design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: cache acceptance rules for causal reads, cache acceptance causal reads, causal read cache hit check, causal token cache hit miss refill, cache hit accept rule causal token, cache miss causal routing, cache refill causal guard, required watermark cache acceptance, notification token cache check, watermark-aware cache hit reject, stale cache after notification click, effect before cause cache bridge, beginner causal cache bridge, cache refill no-fill causal token, cache acceptance rules for causal reads basics

---

## 핵심 개념

초보자가 먼저 잡아야 할 mental model은 간단하다.

> causal token은 "이 read가 최소 어디까지 따라왔어야 하는가"를 적은 기준선이고, cache는 "값이 있나?"보다 "그 기준선을 만족하나?"를 먼저 검사해야 한다.

여기서 `acceptance`는 `LFU/LRU admission` 같은 캐시 저장 정책이 아니다.
이 문서의 acceptance는 **이번 요청의 응답으로 이 경로를 채택해도 되는가**다.

| 헷갈리는 말 | 실제 질문 | 예시 |
|---|---|---|
| cache admission policy | "이 값을 cache에 넣을 가치가 있나?" | hot key만 저장, oversized no-store |
| causal acceptance rule | "이 값을 지금 응답으로 써도 causal token을 안 깨나?" | `entry.watermark >= required_watermark` |

beginner 단계에서는 causal token을 숫자 한 개로 생각해도 충분하다.
그 숫자가 `required_watermark`든 dependency `version floor`든, 읽기 경로는 계속 같은 질문만 하면 된다.

- cache hit: 이 entry가 token 기준선 이상인가?
- cache miss 뒤 source 선택: 이 source가 token 기준선 이상을 읽게 해 주는가?
- cache refill: 지금 읽은 값을 다음 요청도 안전하게 재사용할 수 있는가?

---

## 먼저 그림으로 보기

```text
GET /orders/123
+ causal_token(required_watermark=9001)
            |
            v
       cache lookup
            |
     metadata available?
            |
      +-----+-----+
      |           |
   yes and      no / too old /
   satisfies    missing proof
      |           |
 return cache   treat as miss
                  |
                  v
           choose read source
    replica visible watermark >= 9001?
           |                  |
          yes                 no
           |                  |
      read replica       read primary
           |                  |
           +--------v---------+
                    |
           refill candidate check
        response metadata >= 9001?
             |               |
            yes              no
             |               |
        cache write        no-fill
```

핵심은 "causal token을 request에 실었다"에서 끝나지 않는다는 점이다.
그 token은 **hit accept**, **miss routing**, **refill write-back**까지 계속 살아 있어야 한다.
그리고 refill 단계가 실제로 의미를 가지려면, 그때 저장한 watermark metadata가 다음 hit에도 남아 있어야 한다. 이 persistence 자체를 따로 설명한 문서는 [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)다.
그리고 그 전제 조건은 gateway/BFF hop에서 token이 request context로 살아남는 것이다. 전달 경계에서 어디가 자주 끊기는지는 [Token Propagation Through BFF and Gateway](./token-propagation-through-bff-and-gateway.md)에서 따로 정리한다.

---

## 세 단계 체크표

| 단계 | 무엇을 비교하나 | accept 기준 | 못 맞추면 |
|---|---|---|---|
| cache hit | `entry.watermark` 또는 `entry.version floor` vs token | entry metadata가 token 기준선 이상 | hit를 버리고 miss 경로로 내려감 |
| miss 뒤 source 선택 | `replica.visible_watermark` vs token | replica가 token 기준선 이상을 읽을 수 있음 | primary나 더 안전한 follower로 fallback |
| cache refill | `response.metadata` vs token | 방금 읽은 값이 token 기준선을 만족하고 다음 hit 검증용 metadata도 있음 | 응답은 하되 cache에는 no-fill |

짧게 외우면 이렇다.

- hit는 **accept or reject**
- miss는 **route or fallback**
- refill은 **write back or no-fill**

세 단계가 각자 다른 규칙을 가지면 안 되고, 같은 causal token을 같은 helper로 검사하는 편이 가장 안전하다.

---

## 주문 결제 알림 예시

사용자가 `결제 완료` 알림을 눌러 주문 상세로 들어간다고 하자.

```text
causal_token.required_watermark = 9001
```

### 1. Cache hit

cache entry metadata가 아래처럼 남아 있다.

```text
entry.version = 41
entry.watermark = 8997
```

이 값은 빨리 나왔지만 아직 `9001`에 못 미친다.
따라서 이 hit는 **성공한 hit가 아니라 rejected hit**다.

### 2. Miss 뒤 source 선택

replica가 현재 보여 줄 수 있는 진행도가 아래라고 하자.

```text
replica.visible_watermark = 8999
```

replica도 아직 `9001`을 못 맞춘다.
따라서 이 miss 경로는 replica read가 아니라 primary fallback으로 가야 한다.

### 3. Refill

primary가 아래 응답을 돌려준다.

```text
response.status = PAID
response.version = 42
response.watermark = 9001
```

이제야 causal 기준선을 만족한다.
이 경우에만 아래처럼 refill한다.

```text
cache.put(order:123, response, metadata={version:42, watermark:9001})
```

반대로 replica가 돌려준 값이 `8999`였는데도 refill해 버리면, 순간적인 lag가 다음 요청에서 **지속적인 stale cache**로 바뀐다.
그래서 refill check는 선택 사항이 아니라 causal read의 마지막 gate다.

---

## 구현을 가장 작게 시작하는 법

복잡한 multi-region 설계 전에도 아래 4가지는 바로 적용할 수 있다.

1. 요청에 causal token을 실어 보낸다.
2. cache entry에 `watermark`나 `version` 같은 비교 가능한 metadata를 남긴다.
3. replica 쪽도 `visible_watermark` 같은 최소 진행도를 알려 준다.
4. hit, miss, refill에서 같은 `satisfies(token, metadata)` helper를 쓴다.

아주 단순한 pseudo code는 이 정도다.

```pseudo
function satisfies(meta, token):
  return meta != null and meta.watermark >= token.requiredWatermark

function readCausally(key, token):
  entry = cache.get(key)
  if entry != null and satisfies(entry.meta, token):
    return entry.value

  if replica.visibleWatermark(key) >= token.requiredWatermark:
    value = replica.read(key)
  else:
    value = primary.read(key)

  if satisfies(value.meta, token):
    cache.put(key, value, value.meta)

  return value
```

여기서 중요한 건 복잡한 fallback 분기보다도 **같은 기준선을 세 번 반복해서 검사한다**는 점이다.

---

## 흔한 혼동

- `TTL이 안 지났으니 hit를 써도 된다`는 착각이 흔하다. TTL은 만료 규칙이지 causal proof가 아니다.
- `cache miss면 어차피 DB read니까 fresh하다`고 생각하면 안 된다. miss 뒤 replica가 lagging이면 그대로 stale일 수 있다.
- `rejected hit`를 cache 장애로 오해하면 안 된다. 값은 있었지만 이번 요청 contract에 안 맞았을 뿐이다.
- `refill은 읽은 값을 다시 넣는 기계적 단계`가 아니다. stale 값을 오래 보존하지 않기 위한 마지막 판단 단계다.
- `causal token`을 인증 토큰처럼 이해하면 안 된다. 여기서 token은 권한이 아니라 freshness dependency를 싣는 힌트다.
- 응답 metadata를 저장하지 않으면 다음 요청은 hit를 검증할 수 없다. causal token 검사 코드는 있어도 entry metadata가 없으면 결국 miss 처리만 늘어난다.

---

## 더 깊이 가려면

- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)

---

## 한 줄 정리

causal read에서 cache acceptance rule은 "캐시에 값이 있으면 쓰자"가 아니라 "이 값과 경로가 causal token의 기준선을 증명하면 쓰자"이고, 그 검사는 hit, miss, refill 세 단계에서 끊기지 않아야 한다.
