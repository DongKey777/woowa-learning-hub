---
schema_version: 3
title: Browser Retry Refresh Duplicate Submit Mission Drill
concept_id: network/browser-retry-refresh-duplicate-submit-mission-drill
canonical: false
category: network
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- retry-refresh-duplicate-submit
- browser-devtools
- idempotency
- prg
aliases:
- browser retry refresh duplicate submit drill
- 브라우저 새로고침 중복 제출 드릴
- 504 뒤 다시 누르기 문제
- duplicate POST DevTools drill
- PRG idempotency browser drill
symptoms:
- 504나 timeout 뒤 사용자가 다시 버튼을 눌러도 되는지 헷갈린다
- 같은 POST가 두 번 보일 때 자동 재시도인지 새로고침인지 중복 제출인지 구분하지 못한다
- PRG나 idempotency key가 왜 필요한지 브라우저 Network 흐름과 연결하지 못한다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge
- network/browser-devtools-first-checklist-1minute-card
next_docs:
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
- network/post-redirect-get-prg-beginner-primer
- system-design/shopping-cart-checkout-consistency-mission-bridge
linked_paths:
- contents/network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/system-design/shopping-cart-checkout-consistency-mission-bridge.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
confusable_with:
- network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge
- system-design/shopping-cart-checkout-consistency-mission-bridge
- network/post-redirect-get-prg-beginner-primer
forbidden_neighbors:
- contents/network/browser-devtools-error-path-cors-vs-actual-401-403-bridge.md
expected_queries:
- 504 뒤 다시 누르기와 중복 제출을 문제로 연습하고 싶어
- 같은 POST가 두 번 보이면 자동 재시도인지 사용자 재클릭인지 어떻게 구분해?
- roomescape 예약 생성이나 shopping-cart checkout 중복 제출을 DevTools로 판단해줘
- PRG와 idempotency key가 브라우저 새로고침 문제와 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 browser retry refresh duplicate submit mission drill이다.
  504 timeout, same POST twice, user refresh, button reclick, PRG, idempotency
  key, duplicate reservation/order/payment 같은 미션 질문을 DevTools와 HTTP
  retry 판별 문제로 매핑한다.
---
# Browser Retry Refresh Duplicate Submit Mission Drill

> 한 줄 요약: 같은 요청이 두 번 보이면 "누가 다시 보냈는가"와 "서버 상태가 두 번 바뀌었는가"를 나눠야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
POST /orders가 504로 보인 뒤 사용자가 결제 버튼을 다시 눌렀다.
```

답:

중복 제출 위험이다. 첫 요청이 서버에서 성공했을 수 있으므로 idempotency key나 order/payment 상태 재조회가 필요하다.

## 문제 2

상황:

```text
POST /reservations 뒤 303 redirect로 GET /reservations/10이 보이고 사용자가 새로고침했다.
```

답:

PRG가 중복 POST 위험을 줄인 장면이다. 새로고침이 마지막 `GET`을 반복하므로 같은 reservation 생성 POST를 다시 보내지 않는다.

## 문제 3

상황:

```text
GET /products가 짧은 간격으로 두 번 보이고 첫 줄만 504다.
```

답:

조회성 재시도 후보로 먼저 본다. 그래도 자동 재시도라고 단정하지 말고 initiator, timing, method를 확인한다.

## 빠른 체크

| 신호 | 먼저 볼 질문 |
|---|---|
| 같은 `POST` 두 번 | business duplicate risk |
| `POST -> 303 -> GET` | PRG flow |
| 같은 `GET` 두 번 | retry/cache/refresh split |
| 같은 idempotency key | replay-safe retry 가능성 |
