# Rejected-Hit Observability Primer

> 한 줄 요약: cache hit을 버린 이유, replica 대신 primary로 fallback한 이유, 읽은 값을 cache에 다시 채우지 않은 이유를 로그와 메트릭으로 설명할 수 있게 만드는 입문 문서다.

retrieval-anchor-keywords: rejected hit observability primer, rejected cache hit logging, cache hit reject reason, rejected_hit_reason, cache accept reject metrics, replica fallback reason, primary fallback reason, fallback_reason recent_write min_version replica_lag, refill no-fill decision, cache refill no-fill reason, no_fill_reason stale_replica, safe refill observability, cache hit miss refill observability, freshness routing observability, beginner cache replica observability, mixed cache replica freshness logs, by-source freshness metrics

**난이도: 🟢 Beginner**

관련 문서:

- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
- [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
- [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)

---

## 핵심 개념

cache와 replica가 같이 있는 read path에서 초보자가 먼저 잡아야 할 mental model은 간단하다.

> 빠른 경로를 봤다는 것과 그 경로를 **채택했다**는 것은 다르다.

예를 들어 cache에서 값이 나왔다고 해도, 지금 요청이 원하는 최신성 조건을 못 맞추면 그 hit은 응답으로 쓰면 안 된다.
이때 필요한 관측성은 "cache hit ratio가 몇 퍼센트인가"가 아니라 아래 질문에 답하는 신호다.

- cache hit이 났는데 왜 버렸나?
- replica를 읽을 수 있었는데 왜 primary로 fallback했나?
- 값을 읽었는데 왜 cache refill을 하지 않았나?

이 세 질문에 답하려면 로그와 메트릭의 역할을 나눠야 한다.

| 관측 신호 | 답하는 질문 | 예시 |
|---|---|---|
| structured log | 이 요청 하나가 왜 이 경로를 탔나 | `rejected_hit_reason=min_version`, `fallback_reason=recent_write` |
| metric counter | 같은 일이 얼마나 자주 생기나 | `cache_hit_rejected_total{reason="min_version"}` |
| histogram | 지연/나이/lag가 어느 정도였나 | `cache_entry_age_ms`, `replica_lag_ms` |
| trace attribute | 여러 hop 중 어디서 결정이 바뀌었나 | `read.source=primary`, `cache.decision=rejected` |

한 줄로 줄이면 이렇다.

- 로그는 **왜**를 남긴다
- 메트릭은 **얼마나 자주**를 본다
- trace는 **어느 hop에서**를 이어 준다

---

## 먼저 그림으로 보기

```text
Request + freshness context
  - recent_write?
  - min_version?
  - required_watermark?

        |
        v
   cache lookup
        |
  hit? yes
        |
  satisfies freshness?
    |             |
   yes            no
    |             |
 return cache   log rejected_hit
                metric cache_hit_rejected_total
                  |
                  v
             choose source
          replica safe enough?
             |            |
            yes           no
             |            |
        read replica   log fallback_reason
             |         metric replica_fallback_total
             +-----v---+
                   |
             refill decision
        safe to write into cache?
             |            |
            yes           no
             |            |
        cache fill     log no_fill_reason
                       metric cache_refill_no_fill_total
```

중요한 점은 세 decision이 서로 다른 단계라는 것이다.

| 단계 | 성공 이름 | 거절 이름 | 이유 필드 |
|---|---|---|---|
| cache hit accept | `hit_accepted` | `hit_rejected` | `rejected_hit_reason` |
| replica source selection | `replica_selected` | `primary_fallback` | `fallback_reason` |
| cache refill | `filled` | `no_fill` | `no_fill_reason` |

이 이름을 분리해 두면 "cache hit이 줄었다"와 "hit은 났지만 최신성 때문에 버렸다"를 구분할 수 있다.

---

## 세 가지 결정을 어떻게 기록하나

### 1. Rejected cache hit

rejected hit은 cache가 장애가 났다는 뜻이 아니다.
cache에는 값이 있었지만 **이번 요청의 freshness contract를 만족하지 못했다**는 뜻이다.

대표 reason:

| reason | 의미 | 흔한 다음 경로 |
|---|---|---|
| `min_version` | cache entry version이 요청의 최소 version보다 낮다 | replica 검사 후 primary fallback 가능 |
| `recent_write` | 방금 쓴 값 이후라는 증거가 cache entry에 없다 | primary 또는 pinned source |
| `watermark` | causal token이나 dependency watermark를 만족하지 못한다 | watermark 만족 source 선택 |
| `missing_metadata` | cache entry에 version/updated_at/watermark가 없다 | 보수적으로 miss 처리 |
| `too_old` | TTL은 남았지만 endpoint freshness budget보다 오래됐다 | replica 또는 primary |

structured log 예시는 아래처럼 둔다.

```text
event=cache_hit_rejected
route=GET /orders/{id}
entity_type=order
cache_tier=redis
entry_version=40
min_required_version=42
entry_age_ms=1800
rejected_hit_reason=min_version
trace_id=...
```

metric은 요청 수를 세는 counter로 시작한다.

```text
cache_hit_rejected_total{service, route, entity_type, cache_tier, reason}
cache_hit_accepted_total{service, route, entity_type, cache_tier}
cache_entry_age_ms_bucket{service, route, entity_type, cache_tier}
```

주의할 점은 `cache_key`, `user_id`, `order_id`, `trace_id`를 metric label로 넣지 않는 것이다.
그런 값은 cardinality를 폭발시키므로 log나 trace에만 제한적으로 남긴다.

### 2. Replica fallback reason

replica fallback은 "replica가 항상 나쁘다"가 아니라, **이번 요청에서는 replica를 믿을 근거가 부족했다**는 뜻이다.

대표 reason:

| reason | 의미 | 확인할 metric |
|---|---|---|
| `recent_write` | write 직후 읽기라 replica lag window를 피한다 | `primary_fallback_total{reason="recent_write"}` |
| `min_version` | replica visible version이 요청 기준선보다 낮다 | `replica_version_gap` |
| `replica_lag` | 현재 lag가 endpoint budget을 넘었다 | `replica_lag_ms` |
| `watermark` | required watermark를 replica가 아직 만족하지 못한다 | `replica_watermark_gap` |
| `replica_error` | replica read가 timeout/error를 냈다 | `replica_read_errors_total` |
| `policy_primary` | endpoint 정책상 primary만 허용한다 | `primary_read_total{reason="policy_primary"}` |

structured log 예시:

```text
event=replica_primary_fallback
route=GET /orders/{id}
entity_type=order
fallback_reason=recent_write
replica_lag_ms=650
lag_budget_ms=200
min_required_version=42
replica_visible_version=41
selected_source=primary
trace_id=...
```

metric은 fallback 비율과 primary headroom을 같이 본다.

```text
read_source_total{service, route, entity_type, source}
primary_fallback_total{service, route, entity_type, reason}
replica_lag_ms_bucket{service, replica_pool}
replica_read_errors_total{service, replica_pool, error_class}
```

fallback metric만 있고 primary 부하 metric이 없으면 위험하다.
안전 경로가 늘어나는 순간 primary가 버틸 수 있는지도 같이 봐야 한다.

### 3. Refill no-fill decision

no-fill은 cache에 쓰는 것을 실패했다는 뜻이 아닐 수 있다.
오히려 stale 값을 cache에 다시 넣지 않기 위한 정상적인 보호 동작일 때가 많다.

대표 reason:

| reason | 의미 | 왜 중요한가 |
|---|---|---|
| `stale_source` | 읽은 값이 freshness context를 만족하지 못한다 | stale replica 값을 cache에 고정하지 않는다 |
| `missing_metadata` | cache에 넣어도 다음 요청이 freshness를 검증할 수 없다 | 다음 hit accept 판단이 불가능하다 |
| `unsafe_endpoint` | 이 endpoint 결과는 cache material로 쓰기 위험하다 | 사용자별/권한별 결과 오염 방지 |
| `partial_response` | fallback/degraded 응답이라 cache하면 안 된다 | 일시적 degraded 상태를 오래 남기지 않는다 |
| `oversized` | 값이 너무 커 cache 효율을 해친다 | 성능 보호 |
| `write_race` | write와 refill 순서가 애매하다 | 옛 값을 새 write 뒤에 덮어쓰지 않는다 |

structured log 예시:

```text
event=cache_refill_no_fill
route=GET /orders/{id}
entity_type=order
read_source=replica
value_version=41
min_required_version=42
no_fill_reason=stale_source
cache_tier=redis
trace_id=...
```

metric 예시:

```text
cache_refill_total{service, route, entity_type, source}
cache_refill_no_fill_total{service, route, entity_type, source, reason}
cache_refill_latency_ms_bucket{service, cache_tier}
```

beginner 단계에서는 refill 성공률보다 `source`와 `reason`을 같이 보는 것이 중요하다.
`source=replica, reason=stale_source`가 늘면 cache 문제가 아니라 replica lag가 cache를 오염시킬 뻔한 신호다.

---

## 주문 결제 흐름으로 보기

주문 `#123`을 결제한 직후 같은 사용자가 주문 상세를 읽는다고 하자.

```text
freshness context
- recent_write=true
- min_version(order:123)=42
- required_watermark=payment_confirmed@9001
```

### 1. cache hit이 났지만 버린다

```text
cache entry
- version=40
- watermark=8990
```

이 값은 빠르게 읽혔지만 현재 요청 기준을 만족하지 못한다.
따라서 아래를 남긴다.

```text
event=cache_hit_rejected
rejected_hit_reason=min_version
entry_version=40
min_required_version=42
```

### 2. replica도 아직 부족해서 primary로 간다

```text
replica visible version=41
replica watermark=8998
```

여기도 기준선보다 낮다.

```text
event=replica_primary_fallback
fallback_reason=min_version
replica_visible_version=41
min_required_version=42
selected_source=primary
```

### 3. primary 값만 cache에 채운다

```text
primary value
- version=42
- watermark=9001
```

이제 cache refill이 안전하다.

```text
event=cache_refill
read_source=primary
value_version=42
cache_tier=redis
```

이 흐름에서 중요한 운영 질문은 "cache hit이 있었나?"가 아니다.
**왜 hit을 버렸고, 왜 primary까지 갔고, 왜 이 값은 refill해도 안전했는가**를 설명할 수 있어야 한다.

---

## 대시보드는 이렇게 시작한다

처음부터 복잡한 대시보드를 만들 필요는 없다.
아래 네 줄이면 mixed cache/replica read path의 품질을 훨씬 잘 볼 수 있다.

| 패널 | 봐야 할 것 | 해석 |
|---|---|---|
| read source 분포 | `cache`, `replica`, `primary` 비율 | primary fallback이 갑자기 늘었는지 본다 |
| rejected hit reason | `min_version`, `recent_write`, `missing_metadata` | hit ratio 뒤에 숨은 freshness 거절을 본다 |
| fallback reason | `recent_write`, `replica_lag`, `replica_error` | primary로 간 이유를 분리한다 |
| no-fill reason | `stale_source`, `partial_response`, `missing_metadata` | stale refill을 막고 있는지 본다 |

알람은 처음엔 아래처럼 좁게 잡는 편이 좋다.

- `post-write` 경로에서 `cache_hit_rejected_total`이 급증한다
- `primary_fallback_total{reason="replica_lag"}`가 평소보다 크게 오른다
- `cache_refill_no_fill_total{source="replica", reason="stale_source"}`가 늘어난다
- `read_source_total{source="primary"}` 증가와 primary latency 상승이 같이 보인다

---

## 흔한 혼동

- `cache hit rejected`를 cache 장애로 보면 안 된다. 값은 있었지만 요청 기준을 못 맞춘 것이다.
- `primary fallback`을 무조건 나쁜 지표로 보면 안 된다. write 직후 최신성을 지키는 정상 경로일 수 있다.
- `no-fill`을 refill 실패로만 보면 안 된다. stale 값이나 partial response를 cache에 남기지 않는 보호 동작일 수 있다.
- metric label에 `user_id`, `order_id`, `cache_key`를 넣으면 안 된다. 요청 단위 식별자는 log/trace로 보내고 metric은 낮은 cardinality label만 쓴다.
- `reason=unknown`을 오래 방치하면 안 된다. unknown은 "아직 분류하지 못한 운영 debt"로 보고 줄여야 한다.

---

## 빠른 체크리스트

- cache hit을 `accepted`와 `rejected`로 나눠 기록하는가
- `rejected_hit_reason`을 `min_version`, `recent_write`, `watermark`, `missing_metadata`, `too_old`처럼 낮은 cardinality 값으로 남기는가
- replica를 우회할 때 `fallback_reason`과 `selected_source`를 같이 남기는가
- refill하지 않을 때 `no_fill_reason`과 `read_source`를 같이 남기는가
- metric label에는 route, entity type, source, reason처럼 bounded 값만 넣는가
- trace에는 `cache.decision`, `read.source`, `fallback.reason`, `cache.refill.decision`을 attribute로 이어 주는가

이 체크리스트를 만족하면 "cache hit ratio는 좋은데 저장 직후 옛값이 보인다" 같은 문제를 훨씬 빨리 설명할 수 있다.

## 꼬리질문

> Q: rejected hit은 cache miss와 같은가요?  
> 의도: lookup 결과와 freshness decision을 구분하는지 확인  
> 핵심: 물리적으로는 hit이지만 정책상 응답에 쓰지 않으므로 miss 경로로 내려간다.

> Q: fallback reason을 왜 나눠야 하나요?  
> 의도: primary fallback 증가를 원인별로 해석하는지 확인  
> 핵심: `recent_write` 증가는 정상 제품 흐름일 수 있고, `replica_lag`나 `replica_error` 증가는 운영 문제일 수 있다.

> Q: no-fill은 cache 성능을 낮추는 것 아닌가요?  
> 의도: cache refill과 정합성 보호를 함께 보는지 확인  
> 핵심: stale 값을 채워 넣으면 이후 요청이 더 오래 틀릴 수 있으므로, 안전하지 않은 값은 no-fill이 맞다.

> Q: metric에는 어떤 label을 피해야 하나요?  
> 의도: observability cardinality 기본기를 확인  
> 핵심: `user_id`, `order_id`, `cache_key`, `trace_id`처럼 값이 거의 무한한 label은 metric이 아니라 log/trace로 보낸다.
