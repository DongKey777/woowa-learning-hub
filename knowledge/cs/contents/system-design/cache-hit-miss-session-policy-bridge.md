---
schema_version: 3
title: Cache Hit/Miss Session Policy Bridge
concept_id: system-design/cache-hit-miss-session-policy-bridge
canonical: false
category: system-design
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- recent-write-hint-propagation
- cache-refill-safety
- min-version-fallback
aliases:
- cache hit miss session policy bridge
- recent-write min-version cache bridge
- recent write min version hit miss refill
- cache hit accept miss fallback refill write-back
- session policy through cache
- session hint survives cache hit
- session hint survives cache miss
- cache refill session policy
- beginner cache freshness bridge
- recent-write cache accept rule
- min-version cache accept rule
- recent-write primary fallback
- min-version replica fallback
- cache hit reject recent write
- cache refill no-fill beginner
symptoms:
- 방금 저장한 뒤에는 cache hit도 못 믿어야 하는지 헷갈려
- cache miss면 fresh read라고 생각했는데 아닌 것 같아
- min-version을 어디에서 검사해야 할지 모르겠어
intents:
- comparison
prerequisites:
- system-design/read-after-write-consistency-basics
- system-design/monotonic-reads-and-session-guarantees-primer
- system-design/caching-vs-read-replica-primer
next_docs:
- system-design/session-policy-implementation-sketches
- system-design/mixed-cache-replica-freshness-bridge
- system-design/mixed-cache-replica-read-path-pitfalls
linked_paths:
- contents/system-design/session-policy-implementation-sketches.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
- contents/system-design/cache-acceptance-rules-for-causal-reads.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/list-detail-monotonicity-bridge.md
- contents/system-design/read-after-write-consistency-basics.md
- contents/system-design/monotonic-reads-and-session-guarantees-primer.md
- contents/system-design/mixed-cache-replica-read-path-pitfalls.md
confusable_with:
- system-design/read-after-write-routing-primer
- system-design/mixed-cache-replica-freshness-bridge
- system-design/cache-acceptance-rules-for-causal-reads
forbidden_neighbors:
- contents/system-design/read-after-write-routing-primer.md
expected_queries:
- recent-write 힌트를 cache hit, miss, refill 전부에 어떻게 이어 붙여?
- min-version이 있으면 cache entry를 버리는 기준을 어디에 둬야 해?
- cache miss 뒤 replica 결과를 다시 cache에 넣어도 되는지 판단하는 법
- session policy가 cache 앞단에서만 쓰이는 옵션이 아니라는 뜻을 예시로 설명해줘
- 저장 직후 상세 조회에서 hit reject, primary fallback, no-fill이 왜 한 세트야?
- cache freshness 정책과 read routing 정책을 하나로 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 학습자가 recent-write와 min-version을 read routing 앞단 옵션이
  아니라 cache hit accept, miss fallback, refill write-back까지 이어지는
  하나의 session policy로 이해하게 돕는 beginner bridge다. 저장 직후
  cache hit를 왜 버릴 수 있는지, cache miss가 왜 fresh read와 같지
  않은지, replica 결과를 언제 no-fill 해야 하는지, hit reject와 primary
  fallback을 왜 같은 기준선으로 설명해야 하는지 같은 자연어 질문이 본
  문서의 연결 고리에 매핑된다.
---
# Cache Hit/Miss Session Policy Bridge

> 한 줄 요약: `recent-write`와 `min-version`은 request 입구에서만 읽고 버리는 힌트가 아니라, cache hit accept, miss fallback, refill write-back까지 같은 기준선으로 살아남아야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [system design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: cache hit miss session policy bridge, recent-write min-version cache bridge, recent write min version hit miss refill, cache hit accept miss fallback refill write-back, session policy through cache, session hint survives cache hit, session hint survives cache miss, cache refill session policy, beginner cache freshness bridge, recent-write cache accept rule, min-version cache accept rule, recent-write primary fallback, min-version replica fallback, cache hit reject recent write, cache refill no-fill beginner

---

## 핵심 개념

가장 먼저 잡아야 할 mental model은 이것이다.

> session policy는 "read 전에 잠깐 참고하는 옵션"이 아니라, 요청이 끝날 때까지 들고 가는 작은 힌트 봉투다.

이 봉투 안에서 beginner가 먼저 볼 두 가지는 아래다.

| 힌트 | 막고 싶은 문제 | 가장 쉬운 질문 |
|---|---|---|
| `recent-write` | 방금 저장했는데 바로 옛값이 다시 보임 | "지금은 더 안전한 read path로 우회해야 하나?" |
| `min-version` | 방금 본 값보다 뒤로 감 | "이 후보 값이 내가 이미 본 version 아래인가?" |

핵심은 힌트가 세 군데에서 모두 살아 있어야 한다는 점이다.

- cache hit: 이 hit를 받아들여도 되나
- cache miss: replica를 읽어도 되나, primary로 fallback해야 하나
- cache refill: 방금 읽은 값을 다시 cache에 넣어도 다음 요청에 안전한가

---

## 먼저 흐름으로 보기

```text
request arrives
  with session hints
  - recent_write_until(order:123)=12:00:03
  - min_version(order:123)=42

        |
        v
    cache lookup
        |
   hit acceptable?
   - recent-write window safe?
   - version >= 42 ?
        |
   +----+----+
   |         |
  yes        no
   |         |
 return    treat as miss
             |
             v
      choose read source
   replica can satisfy both hints?
        |              |
       yes             no
        |              |
   read replica   fallback primary
        |              |
        +------v-------+
               |
       refill acceptable?
       - value proves fresh enough?
       - version >= 42 ?
               |
          yes / no-fill
```

짧게 외우면:

- hit에서는 **accept or reject**
- miss에서는 **read replica or fallback**
- refill에서는 **write back or no-fill**

---

## 힌트가 단계마다 어떻게 살아남는가

| 단계 | `recent-write`가 하는 일 | `min-version`이 하는 일 | 실패 시 행동 |
|---|---|---|---|
| cache hit accept | 방금 write 직후라 freshness 증거가 약하면 hit를 버린다 | `entry.version >= minVersion`인지 본다 | reject hit, miss 경로로 내려감 |
| miss fallback | recent-write 구간이면 primary나 더 안전한 source로 bias를 건다 | replica가 floor 이상을 읽을 수 있는지 본다 | primary fallback |
| refill write-back | 읽은 값이 recent-write 구간에서도 안전한지 본다 | 응답 version이 floor 이상인지 확인한다 | no-fill 또는 짧은 TTL |

여기서 중요한 점은 규칙 이름이 달라도 질문은 같다는 것이다.

- "이 값이 지금 요청 기준선을 만족하나?"
- "만족 못 하면 더 안전한 경로로 갈까?"

---

## 주문 상태 예시

사용자가 주문 결제를 끝내고 바로 주문 상세를 다시 연다고 하자.

```text
session hints
- recent_write_until(order:123) = now + 3s
- min_version(order:123) = 42
```

### 1. cache hit accept

cache entry가 아래라고 하자.

```text
entry.version = 40
entry.cached_at = 11:59:58
```

이 hit는 두 이유로 위험하다.

- `min-version 42`를 못 맞춘다
- recent-write 구간인데 entry가 write 이후 값임을 증명하지 못한다

그래서 "cache에 값이 있다"와 "이 hit를 써도 된다"는 다른 말이다.

### 2. miss fallback

이제 replica 상태가 아래라고 하자.

```text
replica.visible_version(order:123) = 41
```

replica도 아직 `42`를 못 맞춘다.
그리고 recent-write 구간이라 더 보수적으로 가야 한다.
따라서 primary fallback이 맞다.

### 3. refill write-back

primary가 아래 응답을 돌려준다.

```text
response.version = 42
response.status = PAID
```

이제는 두 힌트를 모두 만족한다.
이때만 아래처럼 refill한다.

```text
cache.put(order:123, response, metadata={version:42})
```

반대로 replica가 `41`을 읽은 직후 그 값을 refill하면, 잠깐의 replica lag가 다음 요청의 stale cache로 길게 남는다.

---

## 가장 단순한 구현 스케치

```pseudo
function canAccept(entry, hints, key):
  if entry == null:
    return false
  if hints.hasRecentWrite(key) and not entry.provesFreshEnough():
    return false
  if entry.version < hints.minVersion(key):
    return false
  return true

function readWithSessionPolicy(key, hints):
  entry = cache.get(key)
  if canAccept(entry, hints, key):
    return entry.value

  if hints.hasRecentWrite(key):
    value = primary.read(key)
  else:
    value = replica.read(key)
    if value.version < hints.minVersion(key):
      value = primary.read(key)

  if canAccept(value, hints, key):
    cache.put(key, withMetadata(value))

  hints.raiseMinVersion(key, value.version)
  return value
```

초보자에게 중요한 포인트는 복잡한 최적화가 아니다.
같은 힌트를 hit, miss, refill에서 반복해서 쓴다는 점이다.

---

## 흔한 혼동

- `recent-write`는 hit 단계에서는 안 보고 miss routing에서만 본다고 생각하기 쉽다. 하지만 write 직후 stale cache hit도 막아야 한다.
- `min-version`은 목록/상세 이동에서만 쓴다고 생각하기 쉽다. cache entry accept에도 바로 쓸 수 있다.
- `cache miss면 DB read니까 fresh하다`는 오해가 많다. miss 뒤 replica는 여전히 stale일 수 있다.
- `refill은 성능용이니 일단 넣고 보자`는 접근이 위험하다. unsafe refill이 stale window를 늘린다.

---

## 한 줄 정리

`recent-write`와 `min-version`은 cache 앞에서 사라지는 힌트가 아니라, hit를 거절할지, miss를 어디로 보낼지, refill을 허용할지까지 같은 session policy로 이어져야 하는 기준선이다.
