# Session Guarantees Decision Matrix

> 한 줄 요약: session guarantee는 "이 사용자가 지금까지 한 일과 본 것"을 기준선으로 들고 다니며, 제품 흐름마다 read-after-write, monotonic reads, writes-follow-reads, monotonic writes를 필요한 만큼 묶어 쓰는 정책이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

retrieval-anchor-keywords: session guarantees decision matrix, session guarantee policy bundle, session policy implementation sketches, gateway app db session hints, list-detail-search monotonicity, list detail monotonicity bridge, list detail search min-version floor, read-after-write monotonic reads writes-follow-reads monotonic writes, writes-follow-reads beginner, monotonic writes beginner, monotonic writes ordering primer, session write sequence primer, idempotency key vs sequence number, monotonic writes vs version check, product flow consistency matrix, checkout session consistency, profile edit session guarantee, cart checkout monotonic writes, edit form if-match writes-follow-reads, per-session write ordering, per-session consistency policy, beginner session consistency, read your writes monotonic writes decision

---

## 핵심 개념

session guarantee는 "DB 전체를 항상 최신으로 보이게 하자"가 아니다.
한 사용자가 한 흐름 안에서 **방금 쓴 것, 이미 본 것, 그 다음에 쓰려는 것, 연속으로 보낸 write 순서**가 어색하게 깨지지 않게 하는 약속이다.

가장 쉬운 mental model은 네 개의 기준선을 세션이 들고 다닌다고 생각하는 것이다.

| 기준선 | 보장 이름 | 사용자가 기대하는 말 |
|---|---|---|
| 내가 방금 쓴 값 | read-after-write | "저장했으면 바로 보여야죠" |
| 내가 이미 본 최신값 | monotonic reads | "아까 `PAID`였는데 왜 다시 `PENDING`이죠?" |
| 내가 보고 나서 그 판단으로 쓰는 값 | writes-follow-reads | "방금 본 재고/버전을 기준으로 저장해야죠" |
| 내가 연속으로 보낸 write 순서 | monotonic writes | "첫 번째 변경보다 두 번째 변경이 먼저 적용되면 안 되죠" |

이 문서는 각 보장을 깊게 증명하기보다, 제품 흐름을 봤을 때 **어떤 보장을 한 묶음으로 고를지** 빠르게 판단하는 입문용 decision matrix다.

---

## 네 보장을 한 문장씩 구분하기

| 보장 | 막는 실패 | 가장 단순한 힌트 | 흔한 구현 시작점 |
|---|---|---|---|
| Read-after-write | 저장 성공 직후 옛값이나 404가 보임 | `recent_write_until`, written `entity_id` | 짧은 primary fallback, same-leader read |
| Monotonic reads | 한 세션에서 값이 과거로 되감김 | `min_version(key)`, last seen LSN | version 미달 cache/replica 거부 |
| Writes-follow-reads | 오래된 상태를 보고 그 위에 write를 얹음 | `if_match_version`, read watermark | optimistic lock, precondition check, fresher write route |
| Monotonic writes | 같은 세션 write 2개가 순서 뒤집혀 반영됨 | `session_write_seq`, idempotency/order key | per-session ordering, single writer queue, fenced retry |

초보자가 기억할 핵심은 이렇다.

- read-after-write와 monotonic reads는 주로 **read 경로**를 고르는 문제다.
- writes-follow-reads와 monotonic writes는 주로 **write를 받아도 되는 기준**을 확인하는 문제다.
- 네 보장은 서로 대체재가 아니라, 제품 흐름에 맞춰 조합하는 재료다.

---

## 제품 흐름별 Decision Matrix

| 제품 흐름 | 필요한 정책 묶음 | 왜 필요한가 | 시작 설계 |
|---|---|---|---|
| 프로필 저장 후 내 프로필 보기 | read-after-write | 저장 성공 직후 예전 닉네임이 보이면 저장 실패처럼 보임 | 최근 write한 사용자만 1~3초 primary fallback |
| 주문 생성 -> 상세 -> 목록 이동 | read-after-write + monotonic reads | 상세에는 새 주문이 보였는데 목록에서 사라지면 시간선이 깨짐 | 생성 직후 상세 primary, 이후 세션 `min_version(order)` 유지 |
| 결제 완료 -> 영수증 -> 주문 상태 확인 | read-after-write + monotonic reads | `PAID`를 본 뒤 `PENDING`으로 내려가면 중복 결제 행동을 유도함 | 결제/영수증 경로 strong read, 목록도 `min_version` 미달 결과 거부 |
| 장바구니 수량 변경 -> 쿠폰 적용 -> 결제 | writes-follow-reads + monotonic writes | 쿠폰 적용 write가 예전 장바구니를 기준으로 계산되거나 checkout이 add보다 먼저 처리되면 안 됨 | cart version `If-Match`, per-cart write sequence |
| 문서 편집 화면 열기 -> 수정 저장 | writes-follow-reads | 사용자가 본 version보다 오래된 version 위에 저장하면 다른 변경을 덮을 수 있음 | edit form에 version 포함, mismatch면 merge/reload 요구 |
| 이메일 변경 -> 인증 메일 재발송 -> 로그인 알림 | monotonic writes + read-after-write | 이메일 변경보다 재발송 write가 먼저 처리되면 잘못된 주소로 후속 작업이 감 | account 단위 write order key, 변경 직후 계정 read primary |
| 권한 제거 -> 접근 확인 -> 감사 로그 보기 | read-after-write + monotonic reads + monotonic writes | revoke write가 늦거나 확인 화면이 뒤로 가면 보안 경계가 흔들림 | revoke path strong write/read, audit/read model은 revoke version 하한 유지 |
| 알림 클릭 -> 원본 댓글/주문 열기 | causal consistency + monotonic reads | 알림이라는 결과를 봤는데 원인 데이터가 없거나 과거 상태로 보이면 혼란이 큼 | notification causal token, source read watermark 확인 |

이 표를 외울 필요는 없다.
새 기능을 설계할 때는 "이 흐름에서 사용자가 이전 행동을 근거로 다음 행동을 하나?"를 먼저 묻는다.
그 답이 yes라면 session guarantee 후보가 생긴다.

---

## 묶음 선택을 위한 빠른 질문

1. 사용자가 write 성공 직후 같은 데이터를 바로 보나?
   그러면 read-after-write를 넣는다.

2. 사용자가 여러 화면에서 같은 객체나 상태를 반복해서 보나?
   그러면 monotonic reads를 넣는다.

3. 사용자가 화면에서 본 version이나 잔액, 재고, 권한을 근거로 다음 write를 하나?
   그러면 writes-follow-reads를 넣는다.

4. 같은 세션이 짧은 시간에 관련 write를 여러 개 보내나?
   그러면 monotonic writes를 넣는다.

5. 알림, 이벤트, 승인 결과처럼 "결과"를 먼저 보고 source로 들어가나?
   그러면 causal consistency도 같이 본다.

---

## 정책 묶음 예시

### 1. 가벼운 설정 저장

```text
session_policy = profile_settings

- after POST /settings: read-after-write for /me and /settings
- keep min_version(user) while moving between settings pages
```

이 흐름은 금전 사고까지는 아니지만 UX 신뢰가 중요하다.
따라서 전체 strong consistency보다 짧은 fallback과 `min_version`이 현실적인 시작점이다.

### 2. 장바구니와 결제

```text
session_policy = checkout

- cart update uses If-Match: cart_version
- cart writes carry session_write_seq
- order confirmation uses read-after-write
- order list rejects versions older than already seen paid/order version
```

checkout은 read와 write가 섞인다.
장바구니 화면에서 본 상태를 기준으로 쿠폰/결제 write를 하므로 writes-follow-reads가 필요하고, `add -> coupon -> checkout` 순서가 뒤집히면 안 되므로 monotonic writes도 필요하다.

### 3. 협업 문서 저장

```text
session_policy = document_edit

- editor loads document_version=41
- save request includes If-Match: 41
- if current version is 42, reject with reload/merge path
```

여기서는 "방금 저장한 값이 보이나"보다 "내가 본 version 위에 안전하게 write하나"가 더 중요하다.
그래서 writes-follow-reads가 핵심이고, 저장 성공 뒤 다시 읽는 화면에는 read-after-write를 추가한다.

---

## 흔한 오해

- `session guarantee`는 로그인 세션 저장 방식이 아니다. app sticky session, cookie, JWT와는 다른 consistency 정책 이름이다.
- `read-after-write`만 켜면 충분하다고 보기 쉽다. 하지만 이미 본 값이 뒤로 가는 문제와, 오래된 read를 근거로 write하는 문제는 따로 남는다.
- `monotonic reads`는 write 순서를 보장하지 않는다. 같은 사용자의 write 순서를 지키려면 monotonic writes를 별도로 봐야 한다.
- `writes-follow-reads`는 모든 write를 막자는 뜻이 아니다. 사용자가 본 version을 기준으로 하는 write에 precondition을 붙이자는 뜻이다.
- `retry`는 ordering contract가 아니다. 중복 요청과 out-of-order apply를 막으려면 sequence, idempotency key, version check 같은 힌트가 필요하다.

---

## 더 깊이 가려면

- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)

## 한 줄 정리

session guarantee decision은 "얼마나 강한 DB를 쓸까"보다 "이 제품 흐름에서 사용자가 들고 다니는 기준선이 무엇인가"를 고르는 문제이고, 그 기준선에 따라 read-after-write, monotonic reads, writes-follow-reads, monotonic writes를 작게 묶어 적용한다.
