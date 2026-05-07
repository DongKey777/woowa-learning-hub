---
schema_version: 3
title: Unique Precheck Race Review Drill
concept_id: database/unique-precheck-race-review-drill
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/baseball
- missions/shopping-cart
review_feedback_tags:
- unique-constraint
- precheck-race
- insert-first-arbitration
- mission-drill
aliases:
- unique precheck race drill
- exists then insert race drill
- unique constraint review drill
- 중복 확인 후 저장 race
- insert first arbitration practice
symptoms:
- exists/select precheck 뒤 insert하면 중복이 절대 생기지 않는다고 생각한다
- duplicate key를 예외로만 보고 기존 결과 재조회나 conflict 번역을 하지 못한다
- validation, unique constraint, idempotency key를 같은 중복 방지로 뭉갠다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- database/unique-vs-locking-read-duplicate-primer
- database/idempotency-key-and-deduplication
next_docs:
- database/unique-claim-existing-row-reuse-primer
- database/duplicate-key-vs-busy-response-mapping
- database/unique-vs-idempotency-key-vs-pending-row-recovery-decision-guide
linked_paths:
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/unique-claim-existing-row-reuse-primer.md
- contents/database/duplicate-key-vs-busy-response-mapping.md
- contents/database/unique-vs-idempotency-key-vs-pending-row-recovery-decision-guide.md
- contents/database/roomescape-reservation-concurrency-bridge.md
confusable_with:
- database/unique-vs-locking-read-duplicate-primer
- database/idempotency-key-and-deduplication
- database/duplicate-key-vs-busy-response-mapping
forbidden_neighbors:
- contents/database/index-basics.md
expected_queries:
- exists 확인 후 insert가 왜 race가 되는지 드릴로 풀어줘
- unique constraint와 validation precheck 차이를 미션 예제로 연습하고 싶어
- duplicate key가 나면 어떻게 fresh read나 conflict로 번역하는지 문제로 알려줘
- 중복 예약, 중복 구매, 같은 추측 저장을 unique 관점으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 unique precheck race review drill이다. exists then insert,
  duplicate key, unique constraint, idempotency key, insert-first arbitration,
  중복 예약/구매/추측 저장 같은 질문을 DB 승자 결정 판별 문제로 매핑한다.
---
# Unique Precheck Race Review Drill

> 한 줄 요약: `exists` 확인은 사용자에게 친절한 사전 안내일 수 있지만, 동시 요청의 최종 승자는 보통 unique constraint나 lock 같은 저장소 arbitration이 정해야 한다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`exists` 확인하고 저장하면 중복은 막히는 거 아닌가요?" | roomescape 같은 시간 예약 요청 두 개가 동시에 들어오는 흐름 | 두 요청이 같은 빈 상태를 볼 수 있다는 race를 본다 |
| "duplicate key가 나면 그냥 500인가요?" | unique constraint가 중복 구매/예약을 막았지만 응답 번역이 없는 코드 | fresh read, conflict, already exists 중 어떤 의미인지 나눈다 |
| "validation과 unique constraint가 둘 다 중복 방지 아닌가요?" | request shape 검증과 DB identity arbitration을 같은 방어선으로 보는 상황 | 입력 검증과 저장소 승자 결정을 분리한다 |

**난이도: Beginner**

## 문제 1

상황:

```text
SELECT count(*)로 예약이 없는지 확인한 뒤 INSERT한다. 두 요청이 동시에 들어왔다.
```

답:

precheck race다. 둘 다 count 0을 볼 수 있으므로 `(date, time_id)` unique constraint나 locking strategy가 필요하다.

## 문제 2

상황:

```text
UNIQUE violation이 났는데 이미 저장된 row가 같은 idempotency key와 같은 body hash다.
```

답:

같은 요청 replay일 수 있다. 실패로 끝내기보다 기존 결과를 다시 읽어 재생하는 후보로 본다.

## 문제 3

상황:

```text
UNIQUE violation이 났는데 같은 key의 body hash가 다르다.
```

답:

conflict 후보다. 같은 identity로 다른 의미의 요청을 보낸 것이므로 안정적인 409와 error code로 번역한다.

## 빠른 체크

| 신호 | 먼저 볼 것 |
|---|---|
| 같은 빈 상태를 둘 다 봄 | precheck race |
| 같은 identity는 하나만 허용 | unique constraint |
| 같은 요청 재전송 | idempotency key |
| 같은 key 다른 body | conflict |
