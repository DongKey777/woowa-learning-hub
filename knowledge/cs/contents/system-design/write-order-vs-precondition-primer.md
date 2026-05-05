---
schema_version: 3
title: Write Order vs Precondition Primer
concept_id: system-design/write-order-vs-precondition-primer
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- ordering-vs-precondition
- stale-read-vs-out-of-order-write
- if-match-vs-sequence
aliases:
- write order vs precondition primer
- monotonic writes vs version check
- monotonic writes vs if-match
- session write ordering vs expected version
- checkout ordering vs cart version
- sequence number vs version column
- idempotency key vs expected version
- write sequence vs etag
- monotonic writes beginner confusion
- writes-follow-reads beginner confusion
- 처음 시스템 설계 배우는데 write order precondition 차이
- if-match가 순서 보장을 해주나요
- version check만 있으면 순서도 안전한가요
- stale save 막기와 write ordering 차이
- 언제 sequence를 쓰고 언제 if-match를 쓰나요
symptoms:
- If-Match를 붙였는데도 저장 순서가 꼬일 수 있는지 모르겠어
- version 체크만 하면 checkout 순서도 안전한 줄 알았어
- stale save 막기랑 write ordering 보장을 자꾸 같은 문제로 봐
intents:
- definition
prerequisites:
- system-design/writes-follow-reads-primer
- system-design/monotonic-writes-ordering-primer
next_docs:
- system-design/conditional-write-status-code-bridge
- system-design/session-guarantees-decision-matrix
- system-design/session-policy-implementation-sketches
linked_paths:
- contents/system-design/conditional-write-status-code-bridge.md
- contents/system-design/monotonic-writes-ordering-primer.md
- contents/system-design/writes-follow-reads-primer.md
- contents/system-design/session-guarantees-decision-matrix.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/session-policy-implementation-sketches.md
- contents/database/compare-and-set-version-columns.md
- contents/design-pattern/aggregate-version-optimistic-concurrency-pattern.md
confusable_with:
- system-design/writes-follow-reads-primer
- system-design/monotonic-writes-ordering-primer
- system-design/conditional-write-status-code-bridge
forbidden_neighbors:
- contents/system-design/monotonic-writes-ordering-primer.md
expected_queries:
- write 순서 보장과 version check는 무엇이 다르고 왜 둘 다 필요할 수 있어?
- If-Match가 있으면 같은 흐름의 요청 순서까지 안전하다고 봐도 돼?
- checkout 요청 순서 문제와 stale 화면 저장 문제를 어떻게 구분해 설명하지?
- sequence number를 붙여야 할 상황과 expected_version을 붙여야 할 상황을 비교해줘
- monotonic writes와 optimistic lock을 beginner 관점에서 나란히 설명해줘
- 같은 write 흐름에서 precondition check와 ordering guard를 함께 두는 이유가 궁금해
contextual_chunk_prefix: |
  이 문서는 같은 흐름의 write 순서 보장과 예전 상태 기준 저장 차단을
  어떻게 구분해야 하는지 처음 잡는 primer다. 줄 서는 순서 보호, 오래된
  화면 기준 저장 막기, checkout 순서 뒤집힘과 stale save 나눠 보기,
  sequence와 If-Match의 질문 차이, 순서 보장과 입장 자격 검사를 함께
  이해하기 같은 자연어 paraphrase가 본 문서의 비교 축에 매핑된다.
---
# Write Order vs Precondition Primer

> 한 줄 요약: monotonic writes는 "같은 흐름의 write 두 개가 서버에서 순서대로 적용되나?"를 묻고, version/precondition check는 "내가 보고 판단한 상태가 아직 유효할 때만 이 write를 받나?"를 묻는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)
- [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)
- [Aggregate Version and Optimistic Concurrency Pattern](../design-pattern/aggregate-version-optimistic-concurrency-pattern.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: write order vs precondition primer, monotonic writes vs version check, monotonic writes vs if-match, session write ordering vs expected version, checkout ordering vs cart version, sequence number vs version column, idempotency key vs expected version, write sequence vs etag, monotonic writes beginner confusion, writes-follow-reads beginner confusion, 처음 시스템 설계 배우는데 write order precondition 차이, if-match가 순서 보장을 해주나요, version check만 있으면 순서도 안전한가요, stale save 막기와 write ordering 차이, 언제 sequence를 쓰고 언제 if-match를 쓰나요

---

## 핵심 개념

## 이 문서가 먼저 맞는 질문

- "처음 배우는데 `If-Match`랑 write 순서 보장이 뭐가 다른지 헷갈려요"
- "optimistic lock이 있으면 checkout 요청 순서도 안전한 거 아닌가요?"
- "언제 `expected_version`을 붙이고, 언제 sequence/order key를 붙여야 하나요?"

가장 쉬운 mental model은 질문을 둘로 나누는 것이다.

- monotonic writes: "write A 다음에 write B를 보냈다면, 서버도 A 다음 B로 적용하나?"
- version/precondition check: "나는 version 12를 보고 저장을 눌렀는데, 지금도 아직 version 12일 때만 저장하나?"

짧게 기억하면:

- monotonic writes는 **write끼리의 순서**
- precondition check는 **write가 기대한 read 기준선**

둘 다 write 쪽 이야기라서 헷갈리지만, 막는 사고가 다르다.

| 질문 | 필요한 보호 장치 | 대표 힌트 |
|---|---|---|
| "첫 번째 변경보다 두 번째 변경이 먼저 적용되면 안 된다" | monotonic writes | `session_write_seq`, order key, per-key queue |
| "내가 본 화면이 이미 낡았다면 저장을 막아야 한다" | version/precondition check | `If-Match`, `expected_version`, version column |

---

## 먼저 두 장면으로 보기

### 장면 1. checkout 흐름

```text
1. 장바구니 수량 변경
2. 쿠폰 적용
3. checkout
```

여기서 주된 질문은 "3번이 1번보다 먼저 적용되면 안 되지 않나?"다.
이건 monotonic writes 질문이다.

하지만 같은 checkout 흐름에도 다른 질문이 있다.

```text
사용자가 cart version 12를 보고 할인 가능 여부를 판단했다
그 사이 다른 탭에서 수량이 바뀌어 version 13이 됐다
이제 예전 계산으로 checkout을 받아도 되나?
```

이건 version/precondition check 질문이다.

즉 checkout은 종종 둘 다 필요하다.

### 장면 2. 관리자 설정 화면

```text
관리자 A가 policy version 7 화면을 열어 둔다
관리자 B가 먼저 정책을 바꿔 version 8이 된다
관리자 A가 예전 화면으로 다시 저장한다
```

여기서 먼저 터지는 문제는 "예전 화면 기준 저장"이다.
이건 version/precondition check가 핵심이다.

반대로 관리자가 같은 정책에 대해 아래처럼 연속 명령을 보내는 경우도 있다.

```text
1. role 제거
2. access token 강제 만료
3. audit log 기록
```

이 흐름은 후속 write가 앞선 write보다 먼저 적용되면 안 된다.
이건 monotonic writes 쪽 질문이다.

---

## 한눈에 비교

| 구분 | monotonic writes | version/precondition check |
|---|---|---|
| 먼저 묻는 질문 | "내 write 두 개가 순서대로 적용되나?" | "내가 본 상태가 아직 유효할 때만 저장되나?" |
| 기준선 | 이전 write의 순서 | 이전 read에서 본 version/ETag |
| 대표 문제 | `checkout`이 `coupon apply`보다 먼저 적용 | 오래 열린 admin 화면이 최신 정책을 덮어씀 |
| 대표 힌트 | `session_write_seq`, queue, fence | `If-Match`, `expected_version`, `WHERE version = ?` |
| 실패 응답 의미 | gap, stale sequence, out-of-order write | version mismatch, precondition failed |
| 혼자서는 못 막는 것 | stale read를 근거로 한 잘못된 저장 | 서로 다른 write의 적용 순서 뒤집힘 |

표를 한 문장으로 줄이면 이렇다.

> monotonic writes는 "줄 서는 순서"를 지키고, precondition check는 "입장 자격"을 검사한다.

---

## checkout 예시: 왜 둘 다 필요한가

아래 흐름을 보자.

```http
PATCH /carts/123/items/A
X-Session-Write-Seq: 41
Idempotency-Key: cart-123:41:update-qty
If-Match: "cart-v12"
```

```http
POST /carts/123/coupons
X-Session-Write-Seq: 42
Idempotency-Key: cart-123:42:coupon
If-Match: "cart-v13"
```

```http
POST /carts/123/checkout
X-Session-Write-Seq: 43
Idempotency-Key: cart-123:43:checkout
If-Match: "cart-v14"
```

여기서 각 필드의 역할은 다르다.

| 필드 | 보는 질문 | 막는 문제 |
|---|---|---|
| `X-Session-Write-Seq` | "이 write가 몇 번째인가?" | `43`이 `42`보다 먼저 적용되는 문제 |
| `Idempotency-Key` | "같은 요청 재시도인가?" | timeout 뒤 같은 checkout 중복 실행 |
| `If-Match` | "내가 본 cart version이 아직 유효한가?" | 다른 탭 변경을 모르고 예전 계산으로 저장 |

checkout 흐름을 이렇게 분리해서 보지 않으면 흔히 두 가지 오해가 생긴다.

- "`If-Match`만 있으면 순서도 안전하다"
- "`sequence`만 있으면 예전 장바구니 기준 저장도 막힌다"

둘 다 틀리다.

### checkout에서 생기는 서로 다른 실패

| 실패 장면 | 무엇이 빠졌나 | 설명 |
|---|---|---|
| `checkout(43)`이 `coupon(42)`보다 먼저 적용 | monotonic writes | checkout 순서 보호가 없어서 write time line이 뒤집힘 |
| 사용자가 본 cart `v12`는 낡았는데 저장을 받아 버림 | precondition check | stale read 기반 계산을 막지 못함 |
| 같은 checkout 재시도가 두 번 결제 시도 | idempotency | 중복 요청 흡수가 없음 |

---

## 관리자 예시: 무엇을 먼저 붙여야 하나

관리자 화면은 초보자가 monotonic writes를 과하게 붙이기 쉬운 영역이다.
하지만 대부분의 첫 번째 문제는 "오래 열린 화면"이다.

### 예시 1. 정책 편집 화면

```text
관리자 A가 policy v7을 본다
관리자 B가 policy를 수정해 v8이 된다
관리자 A가 여전히 v7 기준으로 저장을 누른다
```

이 경우 가장 작은 시작 설계는 아래다.

- `GET /policies/42` 응답에 `ETag: "policy-v7"`
- `PATCH /policies/42` 요청에 `If-Match: "policy-v7"`
- mismatch면 저장 거절 후 최신 정책 재조회

여기서는 "관리자 A의 첫 저장" 자체가 문제이지, "A의 write 두 개 순서"가 핵심은 아니다.
즉 먼저 붙일 것은 version/precondition check다.

### 예시 2. 권한 제거 후 후속 조치

```text
1. 관리자 권한 제거
2. 기존 세션 revoke
3. 감사 로그 기록
```

이 흐름은 순서가 중요하다.
`2`나 `3`이 `1`보다 먼저 적용되면 보안 설명이 어색해진다.
이때는 account/admin 대상 key 기준으로 monotonic writes를 붙이는 쪽이 맞다.

짧게 정리하면:

- **화면 저장 충돌**은 precondition check 우선
- **연속 운영 명령 순서**는 monotonic writes 우선

---

## 초보자용 판단 질문

새 write 흐름을 보면 아래 순서로 물으면 된다.

1. 이 write가 사용자가 방금 본 값, 버전, 재고, 권한을 근거로 계산됐나?
2. 그렇다면 `If-Match`나 `expected_version` 같은 precondition이 필요한가?
3. 같은 세션이나 같은 aggregate가 연속 write를 짧게 여러 번 보내나?
4. 그렇다면 `session_write_seq`나 per-key queue가 필요한가?
5. 재시도로 같은 요청이 반복될 수 있나?
6. 그렇다면 idempotency key도 같이 두었나?

이 체크리스트를 적용하면 "write 쪽 문제"를 한 덩어리로 보지 않게 된다.

---

## 흔한 혼동

- `version`이 올라간다고 해서 write 순서가 자동 보장되지는 않는다. version mismatch는 stale save를 잡지만, 서로 다른 write의 도착 순서를 정해 주지 않는다.
- `409`, `412`, `428`은 모두 write 거절처럼 보이지만 이유가 다르다. precondition이 없으면 `428`, precondition이 stale하면 `412`, 최신 상태 기준으로도 명령 자체가 충돌하면 `409`로 갈리는 경우가 많다.
- `sequence`가 있다고 해서 stale read 기반 저장이 안전해지지는 않는다. 순서 표지는 "언제 봤는가"가 아니라 "몇 번째 write인가"를 말한다.
- checkout 같은 흐름은 둘 중 하나만 고르는 문제가 아니다. 순서 보호와 stale-read 보호를 같이 볼 수 있다.
- admin 화면도 항상 precondition만 보면 되는 것은 아니다. 화면 저장은 version check가 중심이지만, revoke나 disable 같은 후속 운영 명령 체인은 monotonic writes가 필요할 수 있다.

---

## 같이 쓰는 최소 조합

| 흐름 | 최소 조합 | 이유 |
|---|---|---|
| 장바구니 수량 변경 -> 쿠폰 -> checkout | `session_write_seq` + idempotency + `If-Match` | 순서, 중복, stale cart 기준 계산을 함께 보호 |
| 관리자 정책 편집 | `If-Match` 또는 `expected_version` | 오래 열린 화면 overwrite를 먼저 막음 |
| 관리자 권한 제거 -> 세션 revoke -> 감사 기록 | order key/sequence + idempotency | 후속 운영 write가 앞서지 않게 함 |
| 협업 문서 autosave | version check + 필요 시 document write seq | stale save와 역순 autosave 둘 다 가능 |

---

## 더 깊이 가려면

- [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
- [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)
- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)

## 한 줄 정리

write 설계에서 먼저 갈라야 할 질문은 두 개다: "내 write들이 순서대로 적용되나?"는 monotonic writes이고, "내가 본 상태가 아직 유효할 때만 저장되나?"는 version/precondition check다.
