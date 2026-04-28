# Idempotency 리뷰 문장 카드

> 한 줄 요약: whole-transaction retry를 넣는 코드 리뷰에서는 "다시 시도는 가능하지만 결과 반영은 한 번만 되는가?"를 먼저 묻고, 그 답이 없으면 idempotency key, side effect 분리, fresh transaction 경계를 요청하거나 차단 문장으로 닫는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Retry Envelope 위치 Primer](./spring-retry-envelope-placement-primer.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)
- [Transaction Boundary 외부 I/O 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)
- [System Design: Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: idempotency review sentence card, whole transaction retry review, duplicate write review comment, retry outside transactional review, idempotency key review phrase, outbox duplicate side effect review, replay safe retry review, same request duplicate payment review, transaction retry blocker phrase, reviewer sentence idempotency card, whole-transaction retry beginner, duplicate write beginner

## 먼저 보는 장면

초보자는 이 장면을 "`재시도` 버튼이 아니라 `되감기 + 다시 실행`"으로 보면 쉽다.

- `40001`, deadlock, timeout 뒤 retry loop가 보인다.
- 그런데 주문 생성, 결제 승인, 이벤트 발행 같은 write도 같이 감싸져 있다.
- 이때 핵심 질문은 "`다시 해도 되나?`"가 아니라 **"`두 번 반영돼도 안전한가?`"** 다.

짧게 고정하면 이렇다.

| 보이는 코드 냄새 | 초보자 해석 | 리뷰 초점 |
|---|---|---|
| `@Transactional` 안에서 재시도 | 같은 시도를 되살리려는 착시일 수 있다 | 새 transaction per attempt인지 |
| DB write와 외부 API가 같은 loop 안 | commit 전후 어긋나면 중복 부작용이 난다 | outbox/멱등성 분리 여부 |
| duplicate 뒤 blind retry | 이미 winner가 있는데 loser만 반복할 수 있다 | fresh read/replay 계약 여부 |

## 30초 체크표

| 먼저 물을 것 | yes면 | no면 |
|---|---|---|
| retry가 매번 새 transaction으로 시작되나 | 다음으로 간다 | `@Transactional` 바깥 retry 경계 요청 |
| 같은 요청을 구분할 idempotency key/business key가 있나 | 다음으로 간다 | duplicate write 위험 지적 |
| 외부 side effect가 outbox 또는 replay-safe 계약으로 분리됐나 | bounded retry 후보가 된다 | 중복 결제/중복 발행 차단 |
| duplicate 뒤 기존 결과 replay/fresh read가 있나 | 사용자 응답 계약까지 닫힌다 | blind retry 수정 요청 |

이 표에서 하나라도 `no`면 "retry 자체"보다 **중복 반영 위험**을 먼저 적는 편이 안전하다.

## 바로 붙이는 리뷰 문장

### 질문형

- "이 retry가 whole transaction을 새로 시작하는 구조인가요, 아니면 같은 `@Transactional` 시도를 안에서 다시 돌리는 구조인가요?"
- "같은 요청이 두 번 들어왔을 때 `idempotency key`나 business key로 기존 결과를 replay하는 경로가 있나요?"
- "DB commit 직전/직후에 실패해도 외부 호출이 두 번 나가지 않도록 outbox나 별도 멱등성 계약이 있나요?"
- "`DuplicateKeyException` 뒤에 같은 insert를 다시 retry하지 않고, winner row fresh read로 상태를 재분류하나요?"

### 요청형

- "retry 경계를 `@Transactional` 바깥 facade/application service로 올리고, attempt마다 새 transaction이 열리게 분리해 주세요."
- "이 write path에는 같은 요청 재전송을 구분할 `idempotency key` 또는 명시적 business key를 추가해 주세요."
- "외부 API 호출/이벤트 발행은 retry loop 안에 두지 말고 outbox 또는 replay-safe publish 단계로 분리해 주세요."
- "duplicate 발생 시 blind retry 대신 fresh read 후 `processing`/replay/`409 conflict`로 닫는 계약을 코드에 드러내 주세요."

### 차단형

- "현재 구조는 whole-transaction retry가 중복 write를 만들 수 있어서 그대로 merge하기 어렵습니다."
- "`@Transactional` 안 재시도 + 외부 side effect 동시 수행은 commit 경계가 어긋날 때 중복 결제/중복 발행 위험이 있어 차단이 필요합니다."
- "idempotency key 없이 retry만 추가하면 장애 복구가 아니라 duplicate 생성기로 바뀔 수 있어, 중복 방지 계약이 먼저 필요합니다."
- "duplicate 뒤 결과 재조회 없이 재삽입만 반복하는 흐름은 winner/loser를 구분하지 못해서 리뷰 기준상 통과시키기 어렵습니다."

## 자주 헷갈리는 한 쌍

| 헷갈리는 말 | 같은 뜻이 아닌 이유 |
|---|---|
| retry 가능 | 중복 write까지 안전하다는 뜻은 아니다 |
| duplicate key | 무조건 재시도 대상이 아니라 winner 존재 신호일 수 있다 |
| `processing` | 영구 실패가 아니라 기존 요청 진행 중 안내일 수 있다 |
| `REQUIRES_NEW` | retry 복구가 아니라 중간 commit 조각내기일 수 있다 |

리뷰에서 가장 덜 흔들리는 한 줄은 이것이다.

> "`재시도 가능`과 `중복 반영 안전`을 분리해서 확인해 주세요."

## 한 줄 정리

whole-transaction retry 리뷰는 "다시 시도해도 되는가?"보다 "같은 요청이 두 번 반영되지 않는가?"를 먼저 확인하고, 답이 없으면 idempotency key, fresh transaction 경계, side effect 분리를 질문형/요청형/차단형 문장으로 바로 남기면 된다.
