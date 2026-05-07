---
schema_version: 3
title: Backend Idempotency Status Contract Drill
concept_id: database/backend-idempotency-status-contract-drill
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/shopping-cart
- missions/payment
- missions/backend
review_feedback_tags:
- idempotency-key
- duplicate-submit
- processing-replay-conflict
- status-contract
aliases:
- backend idempotency status contract drill
- idempotency key replay processing conflict drill
- duplicate submit status contract exercise
- PENDING PROCESSING SUCCEEDED drill
- 멱등성 상태 응답 계약 드릴
symptoms:
- duplicate idempotency key를 만나면 기존 row를 읽지 않고 다시 처리하려 한다
- PENDING, PROCESSING, SUCCEEDED 저장 상태와 202, replay, 409 응답 계약을 섞는다
- 같은 key 다른 request hash를 replay로 처리해 다른 요청을 같은 결과로 뭉갠다
intents:
- drill
- troubleshooting
- design
prerequisites:
- database/idempotency-key-status-contract-examples
- database/idempotency-key-and-deduplication
next_docs:
- database/duplicate-key-replay-vs-in-progress-vs-conflict-decision-guide
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
- software-engineering/api-design-error-handling
linked_paths:
- contents/database/idempotency-key-status-contract-examples.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/duplicate-key-replay-vs-in-progress-vs-conflict-decision-guide.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/software-engineering/api-design-error-handling.md
confusable_with:
- database/idempotency-key-status-contract-examples
- database/idempotency-key-and-deduplication
- database/duplicate-key-replay-vs-in-progress-vs-conflict-decision-guide
forbidden_neighbors:
- contents/database/transaction-lost-update-mission-drill.md
expected_queries:
- backend idempotency key 상태 응답 계약을 문제로 연습하고 싶어
- duplicate key 뒤 PENDING PROCESSING SUCCEEDED를 어떻게 응답으로 바꿔?
- 같은 key 같은 hash는 replay하고 다른 hash는 409로 닫는 이유를 드릴해줘
- 결제 재시도 중 처리 중인 row를 202로 돌려도 되는지 판단해줘
- duplicate submit을 새로 실행하지 않고 fresh read로 닫는 문제를 풀어줘
contextual_chunk_prefix: |
  이 문서는 backend idempotency status contract drill이다. duplicate
  idempotency key, fresh read, PENDING/PROCESSING/SUCCEEDED, replay response,
  hash mismatch 409, duplicate submit 같은 미션 질문을 DB/API 응답 계약
  문제로 매핑한다.
---
# Backend Idempotency Status Contract Drill

> 한 줄 요약: 같은 idempotency key가 다시 오면 새로 실행하기 전에 기존 row 상태를 읽고, processing/replay/conflict 중 하나로 응답해야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
같은 idempotency key가 다시 들어왔고 기존 row 상태는 PROCESSING이다.
```

답:

새 작업을 실행하지 않는다. 아직 처리 중이라는 응답, 예를 들면 `202 PROCESSING`과 retry-after 또는 status endpoint를 제공하는 계약을 검토한다.

## 문제 2

상황:

```text
같은 key, 같은 request hash가 다시 들어왔고 기존 row는 SUCCEEDED이며 response snapshot이 있다.
```

답:

replay-safe 응답 후보가 된다. 외부 호출이나 주문 생성을 다시 하지 않고 기존 결과를 재생한다.

## 문제 3

상황:

```text
같은 key인데 request hash가 다르다.
```

답:

conflict다. 같은 key가 다른 의미의 요청을 대표하면 안 되므로 409 후보로 닫고 새 key를 요구한다.

## 빠른 체크

| 기존 row | 응답 계약 |
|---|---|
| 없음 | claim 후 처리 시작 |
| PROCESSING/PENDING | 202 또는 처리 중 응답 |
| SUCCEEDED + same hash | replay |
| same key + different hash | 409 conflict |
