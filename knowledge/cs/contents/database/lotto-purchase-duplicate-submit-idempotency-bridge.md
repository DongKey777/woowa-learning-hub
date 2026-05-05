---
schema_version: 3
title: 'lotto 구매 재시도/중복 티켓 저장 ↔ 멱등성 키와 UNIQUE 브릿지'
concept_id: database/lotto-purchase-duplicate-submit-idempotency-bridge
canonical: false
category: database
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- purchase-idempotency
- duplicate-submit
- insert-first-arbitration
aliases:
- lotto 구매 중복 저장
- 로또 구매 재시도 중복 생성
- lotto purchase idempotency
- 로또 더블클릭 티켓 중복
- lotto duplicate ticket save
symptoms:
- 구매 버튼을 두 번 눌렀더니 같은 로또 세트가 두 번 저장돼요
- 응답이 늦어서 다시 요청했더니 purchase row와 ticket row가 둘 다 늘어났어요
- 중복 구매 방지를 service if 문으로만 했는데 새로고침 뒤 duplicate가 나요
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- software-engineering/lotto-purchase-flow-service-layer-bridge
- database/lotto-purchase-ticket-parent-child-modeling-bridge
- database/transaction-basics
next_docs:
- database/idempotency-key-and-deduplication
- database/unique-vs-locking-read-duplicate-primer
- database/lotto-purchase-ticket-parent-child-modeling-bridge
linked_paths:
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
- contents/database/lotto-purchase-ticket-parent-child-modeling-bridge.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/duplicate-key-vs-busy-response-mapping.md
confusable_with:
- database/idempotency-key-and-deduplication
- database/unique-vs-locking-read-duplicate-primer
- database/lotto-purchase-ticket-parent-child-modeling-bridge
forbidden_neighbors: []
expected_queries:
- 로또 구매 요청이 재전송되면 같은 티켓 묶음이 두 번 저장되지 않게 DB에서 어떻게 막아?
- lotto를 웹으로 옮겼더니 새로고침 뒤 purchase와 ticket이 중복 생성돼. 어떤 제약을 먼저 봐야 해?
- 구매 내역이 한 번만 생겨야 하는데 exists 확인 후 save로는 왜 부족해?
- 로또 자동 구매 요청이 timeout 뒤 재시도될 때 같은 구매를 재생할 수 있게 만들려면?
- 로또 구매 중복을 락으로만 막지 말고 멱등성 키를 두라는 리뷰는 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션을 웹과 DB로 확장할 때 구매 요청 재시도나
  더블클릭 때문에 같은 purchase와 ticket 묶음이 두 번 저장되는 문제를
  멱등성 키와 UNIQUE 제약으로 설명하는 mission_bridge다. 로또 구매 중복 저장,
  timeout 뒤 재전송, 새로고침 duplicate, service if문으로만 중복 방지,
  같은 구매를 한 번만 인정하고 이전 결과를 재사용하기 같은 학습자 표현을
  insert-first arbitration과 dedup 관점으로 매핑한다.
---

# lotto 구매 재시도/중복 티켓 저장 ↔ 멱등성 키와 UNIQUE 브릿지

## 한 줄 요약

> lotto 구매 한 번은 "금액을 내고 여러 티켓 묶음을 확정한 요청"이다. 웹으로 옮기면 같은 요청이 재전송될 수 있으므로, `exists` 확인 뒤 저장하기보다 `idempotency_key`나 구매 요청 키를 `UNIQUE`로 잠가 DB가 한 번만 승자를 정하게 하는 편이 덜 흔들린다.

## 미션 시나리오

콘솔 lotto에서는 사용자가 Enter를 한 번 치면 구매 흐름도 한 번 끝난다. 하지만 웹으로 확장하면 구매 버튼 더블클릭, timeout 뒤 재시도, 새로고침 재전송 때문에 같은 "10,000원 구매" 요청이 두 번 들어올 수 있다. 이때 서비스가 먼저 "`이미 구매했나?`"를 조회하고 없으면 `purchase`와 `ticket`을 저장하는 식이면, 두 요청이 같은 빈 상태를 보고 둘 다 통과할 수 있다.

리뷰에서 "`중복 구매 확인을 if문으로만 두지 말고 DB가 같은 요청을 한 번만 인정하게 하세요`"라는 말이 나오는 자리가 여기다. 문제의 핵심은 티켓 번호 생성 로직보다 "이번 요청이 새 구매인지, 방금 성공한 같은 구매의 재전송인지"를 닫는 기준이다.

## CS concept 매핑

여기서 닿는 개념은 멱등성 키와 insert-first arbitration이다. 예를 들어 `purchase_request(idempotency_key)`에 `UNIQUE`를 두고, 먼저 그 row를 선점한 요청만 `purchase`와 `ticket` 자식 row를 만들게 하면 된다.

```sql
INSERT INTO purchase_request (idempotency_key, status)
VALUES (?, 'PENDING');
```

이 insert가 성공한 요청만 실제 구매를 진행하고, 같은 키로 다시 온 요청은 duplicate key를 보고 "이미 처리 중" 또는 "이미 성공한 구매 결과"를 읽어 재생할 수 있다. 중요한 점은 `purchase` 1건과 `ticket` 여러 건의 1:N 모델링과, "같은 구매 요청을 한 번만 인정한다"는 dedup 계약이 다른 축이라는 것이다. 전자는 구조 문제이고 후자는 요청 identity 문제다.

## 미션 PR 코멘트 패턴

- "`existsBy...` 후 `save()` 패턴은 재전송 경쟁에서 둘 다 통과할 수 있습니다."
- "구매 한 번의 identity를 금액이나 티켓 번호로 추측하지 말고, 요청 키를 별도로 두세요."
- "중복 요청을 락으로 오래 잡기보다, `UNIQUE` 제약이 먼저 승자를 정하고 나머지는 기존 결과를 읽게 만드는 편이 단순합니다."
- "`purchase`와 `ticket`을 나눠 저장하는 것만으로는 중복 구매 방지가 끝나지 않습니다. 부모 row를 만들기 전 dedup 경계가 필요합니다."

## 다음 학습

- 멱등성 키 저장소와 replay 응답 패턴을 더 넓게 보려면 `database/idempotency-key-and-deduplication`
- duplicate check를 읽기 기반으로 할지 DB 제약으로 닫을지 비교하려면 `database/unique-vs-locking-read-duplicate-primer`
- 구매 1건과 티켓 여러 장의 구조 자체를 다시 보려면 `database/lotto-purchase-ticket-parent-child-modeling-bridge`
- 메모리 안 구매 흐름 조립 책임을 먼저 복습하려면 `software-engineering/lotto-purchase-flow-service-layer-bridge`
