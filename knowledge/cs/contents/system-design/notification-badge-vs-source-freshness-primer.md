# Notification Badge vs Source Freshness Primer

> 한 줄 요약: 알림 배지나 unread count는 빠른 요약 read model이라 조금 stale할 수 있지만, 알림을 눌러 들어간 source 상세는 알림이 전제로 한 원인 데이터를 보여 주는 별도 causal 보장이 필요하다.

retrieval-anchor-keywords: notification badge vs source freshness, notification badge source freshness primer, unread badge count read model, unread count stale source detail, badge count stale independently, notification count projection lag, badge read model consistency, source detail causal guarantee, notification click source causal token, badge count vs causal consistency, unread count vs source of truth, 알림 배지 stale, unread count stale, 알림 카운트와 원본 신선도, system-design-00058

**난이도: 🟢 Beginner**

관련 문서:

- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Notification 시스템 설계](./notification-system-design.md)
- [Mobile Push Notification Pipeline Design](./mobile-push-notification-pipeline-design.md)

---

## 핵심 개념

먼저 화면을 둘로 나누면 덜 헷갈린다.

| 화면 요소 | 쉬운 말 | 보통 읽는 곳 | 사용자 기대 |
|---|---|---|---|
| 배지, 빨간 점, unread count | "뭔가 새 게 있을지도 몰라요"라는 요약 신호 | count projection, cache, notification inbox summary | 대략 맞고 금방 고쳐지면 됨 |
| 알림 목록 row | "이 이벤트가 있었어요"라는 항목 | notification read model | row가 사라지거나 뒤집히지 않기를 기대 |
| 클릭 후 source 상세 | 댓글, 주문, 승인 같은 원본 화면 | source DB, replica, cache, detail read model | 알림이 말한 원인이 반드시 보여야 함 |

배지는 source-of-truth가 아니라 **요약 read model**이다.
그래서 배지가 `3`인데 목록에는 아직 `2`개만 보이거나, 이미 읽었는데 배지가 잠깐 `1`로 남을 수 있다.

하지만 알림을 눌렀을 때 원본 댓글이나 주문 상태가 안 보이는 것은 다른 문제다.
사용자는 이미 "새 댓글이 있다", "결제가 완료됐다"는 결과를 봤다.
그 결과를 설명하는 source 데이터가 이어서 보여야 하므로, 이 경로는 [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)의 문제다.

---

## 왜 서로 독립적으로 stale해지나

알림 하나가 만들어져도 내부 경로는 보통 여러 갈래다.

```text
source write: comment:777 committed at watermark 9001
        |
        +-> notification row projection
        +-> unread badge/count projection
        +-> push delivery
        +-> source detail replica/cache catch-up
```

이 네 갈래는 속도와 실패 방식이 다르다.
그래서 아래 조합이 모두 가능하다.

| badge/count | source 상세 | 실제 의미 |
|---|---|---|
| stale | fresh | 배지는 아직 `0`인데 deep link로 들어가면 댓글은 보인다 |
| fresh | stale | 배지는 `1`인데 상세 replica가 늦어서 댓글이 안 보일 수 있다 |
| stale | stale | count projection도 늦고 detail read path도 늦다 |
| fresh | fresh | 둘 다 따라왔다 |

중요한 점은 **badge가 맞다고 source 상세도 맞는 것이 아니고, source 상세가 맞다고 badge가 즉시 맞는 것도 아니라는 것**이다.

---

## 카운트 보장과 클릭 보장은 다르다

| 질문 | 대상 | 필요한 보장 | 흔한 시작 설계 |
|---|---|---|---|
| "배지 숫자가 얼마나 정확해야 하나?" | unread count read model | bounded staleness, correction, projection lag SLO | count projection watermark, 짧은 TTL, 재계산/보정 job |
| "알림 목록에서 방금 본 row가 뒤로 가도 되나?" | notification inbox row | monotonic reads 또는 `min_version` | row version floor, stale row suppress/patch |
| "알림을 누르면 원본이 보여야 하나?" | source detail | causal consistency | notification causal token, source watermark 확인, primary fallback |

배지는 대개 "몇 초까지 stale 허용" 같은 freshness budget으로 다룬다.
반대로 클릭 후 source 상세는 "알림이 요구한 watermark보다 오래된 응답을 보여 주면 안 된다"는 식으로 다룬다.

```pseudo
function openNotification(notification):
  token = notification.causalToken
  detail = readSourceWithWatermark(notification.sourceId, token.requiredWatermark)
  return detail

function getBadge(user):
  count = unreadCountProjection.get(user)
  return { count, projectionWatermark, generatedAt }
```

두 함수가 같은 이벤트에서 출발해도 계약은 다르다.
`getBadge`가 잠깐 늦는 것은 UX 품질 문제일 수 있지만, `openNotification`이 token보다 오래된 source를 보여 주는 것은 causal contract 위반이다.

---

## 댓글 알림 예시

### 1. 새 댓글이 생성된다

```text
comment:777 created
thread:42 version=18
commit watermark=9001
```

notification payload에는 source로 돌아갈 단서가 들어간다.

```json
{
  "type": "comment_created",
  "source_id": "thread:42/comment:777",
  "causal_token": {
    "required_watermark": 9001,
    "entity_version": 18
  }
}
```

### 2. 배지 projection은 별도로 따라온다

badge read model은 `user:5 unread_count += 1`을 반영해야 한다.
하지만 이 projection은 queue lag, cache TTL, collapse 정책 때문에 잠깐 늦을 수 있다.

```text
badge response
- unread_count = 0
- projection_watermark = 8998
```

이 상태에서도 source 댓글 자체가 사라진 것은 아니다.
배지 projection이 아직 `9001`까지 따라오지 않았다는 뜻이다.

### 3. 알림 클릭은 badge가 아니라 token을 믿는다

사용자가 push나 알림 목록 row를 눌렀다면 source 상세 요청은 badge count를 기준으로 판단하지 않는다.
notification이 들고 온 causal token을 기준으로 cache/replica/primary를 고른다.

```text
GET /threads/42/comments/777
required_watermark = 9001

cache watermark = 8995    -> reject
replica watermark = 8999  -> fallback
primary/source = 9001+    -> accept
```

즉, badge가 아직 `0`이어도 클릭한 source 상세는 보일 수 있어야 한다.
반대로 badge가 `1`이라고 해서 source 상세를 아무 replica에서 읽어도 된다는 뜻은 아니다.

---

## 흔한 혼동

- `배지가 1이면 원본 상세도 반드시 fresh하다`고 보면 안 된다. 배지는 count projection이고 source 상세는 별도 read path다.
- `causal token을 넣었으니 unread count도 정확해진다`고 보면 안 된다. token은 클릭 후 source read를 보호하지, count projection lag를 자동으로 없애지 않는다.
- `배지를 source DB에서 매번 count하면 해결된다`고 단정하면 안 된다. fan-out count는 비싸고, 읽음 처리와 collapse 정책까지 섞이면 병목이 될 수 있다.
- `배지가 틀렸으니 이벤트 유실이다`라고 바로 판단하면 안 된다. 먼저 projection lag, cache TTL, read receipt 처리 지연을 봐야 한다.
- `상세가 causal하게 보이면 배지는 중요하지 않다`도 과하다. 배지 숫자가 오래 틀리면 사용자는 계속 새 알림이 있다고 오해하므로 별도 SLO가 필요하다.

---

## 가장 작은 설계 모양

beginner 단계에서는 아래처럼 두 계약을 분리해서 말하면 충분하다.

| 영역 | 최소 필드 | 최소 정책 |
|---|---|---|
| badge/count read model | `unread_count`, `projection_watermark`, `generated_at` | count lag가 예산을 넘으면 stale 표시, refresh, 재계산 |
| notification payload | `source_id`, `causal_token.required_watermark` | 클릭 request까지 token 전달 |
| source read path | cache/replica `watermark`, response `version` | token 미달 cache/replica는 거절하고 fallback |
| read receipt/mark-read | `read_at`, `notification_id`, count correction delta | count decrement와 source read 성공을 느슨하게 연결하되 보정 가능하게 기록 |

한 문장으로 줄이면 이렇다.

> 배지는 projection freshness로 운영하고, 클릭 후 상세는 causal freshness로 보호한다.

---

## 관측성도 따로 본다

badge 문제와 source 문제를 같은 metric 하나로 보면 원인 분리가 어렵다.

| 증상 | 먼저 볼 metric/log |
|---|---|
| 배지가 오래 틀림 | `badge_projection_lag_ms`, `badge_count_correction_total`, `badge_cache_age_ms` |
| 목록에는 row가 있는데 배지가 0 | notification row watermark와 badge projection watermark 차이 |
| 배지는 1인데 상세가 404/stale | source read `required_watermark`, rejected hit reason, primary fallback 여부 |
| 읽었는데 배지가 다시 살아남 | mark-read event lag, decrement/idempotency key, correction job delta |

source 상세의 rejected cache hit, replica fallback, no-fill 이유는 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)에서 이어서 보면 된다.

---

## 더 깊이 가려면

- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Notification 시스템 설계](./notification-system-design.md)

---

## 면접/시니어 질문 미리보기

> Q: unread badge가 stale해도 notification click source는 반드시 보여야 한다고 말하는 이유는 무엇인가요?
> 의도: summary read model의 freshness budget과 source-detail causal contract를 구분하는지 확인
> 핵심: badge는 요약 projection이라 bounded stale을 허용할 수 있지만, click source는 사용자가 이미 본 notification의 dependency를 만족해야 한다.

> Q: badge count를 정확하게 만들면 source stale 문제가 해결되나요?
> 의도: read model freshness와 source read path freshness를 분리하는지 확인
> 핵심: 아니다. count projection이 fresh해도 source detail replica/cache가 causal token을 만족하지 못하면 클릭 후 stale/404가 날 수 있다.

> Q: 가장 작은 구현 시작점은 무엇인가요?
> 의도: 과한 global consistency 없이 두 계약을 나눠 설계하는지 확인
> 핵심: badge response에는 projection watermark와 generated time을 두고, notification click에는 source causal token을 전달해 cache/replica watermark를 검사한다.

---

## 한 줄 정리

notification badge/count는 "요약 read model의 freshness" 문제이고, notification click source는 "결과를 봤으면 원인도 보여야 하는 causal freshness" 문제라서 서로 독립적으로 설계하고 관측해야 한다.
