# Trace Attribute Freshness / Read-Source Bridge

> 한 줄 요약: freshness context 자체는 요청 문맥으로 들고 가되, trace에는 `무엇을 읽었는지`와 `왜 그렇게 읽었는지`를 저카디널리티 decision attribute로 남겨야 초보자도 stale read를 추적할 수 있다.

retrieval-anchor-keywords: trace attribute freshness read source bridge, freshness trace attributes, read source trace tag, stale read tracing, trace attribute bridge, low cardinality tracing, high cardinality tags, baggage vs span attribute, freshness context propagation, read source decision tracing, selected_source trace, fallback_reason trace, cache reject trace, observability beginner bridge, trace attribute freshness read source bridge basics

**난이도: 🟢 Beginner**

관련 문서:

- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
- [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
- [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)

---

## 핵심 개념

초보자가 먼저 잡아야 할 mental model은 하나다.

> 요청은 **원본 freshness context**를 들고 이동하고, trace는 그 context로 내린 **결정 요약**을 남긴다.

즉 아래 둘은 같은 것이 아니다.

- 요청 문맥: `min_version=428811`, `required_watermark=9001`, `entity_key=order:123`
- trace attribute: `read.source=primary`, `read.decision=primary_fallback`, `read.reason=min_version`

raw context를 trace attribute로 그대로 복사하면 검색은 편해 보여도 금방 비용과 cardinality가 터진다.
trace에는 "이번 hop이 어떤 종류의 판단을 했는가"를 남기고, 숫자 원본이나 entity id는 request context나 structured log 쪽에 둔다.

한 줄로 줄이면 이렇다.

- context는 **전달용**
- trace attribute는 **판정용**
- log는 **상세 증거용**

---

## 먼저 그림으로 보기

```text
request context
  - recent_write_until=...
  - min_version(order:123)=428811
  - required_watermark=9001

        |
        v
service A cache check
  trace attrs:
  - read.source=cache
  - cache.decision=rejected
  - read.reason=min_version

        |
        v
service A replica check
  trace attrs:
  - read.source=replica
  - replica.decision=rejected
  - read.reason=watermark

        |
        v
service A primary read
  trace attrs:
  - read.source=primary
  - read.decision=primary_fallback
  - read.reason=min_version

        |
        v
service B downstream call
  request context keeps moving
  trace keeps only normalized decision attrs
```

핵심은 trace가 `min_version=428811` 같은 값을 hop마다 퍼뜨리는 것이 아니라,
`min_version 때문에 primary로 갔다`는 **결정 사실**을 이어 주는 데 있다는 점이다.

---

## 무엇을 어디에 두나

| 위치 | 넣는 것 | 왜 여기 두나 | 넣지 말아야 할 것 |
|---|---|---|---|
| request context / baggage | `min_version`, `required_watermark`, recent-write flag, entity-scoped freshness token | 다음 hop가 실제 판단을 계속할 수 있어야 한다 | 영구 저장용 장황한 설명 |
| trace attribute | `read.source`, `read.decision`, `read.reason`, `freshness.contract` 같은 enum/band | trace 검색과 hop 비교를 싸게 만든다 | `user_id`, `order_id`, raw watermark, raw version |
| structured log | raw version 값, watermark 값, entity key, exact lag | incident 때 한 요청을 깊게 재구성한다 | 매 요청마다 너무 큰 payload |
| metric label | source, reason, route, endpoint class | 집계와 대시보드에 쓴다 | trace id, entity id, version number |

이 표만 기억해도 첫 설계 실수 대부분을 피할 수 있다.

---

## trace attribute는 enum과 band로 고정한다

trace attribute 설계의 목표는 "세부값을 다 담기"가 아니라 "hop 간 비교가 가능한 vocabulary 만들기"다.

### 추천 starter set

| attribute | 예시 값 | 의미 |
|---|---|---|
| `freshness.contract` | `strong`, `session_monotonic`, `bounded_stale` | 이 요청이 어떤 최신성 계약을 원하나 |
| `read.source` | `cache`, `replica`, `primary` | 실제로 어느 source를 읽었나 |
| `read.decision` | `hit_accepted`, `hit_rejected`, `replica_selected`, `primary_fallback` | 이번 hop에서 어떤 판정이 났나 |
| `read.reason` | `recent_write`, `min_version`, `watermark`, `replica_lag`, `policy_primary` | 왜 그 결정을 했나 |
| `lag.band` | `lt50ms`, `50to200ms`, `gt200ms` | exact lag 대신 운영 band만 남긴다 |
| `version.band` | `met`, `near`, `behind` | exact version gap 대신 상태만 남긴다 |

### raw 값을 같이 보고 싶을 때

| 필요한 값 | trace 대신 어디에 두나 |
|---|---|
| `min_version=428811` | structured log field |
| `required_watermark=9001` | structured log field |
| `order_id=123` | log field 또는 sampled debug event |
| `replica_lag_ms=187` | histogram/structured log |

처음부터 band를 나누기 어렵다면 `lt_budget`, `near_budget`, `over_budget` 정도만 써도 충분하다.

---

## 예시: 주문 결제 직후 stale read 추적

주문 결제 직후 사용자가 상세 화면을 다시 연다고 하자.

### 나쁜 설계

```text
trace attrs:
- order_id=123
- min_version=428811
- required_watermark=9001
- replica_lag_ms=187
```

문제:

- query index가 raw 값으로 퍼진다
- 비슷한 trace를 묶어 보기 어렵다
- metric과 vocabulary가 어긋난다

### 더 나은 설계

```text
request context:
- order_id=123
- min_version=428811
- required_watermark=9001

trace attrs:
- freshness.contract=session_monotonic
- read.source=primary
- read.decision=primary_fallback
- read.reason=min_version
- lag.band=near_budget
- version.band=behind
```

이렇게 두면 초보자도 trace UI에서 바로 아래 질문에 답할 수 있다.

- cache hit이 거절됐나
- replica가 선택됐나 아니면 primary fallback이 났나
- 이유가 `recent_write`인지 `min_version`인지 `replica_lag`인지

정확한 숫자가 더 필요하면 같은 `trace_id`로 log를 열면 된다.

---

## hop마다 어떤 속성을 갱신하나

| hop | 남기면 좋은 attribute | raw context는 계속 들고 가나 |
|---|---|---|
| gateway | `freshness.contract`, `recent_write=true/false` | 예 |
| cache layer | `read.source=cache`, `read.decision=hit_accepted|hit_rejected`, `read.reason` | 예 |
| replica chooser | `read.source=replica|primary`, `read.decision=replica_selected|primary_fallback`, `lag.band` | 예 |
| downstream service | 앞 hop decision을 참고해 같은 vocabulary 재사용 | 예 |
| async consumer | 새 span을 열되 같은 contract/reason family를 유지 | 예 |

중요한 점은 "모든 hop이 새 이름을 만들지 말라"는 것이다.
`primary_because_replica_old`, `replica_not_fresh_enough`, `version_floor_miss`처럼 팀마다 다른 표현을 쓰기 시작하면 trace 검색이 바로 망가진다.

---

## baggage와 trace attribute를 어떻게 구분하나

초보자가 자주 헷갈리는 지점이라 비교로 보는 편이 빠르다.

| 질문 | baggage / request context | trace attribute |
|---|---|---|
| 다음 hop 판단에 직접 필요한가 | 예 | 보통 아니오 |
| raw 숫자를 들고 가나 | 예 | 가급적 아니오 |
| trace 검색 필드로 쓰나 | 아니오 또는 제한적 | 예 |
| cardinality 비용을 가장 조심해야 하나 | 중간 | 매우 높음 |

짧게 기억하면:

- baggage는 `판단 재료`
- trace attribute는 `판단 결과`

---

## 흔한 혼동

- `trace는 로그보다 비싸지 않으니 raw version도 넣어도 된다`는 오해가 흔하다. trace backend도 attribute index와 query 비용 때문에 high cardinality에 약하다.
- `trace attribute를 줄이면 디버깅이 안 된다`도 오해다. trace에는 분류값을, 로그에는 원본값을 두면 둘을 함께 써서 더 잘 본다.
- `read.source=primary`만 남기면 충분하다`도 부족하다. primary를 정책상 택한 것과 `min_version` 때문에 fallback한 것은 운영 의미가 다르다.
- `reason`만 있고 `contract`가 없으면 해석이 흔들린다. `bounded_stale`에서의 `replica_selected`와 `strong`에서의 `replica_selected`는 같은 안전선이 아니다.

---

## 시작 템플릿

처음 붙일 때는 아래 정도면 충분하다.

```text
trace attrs
- freshness.contract=strong|session_monotonic|bounded_stale
- read.source=cache|replica|primary
- read.decision=hit_accepted|hit_rejected|replica_selected|primary_fallback
- read.reason=recent_write|min_version|watermark|replica_lag|policy_primary
- lag.band=lt_budget|near_budget|over_budget
```

```text
structured log
- trace_id
- entity_type
- entity_id
- min_required_version
- replica_visible_version
- required_watermark
- replica_watermark
- replica_lag_ms
```

이 starter set은 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)의 reason enum과 맞춰 두는 편이 좋다.
그래야 trace, metric, log가 같은 단어로 이어진다.

---

## 어디까지 보면 다음 문서로 넘어가나

| 지금 궁금한 것 | 다음 문서 |
|---|---|
| freshness context가 hit/miss/refill 전체에 어떻게 이어지나 | [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md) |
| `fallback_reason`과 `rejected_hit_reason`를 어떻게 로그/메트릭으로 묶나 | [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) |
| tracing backend의 sampling, ingest, query 구조까지 알고 싶다 | [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md) |

## 한 줄 정리

freshness context는 요청이 판단할 재료로 들고 가고, trace에는 `source`, `decision`, `reason` 같은 저카디널리티 결과만 남겨야 stale read와 fallback 경로를 싸고 일관되게 추적할 수 있다.
