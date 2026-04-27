# Rejected-Hit Observability Primer

> 한 줄 요약: cache hit을 버린 이유, replica watermark miss 때문에 primary로 fallback한 이유, 읽은 값을 cache에 다시 채우지 않은 이유를 로그와 메트릭으로 설명할 수 있게 만드는 입문 문서다.

retrieval-anchor-keywords: rejected hit observability primer, rejected cache hit logging, cache hit reject reason, rejected_hit_reason, primary fallback reason, fallback_reason recent_write min_version replica_lag unknown, cache watermark reject reason, fallback headroom band, refill no-fill decision, no_fill_reason checklist, cache hit miss refill observability, unknown fallback cleanup, 처음 배우는데 rejected hit 뭐예요, rejected hit basics, rejected hit observability primer basics

**난이도: 🟢 Beginner**

관련 문서:

- [First 15-Minute Triage Flow Card](./first-15-minute-triage-flow-card.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Watermark Mismatch Fallback UX Primer](./watermark-mismatch-fallback-ux-primer.md)
- [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
- [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Notification Read to Min-Version Bridge](./notification-read-to-min-version-bridge.md)
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

처음 배우는데 rejected hit이 뭐예요, basics만 먼저 알고 싶다 싶으면 "값을 봤지만 지금 요청 기준에는 못 써서 버린 것"이라고 먼저 답하면 된다.

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

## 로그 용어 맞추기

### 먼저 용어를 맞춘다

[Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)는 초보자 설명을 위해 `recent-write`, `min-version`, `causal token` 같은 말을 먼저 쓴다.
이 문서는 로그/메트릭 enum을 설명하므로 아래처럼 `snake_case` 값으로 고정한다.

| bridge에서 읽는 개념 | 이 문서의 기록용 값 | 같은 뜻으로 읽는 포인트 |
|---|---|---|
| `recent-write` | `recent_write` | write 직후라 안전 경로를 강제했다 |
| `min-version` | `min_version` | 이미 본 기준선보다 replica가 뒤에 있다 |
| `causal token` / required watermark | `watermark` | dependency visibility 기준선을 replica가 아직 못 맞췄다 |

헷갈리면 이렇게 기억하면 된다.

- bridge는 사람이 이해하기 쉬운 말
- observability primer는 로그에 박히는 enum 이름
- 둘 중 하나만 새 개념인 것이 아니라, 같은 판단을 다른 자리에서 다르게 표기하는 것이다

## `watermark`, `min-version`, `recent-write`를 cache hit 예시로 먼저 구분하기

초보자는 세 reason이 전부 "stale이라서 버렸다"로 들려서 자주 섞는다.
하지만 rejected hit의 이유는 "무엇을 기준으로 reject했는가"가 다르다.

> 같은 주문 cache hit이라도, 비교하는 기준선이 다르면 reject 이름도 달라진다.

주문 `order:123` cache entry가 아래처럼 있다고 하자.

```text
cache entry
- status = PENDING
- version = 40
- applied_watermark = 8998
- cached_at = 10:00:01
```

이때 요청 문맥이 무엇이냐에 따라 결과가 달라진다.

| 요청이 들고 온 기준 | cache hit 비교 | rejected hit reason | 왜 reject하나 |
|---|---|---|---|
| `required_watermark=9001` | `8998 < 9001` | `watermark` | 원인까지 보였다는 증거가 아직 부족하다 |
| `min_version(order:123)=42` | `40 < 42` | `min_version` | 내가 이미 본 최신선보다 뒤로 간다 |
| `recent_write_until=10:00:05` | `cached_at=10:00:01`만으로는 write 이후 증명이 안 됨 | `recent_write` | 방금 쓴 직후라 안전한 경로를 강제해야 한다 |

짧게 외우면 이렇다.

- `watermark`: "이 결과의 원인까지 따라왔나?"
- `min-version`: "내가 이미 본 값보다 뒤로 가나?"
- `recent-write`: "방금 쓴 직후라 빠른 경로를 잠깐 못 믿나?"

### 같은 hit, 다른 reject 예시

| 상황 | cache에는 값이 있나 | 그래도 reject되는 이유 |
|---|---|---|
| 결제 완료 알림 직후 주문 상세 진입 | 있다 | 알림이 준 `required_watermark`를 hit가 못 맞추면 `watermark` |
| 방금 `PAID` 상세를 본 뒤 주문 목록 재진입 | 있다 | 목록 row version이 세션 floor보다 낮으면 `min_version` |
| 사용자가 막 주소를 수정하고 곧바로 프로필 조회 | 있다 | write 직후 guard 기간이라 cache가 새 write 이후임을 증명 못 하면 `recent_write` |

헷갈릴 때는 "요청이 들고 온 토큰/힌트가 무엇인가?"부터 보면 된다.

- causal dependency를 들고 왔으면 `watermark`
- 이미 본 최신선을 들고 왔으면 `min_version`
- 방금 쓴 사실 자체가 핵심이면 `recent_write`

이 세 구분을 먼저 해 두면, 운영 로그에서 `rejected_hit_reason`을 봤을 때 "cache가 느리다"가 아니라 "어떤 freshness contract가 발동했는가"를 바로 읽을 수 있다.

---

## 세 가지 결정을 어떻게 기록하나

아래 카드는 `rejected_hit_reason`, `fallback_reason`, `no_fill_reason`를 각각 따로 읽고, 그 다음에 Green/Yellow/Red headroom 카드로 운영 해석을 붙이는 순서를 잡아 준다.

초보자가 가장 많이 섞는 지점은 "셋 다 stale이라서 찍히는 비슷한 로그"처럼 보는 것이다.
하지만 실제로는 같은 요청 안에서도 질문이 다르다.

| 필드 | decision stage | 먼저 답하는 질문 | 값이 찍히는 시점 | junior가 자주 하는 오해 |
|---|---|---|---|---|
| `rejected_hit_reason` | cache hit accept | "cache에 있던 기존 값을 왜 못 썼지?" | cache hit을 본 직후 | fallback까지 이미 결정됐다고 생각함 |
| `fallback_reason` | source selection | "왜 replica 대신 더 아래 source로 갔지?" | cache reject 뒤 source를 고를 때 | cache miss 이유와 같은 말이라고 섞음 |
| `no_fill_reason` | cache refill | "이번 정답을 왜 cache에 다시 안 넣지?" | 최종 read 뒤 refill 여부를 정할 때 | read 실패 로그라고 오해함 |

짧게 외우면 순서는 `기존 값 거절 -> 다음 source 선택 -> 이번 정답 재적재 판단`이다.

## 같은 요청을 세 로그로 붙여 보기

한 요청 안에서도 `rejected_hit_reason`, `fallback_reason`, `no_fill_reason`는 서로 다른 decision으로 연달아 찍힐 수 있다.

상황: 사용자가 결제 직후 `GET /orders/123`을 호출했고, 요청은 `required_watermark=9001`을 들고 왔다. cache entry는 `applied_watermark=8998`, replica는 `visible_watermark=9000`까지만 따라왔고, primary는 정답이지만 이번 응답은 개인화 필드가 섞여 shared cache에 다시 넣지 않기로 했다고 하자.

| 단계 | 판단 | 남길 핵심 필드 | 한 줄 해석 |
|---|---|---|---|
| cache hit 검사 | reject | `rejected_hit_reason=watermark` | cache에 값은 있었지만 요청 기준선을 못 맞췄다 |
| source 선택 | fallback | `fallback_reason=watermark` | replica도 같은 watermark 기준을 못 맞춰 primary로 내려갔다 |
| refill 결정 | no fill | `no_fill_reason=personalized_response` | 응답은 맞췄지만 shared cache 재사용은 안전하지 않았다 |

```text
event=cache_hit_rejected route=GET /orders/123 required_watermark=9001 entry_watermark=8998 rejected_hit_reason=watermark
event=replica_primary_fallback route=GET /orders/123 required_watermark=9001 replica_visible_watermark=9000 fallback_reason=watermark
event=cache_refill_skipped route=GET /orders/123 fill_source=primary no_fill_reason=personalized_response
```

초보자 기준으로는 이렇게 읽으면 된다.

- `rejected_hit_reason`: 왜 **기존 cache 값**을 못 썼는가
- `fallback_reason`: 왜 **다음 source**로 더 내려갔는가
- `no_fill_reason`: 왜 **이번 정답**을 다시 cache에 안 넣었는가

## 1. Rejected cache hit

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

`rejected_hit_reason=watermark`라면 version 대신 watermark 쌍을 먼저 남기는 편이 초보자에게 더 읽기 쉽다.

```text
event=cache_hit_rejected
route=GET /orders/{id}
entity_type=order
cache_tier=redis
entry_watermark=8998
required_watermark=9001
rejected_hit_reason=watermark
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

## 2. Replica fallback reason

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

## 2-A. Causal-token read path를 세 줄로 기록하는 starter

causal-token read path에서 초보자가 가장 먼저 익혀야 할 흐름은 아래 세 줄이다.

> cache hit rejection, replica watermark miss, primary fallback은 한 사건의 세 장면일 수 있다.

주문 결제 직후 상세 조회를 예로 들면:

```text
required_watermark=9001
cache entry watermark=8998
replica watermark=8999
selected source=primary
```

이때 남길 starter log는 아래처럼 읽으면 된다.

| 단계 | event | 꼭 남길 필드 | 왜 필요한가 |
|---|---|---|---|
| cache hit 거절 | `cache_hit_rejected` | `required_watermark`, `entry_watermark`, `rejected_hit_reason=watermark` | cache 값이 있었지만 causal 기준선을 못 맞췄다는 증거 |
| replica 판정 실패 | `replica_primary_fallback` | `required_watermark`, `replica_watermark`, `fallback_reason=watermark`, `selected_source=primary` | replica가 왜 탈락했고 왜 primary로 갔는지 설명 |
| primary 채택 후 refill | `cache_refill` 또는 `cache_refill_no_fill` | `read_source=primary`, `value_watermark`, `required_watermark` | 최종 응답과 다음 cache 상태가 안전했는지 설명 |

복잡하게 느껴지면 아래 한 줄만 먼저 외우면 된다.

- cache rejection은 `entry_*` 대 `required_*`
- replica miss는 `replica_*` 대 `required_*`
- primary fallback은 `selected_source=primary`를 reason과 함께 남긴다

한 요청에서 세 줄이 모두 보이면, 초보자도 "왜 stale cache를 안 썼고 왜 replica도 안 썼는지"를 추측이 아니라 증거로 따라갈 수 있다.

## 2-0. Fallback reason log-field playbook snippet

초보자에게 가장 쉬운 규칙은 이것이다.

> `fallback_reason`마다 "이 값 하나만은 꼭 남겨야 한다"는 짝 필드를 미리 정해 둔다.

이렇게 해 두면 incident 때마다 "이번엔 뭘 로그로 남기지?"를 다시 고민하지 않아도 된다.

## 2-0A. fallback_reason별 must-have 필드

| `fallback_reason` | must-have | optional | copy/paste starter |
|---|---|---|---|
| `recent_write` | `event`, `route`, `fallback_reason`, `selected_source`, `recent_write=true` | `write_age_ms`, `session_id`, `entity_id` | `event=replica_primary_fallback fallback_reason=recent_write selected_source=primary recent_write=true` |
| `min_version` | `event`, `route`, `fallback_reason`, `selected_source`, `min_required_version`, `replica_visible_version` | `version_gap`, `entity_id`, `cache_entry_version` | `event=replica_primary_fallback fallback_reason=min_version min_required_version=42 replica_visible_version=41 selected_source=primary` |
| `replica_lag` | `event`, `route`, `fallback_reason`, `selected_source`, `replica_lag_ms`, `lag_budget_ms` | `replica_pool`, `replica_region`, `endpoint_tier` | `event=replica_primary_fallback fallback_reason=replica_lag replica_lag_ms=650 lag_budget_ms=200 selected_source=primary` |

## 2-0A-2. 나머지 fallback_reason 필드

| `fallback_reason` | must-have | optional | copy/paste starter |
|---|---|---|---|
| `watermark` | `event`, `route`, `fallback_reason`, `selected_source`, `required_watermark`, `replica_watermark` | `watermark_gap`, `token_type`, `dependency_name` | `event=replica_primary_fallback fallback_reason=watermark required_watermark=9001 replica_watermark=8998 selected_source=primary` |
| `replica_error` | `event`, `route`, `fallback_reason`, `selected_source`, `error_class` | `error_code`, `timeout_ms`, `replica_pool` | `event=replica_primary_fallback fallback_reason=replica_error error_class=timeout selected_source=primary` |
| `policy_primary` | `event`, `route`, `fallback_reason`, `selected_source`, `policy_name` | `policy_version`, `endpoint_tier`, `owner_team` | `event=replica_primary_fallback fallback_reason=policy_primary policy_name=post_write_strong_read selected_source=primary` |

## 2-0A-3. `fallback_reason=unknown`은 언제 잠깐 허용되나

초보자용 mental model은 간단하다.
`unknown`은 정상 reason이 아니라, "아직 이름표를 못 붙인 fallback"이라는 임시 바구니다.

아래 두 경우에는 짧게 허용할 수 있다.

| 잠깐 허용 가능한 상황 | 왜 바로 0으로 못 만들 수 있나 | 대신 꼭 같이 남길 것 |
|---|---|---|
| 새 read path를 막 계측에 붙인 첫 배포 | enum 분류보다 로그 연결을 먼저 열어야 할 수 있다 | `route`, `selected_source`, `replica_lag_ms` 같은 원본 필드 |
| 기존 로그 포맷을 enum 기반으로 정리하는 migration 중 | 예전 producer가 아직 새 reason set을 다 못 채울 수 있다 | `reason_version`, `producer`, `fallback_reason_raw` |

반대로, 아래처럼 쓰기 시작하면 위험 신호다.

| 피해야 할 상태 | 왜 위험한가 |
|---|---|
| `unknown`이 평소 reason처럼 오래 누적됨 | 운영팀이 원인별 첫 액션을 잃고 "primary가 늘었다"만 보게 된다 |
| `unknown`인데 원본 필드도 없음 | 나중에 `recent_write`였는지 `replica_lag`였는지 재분류할 근거가 사라진다 |

작게 줄이는 순서는 이렇다.

1. 먼저 `unknown` 비율을 route별로 본다.
2. 비율이 큰 상위 route 1~2개만 골라 raw field를 확인한다.
3. 가장 많이 반복되는 패턴부터 새 enum으로 승격한다.
4. 분류가 끝난 뒤에야 alert를 `unknown` 감소 기준으로 강화한다.

짧은 예시:
처음엔 `fallback_reason=unknown`, `replica_lag_ms=480`, `lag_budget_ms=200`만 남았다고 하자.
이 패턴이 반복되면 다음 배포에서 `replica_lag`로 승격하고, 그 뒤에야 `unknown` 알람 상한을 더 낮춘다.
이 순서가 안전한 이유는, 관측 공백을 먼저 메우고 분류를 좁혀야 오분류로 인한 잘못된 튜닝을 줄일 수 있기 때문이다.

작게 시작하려면 아래처럼 읽으면 된다.

## 2-0B. must-have와 optional을 읽는 법

| 구분 | 뜻 |
|---|---|
| must-have | reason을 나중에 다시 설명할 수 있게 만드는 최소 필드 |
| optional | 있으면 triage가 빨라지지만, 없어도 reason 자체는 해석 가능한 필드 |

흔한 혼동:

- `entity_id`, `session_id` 같은 값은 log에는 도움이 되지만 metric label로 올리면 안 된다.
- `selected_source=primary`만 남기고 reason 짝 필드를 빼면 "왜 primary였는지"를 다시 추측해야 한다.
- `version_gap`, `watermark_gap`처럼 계산 가능한 값은 optional로 두고, 원본 값 두 개를 must-have로 남기는 편이 재해석에 유리하다.

## 초보자용 Reason -> First Action Starter Matrix

초보자에게 `fallback_reason`은 "원인 이름"보다 "첫 행동 버튼"으로 읽히는 게 더 쉽다.
아래 표는 incident deep dive 전에 10~15분 안에 먼저 확인할 최소 동작만 모아 둔 시작점이다.

| `fallback_reason` | 첫 operational action (가장 먼저 할 1개) | 왜 이걸 먼저 보나 |
|---|---|---|
| `recent_write` | write 직후 경로인지 확인하고 `primary_fallback_total{reason="recent_write"}`를 write QPS와 같이 본다 | write 피크와 함께 오르면 정상 보호 동작일 가능성이 높다 |
| `min_version` | `min_required_version`과 `replica_visible_version` gap이 큰 route를 상위 3개만 뽑는다 | "어디서 version 기준선을 못 맞추는지"를 먼저 좁혀야 다음 액션이 정해진다 |
| `replica_lag` | replica pool별 `replica_lag_ms`가 route lag budget을 넘는지 즉시 대조한다 | lag가 budget 초과인지 먼저 확인해야 routing 문제와 infra 문제를 구분할 수 있다 |
| `watermark` | 요청 로그에서 `required_watermark`가 downstream까지 전달됐는지 한 trace로 확인한다 | token 전달 누락이면 DB/replica 튜닝보다 전달 경로 수정이 우선이다 |
| `replica_error` | `replica_read_errors_total`를 `error_class` 기준으로 분리해 timeout/connection 급증 여부를 확인한다 | replica 자체 장애인지 정책 이슈인지를 가장 빨리 분기할 수 있다 |

짧은 번역표를 같이 두면 첫 회독이 빨라진다.

| 로그에서 본 값 | bridge에서 떠올릴 말 |
|---|---|
| `recent_write` | `recent-write` |
| `min_version` | `min-version` |
| `watermark` | `causal token` 또는 required watermark 미충족 |

처음 대응에서 공통으로 지킬 점은 하나다.
"바로 튜닝"보다 "해당 reason이 정상 보호인지, 운영 이상인지 분류"를 먼저 끝낸다.

## 2-1. 임계치 표현을 다른 primer와 맞춘다

초보자 문서에서 `headroom 임계값`, `경고선`, `위험 구간`을 제각각 쓰면 알람 해석이 흔들린다.
그래서 fallback 관련 용어는 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)와 같은 단어를 재사용한다.

용어 먼저:
[recent-write](./cross-primer-glossary-anchors.md#term-recent-write), [min-version floor](./cross-primer-glossary-anchors.md#term-min-version-floor), [stale window](./cross-primer-glossary-anchors.md#term-stale-window), [headroom](./cross-primer-glossary-anchors.md#term-headroom)을 먼저 고정하면 이 섹션의 `stale peak multiplier`와 `fallback headroom band`를 같은 문맥으로 읽기 쉽다.

| 통일 용어 | 이 문서에서 쓰는 방법 |
|---|---|
| stale peak multiplier | fallback reason 급증이 사용자 stale 증상 급증(`baseline 대비 2x`)과 같이 보이는지 확인한다 |
| fallback headroom ratio | `remaining_safe_qps / fallback_qps`로 primary 여유를 같이 본다 |
| fallback headroom band | `Green >= 3x`, `Yellow 1.5x~3x`, `Red < 1.5x` 기준으로 escalation 우선순위를 맞춘다 |

## 2-2. 공통 미니 예시 카드: stale/headroom 숫자 고정

아래 숫자 카드는 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md), [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)와 동일하게 사용한다.
`fallback headroom ratio` 계산이 낯설면 Post-Write primer의 `headroom 계산 미니 카드`에서 `240 / 60 = 4.0x`를 먼저 보고 이 표로 돌아오면 읽기가 훨씬 쉽다.

| 항목 | 값 | 같은 해석 |
|---|---|---|
| baseline stale rate | `0.2%` | 평소 기준선 |
| current stale rate | `5.8%` | 현재 증상 |
| stale peak multiplier | `29x` (`5.8 / 0.2`) | `2x`를 크게 넘으므로 stale 급증 |
| fallback headroom ratio | `4.0x` | `Green (>=3x)`라 capacity 여유는 아직 있음 |
| read source mix 변화 | replica `22% -> 31%`, primary `10% -> 9%` | fallback 불능보다 routing/pinning miss를 먼저 의심 |

초보자용 한 줄: 이 카드에서는 `capacity 부족`보다 `누락된 freshness routing`이 1순위 원인이다.

## 2-3. 공통 중간 카드: 같은 stale 급증이어도 `headroom 2.0x (Yellow)`면 첫 판정이 달라진다

이 카드는 Green과 Red 사이의 shared Yellow 예시다.
로그에서는 보호 동작이 보이기 시작해도, 운영 해석은 "좋다"가 아니라 "계속 맞는지 더 자주 재자"에 가깝다.

| 항목 | 값 | Green/Red 사이에서 달라지는 해석 |
|---|---|---|
| baseline stale rate | `0.2%` | 평소 기준선 |
| current stale rate | `5.8%` | 현재 증상 |
| stale peak multiplier | `29x` (`5.8 / 0.2`) | stale 급증 자체는 Green/Red 카드와 같다 |
| fallback headroom ratio | `2.0x` | `Yellow (1.5x~3x)`라 reason 기반 fallback은 가능하지만 총량 확대는 조심해야 한다 |
| read source mix 변화 | replica `22% -> 25%`, primary `10% -> 18%` | `fallback_reason`이 늘기 시작했어도 primary 여유가 빠르게 줄 수 있다 |

초보자용 한 줄: Yellow 카드에서는 `reason 분류가 맞다`에서 끝내지 않고, `이 reason 때문에 늘어난 fallback 총량이 아직 안전한가`를 같이 본다.

## 2-4. 공통 반례 카드: 같은 stale 급증이어도 `headroom 1.4x (Red)`면 첫 판정이 달라진다

같은 stale 급증이어도 headroom이 Red면 log를 읽는 우선순위가 바뀐다.
Green 카드에서는 `왜 fallback이 덜 걸렸나`를 먼저 보기 쉬웠다면, Red 카드에서는 `fallback을 더 늘리면 primary가 버티나`를 같이 봐야 한다.

| 항목 | 값 | 같은 숫자여도 달라지는 해석 |
|---|---|---|
| baseline stale rate | `0.2%` | 평소 기준선 |
| current stale rate | `5.8%` | 현재 증상 |
| stale peak multiplier | `29x` (`5.8 / 0.2`) | stale 급증 자체는 Green 카드와 같다 |
| fallback headroom ratio | `1.4x` | `Red (<1.5x)`라 fallback 총량을 더 늘리기 어렵다 |
| read source mix 변화 | replica `22% -> 14%`, primary `10% -> 34%` | `fallback_reason`이 늘어도 "보호 동작 성공"으로만 읽으면 안 된다 |

초보자용 한 줄: Red 카드에서는 `reason 분류`와 함께 `primary 보호 필요 여부`를 동시에 본다.

| 같은 stale 급증인데 | Green 카드 (`4.0x`) | Yellow 중간 카드 (`2.0x`) | Red 반례 카드 (`1.4x`) |
|---|---|---|---|
| `recent_write` 증가 해석 | 정상 보호 동작일 가능성이 큼 | 보호 동작은 맞지만 endpoint별 총량 상한을 같이 봐야 한다 | 보호 동작이지만 이미 primary 여유를 거의 소진할 수 있다 |
| `min_version`/`replica_lag` 증가 해석 | routing 누락 route를 찾는 단서 | routing 누락을 찾되 fallback 확대는 단계별로만 늘린다 | routing 누락을 찾되 fallback 확대는 좁게 묶어야 하는 경고 |
| 첫 운영 질문 | "왜 stale인데 fallback이 덜 걸렸지?" | "이 reason이 늘어난 속도만큼 headroom도 빠르게 줄고 있나?" | "이 fallback을 더 키우면 primary가 버티나?" |

흔한 혼동:

- `fallback_reason`이 많이 찍힌다고 항상 좋은 것은 아니다. Red에서는 "보호는 되지만 오래 못 버틴다"일 수 있다.
- `Yellow`에서는 `reason`이 잘 찍혀도 바로 안심하지 않는다. 같은 reason이라도 fallback 총량이 빠르게 커지면 다음 단계가 Red가 될 수 있다.
- `primary 비율 증가`를 안정화 신호로만 읽으면 안 된다. 같은 로그가 capacity 경고일 수도 있다.
- 그래서 Red 카드에서는 `reason` 패널만 보지 말고 `fallback_headroom_ratio`를 같은 시간축에 붙여 본다.

## 3. Refill no-fill decision

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

## 3-0A. `no_fill_reason`별 must-have 필드

`fallback_reason`과 같은 방식으로, `no_fill_reason`도 "이 reason이면 이 짝 필드는 반드시 남긴다"로 맞춰 두면 복붙해서 쓰기 쉽다.

| `no_fill_reason` | must-have | optional | copy/paste starter |
|---|---|---|---|
| `stale_source` | `event`, `route`, `read_source`, `no_fill_reason`, `value_version`, `min_required_version` | `version_gap`, `required_watermark`, `replica_lag_ms` | `event=cache_refill_no_fill read_source=replica no_fill_reason=stale_source value_version=41 min_required_version=42` |
| `missing_metadata` | `event`, `route`, `read_source`, `no_fill_reason`, `missing_field` | `value_version`, `schema_version`, `producer` | `event=cache_refill_no_fill read_source=replica no_fill_reason=missing_metadata missing_field=watermark` |
| `unsafe_endpoint` | `event`, `route`, `read_source`, `no_fill_reason`, `cache_policy` | `endpoint_tier`, `viewer_scope`, `auth_context` | `event=cache_refill_no_fill read_source=primary no_fill_reason=unsafe_endpoint cache_policy=user_scoped_only` |

## 3-0A-2. 나머지 `no_fill_reason` 필드

| `no_fill_reason` | must-have | optional | copy/paste starter |
|---|---|---|---|
| `partial_response` | `event`, `route`, `read_source`, `no_fill_reason`, `degraded_by` | `missing_component`, `fallback_mode`, `response_completeness` | `event=cache_refill_no_fill read_source=primary no_fill_reason=partial_response degraded_by=inventory_timeout` |
| `oversized` | `event`, `route`, `read_source`, `no_fill_reason`, `value_size_bytes`, `cache_limit_bytes` | `entity_type`, `compression_ratio`, `cache_tier` | `event=cache_refill_no_fill read_source=primary no_fill_reason=oversized value_size_bytes=182000 cache_limit_bytes=131072` |
| `write_race` | `event`, `route`, `read_source`, `no_fill_reason`, `value_version`, `newer_committed_version` | `race_window_ms`, `writer_trace_id`, `entity_id` | `event=cache_refill_no_fill read_source=replica no_fill_reason=write_race value_version=41 newer_committed_version=42` |

## 3-0B. `no_fill_reason`에서 must-have와 optional을 읽는 법

| 구분 | 뜻 |
|---|---|
| must-have | "왜 안 채웠는지"를 나중에 다시 설명할 수 있게 만드는 최소 필드 |
| optional | 있으면 triage가 빨라지지만, 없어도 no-fill 판단 자체는 해석 가능한 필드 |

초보자에게 특히 중요한 읽는 법은 세 가지다.

- `no_fill_reason`만 있고 `read_source`가 없으면, stale replica를 막은 건지 primary degraded 응답을 막은 건지 구분이 안 된다.
- `version_gap`처럼 계산 가능한 값은 optional로 두고, `value_version`과 `min_required_version` 같은 원본 값 두 개를 must-have로 남기는 편이 재해석에 유리하다.
- `missing_field=watermark`처럼 비어 있던 metadata 이름을 그대로 남기면, "왜 다음 hit 검증이 불가능했는가"를 초보자도 바로 읽을 수 있다.

---

## 주문 결제 흐름으로 보기

주문 `#123`을 결제한 직후 같은 사용자가 주문 상세를 읽는다고 하자.

```text
freshness context
- recent_write=true
- min_version(order:123)=42
- required_watermark=order_paid@9001
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

- `증상 급증 + Green headroom = 라우팅 점검 우선`이다. reject/fallback reason이 늘어도 primary 여유가 충분하면, 먼저 routing miss를 분류해 새는 route를 좁힌다.
- `cache hit rejected`를 cache 장애로 보면 안 된다. 값은 있었지만 요청 기준을 못 맞춘 것이다.
- `primary fallback`을 무조건 나쁜 지표로 보면 안 된다. write 직후 최신성을 지키는 정상 경로일 수 있다.
- fallback reason별 첫 액션이 다르다. `recent_write` 급증은 트래픽 맥락 확인이 먼저고, `replica_lag` 급증은 lag budget 초과 여부 확인이 먼저다.
- bridge의 `recent-write`, `min-version`, `causal token`을 이 문서의 다른 분류라고 착각하면 안 된다. 이 문서에서는 같은 판단을 로그용 enum인 `recent_write`, `min_version`, `watermark`로 적는다.
- `no-fill`을 refill 실패로만 보면 안 된다. stale 값이나 partial response를 cache에 남기지 않는 보호 동작일 수 있다.
- metric label에 `user_id`, `order_id`, `cache_key`를 넣으면 안 된다. 요청 단위 식별자는 log/trace로 보내고 metric은 낮은 cardinality label만 쓴다.
- `fallback_reason=unknown`은 새 계측 연결이나 enum migration 초반에만 잠깐 허용한다. 이때도 `route`, raw field, producer 정보를 같이 남겨야 나중에 안전하게 줄일 수 있다.

---

## 빠른 체크리스트

- cache hit을 `accepted`와 `rejected`로 나눠 기록하는가
- `rejected_hit_reason`을 `min_version`, `recent_write`, `watermark`, `missing_metadata`, `too_old`처럼 낮은 cardinality 값으로 남기는가
- replica를 우회할 때 `fallback_reason`과 `selected_source`를 같이 남기는가
- refill하지 않을 때 `no_fill_reason`과 `read_source`를 같이 남기는가
- metric label에는 route, entity type, source, reason처럼 bounded 값만 넣는가
- trace에는 `cache.decision`, `read.source`, `fallback.reason`, `cache.refill.decision`을 attribute로 이어 주는가

이 체크리스트를 만족하면 "cache hit ratio는 좋은데 저장 직후 옛값이 보인다" 같은 문제를 훨씬 빨리 설명할 수 있다.

## 한 줄 정리

이 문서의 핵심은 `hit이 있었는가`보다 `왜 버렸고 왜 fallback했고 왜 refill하지 않았는가`를 같은 언어로 남기는 것이다. 같은 stale 급증이라도 `headroom 4.0x`, `2.0x`, `1.4x`는 각기 다른 운영 질문을 만든다.

### 꼬리질문

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
