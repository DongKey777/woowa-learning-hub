# Watermark Metadata Persistence Basics

> 한 줄 요약: outbox가 만든 `required_watermark`와 projection이 만든 `applied_watermark`는 cache refill 때 entry metadata로 같이 저장해야 하고, 그래야 다음 cache hit에서 "이 값을 지금 바로 써도 되나?"를 숫자 비교 한 번으로 판단할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)
- [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)
- [system design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: watermark metadata persistence basics, cache entry watermark metadata, cache refill watermark metadata, applied watermark cache entry, required watermark cache hit check, outbox watermark to cache metadata, cache causal hit metadata, refill metadata enables later hit check, watermark aware cache refill beginner, cache metadata persistence primer, causal cache metadata design, outbox projection cache bridge, cache entry observed watermark, cache metadata scope watermark, beginner watermark cache bridge, system-design-00081

---

## 먼저 잡을 mental model

초보자는 watermark 이야기를 듣고 outbox나 projection까지만 떠올리기 쉽다.
하지만 운영에서 실제로 막히는 지점은 그다음이다.

> fresh한 값을 한 번 읽어 왔다고 끝이 아니라, 그 fresh함을 다음 cache hit도 다시 증명할 수 있게 metadata로 남겨야 한다.

즉 흐름은 이렇게 이어진다.

1. source transaction이 `required_watermark`를 만든다
2. projection/read model이 `applied_watermark`를 가진다
3. read path가 안전한 값을 읽는다
4. cache refill 때 그 값을 그냥 payload만 넣지 않고 watermark metadata도 같이 저장한다
5. 다음 요청은 cache hit에서 그 metadata를 보고 causal hit 여부를 판단한다

한 줄로 줄이면:

- outbox는 "어디까지 따라와야 하나"를 만든다
- projection은 "지금 어디까지 따라왔나"를 보여 준다
- cache metadata persistence는 "다음 hit도 그 사실을 다시 검사할 수 있게 남긴다"

## 왜 persistence가 빠지면 곧바로 약해지나

주문 상세를 primary에서 fresh하게 읽어 왔다고 하자.
응답 시점에는 `required_watermark=9001`을 만족했다.

그런데 cache에 아래처럼 값만 저장하면 문제가 남는다.

```text
cache entry
- status = PAID
- total_price = 42000
```

다음 요청에서 시스템은 이런 질문에 답하지 못한다.

- 이 값이 `9001` 이후 상태라는 증거가 cache 안에 남아 있나?
- 아니면 우연히 값이 비슷해 보일 뿐인가?

반대로 refill 때 metadata를 같이 넣으면 다음 hit 판단이 가능해진다.

```text
cache entry
- status = PAID
- total_price = 42000
- applied_watermark = 9001
- watermark_scope = orders-shard-a
```

이제 다음 요청이 `required_watermark=9001`을 들고 오면 읽기 경로는 아래 한 줄을 물을 수 있다.

- `entry.applied_watermark >= required_watermark` 인가?

즉 persistence의 목적은 "디버깅용 장식"이 아니라 **다음 cache hit 검사를 가능하게 만드는 것**이다.

## 한눈에 보기

| 단계 | 생기는 값 | 어디에 저장되나 | 다음 단계에서 왜 필요한가 |
|---|---|---|---|
| source commit | `required_watermark=9001` | event / request context | "최소 어디까지 보여야 하나?" |
| projection apply | `applied_watermark=9001` | read model row 또는 checkpoint | "이 읽기 값이 그 기준선을 만족하나?" |
| safe read 성공 | `value + applied_watermark=9001` | response metadata | "지금 응답은 왜 안전한가?" |
| cache refill | `cache.applied_watermark=9001` | cache entry metadata | "다음 hit도 안전한가?" |
| later cache hit | `entry.applied_watermark` vs `required_watermark` | cache lookup 시 비교 | "hit를 바로 채택해도 되나?" |

```text
outbox required_watermark
  -> projection applied_watermark
  -> safe read succeeds
  -> cache refill persists applied_watermark
  -> later cache hit checks required <= applied
```

## 어떤 metadata를 같이 저장하면 시작하기 쉬운가

beginner 단계에서는 "완벽한 universal metadata"보다 **나중에 비교에 꼭 필요한 최소 집합**부터 잡는 편이 낫다.

| 필드 | 가장 단순한 역할 | 왜 필요한가 |
|---|---|---|
| `applied_watermark` | 이 값이 최소 어디까지 반영했는지 | 다음 hit accept/reject 비교의 핵심 |
| `watermark_scope` | 이 숫자가 어느 shard/partition 범위 것인지 | 다른 범위 숫자와 잘못 비교하지 않기 위해 |
| `entity_version` 또는 `row_version` | 단건 monotonicity 보조 기준선 | watermark만으로 부족한 화면에서 보조 판단 |
| `read_source` | `primary`, `replica`, `projection-cache` 등 | 왜 이 값이 cache에 들어왔는지 추적하기 쉬움 |
| `cached_at` | 언제 넣었는지 | TTL, triage, 최근 write와 함께 보기 쉬움 |

초보자는 우선 아래 둘을 반드시 기억하면 된다.

- `applied_watermark`
- `watermark_scope`

scope 없이 숫자만 저장하면 shard가 갈라진 순간 설명이 깨질 수 있다.
이 범위 문제는 [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)에서 더 자세히 다룬다.

## 주문 결제 예시로 따라가기

주문 `#123` 결제가 끝났다.

```text
source tx commit
- orders[123].status = PAID
- outbox.id = 9001
```

event에는 이 기준선이 실린다.

```json
{
  "event_type": "order_paid",
  "order_id": "123",
  "required_watermark": 9001
}
```

주문 상세 projection이 반영을 마친 뒤 row는 이렇게 된다.

```text
orders_read[123]
- status = PAID
- applied_watermark = 9001
```

이제 알림 클릭 같은 요청이 들어와 primary나 fresh projection read로 안전한 값을 읽었다고 하자.
여기서 refill을 아래처럼 해야 다음 요청이 쉬워진다.

```text
cache.put(
  key = "order:123",
  value = { status: "PAID" },
  metadata = {
    applied_watermark: 9001,
    watermark_scope: "orders-main",
    entity_version: 42
  }
)
```

다음 요청이 같은 주문 상세를 열 때:

```pseudo
entry = cache.get("order:123")

if entry.meta.watermark_scope == request.requiredScope
   and entry.meta.applied_watermark >= request.requiredWatermark:
  return entry.value

return fallback_to_fresher_source()
```

중요한 점은 cache value 자체가 `PAID`라는 문자열을 담고 있다는 사실보다,
그 값이 **왜 믿을 만한지**를 metadata가 계속 설명해 준다는 것이다.

## refill 시점에 무엇을 같이 써야 하나

이 주제의 핵심은 "cache write를 할 때 무엇을 절대 빼먹지 말아야 하나"다.

| refill 상황 | 같이 저장해야 하는 것 | 빠지면 생기는 문제 |
|---|---|---|
| primary fallback 후 refill | `applied_watermark`, `watermark_scope` | 다음 hit가 fresh proof 없이 TTL만 믿게 된다 |
| fresh projection row refill | projection row의 `applied_watermark` | read model은 안전했는데 cache는 그 사실을 잊는다 |
| notification causal read 후 refill | 응답이 만족한 `required_watermark` 이상 metadata | click 직후는 맞았는데 다음 클릭에서 다시 stale 가능 |
| replica read 후 refill | replica가 실제로 만족한 watermark metadata | lagging replica 값을 오래 cache할 위험이 있다 |

짧게 말하면:

- 안전한 read를 했다면, 그 안전성의 근거도 같이 cache에 저장해야 한다
- 그렇지 않으면 다음 hit는 다시 "증거 없는 빠른 길"이 된다

## 흔한 오해

- `TTL이 짧으면 watermark metadata는 없어도 된다`
  - TTL은 만료 규칙일 뿐이고, causal hit 검사의 근거는 아니다.
- `cache에 value만 맞으면 된다`
  - 다음 요청은 그 value가 어떤 기준선 이후 값인지 알 수 없다.
- `required_watermark`를 cache entry에 그대로 저장하면 끝이다
  - 보통 다음 hit에서는 "이 entry가 실제로 어디까지 반영했나"를 보여 주는 `applied_watermark`가 더 직접적인 기준이다.
- `primary에서 읽어 왔으니 metadata 없이도 fresh하다`
  - 그건 refill 순간의 사실일 뿐이다. 다음 hit 시점에는 persisted metadata가 없으면 다시 증명할 수 없다.
- `scope는 advanced라서 나중에 붙이면 된다`
  - 단일 shard가 아니면 처음부터 scope를 같이 저장하는 편이 beginner 문서 기준으로도 덜 위험하다.

## 초보자용 최소 설계

복잡한 캐시 프레임워크 없이도 아래 정도면 출발점이 된다.

1. request context에 `required_watermark`를 들고 다닌다.
2. read model이나 safe source가 `applied_watermark`를 응답 metadata로 준다.
3. cache refill helper가 payload와 함께 `applied_watermark`, `watermark_scope`를 저장한다.
4. cache hit helper는 TTL보다 먼저 `required <= applied`를 검사한다.
5. mismatch면 rejected hit로 기록하고 fresher source로 내려간다.

가장 작은 pseudo code는 이 정도다.

```pseudo
function refillCache(key, value, meta):
  cache.put(key, value, {
    applied_watermark: meta.appliedWatermark,
    watermark_scope: meta.watermarkScope,
    entity_version: meta.entityVersion
  })

function canAcceptHit(entry, required):
  return entry.meta != null
    and entry.meta.watermark_scope == required.scope
    and entry.meta.applied_watermark >= required.watermark
```

## 어디까지 이 문서에서 다루고, 어디서 멈추나

이 문서는 beginner를 위해 아래 질문까지만 다룬다.

- outbox watermark가 cache metadata와 왜 이어지나
- refill metadata가 왜 다음 causal hit 검사를 가능하게 하나
- cache entry에 최소 무엇을 남겨야 하나

반대로 아래는 연결 문서로 넘긴다.

- shard별 비교 범위 상세 규칙: [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)
- hit/miss/refill 전체 read path 정책: [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- rejected hit 로그와 메트릭 설계: [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- causal read accept helper 설계: [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)

## 한 줄 정리

watermark metadata persistence의 본질은 "fresh한 값을 한 번 읽었다"를 cache에 남기는 것이 아니라, 그 값이 **어느 watermark까지 반영된 결과인지**를 같이 저장해 다음 cache hit에서도 causal accept 여부를 다시 증명할 수 있게 만드는 데 있다.
