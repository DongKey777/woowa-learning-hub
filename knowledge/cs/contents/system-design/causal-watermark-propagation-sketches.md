---
schema_version: 3
title: Causal Watermark Propagation Sketches
concept_id: system-design/causal-watermark-propagation-sketches
canonical: false
category: system-design
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- causal watermark propagation sketches
- causal token watermark propagation
- required watermark propagation sketch
- observed watermark propagation beginner
aliases:
- causal watermark propagation sketches
- causal token watermark propagation
- required watermark propagation sketch
- observed watermark propagation beginner
- notification after read watermark carry
- event driven read watermark carry
- gateway app database watermark pseudo code
- gateway app db causal token pseudo code
- notification required watermark session context
- event signal causal token app flow
- successful causal read observed watermark
- watermark handoff after notification click
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/notification-causal-token-walkthrough.md
- contents/system-design/token-propagation-through-bff-and-gateway.md
- contents/system-design/notification-read-to-min-version-bridge.md
- contents/system-design/projection-applied-watermark-basics.md
- contents/system-design/watermark-metadata-persistence-basics.md
- contents/system-design/cache-acceptance-rules-for-causal-reads.md
- contents/system-design/session-policy-implementation-sketches.md
- contents/system-design/trace-attribute-freshness-read-source-bridge.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Causal Watermark Propagation Sketches 설계 핵심을 설명해줘
- causal watermark propagation sketches가 왜 필요한지 알려줘
- Causal Watermark Propagation Sketches 실무 트레이드오프는 뭐야?
- causal watermark propagation sketches 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Causal Watermark Propagation Sketches를 다루는 deep_dive 문서다. notification이나 event signal이 `required_watermark`를 들고 들어오면, gateway는 그 기준선을 복원하고, app은 후속 read policy로 번역하고, database/repository는 실제 비교를 집행한 뒤, 성공 응답의 `observed_watermark`를 다시 다음 요청용 힌트로 올려 보내야 한다. 검색 질의가 causal watermark propagation sketches, causal token watermark propagation, required watermark propagation sketch, observed watermark propagation beginner처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Causal Watermark Propagation Sketches

> 한 줄 요약: notification이나 event signal이 `required_watermark`를 들고 들어오면, gateway는 그 기준선을 복원하고, app은 후속 read policy로 번역하고, database/repository는 실제 비교를 집행한 뒤, 성공 응답의 `observed_watermark`를 다시 다음 요청용 힌트로 올려 보내야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Token Propagation Through BFF and Gateway](./token-propagation-through-bff-and-gateway.md)
- [Notification Read to Min-Version Bridge](./notification-read-to-min-version-bridge.md)
- [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)
- [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)
- [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
- [system design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: causal watermark propagation sketches, causal token watermark propagation, required watermark propagation sketch, observed watermark propagation beginner, notification after read watermark carry, event driven read watermark carry, gateway app database watermark pseudo code, gateway app db causal token pseudo code, notification required watermark session context, event signal causal token app flow, successful causal read observed watermark, watermark handoff after notification click, beginner causal propagation code example, system-design-00088, causal watermark propagation sketches basics

---

## 먼저 잡을 mental model

이 문서에서 가장 먼저 잡아야 할 그림은 **입장권 + 도장**이다.

- `required_watermark`: "이 read는 최소 여기까지 따라온 결과만 보여 달라"는 입장권
- `observed_watermark`: "이번 read는 실제로 여기까지 반영된 값을 보여 줬다"는 도장

즉 notification이나 event signal이 주는 값은 출발점일 뿐이다.
실무에서 더 중요한 것은 아래 두 동작이 끊기지 않는가다.

1. 들어올 때 `required_watermark`를 복원했는가
2. 성공하고 나갈 때 `observed_watermark`를 다음 요청용 힌트로 다시 올렸는가

짧게 외우면 이렇다.

- 들어올 때: `required_watermark`
- 성공한 뒤: `observed_watermark`
- 다음 read에서 다시 쓸 때: `required_watermark = max(기존값, observed값)`

---

## 한 장 그림으로 보기

```text
notification / event signal
  -> gateway restores required_watermark
  -> app builds read policy
  -> repository checks cache / replica / primary
  -> response returns observed_watermark
  -> gateway/app stores raised watermark hint
  -> next list/detail/search read reuses that raised floor
```

| 레이어 | 들어올 때 하는 일 | 성공 응답 뒤 하는 일 |
|---|---|---|
| gateway / app entry | deep link, push payload, SSE event에서 `required_watermark` 복원 | session/app memory/header에 올린 watermark를 저장 |
| app / BFF | `required_watermark`를 read policy로 번역 | `observed_watermark`로 다음 요청용 floor를 raise-only 갱신 |
| database / repository | cache/replica/primary가 기준선을 만족하는지 비교 | 응답 metadata에 실제 `observed_watermark`를 넣어 줌 |

핵심은 database가 혼자 모든 걸 해결하는 게 아니라, **입구와 출구 모두에서 봉투를 다뤄야 한다**는 점이다.

---

## 공통 context 스케치

beginner 단계에서는 아래처럼 아주 작은 봉투 하나로 시작하면 된다.

```pseudo
struct CausalHints {
  requiredWatermarkByKey: Map<Key, Long>
  minVersionByKey: Map<Key, Long>
}
```

여기서 의미는 단순하다.

- `requiredWatermarkByKey["order:123"] = 9001`
- `minVersionByKey["order:123"] = 42`

이 문서의 중심은 `requiredWatermarkByKey`다.
`minVersionByKey`는 성공 응답 뒤 [Notification Read to Min-Version Bridge](./notification-read-to-min-version-bridge.md)와 연결되는 보조 축으로만 같이 둔다.

---

## Sketch 1. notification click에서 상세 read 열기

주문 결제 알림을 눌러 `GET /orders/123`으로 들어가는 가장 작은 흐름이다.

### Gateway

```pseudo
function gatewayHandle(request):
  hints = sessionStore.load(request.sessionId) or CausalHints.empty()
  key = routeKey(request)                       # e.g. "order:123"

  token = parseNotificationToken(
    query = request.query["ct"],
    header = request.header["X-Causal-Token"]
  )

  if token != null:
    hints.requiredWatermarkByKey[key] = max(
      hints.requiredWatermarkByKey.getOrDefault(key, 0),
      token.requiredWatermark
    )

  request.context.key = key
  request.context.hints = hints

  response = app.handle(request)

  sessionStore.save(request.sessionId, response.updatedHints)
  return response.httpResponse
```

gateway의 역할은 deep link나 header를 직접 읽을 수 없는 downstream을 위해,
외부 표현을 `CausalHints`라는 내부 봉투로 바꾸는 것이다.

### App / BFF

```pseudo
function getOrderDetail(request):
  key = request.context.key
  hints = request.context.hints

  readPolicy = ReadPolicy(
    requiredWatermark = hints.requiredWatermarkByKey.getOrDefault(key, 0),
    minVersion = hints.minVersionByKey.getOrDefault(key, 0)
  )

  order = orderRepository.read(key, readPolicy)

  hints.requiredWatermarkByKey[key] = max(
    hints.requiredWatermarkByKey.getOrDefault(key, 0),
    order.observedWatermark
  )
  hints.minVersionByKey[key] = max(
    hints.minVersionByKey.getOrDefault(key, 0),
    order.version
  )

  return Response(order, updatedHints = hints)
```

app이 하는 일은 두 가지다.

## Sketch 1. notification click에서 상세 read 열기 (계속 2)

- 들어온 `required_watermark`를 repository가 이해할 수 있는 read policy로 바꾼다
- 성공 응답이 준 `observed_watermark`와 `version`으로 세션 기준선을 더 높인다

### Database / Repository

```pseudo
function read(key, policy):
  entry = cache.get(key)
  if entry != null and entry.appliedWatermark >= policy.requiredWatermark:
    return Result(
      value = entry.value,
      version = entry.version,
      observedWatermark = entry.appliedWatermark
    )

  if replica.visibleWatermark(key) >= policy.requiredWatermark:
    row = replica.read(key)
  else:
    row = primary.read(key)

  return Result(
    value = row.value,
    version = row.version,
    observedWatermark = row.appliedWatermark
  )
```

repository의 책임은 `required_watermark`를 실제 비교식으로 닫는 것이다.
성공 응답 뒤에는 "읽었다"만 돌려주지 말고,
반드시 **어디까지 본 값인지**를 `observedWatermark`로 올려보내야 한다.

---

## Sketch 2. 성공한 상세 read 뒤 목록/검색으로 이어 주기

초보자가 자주 놓치는 지점은 여기다.

> notification click이 한 번 성공했다고 끝이 아니다.

그 다음 `GET /orders` 목록이나 `GET /orders/search`도 방금 본 watermark 아래로 내려가면 안 된다.

### Gateway

```pseudo
function gatewayHandleNextRead(request):
  hints = sessionStore.load(request.sessionId) or CausalHints.empty()
  key = request.query["focusKey"]              # e.g. "order:123"

  request.context.key = key
  request.context.hints = hints

  response = app.handle(request)
  sessionStore.save(request.sessionId, response.updatedHints)
  return response.httpResponse
```

### App / BFF

```pseudo
function getOrdersList(request):
  focusKey = request.context.key
  hints = request.context.hints

  listPolicy = ListReadPolicy(
    requiredWatermark = hints.requiredWatermarkByKey.getOrDefault(focusKey, 0),
    minVersion = hints.minVersionByKey.getOrDefault(focusKey, 0)
  )

  list = orderListRepository.read(request.userId, listPolicy)
  return Response(list, updatedHints = hints)
```

여기서 핵심은 목록도 같은 봉투를 읽는다는 점이다.
상세만 `required_watermark`를 알고, 목록은 모르면 `PAID -> PENDING` 같은 역행이 바로 생긴다.

### Database / Repository

```pseudo
function read(userId, policy):
  page = listCache.get(userId)

  if page != null and page.appliedWatermark >= policy.requiredWatermark:
    return patchOrAccept(page, policy.minVersion)

  if replica.visibleWatermark(userId) >= policy.requiredWatermark:
    page = replica.readOrderList(userId)
  else:
    page = primary.readOrderList(userId)

  return patchOrAccept(page, policy.minVersion)
```

## Sketch 2. 성공한 상세 read 뒤 목록/검색으로 이어 주기 (계속 2)

여기서는 `required_watermark`와 `min_version`이 같이 움직인다.

- `required_watermark`: 경로가 최소 어디까지 따라왔나
- `min_version`: 내가 이미 본 entity 상태보다 뒤로 가지 않나

즉 notification causal read와 monotonic guard는 따로가 아니라, **성공한 상세 뒤 한 봉투에서 이어지는 두 축**이다.

---

## Sketch 3. notification이 아니라 event signal일 때

이 흐름은 push notification이 없어도 똑같이 쓸 수 있다.
예를 들어 앱이 websocket/SSE 이벤트를 받아 "주문 상태가 변경됨"을 알고 화면 refresh를 하는 경우다.

### Gateway / Client Entry

```pseudo
function onOrderEvent(event):
  appMemory.raiseRequiredWatermark(
    key = event.orderId,
    watermark = event.requiredWatermark
  )
  navigate("/orders/" + event.orderId)
```

### App / BFF

```pseudo
function getOrderAfterEvent(request):
  key = request.path.orderId
  required = appMemory.requiredWatermarkFor(key)

  readPolicy = ReadPolicy(requiredWatermark = required)
  return orderRepository.read(key, readPolicy)
```

### Database / Repository

```pseudo
function readAfterEvent(key, policy):
  if projectionRow.appliedWatermark(key) >= policy.requiredWatermark:
    return projectionRow.read(key)

  return primary.read(key)
```

입력 경로만 다를 뿐, 정신 모델은 동일하다.

- event signal이 `required_watermark`를 들고 온다
- app/BFF가 그 값을 후속 read policy로 바꾼다
- repository가 `applied_watermark`와 비교한다

그래서 이 문서는 notification 전용 꼼수가 아니라, **"결과 신호를 먼저 본 뒤 source를 읽는 흐름" 전체에 쓸 수 있는 starter sketch**다.

---

## 자주 나오는 오해

- `required_watermark`는 notification click 한 번에만 쓰고 버리면 된다
  - 아니다. 성공 응답의 `observed_watermark`를 다시 저장하지 않으면 다음 목록/검색에서 같은 기준선을 잃는다.
- `observed_watermark`는 로그용 숫자다
  - 아니다. 다음 read의 lower bound를 올리는 재료다.
- `version`만 올리면 watermark는 없어도 된다
  - 둘의 질문이 다르다. version은 entity 역행 방지에 강하고, watermark는 경로가 어디까지 따라왔는지 설명하는 데 강하다.
- `gateway`는 token parse만 하면 끝이다
  - 아니다. 응답 뒤 raised watermark를 다시 저장하는 출구 역할도 한다.
- `event-driven refresh`는 notification보다 쉬우니 causal propagation이 필요 없다
  - 아니다. signal을 먼저 보고 source를 읽는 구조는 같으므로 동일한 stale 위험이 남는다.

---

## 30초 체크리스트

- notification, push, SSE, webhook callback 중 무엇이든 `required_watermark`를 후속 read 입력으로 복원하는가
- gateway/BFF가 외부 token을 내부 `CausalHints`나 표준 header/context로 normalize하는가
- repository가 cache/replica/primary에서 실제 `required <= applied` 비교를 하는가
- 성공 응답이 `observed_watermark`를 metadata로 돌려주는가
- gateway/app/session이 `observed_watermark`를 raise-only로 저장해 다음 요청에 다시 쓰는가
- 목록/검색/read model 경로도 같은 hint 봉투를 읽는가

---

## 한 줄 정리

causal-token propagation의 절반은 "입구에서 `required_watermark`를 복원하는 것"이고, 나머지 절반은 "성공 응답의 `observed_watermark`를 다시 저장해 다음 read까지 이어 주는 것"이다. gateway, app, database가 이 두 반쪽을 함께 맡아야 notification이나 event-driven read가 한 번만 맞고 끝나는 우연에 머물지 않는다.
