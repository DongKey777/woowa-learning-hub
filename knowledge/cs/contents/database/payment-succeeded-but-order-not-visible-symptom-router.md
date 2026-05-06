---
schema_version: 3
title: 결제는 성공했는데 주문이 안 보여요 원인 라우터
concept_id: database/payment-succeeded-but-order-not-visible-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- post-payment-read-after-write-triage
- order-complete-stale-read
- projection-vs-primary-read-split
aliases:
- 결제 성공 뒤 주문 안 보임
- 주문 완료 화면 비어 있음 원인
- 결제 후 주문 상세가 안 보여요
- payment success but order missing
- 주문 직후 첫 조회만 비어요
symptoms:
- 결제는 성공했는데 주문 완료 화면이나 주문 상세에 방금 만든 주문이 안 보여요
- 주문 생성 API 응답은 200인데 바로 목록을 열면 방금 주문만 빠져 있어요
- 새로고침 한두 번 뒤에는 보이는데 리다이렉트 직후만 404 또는 빈 화면처럼 보여요
- 주문은 저장된 것 같은데 관리자 조회와 사용자 조회가 잠깐 서로 다른 결과를 보여요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- database/transaction-basics
- database/read-your-writes-session-pinning
next_docs:
- database/shopping-cart-order-complete-read-your-writes-bridge
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
- database/roomescape-admin-reservation-list-pagination-stability-bridge
linked_paths:
- contents/database/shopping-cart-order-complete-read-your-writes-bridge.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/roomescape-admin-reservation-list-pagination-stability-bridge.md
- contents/database/read-after-write-routing-decision-guide.md
- contents/database/pagination-duplicates-missing-symptom-router.md
confusable_with:
- database/shopping-cart-order-complete-read-your-writes-bridge
- database/pagination-duplicates-missing-symptom-router
- database/duplicate-key-then-not-found-symptom-router
forbidden_neighbors:
expected_queries:
- 결제 성공했는데 주문 완료 페이지가 비어 보이면 어디부터 확인해야 해?
- 주문 생성은 됐는데 바로 목록 조회에 안 보일 때 원인을 어떻게 나눠?
- 결제 직후만 404고 새로고침하면 보이는 주문 문제는 왜 생겨?
- shopping-cart에서 방금 주문한 내역이 첫 조회에만 빠질 때 무슨 문서로 가야 해?
- 사용자 화면과 관리자 화면의 주문 조회가 잠깐 다를 때 read-after-write를 먼저 의심해야 해?
contextual_chunk_prefix: |
  이 문서는 결제는 성공했는데 주문 완료 화면이나 주문 상세, 주문 목록 첫
  조회에서 방금 만든 주문이 안 보이는 학습자 증상을 read-after-write 경로,
  replica lag, projection/list 갱신 지연, 잘못된 조회 키나 상태 필터로 나눠
  주는 symptom_router다. 결제는 됐는데 주문 없음, 리다이렉트 직후만 비어 있음,
  새로고침하면 보임, 관리자와 사용자 화면이 잠깐 다름 같은 자연어 표현이
  주문 write 이후 첫 read 분기와 매핑된다.
---

# 결제는 성공했는데 주문이 안 보여요 원인 라우터

> 한 줄 요약: 결제 성공 뒤 주문이 안 보이면 "주문 저장 실패"로 바로 닫지 말고, 방금 쓴 주문을 첫 조회가 어디서 읽었는지부터 나눠야 한다.

**난이도: 🟡 Intermediate**

관련 문서:

- [shopping-cart 결제 직후 주문 조회 ↔ Read-After-Write 브릿지](./shopping-cart-order-complete-read-your-writes-bridge.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)
- [Read-After-Write 라우팅 결정 가이드](./read-after-write-routing-decision-guide.md)
- [페이지네이션 중복/누락 원인 라우터](./pagination-duplicates-missing-symptom-router.md)

retrieval-anchor-keywords: 결제 성공했는데 주문 안 보여요, payment success but order missing, 주문 직후 첫 조회 비어요, 새로고침하면 주문 보여요 why, read after write order missing, replica lag order page, 주문 완료 페이지 404 직후, 관리자 사용자 주문 다르게 보여요, order complete empty after redirect, 첫 페이지 주문 누락 basics

## 핵심 개념

결제 성공 뒤 주문이 안 보인다는 증상은 보통 "write가 실패했다"보다 "첫 read가 다른 경로를 탔다"에 가깝다. 특히 주문 상세 단건 조회인지, 목록 projection인지, replica를 읽는지에 따라 원인이 달라진다. 그래서 이 문서는 `write 성공 여부`보다 `직후 read의 위치와 시점`을 먼저 분기한다.

## 한눈에 보기

| 지금 보이는 장면 | 먼저 확인할 질문 | 다음 문서 |
| --- | --- | --- |
| 리다이렉트 직후 단건 상세만 `404`거나 비어 있음 | 첫 조회가 replica나 일반 read path였나? | [shopping-cart 결제 직후 주문 조회 ↔ Read-After-Write 브릿지](./shopping-cart-order-complete-read-your-writes-bridge.md) |
| 상세는 보이는데 목록/완료 화면만 늦게 보임 | projection, 캐시, 요약 테이블이 늦었나? | [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md) |
| 관리자 화면과 사용자 화면이 잠깐 다름 | 두 화면이 같은 source of truth를 읽나? | [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md) |
| 주문은 있는데 첫 페이지에서만 빠짐 | 정렬, cursor, 상태 필터가 흔들리나? | [페이지네이션 중복/누락 원인 라우터](./pagination-duplicates-missing-symptom-router.md) |

## 가능한 원인

1. **직후 조회가 replica나 일반 read path를 탔다.** 주문 생성은 primary에 commit됐지만 리다이렉트된 첫 `GET /orders/{id}`나 목록 조회가 replica를 타면 아직 최신 주문이 안 보일 수 있다. 이 갈래는 [shopping-cart 결제 직후 주문 조회 ↔ Read-After-Write 브릿지](./shopping-cart-order-complete-read-your-writes-bridge.md)와 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 바로 이어진다.
2. **주문 상세는 source of truth인데 화면은 projection이나 목록 인덱스를 본다.** 결제 직후 상세 row는 이미 생겼어도 목록용 projection, 캐시, 요약 테이블은 뒤늦게 갱신될 수 있다. 사용자 화면과 관리자 화면이 잠깐 다르면 이 분기를 먼저 보고, [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)와 [roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지](./roomescape-admin-reservation-list-pagination-stability-bridge.md)로 내려간다.
3. **조회 key나 상태 필터가 write arbitration key와 다르다.** 결제는 성공했지만 조회는 `status=COMPLETED`만 보거나 다른 사용자 scope, 다른 정렬 커서로 읽어서 방금 주문을 놓칠 수 있다. 이 경우는 [Read-After-Write 라우팅 결정 가이드](./read-after-write-routing-decision-guide.md)에서 fresh read 보장과 조회 조건을 같이 맞춘다.
4. **문제의 본질이 row 부재가 아니라 첫 페이지/window drift다.** 주문은 존재하지만 첫 페이지 정렬 기준이 불안정하거나 cursor/offset 경계가 흔들려 "안 보인다"로 느껴질 수 있다. 새로고침 때마다 위치가 바뀌거나 어떤 페이지에서는 보이는데 첫 화면에서만 사라지면 [페이지네이션 중복/누락 원인 라우터](./pagination-duplicates-missing-symptom-router.md)로 이동한다.

## 빠른 자기 진단

1. 결제 직후 비는 화면이 상세 단건 조회인지, 목록/첫 페이지 조회인지 먼저 나눈다. 단건이면 fresh read 경로를, 목록이면 projection 또는 pagination 경로를 더 먼저 본다.
2. 첫 조회가 primary인지 replica인지 확인한다. primary로 강제하면 바로 보이면 replica lag나 recent-write routing 문제다.
3. 상세는 보이는데 목록만 비면 projection/cursor/정렬 문제를 의심한다. 상세도 목록도 둘 다 비면 조회 key나 상태 필터가 write와 어긋났는지 본다.
4. 같은 주문이 새로고침 후엔 보이면 다시 결제를 보내지 말고 read path를 고정한다. 계속 안 보이면 `order_id`, 사용자 scope, `status` 조건이 실제 저장된 row와 같은지 대조한다.

## 자주 헷갈리는 지점

- 결제 성공 뒤 주문이 안 보인다고 해서 곧바로 "DB에 저장 안 됐다"로 결론내리면 안 된다. 새로고침 뒤 보인다면 저장 실패보다 fresh read 미보장이 더 흔하다.
- 상세와 목록이 다르게 보이면 둘 중 하나가 틀렸다고 단정하면 안 된다. 상세는 primary row를, 목록은 projection이나 캐시를 읽는 구조일 수 있다.
- `404`가 나왔다고 항상 잘못된 `order_id`라고 보면 안 된다. 리다이렉트 직후만 `404`고 조금 뒤엔 보이면 read-after-write 창 문제일 수 있다.

## 다음 학습

- 결제 직후 첫 조회를 왜 따로 설계해야 하는지 보려면 [shopping-cart 결제 직후 주문 조회 ↔ Read-After-Write 브릿지](./shopping-cart-order-complete-read-your-writes-bridge.md)를 본다.
- recent write 사용자의 짧은 strict read window를 어떻게 보장할지 보려면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 간다.
- replica lag와 primary fallback 전략 전체를 다시 정리하려면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)를 읽는다.
- 실제로는 목록 window가 흔들린 경우라면 [페이지네이션 중복/누락 원인 라우터](./pagination-duplicates-missing-symptom-router.md)를 이어서 본다.

## 한 줄 정리

결제는 성공했는데 주문이 안 보이면 write를 다시 보내기 전에, 방금 만든 주문을 첫 read가 primary/replica/ projection/목록 window 중 어디에서 놓쳤는지부터 자르는 편이 빠르다.
