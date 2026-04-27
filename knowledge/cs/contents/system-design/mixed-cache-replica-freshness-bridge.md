# Mixed Cache+Replica Freshness Bridge

> 한 줄 요약: `recent-write`, `min-version`, `causal token`은 cache 앞에 왔다고 사라지면 안 되고, cache hit 판단, cache miss 뒤 source 선택, refill 허용 조건까지 같은 freshness context로 이어져야 한다.

retrieval-anchor-keywords: mixed cache replica freshness bridge, cache hit miss refill consistency, cache hit reject reason, replica fallback reason, refill no-fill reason, recent-write min-version causal token, beginner mixed freshness, why stale after cache miss, why fallback reason is not enough, fallback headroom green red, recent-write recent_write mapping, min-version min_version mapping, mixed cache replica freshness bridge basics, mixed cache replica freshness bridge beginner, mixed cache replica freshness bridge intro

**난이도: 🟢 Beginner**

관련 문서:

- [Cache Hit/Miss Session Policy Bridge](./cache-hit-miss-session-policy-bridge.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Pagination Monotonicity Primer](./pagination-monotonicity-primer.md)
- [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
- [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)

---

## 핵심 개념

이 주제에서 초보자가 가장 많이 놓치는 점은 하나다.

> freshness 힌트는 "DB 읽기 전에만 쓰는 옵션"이 아니라, 요청이 끝날 때까지 들고 다니는 **문맥**이다.

즉, 아래 세 힌트는 어느 한 갈래에서만 쓰면 안 된다.

- `recent-write`: 방금 쓴 값이 바로 사라지지 않게 하는 힌트
- `min-version`: 내가 이미 본 최신선보다 뒤로 가지 않게 하는 힌트
- `causal token`: 먼저 본 결과의 원인도 같이 보이게 하는 힌트

`recent-write`와 `min-version`만 먼저 좁혀서 hit accept, miss fallback, refill write-back에 연결해 보고 싶다면 [Cache Hit/Miss Session Policy Bridge](./cache-hit-miss-session-policy-bridge.md)가 더 짧은 entrypoint다.

용어 먼저:
[recent-write](./cross-primer-glossary-anchors.md#term-recent-write), [min-version floor](./cross-primer-glossary-anchors.md#term-min-version-floor), [stale window](./cross-primer-glossary-anchors.md#term-stale-window), [headroom](./cross-primer-glossary-anchors.md#term-headroom)을 먼저 보고 오면 이 문서의 hit/miss/refill 판단이 더 빨리 읽힌다.

cache가 앞에 붙는 순간 흔히 생기는 버그는 이렇다.

- cache hit이면 힌트를 검사하지 않는다
- cache miss가 나면 힌트를 잊고 replica로 바로 간다
- replica 값을 refill할 때도 힌트를 안 본다

그래서 "hit일 때는 최신, miss일 때는 stale" 같은 이상한 현상이 생긴다.

---

## 먼저 그림으로 보기

```text
Request + freshness context
  - recent_write_until?
  - min_version(key)?
  - causal_token / required_watermark?

          |
          v
      cache lookup
          |
   +------+------+
   |             |
hit and        hit but
satisfies ctx  fails ctx
   |             |
 return        treat as miss
                 |
                 v
           source selection
       replica can satisfy ctx?
           |             |
          yes            no
           |             |
       read replica   read primary
           |             |
           +------v------+
                  |
          safe refill check
      value satisfies ctx/policy?
           |             |
          yes            no-fill
           |
      cache write with
      version/watermark metadata
```

핵심은 간단하다.

- cache hit도 `accept/reject` 판단이 필요하다
- cache miss도 같은 힌트로 source를 골라야 한다
- refill도 "아무 값이나 다시 cache에 넣는 단계"가 아니다

특히 refill은 "값 저장"만이 아니라 다음 hit 검사를 위한 metadata persistence 단계이기도 하다. 이 부분만 따로 beginner 관점으로 잇는 문서는 [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)다.

---

## 세 힌트는 무엇을 비교하나

| 힌트 | 막고 싶은 실패 | cache hit에서 보는 것 | miss 뒤 source 선택에서 보는 것 | 다음 hop으로 넘길 것 |
|---|---|---|---|---|
| `recent-write` | write 직후 옛값 재등장 | cache entry가 방금 write 이후라는 증거가 있나? 증거가 없으면 hit를 버림 | 최근 write 구간이면 primary, same-leader read, 또는 안전한 follower로 pinning | `recent_write_until`, entity-specific recent-write flag |
| `min-version` | 이미 본 값보다 뒤로 감 | `entry.version >= ctx.minVersion(key)` | replica가 그 version 이상을 볼 수 있나 | 더 높은 version을 보면 `min-version`도 올려서 전달 |
| `causal token` | 결과는 봤는데 원인이 안 보임 | `entry.watermark >= ctx.requiredWatermark()` | region/replica watermark가 token을 만족하나 | link/header/message metadata의 `causal_token` |

여기서 특히 중요한 점:

- `recent-write`는 종종 "숫자 비교"보다 **안전 경로를 강제하는 신호**로 쓰인다
- `min-version`은 cache와 replica 둘 다 검사할 수 있는 가장 단순한 기준선이다
- `causal token`은 entity version보다 넓은 dependency를 들고 다닐 때 유용하다

### 초보자용 용어 맞춤표: 개념 이름과 reason enum은 다르게 생길 수 있다

mental model 문서에서는 사람이 읽기 쉬운 용어를 먼저 쓴다.
하지만 로그나 메트릭의 `fallback_reason`은 보통 `snake_case` enum으로 남긴다.

| mental model에서 읽는 말 | `fallback_reason`/로그 필드에서 쓰는 값 | 초보자용 한 줄 |
|---|---|---|
| `recent-write` | `recent_write` | 방금 쓴 직후라 replica 대신 더 안전한 경로를 택했다 |
| `min-version` | `min_version` | replica가 내가 이미 본 기준선보다 아직 뒤에 있다 |
| `causal token` / required watermark | `watermark` | 결과의 원인까지 같이 보여 줄 만큼 replica watermark가 따라오지 못했다 |

외우는 법은 간단하다.

## 세 힌트는 무엇을 비교하나 (계속 2)

- 문서 설명에서는 `recent-write`, `min-version`, `causal token`처럼 읽기 쉬운 말을 쓴다.
- 로그/메트릭 값은 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)와 맞춰 `recent_write`, `min_version`, `watermark`로 고정한다.
- 초보자에게는 "용어가 두 개"보다 "설명용 이름 + 기록용 enum"으로 보는 편이 덜 헷갈린다.

---

## Hit, Miss, Refill에서 무엇이 달라지나

| 단계 | 초보자가 흔히 하는 실수 | 올바른 질문 | 만족 못 하면 |
|---|---|---|---|
| cache hit | hit면 곧 정답이라고 본다 | "이 cache entry가 지금 요청의 freshness contract를 만족하나?" | hit를 버리고 miss 경로로 내려간다 |
| cache miss | miss니까 fresh DB read라고 본다 | "이 요청 문맥으로 replica를 읽어도 되나?" | primary fallback 또는 안전한 follower 선택 |
| cache refill | 읽은 값을 무조건 다시 cache에 넣는다 | "이 값이 다음 요청에게도 안전한 cache material인가?" | no-fill 하거나 짧은 TTL/metadata와 함께 저장 |

한 줄로 줄이면 이렇다.

- hit 단계는 **accept rule**
- miss 단계는 **routing rule**
- refill 단계는 **write-back rule**

세 단계 모두 같은 freshness context를 써야 한다.

---

## 주문 결제 흐름으로 보기

주문 `#123`의 결제가 끝났다고 하자.

```text
POST /orders/123/pay -> primary commit success

session/request context
- recent_write_until(order:123) = now + 3s
- min_version(order:123) = 42
- causal_token = order_paid@9001
```

이제 같은 사용자가 바로 주문 화면으로 간다.

### 1. cache hit가 나도 그냥 쓰면 안 된다

cache entry가 아래 metadata를 들고 있다고 하자.

```text
cache entry
- version = 40
- watermark = 8990
```

이 hit는 빨라 보여도 현재 문맥을 만족하지 못한다.

- `min-version 42`보다 낮다
- `causal token 9001`도 못 맞춘다

따라서 이 hit는 **성공한 hit가 아니라 rejected hit**다.

### 2. cache miss처럼 내려간 뒤에도 같은 힌트를 써야 한다

이제 replica를 볼지 primary를 볼지 결정한다.

```text
replica visible version = 41
replica visible watermark = 8998
```

여기도 아직 부족하다.

- `min-version 42`를 못 맞춘다
- `causal token 9001`도 못 맞춘다

그러면 primary fallback으로 간다.

### 3. refill도 검증 후에만 한다

primary가 아래 값을 돌려줬다고 하자.

```text
primary value
- version = 42
- watermark = 9001
- status = PAID
```

이 값은 현재 요청 문맥을 만족한다.
따라서 이때만 cache refill을 한다.

```text
cache.put(order:123, value, metadata={version:42, watermark:9001})
```

다음 화면이나 다음 요청은 이 metadata를 보고 cache hit를 안전하게 받아들일 수 있다.

핵심은 "POST 다음 GET" 한 번만 지키는 것이 아니다.
**그 뒤 목록, 알림 진입, 영수증 화면으로 넘어가도 같은 기준선이 이어져야 한다.**

---

## 구현을 가장 단순하게 시작하는 방법

복잡한 전역 consistency 설계 전에, beginner 단계에서는 아래 정도만 잡아도 많이 좋아진다.

### 1. 요청에 freshness context를 붙인다

```text
ctx = {
  recent_write_until,
  min_version_by_key,
  required_watermark,
}
```

### 2. cache entry에도 비교할 metadata를 남긴다

```text
cache entry = {
  value,
  version,
  updated_at or commit_lsn,
  dependency_watermark,
}
```

### 3. hit, miss, refill에서 같은 검사를 반복한다

```pseudo
function readWithFreshness(key, ctx):
  cached = cache.get(key)
  if cached != null and satisfies(cached, ctx):
    return cached.withSource("cache")

  value = chooseSourceAndRead(key, ctx)

  if not satisfies(value, ctx):
    value = primary.read(key)

  if safeToFill(value, ctx):
    cache.put(key, withMetadata(value))

  ctx.raiseFloorFrom(value)
  return value
```

`satisfies`는 보통 아래처럼 단순화할 수 있다.

```pseudo
function satisfies(obj, ctx):
  if ctx.hasRecentWrite() and not obj.provesFreshEnough():
    return false
  if ctx.minVersion(key) != null and obj.version < ctx.minVersion(key):
    return false
  if ctx.requiredWatermark() != null and obj.watermark < ctx.requiredWatermark():
    return false
  return true
```

여기서 `recent-write`는 애매하면 보수적으로 처리하는 편이 낫다.

- cache entry가 충분히 새롭다는 증거가 없으면 hit를 버린다
- replica가 충분히 따라왔다는 증거가 없으면 fallback한다

즉, `recent-write`는 "증명 못 하면 우회"가 초보자에게 가장 안전한 시작점이다.

---

## 흔한 혼동

- `cache hit면 consistency 검사는 끝난다`는 오해가 많다. hit도 contract를 못 맞추면 miss처럼 내려가야 한다.
- `cache miss면 fresh read다`도 틀리다. miss 뒤 replica가 stale일 수 있다.
- `refill은 성능 최적화 단계일 뿐`도 틀리다. stale replica 값을 refill하면 incident를 길게 끈다.
- `recent-write`만 있으면 끝난다고 생각하기 쉽다. 여러 화면을 오가면 `min-version`이 같이 필요하고, 알림이나 비동기 결과를 따라가면 `causal token`도 필요하다.
- `causal token`은 event system에서만 쓴다고 오해하기 쉽다. "결과를 먼저 봤다면 원인도 같이 보여야 하는" 화면 이동에도 유용하다.
- `fallback_reason=recent_write`를 보고 새로운 개념이라고 느끼기 쉽다. 이 문서의 `recent-write`를 로그용 enum으로 적은 같은 뜻이다.
- `fallback_reason=watermark`를 "causal token과 다른 이야기"로 읽기 쉽다. 초보자 문서에서는 개념 설명을 위해 `causal token`이라고 쓰고, observability 문서에서는 기록용 이름으로 `watermark`라고 고정한다.

---

## 같은 fallback이어도 Green/Red 해석은 다르다

이 문서는 먼저 "왜 hit를 버렸고 왜 replica 대신 primary로 갔는가"를 설명한다.
하지만 shared 카드에서 같은 `fallback_reason=min_version`이 보여도, primary headroom이 `Green`인지 `Red`인지에 따라 다음 질문은 달라진다.

| headroom 상태 | 여기서 먼저 읽을 말 | 다음 문서에서 이어 볼 말 |
|---|---|---|
| `Green` | freshness contract를 지키려고 fallback했다 | 왜 특정 route에서 reject/fallback이 덜 잡혔는지 |
| `Red` | freshness contract는 지켰지만 primary 보호가 급해졌다 | 이 fallback을 더 늘려도 primary가 버티는지 |

초보자용 한 줄: `reason이 맞다`와 `운영상 안전하다`는 같은 판단이 아니다.
그래서 `Green vs Red`가 보이는 shared 카드는 이 문서의 hit/miss/refill mental model로 먼저 읽고, 바로 다음에 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)의 headroom 카드로 넘어가면 연결이 가장 자연스럽다.

---

## 빠른 체크리스트

- request/session/context에 `recent-write`, `min-version`, `causal token`을 함께 실을 수 있는가
- cache entry에 `version`, `updated_at or LSN`, `dependency watermark`를 남기는가
- cache hit에서 reject 가능한가
- cache miss 뒤 replica 선택에도 같은 기준을 쓰는가
- refill 전에 `safe-to-fill` 검사를 하는가
- log/trace에 `selected_source`, `rejected_hit_reason`, `fallback_reason`, `cache_fill_source`를 남기는가

이 여섯 개가 있으면 beginner 단계에서 가장 흔한 "cache 앞에서 consistency 정책이 끊기는 문제"를 크게 줄일 수 있다.

hit reject, fallback reason, refill no-fill을 먼저 관측성 언어로 잡고 싶다면 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)를 보고, 더 깊게는 by-source observability, stale refill incident, cold-path failover 문제를 [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)에서 이어서 보면 된다.

---

## 한 줄 정리

mixed cache+replica 경로에서는 `recent-write`, `min-version`, `causal token`으로 hit, miss, refill을 같은 기준으로 판단하고, 운영 해석은 headroom의 `Green/Red` 구분까지 이어서 봐야 한다.
