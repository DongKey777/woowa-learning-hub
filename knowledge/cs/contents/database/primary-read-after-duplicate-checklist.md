---
schema_version: 3
title: Primary Read-After-Duplicate Checklist
concept_id: database/primary-read-after-duplicate-checklist
canonical: true
category: database
difficulty: beginner
doc_role: playbook
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- duplicate-key
- read-after-write
- primary-read
- idempotency
aliases:
- primary read after duplicate checklist
- duplicate then not found
- duplicate key then select null
- winner row not visible after duplicate
- stale snapshot after duplicate key
- replica read after duplicate key
- fresh winner lookup checklist
- primary winner lookup
- duplicate key row not found why
- mysql 1062 then row not found
symptoms:
- duplicate key 직후 SELECT가 null이라 winner row가 없다고 판단하고 같은 INSERT를 다시 던지려 해
- duplicate는 primary write path에서 났는데 follow-up read는 replica나 오래된 transaction snapshot을 보고 있어
- fresh primary winner lookup 뒤 request_hash와 status로 replay, processing, conflict를 재분류해야 해
intents:
- troubleshooting
- definition
prerequisites:
- database/duplicate-key-fresh-read-classifier-mini-card
- database/mysql-1062-fresh-read-mini-sequence-diagram
next_docs:
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
- database/mysql-duplicate-key-retry-handling-cheat-sheet
linked_paths:
- contents/database/duplicate-key-fresh-read-classifier-mini-card.md
- contents/database/mysql-1062-fresh-read-mini-sequence-diagram.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/postgresql-mysql-claim-sql-mini-card.md
confusable_with:
- database/mysql-duplicate-key-retry-handling-cheat-sheet
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
forbidden_neighbors: []
expected_queries:
- duplicate key 직후 SELECT가 null이면 winner가 없다고 보고 다시 INSERT해도 돼?
- duplicate then not found가 replica lag나 stale snapshot 때문에 생기는 흐름을 설명해줘
- MySQL 1062 뒤 fresh primary winner lookup으로 replay busy conflict를 나누는 순서를 알려줘
- duplicate 후 같은 transaction에서 SELECT를 반복해도 fresh read가 아닐 수 있는 이유가 뭐야?
- idempotency key duplicate 뒤 primary read를 통해 request_hash와 status를 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 duplicate key 이후 follow-up read가 null일 때 replica lag, stale snapshot, read route mismatch를 의심하고 fresh primary winner lookup을 수행하는 beginner playbook이다.
  duplicate then not found, winner row not visible after duplicate, primary winner lookup 질문이 본 문서에 매핑된다.
---
# Primary Read-After-Duplicate Checklist

> 한 줄 요약: `duplicate key` 직후 row가 안 보이는 것은 "winner가 없다"가 아니라 **replica read나 오래된 snapshot 때문에 아직 못 본다**는 뜻일 수 있으므로, 초보자 기본값은 `INSERT` 재시도보다 **fresh primary winner lookup**이다.

**난이도: 🟢 Beginner**

관련 문서:

- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [MySQL `1062` 후 Fresh-Read 경로 미니 시퀀스 다이어그램](./mysql-1062-fresh-read-mini-sequence-diagram.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Replica Lag와 Read-after-Write 전략](./replica-lag-read-after-write-strategies.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: primary read after duplicate checklist, duplicate then not found, duplicate key then select null, winner row not visible after duplicate, stale snapshot after duplicate key, replica read after duplicate key, fresh winner lookup checklist, primary winner lookup, duplicate key read primary, duplicate after null select beginner, duplicate key row not found why, read after duplicate safely, same transaction snapshot stale duplicate, mysql duplicate then not found, mysql 1062 then row not found

## 먼저 멘탈모델 고정

초보자는 이 장면을 "`개찰구`와 `전광판`"으로 보면 된다.

- `duplicate key`: 개찰구는 이미 누가 먼저 통과했다고 알려 준다.
- follow-up read `null`: 전광판이 늦거나, 다른 카메라를 보고 있을 수 있다.
- fresh primary read: 승자가 실제로 누구인지 **본선 전광판**에서 다시 확인한다.

즉 `duplicate -> null`은 모순이 아니라, **쓰기 판정은 났는데 읽기 경로가 뒤처진 장면**일 수 있다.

## 왜 duplicate 다음에 not found가 나올 수 있나

| 장면 | 왜 `null`이 보일 수 있나 | 초보자 해석 |
|---|---|---|
| replica read | winner row commit은 됐지만 replica apply가 아직 안 끝났다 | "승자는 있는데 복사본이 늦다" |
| 같은 트랜잭션의 오래된 snapshot | 이미 열린 snapshot이 winner 생성 전 시점을 계속 보고 있다 | "같은 눈으로 다시 봐도 옛 장면만 본다" |
| read path가 write path와 다름 | duplicate는 primary가 판단했는데 조회는 다른 datasource/route로 갔다 | "판정한 심판과 확인한 심판이 다르다" |

이때 바로 "`row가 없네, 다시 insert`"로 가면 loser가 같은 패턴을 반복할 수 있다.

## 30초 체크리스트

`duplicate key` 뒤에는 아래 네 줄만 먼저 지키면 된다.

1. 같은 `INSERT`를 바로 다시 던지지 않는다.
2. follow-up read가 replica나 오래된 snapshot인지 먼저 의심한다.
3. **새로운 fresh 경로**에서 winner row를 다시 읽는다.
4. winner row를 읽은 뒤 `idem success` / `in-progress` / `409 conflict`를 고른다.

## fresh winner lookup을 안전하게 하는 가장 단순한 방법

초보자 기준으로는 "방금 duplicate를 본 그 오래된 읽기 경로를 버리고, 새 primary read를 한 번 연다"로 기억하면 충분하다.

| 방법 | 왜 안전한가 | 초보자 기본값 여부 |
|---|---|---|
| 새 트랜잭션에서 primary로 `SELECT` | 오래된 snapshot을 벗어나고 write 판정 노드와 맞춘다 | 기본값 |
| read-your-writes/session pinning 경로로 `SELECT` | 최근 write/duplicate 직후에는 replica를 피한다 | 기본값 |
| GTID/LSN wait 후 읽기 | replica가 winner까지 따라왔는지 확인한다 | 확장 옵션 |

가장 단순한 규칙:

> `duplicate`를 본 직후 조회가 `null`이면, **같은 트랜잭션에서 같은 read를 반복하지 말고** primary/fresh 경로에서 winner를 다시 찾는다.

## 초보자용 safe lookup 순서

| 순서 | 할 일 | 이유 |
|---|---|---|
| 1 | duplicate를 잡는다 | winner 존재 가능성이 매우 높다 |
| 2 | 현재 read가 replica인지, 오래된 transaction snapshot인지 확인한다 | 왜 `null`이 나왔는지 먼저 분리한다 |
| 3 | 새 read 경계에서 primary/fresh lookup을 1회 수행한다 | stale view를 벗어난다 |
| 4 | winner row의 `request_hash`, `status`를 본다 | replay / busy / conflict를 가른다 |
| 5 | fresh lookup에서도 계속 `null`이면 routing/transaction 경계 문제로 본다 | absence로 단정하지 않는다 |

## 아주 짧은 예시

예: `idempotency_key=pay-123`

1. 요청 A가 primary에서 row를 만들고 commit했다.
2. 요청 B가 같은 key로 `INSERT`를 시도해 `1062`를 받았다.
3. 요청 B가 replica에서 바로 읽었더니 `null`이었다.
4. 요청 B가 새 primary read로 다시 읽었더니 `status=SUCCEEDED`, `hash=abc` row가 보였다.
5. 이 경우 B의 정답은 재삽입이 아니라 `idem success`다.

핵심은 3번의 `null`이 "winner 없음"을 뜻하지 않는다는 점이다.

## 코드 스케치

```java
public ApiResponse create(CreateCommand cmd) {
    try {
        return writeTx.insertOnce(cmd);
    } catch (DuplicateKeyException e) {
        WinnerRow row = winnerLookup.findFreshOnPrimary(cmd.idempotencyKey());

        if (row == null) {
            throw new IllegalStateException("fresh primary read still cannot see winner");
        }
        if (!row.requestHash().equals(cmd.requestHash())) {
            throw new ConflictException("same key, different payload");
        }
        if (row.isProcessing()) {
            return ApiResponse.inProgress();
        }
        return ApiResponse.idemSuccess(row.responseBody());
    }
}
```

이 스케치에서 초보자가 볼 포인트는 세 가지다.

- duplicate 뒤 retry 대상은 `INSERT`가 아니라 winner lookup이다.
- lookup은 replica가 아니라 fresh primary/read-your-writes 경로를 쓴다.
- `null`이 나오면 "없음 확정"보다 "read path가 맞나"를 먼저 본다.

## 자주 하는 오해

- "`duplicate`와 `not found`가 같이 나오면 DB가 모순된 것이다"
  - 꼭 아니다. write 판정과 read 경로의 freshness가 다를 수 있다.
- "같은 트랜잭션에서 `SELECT` 한 번 더 하면 fresh read다"
  - 아니다. snapshot이 이미 열려 있으면 같은 옛 장면을 다시 볼 수 있다.
- "replica에서 한 번 안 보였으니 row가 없는 것이다"
  - 아니다. read-after-write 경로에서는 replica lag가 흔한 이유다.
- "fresh lookup에서도 `null`이면 다시 `INSERT`하면 된다"
  - 먼저 routing, datasource, transaction 경계를 의심해야 한다.

## 한 줄 정리

`duplicate key` 뒤 `SELECT`가 `null`이어도 winner가 없는 것이 아닐 수 있다. 초보자 기본값은 **same read path 반복**이 아니라 **fresh primary winner lookup 후 재분류**다.
