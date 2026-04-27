# Monotonic Writes Ordering Primer

> 한 줄 요약: monotonic writes는 "같은 세션이나 같은 사용자 흐름에서 먼저 보낸 write가 나중 write보다 먼저 적용되게 하자"는 약속이고, beginner 단계에서는 sequence number로 순서를 표시하고, idempotency key로 같은 write 재시도를 흡수하고, 필요하면 per-key queue나 fence로 적용 권한을 하나로 줄이는 식으로 시작하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Inventory Reservation System Design](./inventory-reservation-system-design.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [Distributed Lock 설계](./distributed-lock-design.md)
- [Payment System / Ledger / Idempotency / Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
- [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)
- [Aggregate Version and Optimistic Concurrency Pattern](../design-pattern/aggregate-version-optimistic-concurrency-pattern.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: monotonic writes ordering primer, monotonic writes beginner, monotonic writes 뭐예요, session policy implementation sketches, gateway app database write sequence, per-session write ordering, per-session ordering primer, session write sequence, session_write_seq, sequence number ordering primer, idempotency key vs sequence number, duplicate retry out of order write, same user write ordering, cart checkout write order, per-aggregate queue ordering, single writer queue beginner, fenced retry primer, write fence ordering, monotonic writes vs writes-follow-reads, monotonic writes vs version check, monotonic writes vs if-match, order key vs idempotency key, monotonic write guarantee, simple queue fence pattern

---

## 핵심 개념

가장 쉬운 mental model은 "한 사용자가 write마다 번호표를 들고 온다"라고 생각하는 것이다.

- `sequence number`는 "이 write가 몇 번째인가"
- `idempotency key`는 "이 write를 같은 요청으로 다시 보낸 것인가"
- `queue`나 `fence`는 "지금 누가 그 번호를 실제로 적용할 권한이 있는가"

예를 들어 장바구니 흐름이 이렇게 있다고 해 보자.

```text
41. 수량 변경
42. 쿠폰 적용
43. checkout
```

사용자는 분명 이 순서로 눌렀는데, 네트워크 지연이나 retry 때문에 서버 적용 순서가 `43 -> 41 -> 42`가 되면 제품 의미가 깨진다.
monotonic writes는 바로 이 문제를 막는 보장이다.

즉 질문은 이것이다.

> 같은 세션이 연속으로 보낸 write라면, 서버도 적어도 그 순서는 뒤집지 말아야 하지 않을까?

---

## 먼저 흐름으로 보기

beginner 단계에서는 아래 계약 하나만 잡아도 반쯤 이해한 것이다.

```text
각 write는 seq를 가진다
같은 write 재시도는 idempotency key를 재사용한다
서버는 "다음으로 기대한 seq"만 적용한다
```

장바구니 예를 HTTP로 적으면 이런 느낌이다.

```http
PATCH /carts/123/items/A
X-Session-Write-Seq: 41
Idempotency-Key: cart-123:41:update-qty-A-2

{
  "qty": 2
}
```

```http
POST /carts/123/coupons
X-Session-Write-Seq: 42
Idempotency-Key: cart-123:42:apply-SPRING10

{
  "couponCode": "SPRING10"
}
```

```http
POST /carts/123/checkout
X-Session-Write-Seq: 43
Idempotency-Key: cart-123:43:checkout
```

서버가 가장 단순하게 판단하면 이렇다.

- `41`이 오면 적용하고, 다음 기대값을 `42`로 올린다
- 같은 `41`이 같은 idempotency key로 다시 오면 이전 결과를 replay한다
- `43`이 `42`보다 먼저 오면 바로 적용하지 않고 queue에 잠깐 보관하거나 "중간 write가 비었다"고 거절한다

이 흐름이 monotonic writes의 beginner entry다.

---

## sequence number, idempotency key, queue/fence의 역할 구분

초보자가 가장 자주 헷갈리는 점은 "멱등성이 있으면 순서도 안전한 것 아닌가요?"다.
하지만 세 도구는 보는 질문이 다르다.

| 도구 | 답하는 질문 | 막는 문제 | 혼자서는 부족한 것 |
|---|---|---|---|
| `sequence number` | "몇 번째 write인가?" | 서로 다른 write의 순서 뒤집힘 | 같은 write 재시도 replay |
| `idempotency key` | "같은 write를 다시 보낸 것인가?" | timeout/retry로 인한 중복 실행 | 서로 다른 write 간 ordering |
| `per-key queue` | "같은 key의 write를 한 줄로 세울까?" | 동시 apply와 out-of-order consume | consumer failover 뒤 stale worker 실행 |
| `fence` token/epoch | "지금 이 writer가 아직 유효한 owner인가?" | 옛 worker나 옛 lease의 늦은 write | 세밀한 비즈니스 순서 표현 |

짧게 기억하면:

- sequence는 **순서 표지**
- idempotency key는 **중복 표지**
- queue는 **한 줄 세우기**
- fence는 **옛 권한 차단**

네 개를 같은 단어처럼 쓰면 설계가 흐려진다.

---

## 왜 idempotency key만으로는 부족한가

아래처럼 서로 다른 write 두 개를 생각하면 차이가 잘 보인다.

```text
1. 이메일 변경   (idempotency key = K1)
2. 인증 메일 재발송 (idempotency key = K2)
```

둘 다 서로 다른 요청이므로 idempotency key도 다르다.
이때 서버가 `K2`를 먼저 처리하면, 예전 이메일 주소를 기준으로 후속 작업이 실행될 수 있다.

즉 idempotency key는 이렇게만 보장한다.

- `K1`이 두 번 와도 한 번만 실행
- `K2`가 두 번 와도 한 번만 실행

하지만 아래는 보장하지 않는다.

- `K1` 다음에 `K2`가 적용되는가

그래서 monotonic writes가 필요한 흐름은 보통 **idempotency + ordering**을 같이 본다.

| 상황 | idempotency만 있을 때 | monotonic writes까지 있을 때 |
|---|---|---|
| 장바구니 수량 변경 -> checkout | checkout 중복 실행은 줄일 수 있음 | checkout이 수량 변경보다 먼저 적용되는 것도 막음 |
| 이메일 변경 -> 인증 메일 재발송 | 재발송 중복은 줄일 수 있음 | 예전 이메일 기준 재발송도 막음 |
| 권한 제거 -> 감사 이벤트 기록 | 같은 revoke 재시도는 흡수 가능 | revoke보다 먼저 후속 event가 기록되는 문제까지 줄임 |

---

## 가장 단순한 서버 규칙

beginner 설계는 대개 `last_applied_seq` 하나에서 시작한다.

```pseudo
state.lastAppliedSeq(cart123) = 40

handle(request):
  if request.seq <= state.lastAppliedSeq:
    if replayStore.has(request.idempotencyKey):
      return replayStore.result(request.idempotencyKey)
    return reject("stale or duplicate write")

  if request.seq == state.lastAppliedSeq + 1:
    result = apply(request)
    replayStore.save(request.idempotencyKey, result)
    state.lastAppliedSeq = request.seq
    return result

  if request.seq > state.lastAppliedSeq + 1:
    return reject_or_queue("gap before this write")
```

여기서 핵심은 세 가지다.

1. `last_applied_seq + 1`인 write만 바로 받는다.
2. 이미 처리한 같은 write는 idempotency key로 replay한다.
3. 중간 번호가 비면 무작정 apply하지 않는다.

이 규칙 하나만 있어도 "같은 세션에서 2번째 write가 1번째보다 먼저 적용되는 것"을 크게 줄일 수 있다.

---

## queue 패턴은 언제 쉬운가

가장 단순한 ordering 구현은 사실 "같은 key의 write를 한 줄로 세우는 것"이다.

예:

- `cart_id`별 queue
- `account_id`별 queue
- `document_id`별 single-writer partition

mental model은 이렇다.

> 같은 장바구니 관련 명령은 같은 창구 하나로만 들어간다.

| queue 패턴 장점 | 설명 |
|---|---|
| 이해가 쉽다 | 같은 key는 한 소비자가 순서대로 처리한다고 설명할 수 있다 |
| app 서버 동시성을 줄인다 | 여러 인스턴스가 같은 aggregate를 동시에 만지지 않게 한다 |
| seq gap 처리와 궁합이 좋다 | `41 -> 42 -> 43` 순서가 queue 자체에서 드러난다 |

하지만 queue만 믿으면 부족할 때도 있다.

- consumer가 죽었다가 재시작하며 같은 메시지를 다시 받을 수 있다
- failover 후 예전 consumer가 늦게 살아나 늦은 write를 보낼 수 있다
- queue는 순서를 지켜도 downstream side effect는 중복될 수 있다

그래서 queue를 써도 보통 idempotency key는 같이 둔다.

---

## fence 패턴은 무엇을 막나

fence는 "지금 write를 적용하는 주체가 아직 최신 owner인가?"를 확인하는 장치다.

가장 쉬운 예는 lease를 넘겨받은 worker 두 개가 겹치는 상황이다.

```text
worker A가 잠깐 멈춤
lease가 worker B로 넘어감
그 뒤 worker A가 늦게 깨어나 예전 명령을 다시 보냄
```

이때 queue만으로는 늦게 도착한 옛 worker write를 완전히 막기 어렵다.
그래서 더 최신 owner에게 더 큰 `fence token`이나 `epoch`를 준다.

```pseudo
UPDATE cart_state
SET last_seq = 42, writer_epoch = 9, coupon = 'SPRING10'
WHERE cart_id = 123
  AND writer_epoch = 9
  AND last_seq = 41
```

여기서 뜻은 두 개다.

- `last_seq = 41`이어야 하니 순서가 맞아야 한다
- `writer_epoch = 9`여야 하니 옛 owner는 못 쓴다

초보자용으로 줄이면:

- queue는 "한 줄 세우기"
- fence는 "옛 줄 관리자가 뒤늦게 끼어들지 못하게 막기"

둘은 비슷해 보여도 막는 실패가 다르다.

---

## monotonic writes와 writes-follow-reads는 왜 다를까

이 둘은 자주 같이 나오지만 질문이 다르다.

| 보장 | 질문 | 대표 힌트 |
|---|---|---|
| Writes-follow-reads | "내가 본 상태를 기준으로 이 write를 받아도 되나?" | `If-Match`, expected version |
| Monotonic writes | "내 write 두 개가 보낸 순서대로 적용되나?" | `session_write_seq`, order key, queue, fence |

장바구니 예로 보면:

- `cart_version=12`를 보고 쿠폰을 계산했다면 writes-follow-reads가 필요하다
- `수량 변경 -> 쿠폰 적용 -> checkout` 순서가 뒤집히면 안 되므로 monotonic writes도 필요하다

즉 하나는 **read 기준선 검증**이고, 다른 하나는 **write 순서 검증**이다.
checkout 같은 흐름은 둘 다 필요한 경우가 많다.

---

## 어떤 키 단위로 ordering할까

여기서 또 흔한 실수가 "모든 write에 전역 sequence를 두자"다.
보통은 너무 비싸고 필요도 없다.

초보자는 먼저 **같이 순서를 지켜야 하는 범위**를 고르면 된다.

| ordering scope | 잘 맞는 예 | 너무 넓게 잡으면 생기는 문제 |
|---|---|---|
| `session_id` | 같은 사용자의 짧은 wizard/checkout 흐름 | unrelated write까지 서로 기다리게 됨 |
| `cart_id` | 장바구니 수정, 쿠폰, checkout | 다른 cart와 상관없는 병렬성을 잃음 |
| `account_id` | 이메일 변경, 권한 변경, 인증 흐름 | profile edit와 notification preference가 불필요하게 묶일 수 있음 |
| `document_id` | autosave, publish, permission edit | 문서와 무관한 다른 작업까지 순서 제약을 걸 수 있음 |

보통은 "같이 섞이면 의미가 깨지는 aggregate" 단위부터 시작한다.

---

## 흐름별 시작 설계

| 흐름 | 가장 작은 시작 설계 | 이유 |
|---|---|---|
| 장바구니 수량 변경 -> 쿠폰 -> checkout | `cart_id` 단위 seq + idempotency key | 서로 다른 write가 제품 의미상 순서를 가져야 함 |
| 이메일 변경 -> 인증 메일 재발송 | `account_id` 단위 seq + replay-safe retry | 후속 작업이 이전 write 결과를 따라야 함 |
| 문서 autosave 연속 저장 | `document_id` 단위 seq + stale version check | 저장 순서와 stale overwrite 둘 다 문제일 수 있음 |
| 권한 제거 -> revoke event -> 감사 기록 | revoke seq + event idempotency + 필요 시 queue | 보안 경계에서 후속 작업이 앞설 수 없음 |

핵심은 "무조건 큐를 쓰자"가 아니다.
먼저 sequence와 idempotency로 계약을 분명히 하고, gap/동시성/실패 복구가 커질 때 queue나 fence를 붙이는 편이 이해도와 운영성이 좋다.

---

## 흔한 오해와 혼동

- `monotonic writes = strong consistency`는 아니다. 같은 세션이나 같은 key의 write 순서를 다루는 보장이지, 모든 read/write를 전역 최신으로 만들자는 뜻이 아니다.
- `idempotency key가 있으면 순서도 보장된다`는 오해가 많다. 멱등성은 중복 흡수이고, ordering은 서로 다른 write의 선후 관계다.
- `sequence number`를 전역 DB 카운터로 생각하면 너무 무거워지기 쉽다. 보통은 `cart_id`, `account_id`, `document_id` 같은 aggregate 범위가 더 현실적이다.
- `queue를 쓰면 끝`도 아니다. 재전송, consumer failover, downstream side effect 중복 때문에 idempotency와 fence가 여전히 필요할 수 있다.
- `retry`는 ordering contract가 아니다. timeout 뒤 재시도는 오히려 순서를 더 어지럽힐 수 있다.
- `writes-follow-reads`와 같은 말도 아니다. 전자는 read 기준선, 후자는 write 순서 기준선이다.

---

## 빠른 판단법

새 write 흐름을 보면 아래 순서로 물으면 된다.

1. 같은 사용자가 관련 write를 짧은 시간에 여러 개 보내나?
   그러면 monotonic writes 후보가 있다.
2. 서로 다른 write가 순서를 바꾸면 제품 의미가 깨지나?
   그러면 sequence number나 per-key queue가 필요하다.
3. 같은 write 재시도가 흔한가?
   그러면 idempotency key를 같이 둔다.
4. worker failover나 lease overlap이 있나?
   그러면 fence까지 본다.
5. write가 이전 read를 근거로 계산됐나?
   그러면 writes-follow-reads도 같이 본다.

이 다섯 질문이 monotonic writes 입문 판단의 가장 짧은 체크리스트다.

---

## 더 깊이 가려면

- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [Distributed Lock 설계](./distributed-lock-design.md)
- [Payment System / Ledger / Idempotency / Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
- [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
- [Aggregate Version and Optimistic Concurrency Pattern](../design-pattern/aggregate-version-optimistic-concurrency-pattern.md)

## 한 줄 정리

monotonic writes는 "내 write 두 개가 서버에서 같은 순서로 적용되게 하자"는 보장이고, beginner 단계에서는 `sequence number`로 순서를 표시하고, `idempotency key`로 같은 write 재시도를 흡수하고, 필요하면 `per-key queue`와 `fence`로 적용 경로를 하나로 줄이는 식으로 이해하면 된다.
