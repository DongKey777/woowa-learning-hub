# Session Policy Implementation Sketches

> 한 줄 요약: session policy는 거창한 마법이 아니라, `recent-write`, `min-version`, `write-sequence` 같은 작은 힌트 봉투를 gateway가 꺼내고 app이 해석하고 database가 실제 read/write 조건으로 집행하는 방식으로 시작하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Cache Hit/Miss Session Policy Bridge](./cache-hit-miss-session-policy-bridge.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [system design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: session policy implementation sketches, session policy hint propagation, gateway app database hint propagation, gateway app db pseudo code, recent-write min-version write-sequence, recent write min version write seq, session hint envelope, session context propagation, freshness hint propagation, write sequence propagation beginner, beginner session guarantee code example, gateway repository database routing, session policy implementation sketches basics, session policy implementation sketches beginner, session policy implementation sketches intro

---

## 핵심 개념

가장 쉬운 mental model은 **힌트 봉투**다.

- gateway: 봉투를 꺼내서 request context에 넣고, 응답 뒤 다시 저장한다
- app: 봉투를 읽고 "이번 요청은 얼마나 신선해야 하나"를 정책으로 바꾼다
- database/repository: 그 정책을 primary fallback, version floor, sequence check 같은 실제 조건으로 집행한다

이 힌트 봉투가 cache 앞에서 어떻게 살아남아야 하는지에만 집중해서 보고 싶다면 [Cache Hit/Miss Session Policy Bridge](./cache-hit-miss-session-policy-bridge.md)를 먼저 읽으면 된다.

즉 session policy는 DB에 갑자기 생기는 기능이 아니라, **요청이 들고 다니는 힌트가 끊기지 않게 만드는 설계**다.

---

## 먼저 힌트 세 개만 잡기

| 힌트 | 뜻 | 가장 쉬운 시작 형태 | 주로 쓰는 순간 |
|---|---|---|---|
| `recent-write` | 방금 write했으니 stale read를 더 조심해야 함 | `recent_write_until(cart:123)=12:00:03` | write 직후 read |
| `min-version` | 이미 본 버전보다 뒤로 가면 안 됨 | `min_version(cart:123)=17` | 상세 -> 목록 -> 확인 화면 |
| `write-sequence` | 같은 세션 write 순서를 뒤집지 말아야 함 | `write_seq(cart:123)=42` | 수량 변경 -> 쿠폰 -> 결제 |

짧게 외우면:

- `recent-write`는 "지금은 더 신선한 길로 보내라"
- `min-version`은 "이 버전 아래로는 내려가지 마라"
- `write-sequence`는 "내 write 순서를 뒤집지 마라"

---

## 한 장 그림으로 보기

```text
session store / cookie
  -> gateway restores SessionHints
  -> app turns hints into ReadPolicy / WritePolicy
  -> repository/db enforces primary fallback / version floor / seq check
  -> app returns updated hints
  -> gateway persists updated hints
```

| 레이어 | read path에서 하는 일 | write path에서 하는 일 |
|---|---|---|
| gateway | 세션에서 힌트를 꺼내 request context에 넣음 | 현재 `write_seq`를 싣고, 성공 응답 뒤 새 힌트를 저장 |
| app | `recent-write`, `min-version`을 read policy로 바꿈 | entity key를 정하고, `write_seq`를 repository에 넘기고, 성공 후 힌트를 갱신 |
| database / repository | replica 결과가 `min-version` 미만이면 버리고 fallback | `last_applied_seq = expected_seq - 1` 같은 조건으로 순서를 집행 |

이 구조를 먼저 잡아 두면, 나중에 cache, replica, queue, session store가 추가돼도 역할이 덜 헷갈린다.

---

## 공통 context 스케치

아래처럼 힌트를 한 객체에 모아 두면 예시를 읽기 쉽다.

```pseudo
struct SessionHints {
  recentWriteUntilByKey: Map<Key, Instant>
  minVersionByKey: Map<Key, Long>
  nextWriteSeqByKey: Map<Key, Long>
}
```

핵심은 이름보다 의미다.

- `recentWriteUntilByKey["cart:123"] = 12:00:03`
- `minVersionByKey["cart:123"] = 17`
- `nextWriteSeqByKey["cart:123"] = 42`

이 값들을 request마다 다시 계산해서 잃어버리지 말고, gateway와 app이 같은 봉투를 이어서 본다고 생각하면 된다.

---

## Sketch 1. recent-write + min-version read path

장바구니 수량을 바꾼 직후 `GET /carts/123`을 읽는다고 해 보자.
여기서는 "방금 write했나?"와 "이미 본 version보다 뒤로 가면 안 되나?" 두 질문을 같이 본다.

### Gateway

```pseudo
function gatewayHandle(request):
  hints = sessionStore.load(request.sessionId) or SessionHints.empty()
  request.context.key = routeKey(request)        # e.g. "cart:123"
  request.context.hints = hints

  response = app.handle(request)

  sessionStore.save(request.sessionId, response.updatedHints)
  return response.httpResponse
```

gateway의 일은 business rule을 판단하는 것이 아니라, 힌트 봉투를 **꺼내고 다시 넣는 것**이다.

### App

```pseudo
function getCart(request):
  key = request.context.key
  hints = request.context.hints

  readPolicy = ReadPolicy(
    requirePrimary = now() < hints.recentWriteUntilByKey.getOrDefault(key, MIN_TIME),
    minVersion = hints.minVersionByKey.getOrDefault(key, 0)
  )

  cart = cartRepository.read(key, readPolicy)

  hints.minVersionByKey[key] = max(
    hints.minVersionByKey.getOrDefault(key, 0),
    cart.version
  )

  return Response(cart, updatedHints = hints)
```

app은 세션 용어를 repository가 이해할 수 있는 **구체 규칙**으로 바꾼다.

- `recent-write`는 `requirePrimary` 같은 route bias로 변환
- `min-version`은 read 결과가 만족해야 할 floor로 변환

### Database / Repository

```pseudo
function read(key, policy):
  if policy.requirePrimary:
    return primary.queryCart(key)

  row = replica.queryCart(key)
  if row != null and row.version >= policy.minVersion:
    return row

  return primary.queryCart(key)
```

## Sketch 1. recent-write + min-version read path (계속 2)

여기서 database layer가 session policy 이름 전체를 알 필요는 없다.
필요한 것은 아래 두 조건뿐이다.

- 지금 primary를 강제해야 하는가
- replica 결과가 `min-version`을 만족하는가

---

## Sketch 2. write-sequence mutation path

이번에는 `수량 변경 -> 쿠폰 적용 -> 결제`처럼 write 순서가 중요한 흐름을 보자.
beginner 단계에서는 `write-sequence`를 session store에서 들고 가는 예시가 가장 단순하다.

### Gateway

```pseudo
function gatewayHandleMutation(request):
  hints = sessionStore.load(request.sessionId) or SessionHints.empty()
  key = routeKey(request)                        # e.g. "cart:123"
  seq = hints.nextWriteSeqByKey.getOrDefault(key, 1)

  request.context.key = key
  request.context.hints = hints
  request.context.writeSeq = seq

  response = app.handle(request)

  if response.writeApplied:
    hints.nextWriteSeqByKey[key] = seq + 1
    hints.recentWriteUntilByKey[key] = now() + 3 seconds
    hints.minVersionByKey[key] = max(
      hints.minVersionByKey.getOrDefault(key, 0),
      response.entityVersion
    )

  sessionStore.save(request.sessionId, hints)
  return response.httpResponse
```

이 예시는 client가 아니라 gateway/session store가 `nextWriteSeq`를 들고 있는 단순 버전이다.
실무에서는 client-generated seq를 쓰기도 하지만, 입문 단계에서는 이 쪽이 설명이 쉽다.

### App

```pseudo
function updateCartQty(request):
  result = cartRepository.applyChange(
    key = request.context.key,
    expectedSeq = request.context.writeSeq,
    newQty = request.body.qty
  )

  if result == OUT_OF_ORDER:
    return Http409("missing or duplicated earlier write")

  return Response(
    body = result.cart,
    writeApplied = true,
    entityVersion = result.version,
    updatedHints = request.context.hints
  )
```

app의 역할은 `write-sequence`를 DB까지 **그대로 끌고 내려가고**, 성공 시 다음 read를 위한 힌트도 같이 올려 보내는 것이다.

## Sketch 2. write-sequence mutation path (계속 2)

### Database / Repository

```pseudo
function applyChange(key, expectedSeq, newQty):
  row = primary.execute("""
    UPDATE carts
       SET qty = :newQty,
           version = version + 1,
           last_applied_write_seq = :expectedSeq
     WHERE cart_id = :key
       AND last_applied_write_seq = :expectedSeq - 1
     RETURNING version, qty
  """)

  if row == null:
    return OUT_OF_ORDER

  return row
```

이 조건이 막는 것은 단순 duplicate만이 아니다.

- `42` 다음에 와야 할 `43`이 먼저 들어오는 경우
- 이미 처리한 `42`를 다시 보내는 경우
- 이전 write가 빠진 상태에서 늦은 write가 들어오는 경우

즉 `write-sequence`는 database layer에서 **순서 조건**으로 닫힌다.

---

## Sketch 3. 세 힌트가 한 흐름에서 이어지는 모습

```text
1. PATCH /carts/123/items/A
   - gateway attaches write_seq=42
   - db applies seq 42, returns version=17

2. gateway persists
   - next_write_seq(cart:123)=43
   - recent_write_until(cart:123)=now+3s
   - min_version(cart:123)=17

3. GET /carts/123
   - gateway restores those hints
   - app builds ReadPolicy(requirePrimary=true, minVersion=17)
   - replica result older than v17 is rejected
   - user does not see older cart state
```

이 흐름이 session policy의 핵심이다.

- write가 끝나면 `recent-write`와 `min-version`이 생긴다
- 다음 write를 위해 `next_write_seq`도 같이 올라간다
- 다음 read는 그 힌트를 보고 stale replica를 피한다

즉 read policy와 write ordering은 따로 놀지 않고, **같은 세션 봉투 안에서 이어진다**.

---

## 흔한 오해

- `recent-write`는 load balancer sticky session이 아니다. app 인스턴스 affinity와 DB freshness routing은 다른 문제다.
- `min-version`은 "정확히 version 17만 읽어라"가 아니라 "17 아래로는 내려가지 마라"는 floor다.
- `write-sequence`는 idempotency key와 다르다. 전자는 순서, 후자는 같은 요청 재시도 식별에 더 가깝다.
- gateway가 business rule을 다 알아야 하는 것은 아니다. beginner 설계에서는 hint restore/persist만 해도 충분하다.
- database가 `session_policy=checkout` 같은 이름을 몰라도 된다. 실제로는 `requirePrimary`, `minVersion`, `expectedSeq` 같은 concrete 조건만 알면 된다.

---

## 다음 문서로 이어 보기

- read path freshness를 cache hit/miss/refill까지 이어 보고 싶다면 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- 어떤 보장 묶음을 고를지 먼저 정리하고 싶다면 [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- `write-sequence`를 queue, fence, idempotency와 더 구분하고 싶다면 [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- 오래된 read를 근거로 save하는 문제까지 이어서 보고 싶다면 [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)

---

## 한 줄 정리

session policy 구현의 beginner 출발점은 "gateway가 힌트를 꺼내고, app이 정책으로 바꾸고, database가 그 정책을 조건으로 집행한다"는 세 줄 계약을 먼저 세우는 것이다.
