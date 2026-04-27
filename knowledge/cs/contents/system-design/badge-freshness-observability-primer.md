# Badge Freshness Observability Primer

> 한 줄 요약: unread badge 같은 count read model은 "얼마나 늦게 따라오나", "지금 cache 값이 얼마나 오래됐나", "나중에 얼마나 크게 보정되나"를 같이 봐야 초보자도 stale badge를 이벤트 유실과 구분할 수 있다.

retrieval-anchor-keywords: badge freshness observability primer, unread badge observability, badge freshness metrics, count read model observability, projection lag metric, badge projection lag, cache age metric badge, badge cache age, correction delta metric, unread count correction delta, badge count correction, count projection observability, read model freshness observability, stale badge metrics, notification badge lag primer, count read model lag cache correction, projection watermark generated_at observability, badge stale triage starter, beginner badge observability, system-design-00075

**난이도: 🟢 Beginner**

관련 문서:

- [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)
- [Notification Inbox Row Monotonicity Primer](./notification-inbox-row-monotonicity-primer.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)

---

## 먼저 잡을 mental model

badge 숫자가 틀릴 때 초보자는 곧바로 "이벤트가 유실됐나?"를 떠올리기 쉽다.
하지만 count read model에서는 보통 아래 세 시계가 서로 다른 속도로 움직인다.

| 시계 | 쉬운 질문 | 대표 신호 |
|---|---|---|
| projection 시계 | projection이 source write를 얼마나 늦게 따라오나 | `projection_lag_ms` |
| cache 시계 | 지금 읽은 badge 값이 cache 안에서 얼마나 묵었나 | `cache_age_ms` |
| correction 시계 | 나중에 badge를 얼마나 크게 고쳐야 했나 | `correction_delta` |

한 줄로 외우면 이렇다.

> lag는 "뒤처짐", age는 "묵은 정도", correction delta는 "나중에 고친 폭"이다.

세 숫자를 같이 봐야 하는 이유도 단순하다.

- lag만 보면 cache가 오래 붙잡고 있는지 모른다.
- cache age만 보면 projection consumer가 밀리는지 모른다.
- correction delta만 보면 지금 진행 중인 지연인지, 이미 지나간 보정 흔적인지 모른다.

---

## badge count read model에서 실제로 무슨 일이 벌어지나

알림 배지를 예로 들면 경로는 대개 아래처럼 나뉜다.

```text
source write
  -> notification event
  -> badge count projection update
  -> badge cache refresh/invalidate
  -> later correction/recount job
```

그래서 badge가 틀릴 때 가능한 원인은 여러 개다.

| 보이는 증상 | 흔한 실제 원인 | 가장 먼저 볼 숫자 |
|---|---|---|
| badge가 몇 초 동안 낮게 유지됨 | projection consumer lag | `badge_projection_lag_ms` |
| projection은 따라왔는데 화면은 계속 옛 count | cache TTL 또는 invalidation 누락 | `badge_cache_age_ms` |
| 평소엔 괜찮다가 주기적으로 큰 점프가 남 | recount / correction job이 뒤늦게 덮어씀 | `badge_count_correction_delta` |

중요한 점은 badge가 틀렸다는 사실만으로 유실을 단정하면 안 된다는 것이다.
먼저 "projection이 늦은가, cache가 늙었나, correction이 자주 크나"를 분리해야 한다.

---

## 세 메트릭을 어떻게 읽나

### 1. Projection lag: source와 read model 사이 거리

projection lag는 source write가 끝난 시점과 count read model이 그 write를 반영한 시점 사이의 거리다.

| 보고 싶은 것 | 시작 필드 |
|---|---|
| 최신 반영 시각 | `projection_watermark` 또는 `last_applied_event_at` |
| 응답 생성 시각 | `generated_at` |
| 계산 결과 | `projection_lag_ms` |

초보자용 해석:

- `projection_lag_ms`가 크면 consumer, queue, projection worker부터 본다.
- lag가 작아졌는데도 badge가 계속 틀리면 cache age나 correction 문제로 시선을 옮긴다.

아주 단순한 응답 예시는 이렇다.

```json
{
  "unread_count": 7,
  "projection_watermark": 9010,
  "generated_at": "2026-04-27T10:15:02Z",
  "projection_lag_ms": 1800
}
```

이 숫자는 "badge 계산 자체가 source보다 약 1.8초 늦다"는 뜻이지, cache가 1.8초 묵었다는 뜻은 아니다.

### 2. Cache age: 지금 읽은 badge 값이 얼마나 오래 묵었나

cache age는 projection이 만든 값을 cache가 얼마나 오래 들고 있었는지를 본다.

| 보고 싶은 것 | 시작 필드 |
|---|---|
| cache에 들어간 시각 | `cached_at` |
| 지금 응답 시각 | `served_at` |
| 계산 결과 | `cache_age_ms` |

초보자용 해석:

- `projection_lag_ms`는 낮은데 `cache_age_ms`만 크면 cache invalidation/TTL 쪽 문제일 가능성이 크다.
- `cache_age_ms`가 freshness budget보다 크면 hit ratio가 높아도 좋은 cache라고 보기 어렵다.

짧은 예시:

```text
projection_lag_ms = 400
cache_age_ms = 12000
```

이 경우는 "projection은 빨리 따라왔는데, 화면은 12초 묵은 badge를 계속 받고 있다"에 가깝다.

### 3. Correction delta: 나중에 얼마나 크게 고쳐졌나

correction delta는 recount나 repair job이 count를 얼마나 바꿨는지 보는 숫자다.

| 보고 싶은 것 | 시작 필드 |
|---|---|
| 보정 전 count | `before_count` |
| 보정 후 count | `after_count` |
| 계산 결과 | `correction_delta = after_count - before_count` |

초보자용 해석:

- 작은 delta가 드물게 생기면 projection의 자연스러운 늦음일 수 있다.
- 큰 delta가 자주 생기면 read receipt 중복 처리, collapse 규칙, idempotency 누락 같은 구조 문제를 의심한다.

예를 들어 `0 -> 6` 보정이 자주 보이면 "잠깐 늦었다"보다 "중간 경로가 자주 빠진다"에 더 가깝다.

---

## 세 메트릭을 같이 읽는 작은 표

| 상황 | projection lag | cache age | correction delta | 첫 해석 |
|---|---|---|---|---|
| A | 큼 | 작음 | 작음 | projection consumer/queue 지연부터 본다 |
| B | 작음 | 큼 | 작음 | cache invalidation 또는 TTL이 badge freshness를 가리고 있다 |
| C | 작음 | 작음 | 큼 | 평소 응답보다 correction/recount 설계 문제를 먼저 본다 |
| D | 큼 | 큼 | 큼 | projection, cache, correction이 함께 흔들리는 incident 가능성이 크다 |

초보자에게는 이 표 하나가 가장 중요하다.

- lag가 크면 "아직 못 따라왔다"
- age가 크면 "따라왔어도 오래된 복사본을 보고 있다"
- delta가 크면 "나중에 세게 고쳐야 했다"

---

## 아주 작은 badge 예시

사용자 `u-17`에게 unread badge가 `2`로 보였는데 실제 unread는 `5`였다고 하자.

```text
10:00:00 source events committed
10:00:01 projection unread_count=5 applied
10:00:02 cache still serves unread_count=2
10:00:12 cache refreshed to unread_count=5
10:05:00 recount job confirms unread_count=5, correction delta=0
```

이 흐름이면 해석은 이렇게 간다.

| 질문 | 답 |
|---|---|
| projection이 늦었나 | 아니다. 1초 만에 따라왔다 |
| 왜 사용자는 틀린 badge를 봤나 | cache가 10초 이상 묵은 값을 줬다 |
| correction 문제가 있었나 | 아니다. recount delta가 0이므로 구조적 count 불일치는 약하다 |

반대로 아래 흐름이면 이야기가 달라진다.

```text
10:00:00 source events committed
10:00:08 projection unread_count=2 applied
10:03:00 recount job fixes unread_count=5
correction delta=+3
```

이 경우 첫 질문은 cache가 아니라 projection 정확도와 correction 설계다.

---

## starter metric set

처음부터 복잡한 dashboard를 만들 필요는 없다.
badge/count read model이면 아래 정도로 시작해도 triage가 가능하다.

| metric | 타입 | 뜻 |
|---|---|---|
| `badge_projection_lag_ms` | histogram | source write 대비 projection 반영 지연 |
| `badge_cache_age_ms` | histogram | 응답에 사용된 badge cache entry 나이 |
| `badge_count_correction_total` | counter | correction 실행 횟수 |
| `badge_count_correction_delta` | histogram | correction 한 번당 count 변경 폭 |
| `badge_served_total{source=\"cache|projection|recount\"}` | counter | 어느 경로의 값이 응답됐는지 |

가능하면 응답/로그에도 아래 필드를 같이 두는 편이 좋다.

| 필드 | 왜 필요한가 |
|---|---|
| `projection_watermark` | count read model이 어디까지 따라왔는지 설명 |
| `generated_at` | projection 결과가 언제 만들어졌는지 설명 |
| `cached_at` | cache age 계산 근거 |
| `correction_job_id` | 큰 delta가 어느 recount/replay에서 왔는지 연결 |

---

## 흔한 혼동

- `projection_lag_ms`가 작으니 freshness 문제가 없다고 보면 안 된다. cache가 오래된 값을 붙잡고 있을 수 있다.
- `cache_age_ms`가 크다고 꼭 cache만 문제는 아니다. projection이 느리면 오래된 값을 오래 캐시하는 현상이 같이 보일 수 있다.
- `correction_delta`가 있다는 이유만으로 즉시 장애라고 보면 안 된다. 작은 보정은 설계상 정상일 수 있다.
- 반대로 큰 correction delta가 반복되는데 "어차피 나중에 맞아지니까 괜찮다"로 넘기면 안 된다. 초보자에게는 이 숫자가 구조적 불일치의 가장 쉬운 경고다.
- badge count와 clicked source stale을 같은 metric으로 뭉치면 안 된다. count read model 문제와 source causal read 문제는 분리해서 봐야 한다.

---

## 어디까지 연결해서 읽으면 좋은가

| 지금 궁금한 다음 질문 | 이어서 볼 문서 |
|---|---|
| badge stale와 source stale를 왜 따로 봐야 하나 | [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md) |
| badge 다음 단계인 inbox row 역행은 어떻게 막나 | [Notification Inbox Row Monotonicity Primer](./notification-inbox-row-monotonicity-primer.md) |
| source 상세의 cache reject / primary fallback은 어떻게 기록하나 | [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) |
| stale 급증과 headroom을 한 화면에서 어떻게 보나 | [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md) |

---

## 한 줄 정리

badge freshness observability의 시작점은 "projection lag, cache age, correction delta" 세 숫자를 분리해서 보는 것이다. 그래야 초보자도 stale badge를 유실, cache 문제, 늦은 보정 중 어디로 triage해야 하는지 바로 가를 수 있다.
