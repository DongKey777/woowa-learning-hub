---
schema_version: 3
title: Idempotency Key Status Contract Examples
concept_id: database/idempotency-key-status-contract-examples
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/shopping-cart
- missions/payment
- missions/backend
review_feedback_tags:
- idempotency-status-contract
- duplicate-fresh-read-response
- processing-replay-conflict
aliases:
- idempotency key status contract
- idempotency response contract
- pending processing succeeded
- processing succeeded replay hash mismatch
- duplicate key after fresh read api contract
- same key same hash replay
- same key processing 202
- same key different hash 409
- idempotency status header
- 멱등성 key 상태 응답
symptoms:
- idempotency key duplicate 뒤에 다시 처리할지 기존 row를 읽어 응답할지 결정하지 못하고 있어
- PENDING, PROCESSING, SUCCEEDED의 저장 상태와 API 응답 의미를 섞고 있어
- 같은 key 같은 hash replay, processing 202, 다른 hash 409 conflict 응답 계약을 정해야 해
intents:
- comparison
- troubleshooting
- design
prerequisites:
- database/idempotency-key-and-deduplication
- database/duplicate-key-fresh-read-classifier-mini-card
next_docs:
- database/duplicate-key-replay-vs-in-progress-vs-conflict-decision-guide
- database/pending-row-recovery-primer
- database/unique-vs-idempotency-key-vs-pending-row-recovery-decision-guide
- database/idempotency-review-sentence-card
linked_paths:
- contents/database/duplicate-key-fresh-read-classifier-mini-card.md
- contents/database/duplicate-key-vs-busy-response-mapping.md
- contents/database/pending-row-recovery-primer.md
- contents/database/unique-claim-existing-row-reuse-primer.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/duplicate-key-replay-vs-in-progress-vs-conflict-decision-guide.md
- contents/database/unique-vs-idempotency-key-vs-pending-row-recovery-decision-guide.md
confusable_with:
- database/duplicate-key-fresh-read-classifier-mini-card
- database/duplicate-key-vs-busy-response-mapping
- database/pending-row-recovery-primer
forbidden_neighbors: []
expected_queries:
- idempotency key duplicate 뒤 fresh read 결과가 PENDING이면 202 PROCESSING으로 응답해야 해?
- 같은 idempotency key와 같은 request hash가 SUCCEEDED면 기존 결과를 replay하는 계약을 어떻게 잡아?
- 같은 key인데 request hash가 다르면 409 conflict로 닫아야 하는 이유는 뭐야?
- PENDING 저장 상태와 PROCESSING API 응답 의미를 어떻게 구분해?
- duplicate key 이후 다시 실행하지 않고 기존 idempotency row 상태로 응답하는 예시를 보여줘
contextual_chunk_prefix: |
  이 문서는 idempotency key duplicate 이후 fresh read한 row 상태를 PENDING/PROCESSING/SUCCEEDED, replay, hash mismatch conflict 응답 계약으로 매핑하는 beginner chooser다.
  idempotency key status, processing 202, replay response, hash mismatch 409 같은 자연어 질문이 본 문서에 매핑된다.
---
# Idempotency Key Status Contract Examples

> 한 줄 요약: exact-key duplicate가 감지된 뒤에는 새로 처리하려 하지 말고, 기존 idempotency row를 다시 읽어 `PENDING`/`PROCESSING`/`SUCCEEDED` 역할을 먼저 맞춘 뒤, `PROCESSING`, replay, hash-mismatch conflict 셋 중 하나의 **응답 계약**으로 닫으면 된다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| payment/backend 장면 | 먼저 볼 상태 계약 |
|---|---|
| 같은 idempotency key가 다시 들어왔다 | 기존 row를 fresh read했는가 |
| 기존 row가 처리 중이다 | 202/PROCESSING 응답이 필요한가 |
| 이미 성공한 같은 요청이다 | response replay가 가능한가 |
| 같은 key인데 payload가 다르다 | 409 conflict로 막아야 하는가 |

관련 문서:

- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- [PENDING Row Recovery Primer](./pending-row-recovery-primer.md)
- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: idempotency key status contract examples, pending processing succeeded vocabulary alignment, processing succeeded replay hash mismatch, exact key duplicate detection response contract, duplicate key after fresh read api contract, same key same hash replay example, same key processing 202 example, same key different hash 409 example, idempotency response body example, idempotency status header example, replay response contract beginner, processing response contract beginner, hash mismatch conflict beginner, pending row recovery response, processing row takeover versus 202

## 먼저 멘탈모델

초보자는 이 장면을 "같은 열쇠로 문을 다시 연다"로 보면 쉽다.

- `INSERT` 또는 claim에서 이미 같은 `idempotency_key`가 잡혔다.
- 그 뜻은 "누군가 먼저 이 key를 썼다"는 것이다.
- 이제 중요한 질문은 "다시 실행할까?"가 아니라 **"그 기존 row가 지금 무슨 상태인가?"** 다.

그래서 duplicate 뒤 기본 흐름은 이것이다.

1. exact-key duplicate를 감지한다.
2. primary/fresh read로 그 key row를 다시 읽는다.
3. 읽은 row를 `PENDING`/`SUCCEEDED` 저장 상태와 `PROCESSING` 응답 의미로 먼저 해석한다.
4. 그 해석 결과를 `PROCESSING`, replay, `hash mismatch` 중 하나의 응답 계약으로 닫는다.

## 상태 이름 먼저 맞추기

초보자가 가장 많이 헷갈리는 지점은 `PENDING`, `PROCESSING`, `SUCCEEDED`가 모두 "진행/성공 상태"처럼 보인다는 점이다.

이 문서에서는 아래처럼 고정해서 읽는다.

| 이름 | 어디에 붙는 말인가 | 초보자 해석 |
|---|---|---|
| `PENDING` | idempotency row 저장 상태 | winner가 row를 선점했지만 아직 최종 성공으로 닫지 못했다 |
| `PROCESSING` | 중복 요청에 돌려주는 API/헤더 표현 | "기존 `PENDING` row가 아직 살아 있으니 새 실행은 안 한다" |
| `SUCCEEDED` | idempotency row 저장 상태 | 같은 key의 최종 성공 결과가 이미 저장돼 있다 |

짧게 연결하면 이것이다.

- 저장소 안에서는 보통 `PENDING -> SUCCEEDED`
- 중복 요청 응답에서는 보통 `PENDING row 관찰 -> PROCESSING 응답`
- 이미 성공 종료된 row를 다시 읽으면 `SUCCEEDED row -> replay 응답`

## 30초 결정표

| fresh read 결과 | 초보자 해석 | 대표 HTTP | 핵심 응답 의미 |
|---|---|---|---|
| `status = PENDING` + 같은 `request_hash` | winner row는 아직 최종 성공 전 | 보통 `202 Accepted` | "같은 요청의 기존 row가 아직 살아 있으니 새 실행은 안 한다" |
| `status = SUCCEEDED` + 같은 `request_hash` | 이미 끝난 같은 요청 | 보통 기존 `200`/`201` replay | "처리를 다시 하지 않고 이전 결과를 돌려준다" |
| 같은 key인데 `request_hash`가 다름 | 같은 열쇠를 다른 뜻으로 재사용 | `409 Conflict` | "같은 key를 다른 payload에 쓰면 안 된다" |

핵심 한 줄:

> duplicate는 에러 이름이고, 응답 계약은 fresh read 결과의 **상태 해석**이 결정한다.

## 예시에서 가정하는 idempotency row

```sql
CREATE TABLE api_idempotency (
  id BIGINT PRIMARY KEY,
  idempotency_key VARCHAR(100) NOT NULL,
  request_hash CHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  resource_type VARCHAR(50) NULL,
  resource_id VARCHAR(50) NULL,
  response_code INT NULL,
  response_body JSON NULL,
  UNIQUE (idempotency_key)
);
```

이 문서에서는 아래처럼 읽는다.

- `idempotency_key`: 같은 재시도인지 구분하는 열쇠
- `request_hash`: payload가 정말 같은지 확인하는 지문
- `status`: 저장소 안에서 지금 `PENDING`인지 `SUCCEEDED`인지 알려 주는 안내판

## 1. `PENDING row -> PROCESSING` 계약 예시

### 어떤 장면인가

- 요청 B가 요청 A와 같은 `idempotency_key`로 들어왔다.
- exact-key duplicate가 감지됐다.
- fresh read 결과 기존 row가 아직 `PENDING`이다.
- `request_hash`도 같아서 "같은 요청 재전송"으로 본다.

이때 초보자 기본값은 **새 주문을 또 만들지 않는 것**이다.

### HTTP 응답 예시

```http
HTTP/1.1 202 Accepted
Content-Type: application/json
Idempotency-Key: pay_20260427_001
Idempotency-Status: PROCESSING
Retry-After: 2

{
  "code": "IDEMPOTENCY_PROCESSING",
  "message": "같은 요청이 이미 처리 중입니다.",
  "idempotencyKey": "pay_20260427_001",
  "status": "PROCESSING",
  "retryAfterSeconds": 2
}
```

### 초보자용 해석

| 필드 | 왜 있나 |
|---|---|
| `202 Accepted` | 요청을 이해했지만 최종 결과는 아직 아니라는 뜻을 준다 |
| `Idempotency-Status: PROCESSING` | "중복이었고, 지금은 진행 중"이라는 상태를 분리해 준다 |
| `Retry-After: 2` | 클라이언트가 너무 공격적으로 다시 치지 않게 한다 |
| `code = IDEMPOTENCY_PROCESSING` | 일반 `busy`와 구분되는 도메인 코드를 준다 |

짧게 기억하면:

- `PROCESSING`은 row 상태 이름이라기보다 **대기 안내 응답**에 가깝다
- 이 응답은 "새 실행 거절"이지 "영구 충돌"이 아니다

기존 `PROCESSING`/`PENDING` row를 언제 계속 `in-progress`로 두고, 언제 stale row recovery를 시작할지는 [PENDING Row Recovery Primer](./pending-row-recovery-primer.md)를 같이 보면 헷갈림이 줄어든다.

## 2. `SUCCEEDED row -> replay` 계약 예시

### 어떤 장면인가

- 같은 `idempotency_key`
- 같은 `request_hash`
- fresh read 결과 기존 row가 `SUCCEEDED`

이때 핵심은 "또 처리하지 말고 **이전 성공 결과를 replay**한다"는 점이다.

### HTTP 응답 예시

최초 요청이 `201 Created`였다고 가정하자.

```http
HTTP/1.1 201 Created
Content-Type: application/json
Idempotency-Key: pay_20260427_001
Idempotency-Status: SUCCEEDED
Idempotency-Replayed: true
Location: /payments/pmt_9812

{
  "paymentId": "pmt_9812",
  "status": "APPROVED",
  "amount": 12900,
  "currency": "KRW"
}
```

### 초보자용 해석

| 필드 | 왜 있나 |
|---|---|
| 원래와 같은 `201 Created` | "같은 요청이면 같은 결과"라는 계약을 유지한다 |
| `Idempotency-Status: SUCCEEDED` | 이미 끝난 요청의 재전송임을 드러낸다 |
| `Idempotency-Replayed: true` | 이번 호출에서 새 결제를 만든 것이 아님을 알려 준다 |
| 같은 body | 클라이언트 입장에서 결과 복원이 쉽다 |

여기서 중요한 점은 이것이다.

- replay는 "중복이었다"만 말하는 것이 아니다
- 가능하면 **처음 성공과 호환되는 응답**을 다시 주는 것이다

## 3. hash-mismatch conflict 계약 예시

### 어떤 장면인가

- `idempotency_key`는 같다
- 하지만 fresh read로 본 기존 row의 `request_hash`가 다르다
- 즉 같은 열쇠를 다른 payload에 재사용했다

이 장면은 `PROCESSING`이나 replay가 아니다.
이미 같은 key space가 다른 의미로 점유됐기 때문이다.

### HTTP 응답 예시

```http
HTTP/1.1 409 Conflict
Content-Type: application/json
Idempotency-Key: pay_20260427_001
Idempotency-Status: CONFLICT

{
  "code": "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD",
  "message": "같은 Idempotency-Key를 다른 요청 본문에 재사용할 수 없습니다.",
  "idempotencyKey": "pay_20260427_001",
  "status": "CONFLICT"
}
```

### 초보자용 해석

| 필드 | 왜 있나 |
|---|---|
| `409 Conflict` | 같은 key가 이미 다른 의미로 확정됐음을 알려 준다 |
| `Idempotency-Status: CONFLICT` | 처리 중과 구분되는 영구 충돌 의미를 준다 |
| 긴 `code` 이름 | "왜 409인지"를 클라이언트와 서버 로그 모두에서 분명히 한다 |

짧게 기억하면:

- `same key + same hash`면 replay 또는 processing
- `same key + different hash`면 conflict

## 세 응답을 한 표로 다시 보기

| 상황 | 대표 상태 | 다시 실행하나 | 대표 HTTP |
|---|---|---|---|
| 앞 요청이 아직 끝나지 않음 | 저장 row는 `PENDING`, 응답은 `PROCESSING` | 아니다 | `202 Accepted` |
| 앞 요청이 이미 성공 종료 | `SUCCEEDED` | 아니다 | 원래 `200`/`201` replay |
| 같은 key를 다른 payload에 사용 | `CONFLICT` | 아니다 | `409 Conflict` |

표를 보면 공통점이 하나 있다.

> 세 경우 모두 duplicate 뒤에 **새 side effect를 다시 만들지 않는다.**

## 자주 하는 오해

- "`duplicate key`면 무조건 `409`다"
  - 아니다. 같은 hash면 `PROCESSING` 또는 replay일 수 있다.
- "`PROCESSING`이면 서버가 실패한 것이다"
  - 아니다. 보통 앞 요청이 아직 진행 중이라는 뜻이다.
- "replay면 항상 `200 OK`여야 한다"
  - 아니다. 최초 성공이 `201 Created`였다면 그것을 그대로 replay할 수 있다.
- "`request_hash`는 선택사항이라 빼도 된다"
  - beginner 설계에서도 같은 key를 다른 payload에 재사용하는 실수를 막으려면 매우 중요하다.

## 초보자용 한 줄 규칙

1. duplicate를 보면 다시 쓰기 전에 fresh read를 먼저 한다.
2. 같은 key와 같은 hash면 `PENDING -> PROCESSING` 또는 `SUCCEEDED -> replay`를 고른다.
3. 같은 key와 다른 hash면 `409 Conflict`로 닫는다.
4. 세 경우 모두 "새로 한 번 더 실행"을 기본값으로 두지 않는다.

## 다음에 이어서 볼 문서

- duplicate 뒤 분기 자체를 먼저 익히려면 [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- HTTP 선택을 `busy`/`already exists` 관점으로 다시 보면 [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- row 선점과 기존 row 재사용 흐름을 같이 보려면 [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)

## 한 줄 정리

exact-key duplicate가 감지된 뒤에는 새로 처리하려 하지 말고, 기존 idempotency row를 다시 읽어 `PENDING`/`PROCESSING`/`SUCCEEDED` 역할을 먼저 맞춘 뒤, `PROCESSING`, replay, hash-mismatch conflict 셋 중 하나의 **응답 계약**으로 닫으면 된다.
