---
schema_version: 3
title: Notification Inbox Row Monotonicity Primer
concept_id: system-design/notification-inbox-row-monotonicity-primer
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- inbox-row-version-floor
- badge-row-detail-split
- row-regression-after-refresh
aliases:
- notification inbox row monotonicity primer
- notification inbox row monotonicity
- inbox row version floor
- notification row version floor
- notification row min-version floor
- badge summary row detail bridge
- notification unread count row regression
- clicked notification source detail monotonicity
symptoms:
- 알림 inbox에서 방금 본 row가 새로고침 후 더 예전 상태로 내려가
- badge 숫자는 맞는데 row 내용이 뒤로 가서 더 헷갈려
- row freshness와 source detail causal read를 같은 규칙으로 보고 있어
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- system-design/notification-badge-vs-source-freshness-primer
- system-design/monotonic-reads-and-session-guarantees-primer
next_docs:
- system-design/notification-read-to-min-version-bridge
- system-design/list-detail-monotonicity-bridge
- system-design/notification-causal-token-walkthrough
linked_paths:
- contents/system-design/notification-badge-vs-source-freshness-primer.md
- contents/system-design/notification-read-to-min-version-bridge.md
- contents/system-design/notification-causal-token-walkthrough.md
- contents/system-design/list-detail-monotonicity-bridge.md
- contents/system-design/monotonic-reads-and-session-guarantees-primer.md
- contents/system-design/rejected-hit-observability-primer.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
confusable_with:
- system-design/notification-badge-vs-source-freshness-primer
- system-design/list-detail-monotonicity-bridge
- system-design/notification-read-to-min-version-bridge
forbidden_neighbors:
- contents/system-design/notification-badge-vs-source-freshness-primer.md
expected_queries:
- 알림 inbox row가 새로고침 후 예전 상태로 내려가면 어떤 보장을 봐야 해?
- badge freshness랑 inbox row monotonicity는 어떻게 달라?
- notification row version floor를 초보자 기준으로 설명해줘
- 클릭 전 inbox row가 뒤로 가는 문제를 min version으로 어떻게 막아?
- badge는 맞는데 row 내용만 stale할 때 어떤 층이 깨진 거야?
contextual_chunk_prefix: |
  이 문서는 학습자가 notification 경험을 badge summary, inbox row, clicked
  source detail 세 층으로 나누고 그중 inbox row가 뒤로 가지 않게 하는
  monotonicity를 이해하게 돕는 beginner primer다. badge는 맞는데 row가
  내려감, 새로고침하니 방금 본 상태가 뒤집힘, row와 source detail 규칙을
  같은 것으로 봐서 헷갈림 같은 자연어 질문이 본 문서의 row version floor
  설명으로 매핑된다.
---
# Notification Inbox Row Monotonicity Primer

> 한 줄 요약: notification badge는 요약 숫자라 조금 stale할 수 있어도, inbox row는 사용자가 이미 본 row version 아래로 내려가면 안 되고, 그 row를 눌러 들어간 source 상세는 row가 전제로 한 원인을 이어서 보여 줘야 한다.

retrieval-anchor-keywords: notification inbox row monotonicity primer, notification inbox row monotonicity, inbox row version floor, notification row version floor, notification row min-version floor, notification row min version floor, notification inbox monotonic reads, badge summary row detail bridge, badge summary row source detail, notification badge inbox row source detail, notification unread count row regression, clicked notification source detail monotonicity, notification row causal token bridge, notification inbox row monotonicity primer basics, notification inbox row monotonicity primer beginner

**난이도: 🟢 Beginner**

관련 문서:

- [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)
- [Notification Read to Min-Version Bridge](./notification-read-to-min-version-bridge.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 먼저 잡을 mental model

알림 경험을 세 층으로 나누면 훨씬 덜 헷갈린다.

| 화면 | 쉬운 말 | 가장 중요한 약속 |
|---|---|---|
| badge summary | "새 알림이 몇 개 있나" | 숫자가 조금 늦을 수는 있어도 곧 보정된다 |
| inbox row | "무슨 일이 있었나" | 내가 이미 본 row가 더 오래된 요약으로 뒤집히지 않는다 |
| clicked source detail | "그래서 원본 화면은 무엇을 보여 주나" | row가 전제로 한 원인 데이터를 이어서 보여 준다 |

이 문서의 핵심은 가운데다.

> badge는 요약 신호이고, clicked source는 causal read다.
> inbox row monotonicity는 그 둘 사이에서 "이미 본 알림 row가 뒤로 가지 않게" 붙여 주는 다리다.

즉 초보자용 한 줄 구분은 이렇게 외우면 된다.

- badge: count freshness
- inbox row: row version floor
- clicked source: causal token / required watermark

---

## 왜 badge만 보고 설계하면 부족한가

배지가 `1`이라고 해서 inbox row나 source 상세가 자동으로 맞는 것은 아니다.

| 보이는 증상 | 실제로 깨진 층 | 먼저 떠올릴 장치 |
|---|---|---|
| 배지가 `1`인데 목록에는 아직 새 row가 없다 | badge summary projection | count correction, projection watermark |
| inbox row에서 `결제 완료(v42)`를 봤는데 새로고침하니 `결제 대기(v40)`로 내려간다 | inbox row monotonicity | `row version floor`, stale row reject |
| row를 눌렀더니 주문 상세가 아직 `PENDING`이거나 404다 | clicked source detail | `causal token`, `required watermark` |

중요한 점은 세 층이 서로 연결되지만, 같은 규칙 하나로 끝나지 않는다는 것이다.

- badge는 "숫자가 조금 늦어도 되는가"를 본다.
- inbox row는 "이미 본 row가 뒤로 가는가"를 본다.
- clicked source는 "row가 말한 원인을 실제 상세가 따라왔는가"를 본다.

---

## 가장 작은 concrete example

주문 결제 알림을 예로 들자.

```text
source write
- order:123 status=PAID
- order version=42
- commit watermark=9001

notification projections
- badge unread_count=1
- inbox row summary = "주문 123 결제 완료", row_version=42
```

사용자 흐름은 보통 이렇게 간다.

```text
1. 앱 상단 badge에서 unread_count=1을 본다
2. inbox를 열어 "주문 123 결제 완료(v42)" row를 본다
3. 잠시 뒤 inbox를 다시 열거나 새로고침한다
4. row를 눌러 주문 상세로 들어간다
```

여기서 막아야 하는 실패는 두 개다.

| 실패 | 사용자 체감 | 필요한 보호 |
|---|---|---|
| row regression | 2번에서 `결제 완료`를 봤는데 3번에서 `결제 대기`로 내려감 | inbox row floor |
| source missing/stale | 2번의 row를 눌렀는데 4번 상세는 아직 `PENDING` 또는 404 | causal token / watermark routing |

즉 inbox row monotonicity는 "badge 다음, click 이전"에서 끝나는 이야기가 아니라, **row에서 본 최신선을 detail 진입과 다시 연결하는 중간 규칙**이다.

---

## row version floor는 무엇을 기억하나

가장 단순한 시작점은 사용자가 본 row의 하한선을 세션에 올리는 것이다.

```text
seen row
- notification:555
- source_id=order:123
- row_version=42
- row_summary="결제 완료"
```

세션이나 BFF는 아래처럼 기억할 수 있다.

```text
min_row_version(notification:555)=42
min_source_version(order:123)=42
last_seen_row_summary(notification:555)="결제 완료"
```

초보자 단계에서는 둘 다 완벽히 나눌 필요는 없다.
다만 실무적으로는 이렇게 이해하면 안전하다.

| 기억하는 값 | 쓰는 이유 |
|---|---|
| `min_row_version(notification:555)` | 같은 inbox row가 더 낮은 요약으로 내려가지 않게 함 |
| `min_source_version(order:123)` | row를 눌렀다가 다시 목록으로 와도 source 상태가 역행하지 않게 함 |
| `last_seen_row_summary(...)` | stale 후보를 잠깐 숨기거나 overlay할 때 마지막으로 본 문구를 유지 |

핵심은 `raise-only`다.
한 번 `42`를 봤으면 나중에 `40`을 받았다고 floor를 내리면 안 된다.

---

## badge, row, detail을 한 흐름으로 이어 보기

### 1. badge는 floor를 직접 만들지 않는다

badge는 보통 count projection이다.

```text
badge response
- unread_count=1
- projection_watermark=8998
```

이 숫자는 "새 알림이 있을 가능성"을 알려 주지만, 어떤 row가 몇 버전인지 직접 말해 주지 않는다.
그래서 badge 자체를 row floor로 쓰면 안 된다.

### 2. inbox row를 본 순간 floor가 생긴다

inbox API가 아래 row를 줬다고 하자.

```text
notification row
- notification_id=555
- source_id=order:123
- row_version=42
- summary="주문 123 결제 완료"
- causal_token.required_watermark=9001
```

이 row를 렌더링했다면 세션은 최소한 `42` 아래로는 내려가지 않게 기억할 수 있다.

```text
ctx.raiseRowVersion(notification:555, 42)
ctx.raiseSourceVersion(order:123, 42)
```

### 3. 새 후보 row가 floor보다 낮으면 그대로 채택하지 않는다

새로고침 뒤 cache/replica가 오래된 row를 줬다.

```text
candidate row
- notification_id=555
- row_version=40
- summary="주문 123 결제 대기"
```

이때 규칙은 단순하다.

```text
candidate.row_version < min_row_version(notification:555)
-> stale row
-> reject + patch/overlay/suppress
```

beginner 단계에서는 아래 셋 중 하나만 고르면 된다.

| 처리 방식 | 사용자에게 보이는 결과 | 언제 무난한가 |
|---|---|---|
| `row patch` | 더 신선한 row를 다시 읽어 교정 | row 수가 적고 정확한 상태가 중요할 때 |
| `last-seen overlay` | 방금 본 `"결제 완료"` 문구를 잠깐 유지 | 짧은 projection lag를 부드럽게 숨길 때 |
| `suppress + 갱신 중` | 오래된 row를 숨기거나 stale 표식을 붙임 | 대량 inbox에서 row patch 비용이 클 때 |

### 4. row click은 summary가 아니라 causal token을 믿는다

row를 눌러 상세로 갈 때는 summary text가 아니라 causal token을 넘긴다.

```text
GET /orders/123
- required_watermark=9001
- min_source_version(order:123)=42
```

즉 clicked source detail은 두 질문을 함께 본다.

## badge, row, detail을 한 흐름으로 이어 보기 (계속 2)

| 질문 | 왜 필요한가 |
|---|---|
| `required_watermark`를 만족하는가 | row가 말한 원인을 실제 상세가 따라왔는지 확인 |
| `version >= min_source_version`인가 | 이미 본 source 상태보다 뒤로 가지 않게 확인 |

이렇게 해야 "row는 결제 완료인데 상세는 아직 대기" 같은 끊김을 줄일 수 있다.

---

## 초보자용 한 장 표

| 층 | 대표 필드 | stale 허용 방식 | 깨졌을 때 첫 대응 |
|---|---|---|---|
| badge summary | `unread_count`, `projection_watermark` | bounded stale 허용 가능 | refresh, correction, TTL |
| inbox row | `row_version`, `summary`, `source_id` | 이미 본 row 아래로 후퇴 불가 | floor compare 후 reject/patch/overlay |
| clicked source detail | `required_watermark`, `entity_version` | row가 전제한 원인 누락 불가 | cache reject, replica fallback, primary read |

짧게 말하면:

- badge는 "조금 늦어도 되는 숫자"
- row는 "뒤로 가면 안 되는 문구"
- detail은 "정말 그 일이 있었는지 확인하는 원본"

---

## 흔한 혼동 5개

- `badge가 1이면 row도 fresh하다`
  - 아니다. count projection과 row projection은 따로 늦을 수 있다.
- `row만 fresh하면 상세는 아무 replica에서 읽어도 된다`
  - 아니다. row click은 causal token이나 watermark 검사를 계속 가져가야 한다.
- `row floor만 있으면 badge 숫자도 자동으로 맞는다`
  - 아니다. floor는 row regression 방지 장치이고 count correction을 대신하지 않는다.
- `detail에서 성공적으로 열렸으니 inbox row floor는 필요 없다`
  - 아니다. 상세에서 돌아와 다시 inbox를 열었을 때 row가 더 오래된 문구로 내려갈 수 있다.
- `candidate row가 오래돼도 일단 보여 주고 나중에 고치면 된다`
  - 이 예외가 사용자가 가장 먼저 보는 UX 사고가 된다. `candidate < floor`는 그대로 채택하지 않는 편이 안전하다.

---

## 관측성도 세 층으로 나눠 본다

운영에서는 세 층을 한 metric으로 합치면 원인 분리가 어렵다.

| 증상 | 먼저 볼 metric/log |
|---|---|
| badge 숫자가 오래 틀림 | `badge_projection_lag_ms`, `badge_count_correction_total` |
| inbox row가 뒤로 감 | `notification_row_rejected_below_floor_total`, `row_overlay_served_total` |
| row click 후 상세가 stale/404 | `notification_click_required_watermark`, `source_fallback_total`, `rejected_hit_reason` |

초보자에게 가장 중요한 실무 감각은 이것이다.

> "알림이 이상하다"를 한 덩어리로 보지 말고, count 문제인지 row regression 문제인지 detail causal 문제인지 먼저 자른다.

---

## 30초 체크리스트

- badge response와 inbox row response를 같은 freshness 계약으로 설명하지 않는가
- inbox row에 `row_version` 또는 비교 가능한 monotonic marker가 있는가
- row를 렌더링한 뒤 세션/BFF가 `raise-only`로 floor를 올리는가
- floor 미달 row를 그대로 채택하지 않고 `patch / overlay / suppress` 중 하나로 처리하는가
- row click이 `required_watermark` 같은 causal 힌트를 source read까지 전달하는가
- 상세 성공 뒤 `min_source_version`을 다시 올려 inbox 복귀 시 역행을 막는가

---

## 한 줄 정리

notification inbox row monotonicity는 badge summary와 clicked source detail 사이에서 "이미 본 알림 row가 더 오래된 요약으로 뒤집히지 않게" 붙는 보호층이고, row floor와 causal token을 같이 이어야 알림 숫자, row 문구, 원본 상세가 서로 다른 시간선으로 갈라지지 않는다.
