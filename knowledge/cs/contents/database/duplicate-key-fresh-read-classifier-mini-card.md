---
schema_version: 3
title: DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드
concept_id: database/duplicate-key-fresh-read-classifier-mini-card
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 75
mission_ids: []
review_feedback_tags:
- idempotency-replay-contract
- duplicate-key-reclassification
- primary-read-after-write
aliases:
- duplicatekeyexception fresh read classifier
- duplicate key winner row recheck
- primary read after duplicate key
- same key same hash replay
- same key different hash 409 conflict
- duplicate key processing status
- duplicate key blind retry
- duplicate key why not retry insert
- duplicate key means someone already wrote
- duplicate then not found
- stale snapshot duplicate key
- replica read after duplicate
- duplicate 뒤 어떻게 함
- duplicate key fresh read classifier mini card basics
- duplicate key fresh read classifier mini card beginner
symptoms:
- 중복키 예외가 나면 바로 409로 끝내야 하는지 헷갈려
- duplicate 뒤에 다시 읽었는데 row가 안 보여서 막혔어
- 같은 idempotency key 재요청을 성공으로 돌려줘야 하는지 모르겠어
intents:
- drill
prerequisites:
- database/idempotency-key-and-deduplication
- database/unique-claim-existing-row-reuse-primer
next_docs:
- database/primary-read-after-duplicate-checklist
- database/insert-if-absent-retry-outcome-guide
- database/mysql-duplicate-key-retry-handling-cheat-sheet
linked_paths:
- contents/database/duplicate-key-vs-serialization-failure-mini-card.md
- contents/database/idempotency-key-status-contract-examples.md
- contents/database/primary-read-after-duplicate-checklist.md
- contents/database/mysql-1062-fresh-read-mini-sequence-diagram.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/unique-claim-existing-row-reuse-primer.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/read-your-writes-session-pinning.md
- contents/network/http-methods-rest-idempotency-basics.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- database/duplicate-key-vs-serialization-failure-mini-card
- database/duplicate-key-vs-busy-response-mapping
forbidden_neighbors:
- contents/database/postgresql-serializable-retry-playbook.md
expected_queries:
- DuplicateKeyException 났을 때 다음에 뭘 확인해야 해?
- 중복키 예외 후 성공 재응답이랑 충돌 응답을 어떻게 나눠?
- duplicate 뒤 조회 결과가 null이면 어디부터 의심해?
- idem success랑 in-progress를 winner row로 구분하는 흐름 알려줘
- primary에서 다시 읽어야 하는 이유를 초보자 관점으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 insert-if-absent나 멱등성 처리에서 DuplicateKeyException 뒤에
  바로 실패하지 않고 primary/fresh read로 기존 winner row를 다시 확인해
  성공 재생, 처리 중, 진짜 충돌을 가르는 흐름을 확인 질문으로 굳힌다.
  중복키 다음 단계, 이미 누가 쓴 row 해석, 다시 읽어 결과 분류, 재시도
  말고 상태 확인, 같은 요청 재응답, 다른 payload 충돌 판단 같은 자연어
  paraphrase가 본 문서의 재분류 절차에 매핑된다.
---
# DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드

> 한 줄 요약: `DuplicateKeyException`이 났다고 바로 `409 conflict`로 끝내지 말고, **primary/fresh read로 winner row를 다시 읽어 `idem success` / `in-progress` / `409 conflict`를 가르는 것**이 초보자용 기본 흐름이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Duplicate Key vs Serialization Failure 미니 카드](./duplicate-key-vs-serialization-failure-mini-card.md)
- [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)
- [Primary Read-After-Duplicate Checklist](./primary-read-after-duplicate-checklist.md)
- [MySQL `1062` 후 Fresh-Read 경로 미니 시퀀스 다이어그램](./mysql-1062-fresh-read-mini-sequence-diagram.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: duplicatekeyexception fresh read classifier, duplicate key winner row recheck, primary read after duplicate key, same key same hash replay, same key different hash 409 conflict, duplicate key processing status, duplicate key blind retry, duplicate key why not retry insert, duplicate key means someone already wrote, duplicate then not found, stale snapshot duplicate key, replica read after duplicate, duplicate 뒤 어떻게 함, duplicate key fresh read classifier mini card basics, duplicate key fresh read classifier mini card beginner

이 카드를 "`duplicate 뒤 무엇을 읽는가`" 관점에서 더 넓게 보면 [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)가 바로 이어진다.

## 먼저 그림부터

`1062 -> primary/fresh read -> replay|busy|conflict` 흐름을 시퀀스 그림으로 먼저 보고 싶으면 [MySQL `1062` 후 Fresh-Read 경로 미니 시퀀스 다이어그램](./mysql-1062-fresh-read-mini-sequence-diagram.md)부터 보면 된다.

`duplicate` 직후 `SELECT`가 `null`이라 "winner가 없나?"부터 흔들린다면 [Primary Read-After-Duplicate Checklist](./primary-read-after-duplicate-checklist.md)를 먼저 붙여 읽으면 stale snapshot/replica read부터 빠르게 자를 수 있다.

초보자 기준으로는 `UNIQUE`를 "입구", fresh read를 "안내판"으로 보면 된다.

- `INSERT` 성공: 내가 먼저 입장했다.
- `DuplicateKeyException`: 누군가 먼저 입장했다.
- fresh read: 그 먼저 들어간 요청이 **내 요청과 같은 성공인지**, **아직 처리 중인지**, **아예 다른 요청인지**를 확인하는 단계다.

즉 `DuplicateKeyException`은 최종 답이 아니라 **재분류 시작 신호**다.

## 먼저 머릿속 모델 고정

이 카드에서는 `duplicate key`를 이렇게 기억하면 된다.

- `INSERT`는 "내가 새 row를 만들 수 있나?"를 묻는다.
- `duplicate key`는 "이미 누가 만들었다"는 답이다.
- 그래서 다음 질문은 "다시 만들 수 있나?"가 아니라 **"이미 있는 그 row는 무엇을 뜻하나?"**다.

즉 초보자 기본값은 아래 한 줄이다.

> `duplicate key` 뒤에는 blind retry보다 **기존 상태 재조회**가 먼저다.

## blind retry보다 fresh read가 먼저인 이유

| 바로 떠올린 행동 | 왜 초보자 기본값이 아님 | 대신 할 것 |
|---|---|---|
| 같은 `INSERT`를 즉시 다시 retry | 이미 winner가 있는데 loser만 반복할 수 있다 | winner row를 fresh read로 다시 본다 |
| 바로 `409 conflict` 반환 | 같은 payload 재전송까지 충돌로 오분류할 수 있다 | `request_hash`와 `status`를 본다 |
| 같은 트랜잭션에서 `SELECT` 한 번 더 | stale snapshot이면 방금 winner를 못 볼 수 있다 | primary/read-your-writes 경로로 읽는다 |

핵심은 retry 대상이 다르다는 점이다.

- 나쁜 기본값: `INSERT`를 다시 retry
- 좋은 기본값: **winner state를 다시 읽어 분류**

### before / after 한 번만 보기

같은 `idempotency_key = pay-123`로 요청 A와 요청 B가 거의 동시에 왔다고 하자.

| 비교 | blind insert retry | winner-row recheck |
|---|---|---|
| 1단계 | B가 `DuplicateKeyException`을 본다 | B가 `DuplicateKeyException`을 본다 |
| 2단계 | B가 같은 `INSERT`를 또 보낸다 | B가 primary/fresh read로 winner row를 읽는다 |
| 3단계 | 또 duplicate가 나거나, "언제까지 retry하지?"만 남는다 | `SUCCEEDED`면 replay, `PROCESSING`이면 대기, hash 다르면 `409`로 닫힌다 |
| 초보자 관점 한 줄 | **의미를 못 늘린다.** 같은 패배 사실만 다시 확인한다 | **의미가 늘어난다.** 이미 있는 row가 무엇을 뜻하는지 알게 된다 |

즉 `duplicate key` 뒤 blind retry는 "내가 또 질까?"만 반복해서 묻는 셈이고,
winner-row recheck는 "이미 이긴 요청이 성공했나, 아직 처리 중인가, 아니면 다른 payload인가?"를 묻는 셈이다.

## 30초 결정표

| fresh read 결과 | 서비스 분류 | 보통의 응답 예시 | 기억법 |
|---|---|---|---|
| 같은 idempotency key + 같은 request hash + 상태가 `SUCCEEDED` | `idem success` | 이전 성공 응답 재사용, `200`/`201` | 이미 끝난 내 요청이다 |
| 같은 idempotency key + 같은 request hash + 상태가 `PROCESSING` | `in-progress` | `202 Accepted`, `409 in-progress`, `Retry-After` | 앞 요청이 아직 달리는 중이다 |
| 같은 key인데 request hash/payload가 다름 | `409 conflict` | `409 Conflict` | 같은 열쇠를 다른 뜻으로 재사용했다 |

이 카드의 핵심은 한 줄이다.

> duplicate 뒤 retry할 것은 `INSERT`가 아니라 **winner read 분류**다.

세 분기를 실제 HTTP 헤더/바디 예시로 바로 보고 싶다면 [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)로 이어서 보면 된다.

## 왜 primary/fresh read가 필요한가

`DuplicateKeyException` 직후에 row가 안 보인다고 해서 winner가 없는 것은 아니다.

- replica read면 아직 복제가 안 왔을 수 있다.
- 같은 트랜잭션의 오래된 snapshot이면 방금 생긴 winner를 못 볼 수 있다.
- flush 실패 뒤 현재 transaction이 rollback-only라 follow-up read가 믿기 어려울 수 있다.

그래서 beginner 기본 규칙은 아래처럼 잡으면 된다.

1. duplicate를 잡는다.
2. 현재 stale path를 벗어난다.
3. primary 또는 read-your-writes가 보장되는 fresh read로 다시 본다.
4. 그 결과로 `idem success` / `in-progress` / `409 conflict`를 고른다.

### duplicate 다음 `null`을 만났을 때

이 장면만 따로 떼어 보면 아래처럼 정리하면 된다.

| 장면 | 초보자 기본 해석 | 바로 할 일 |
|---|---|---|
| duplicate 뒤 replica read가 `null` | winner는 있는데 복제가 늦을 수 있다 | primary/read-your-writes 경로로 다시 읽는다 |
| duplicate 뒤 같은 트랜잭션 `SELECT`가 `null` | 같은 오래된 snapshot을 다시 보고 있을 수 있다 | 새 read 경계에서 fresh lookup을 연다 |
| fresh primary read에서도 `null` | absence보다 routing/transaction 경계 문제를 먼저 의심한다 | 재삽입보다 read path 점검을 우선한다 |

더 짧은 checklist가 필요하면 [Primary Read-After-Duplicate Checklist](./primary-read-after-duplicate-checklist.md)로 바로 이어서 보면 된다.

### 아주 짧은 비교

| 상황 | blind retry가 만드는 문제 | fresh read가 주는 정보 |
|---|---|---|
| 같은 요청 재전송 | 같은 loser path를 또 밟을 수 있다 | 이미 끝난 성공인지 확인 가능 |
| winner가 아직 처리 중 | 불필요한 재시도 폭증 | `in-progress`로 짧게 대기시킬 수 있다 |
| 같은 key를 다른 payload가 재사용 | 원인 파악 없이 예외만 반복 | `409 conflict`로 의미를 분리할 수 있다 |

## 가장 단순한 예시

예: `idempotency_key = pay-123`

| 순간 | DB에 있는 winner row | 내 응답 |
|---|---|---|
| 요청 A가 먼저 성공 | `key=pay-123`, `hash=abc`, `status=SUCCEEDED` | 요청 B는 `idem success` |
| 요청 A가 아직 처리 중 | `key=pay-123`, `hash=abc`, `status=PROCESSING` | 요청 B는 `in-progress` |
| 다른 payload가 같은 key를 재사용 | `key=pay-123`, `hash=xyz`, `status=SUCCEEDED` | 요청 B는 `409 conflict` |

핵심 비교:

- `same key + same hash`면 replay 쪽을 먼저 본다.
- `same key + different hash`면 conflict 쪽을 먼저 본다.

## Spring 서비스 흐름 스케치

```java
public ApiResponse create(CreateCommand cmd) {
    try {
        return writeTx.insertOnce(cmd);
    } catch (DuplicateKeyException e) {
        WinnerRow row = freshReadService.findByIdempotencyKey(cmd.idempotencyKey());

        if (row == null) {
            throw new IllegalStateException("winner row not visible on fresh read");
        }
        if (!row.requestHash().equals(cmd.requestHash())) {
            throw new ConflictException("same key, different payload");
        }
        if (row.isProcessing()) {
            return ApiResponse.inProgress(row.retryAfterSeconds());
        }
        return ApiResponse.idemSuccess(row.responseBody());
    }
}
```

이 스케치에서 초보자가 먼저 볼 점은 세 가지다.

1. duplicate 뒤에 같은 `INSERT`를 다시 던지지 않는다.
2. fresh read 서비스는 가능하면 primary/read-your-writes 경로를 쓴다.
3. 분류 기준은 예외명이 아니라 `request_hash`와 `status`다.

## 자주 하는 오해

- "`duplicate key`면 DB가 이상해서 retry를 더 세게 걸어야 한다"
  - 보통 아니다. 많은 경우 winner는 이미 생겼고, 필요한 것은 write retry보다 state 확인이다.
- "`DuplicateKeyException`이면 무조건 `409 conflict`다"
  - 아니다. 같은 key와 같은 payload면 `idem success`가 더 자연스럽다.
- "row가 바로 안 보이면 insert가 사실 실패한 것이다"
  - 아니다. stale read, replica lag, old snapshot일 수 있다.
- "`in-progress`도 conflict의 한 종류다"
  - 아니다. conflict는 "다른 의미의 요청"이고, `in-progress`는 "같은 요청이 아직 안 끝남"이다.
- "fresh read는 같은 트랜잭션 안에서 다시 `SELECT`하면 된다"
  - 꼭 아니다. stale snapshot을 벗어나야 할 수 있다.

## 한 줄 정리

처음 읽을 때는 이것만 고정하면 된다.

1. `DuplicateKeyException`은 winner 존재 신호다.
2. 다음 행동은 blind retry가 아니라 primary/fresh read다.
3. fresh read 결과는 보통 `idem success` / `in-progress` / `409 conflict` 셋 중 하나다.

더 넓게 보려면:

- MySQL `1062` 전체 흐름은 [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- duplicate/timeout/deadlock/`40001` 3버킷 비교는 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- 왜 replica가 아니라 primary/fresh read가 필요한지는 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
