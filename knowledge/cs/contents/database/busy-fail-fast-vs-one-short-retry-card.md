---
schema_version: 3
title: Busy Fail Fast vs One Short Retry Card
concept_id: database/busy-fail-fast-vs-one-short-retry-card
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 86
mission_ids:
- missions/roomescape
review_feedback_tags:
- busy-fail-fast
- short-retry
- lock-timeout
- retry-outcome-language
aliases:
- busy fail fast vs short retry
- busy one short retry card
- busy bucket retry policy beginner
- lock timeout fail fast retry once
- connection timeout busy retry once
- busy should fail fast
- busy short bounded retry
- busy 즉시 실패 짧은 재시도
- 락 타임아웃 한 번 재시도
- busy retry 기준
symptoms:
- busy를 retryable과 같은 뜻으로 보고 lock timeout이나 pool contention에서 blind retry를 여러 번 건다
- hot row나 connection pool 혼잡이 보이는데 fail fast 대신 wait와 retry를 늘려 queue를 더 길게 만든다
- 같은 idempotent key 경쟁처럼 한 번만 더 보면 already exists로 재분류될 수 있는 경우와 그렇지 않은 busy를 구분하지 못한다
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/three-bucket-terms-common
- database/lock-timeout-not-already-exists-common-confusion-card
next_docs:
- database/insert-if-absent-retry-outcome-guide
- database/idempotent-transaction-retry-envelopes
- database/connection-timeout-vs-lock-timeout-card
linked_paths:
- contents/database/three-bucket-terms-common-card.md
- contents/database/lock-timeout-not-already-exists-common-confusion-card.md
- contents/database/nowait-vs-short-lock-timeout-busy-guide.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
confusable_with:
- database/booking-guard-row-retry-card
- database/insert-if-absent-retry-outcome-guide
- database/idempotent-transaction-retry-envelopes
- database/connection-timeout-vs-lock-timeout-card
forbidden_neighbors: []
expected_queries:
- busy는 기본 fail fast이고 언제만 한 번 짧게 retry해도 되는지 기준을 알려줘
- lock timeout이 busy로 분류됐을 때 무한 retry가 아니라 1회 확인성 retry만 허용하는 이유가 뭐야?
- 같은 idempotency key 경쟁에서 한 번 더 보면 already exists로 재분류될 수 있는 경우를 설명해줘
- connection pool timeout이나 hot row contention에서는 왜 retry보다 빠른 busy 응답이 기본이야?
- busy와 retryable, already exists를 beginner가 구분하는 체크리스트를 보여줘
contextual_chunk_prefix: |
  이 문서는 Busy Fail Fast vs One Short Retry Card beginner chooser로, busy bucket은 기본적으로
  fail fast 혼잡 신호이며 같은 key/idempotent request의 winner가 곧 확정될 가능성이 높을 때만
  1회 짧은 확인성 retry를 허용하는 기준을 설명한다.
---
# `busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?

> 한 줄 요약: `busy`의 기본값은 무한 retry가 아니라 **빠른 실패**이고, "곧 풀릴 가능성이 높고 같은 요청을 한 번 더 확인하는 비용이 작다"는 조건일 때만 **짧은 1회 재시도**를 붙인다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [`NOWAIT`와 짧은 `lock timeout`은 왜 자동 retry보다 `busy`에 더 가깝게 볼까?](./nowait-vs-short-lock-timeout-busy-guide.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: busy fail fast vs short retry, busy one short retry card, busy bucket retry policy beginner, lock timeout fail fast retry once, connection timeout busy retry once, busy should fail fast, busy short bounded retry, busy 즉시 실패 짧은 재시도, 락 타임아웃 한 번 재시도, beginner busy bucket checklist, busy fast fail primer, 왜 busy면 바로 실패해요, busy retry what is basics, 처음 busy 재시도 기준

## 먼저 멘탈모델

`busy`는 "지금 줄이 막혀 있다"는 뜻이지, "조금만 더 하면 반드시 성공한다"는 뜻이 아니다.

그래서 초보자는 이렇게 먼저 잡으면 된다.

- 기본값: **fail fast**
- 예외: **한 번만 짧게 retry**

핵심 질문은 1개다.

> "이 실패가 잠깐 줄이 막힌 정도라서, 같은 요청을 한 번만 더 확인해도 해석이 더 좋아질까?"

## 이런 질문이면 먼저 이 카드로 온다

아래 질문은 `retryable` playbook보다 이 카드가 먼저다.

- "`busy`면 몇 번 재시도해야 하나요?"
- "lock timeout이 떴는데 바로 실패해야 하나요?"
- "한 번만 다시 보면 `already exists`로 바뀔 수도 있나요?"

핵심은 "성공률을 높이기 위한 무한 retry"가 아니라 "서비스 결과를 더 정확히 번역하기 위한 짧은 확인 1회"인지 구분하는 것이다.

## 한 장 비교표

| 질문 | `fail fast`가 기본인 경우 | `1회 짧은 retry`를 허용해도 되는 경우 |
|---|---|---|
| 막힌 이유가 뚜렷한가 | pool 고갈, hot row, 긴 트랜잭션이 이미 보여서 바로 혼잡 신호로 읽는 편이 낫다 | 같은 key 경쟁처럼 "바로 앞 요청이 곧 끝날" 가능성이 크다 |
| retry가 결과 해석을 바꾸는가 | 다시 해도 여전히 `busy`일 가능성이 높다 | 한 번 더 보면 `already exists`나 성공으로 재분류될 수 있다 |
| 요청 비용이 작은가 | 외부 I/O, 긴 트랜잭션, fan-out이 다시 걸린다 | 같은 멱등 요청을 짧게 한 번 더 확인하는 수준이다 |
| 초보자 기본 선택 | 즉시 `busy` 응답 | 20~100ms 정도 짧게 기다린 뒤 1회만 다시 확인 |

짧게 외우면:

- `busy`는 원칙적으로 장애 복구용 retry가 아니라 **혼잡 신호**
- 다만 winner가 거의 곧 확정될 장면이면 **1회 짧은 확인성 retry**는 가능

## 가장 작은 예시

쿠폰 발급에서 `(event_id, user_id)`가 유일하다고 하자.

1. 요청 A가 insert를 거의 끝내기 직전이다.
2. 요청 B는 같은 key로 들어와 lock wait 끝에 `busy`로 분류됐다.
3. 이때 B가 30ms 정도 쉬고 **딱 한 번** fresh read 또는 동일 멱등 경로를 다시 보면:
4. 결과가 `busy`에서 `already exists`로 바뀔 수 있다.

반대로 pool 고갈 때문에 `Connection is not available`이 난 경우는 다르다.

- 다시 때리면 같은 풀 입구에서 또 막힐 가능성이 높다.
- 이 경우 `busy`는 곧바로 fail fast 하는 편이 보통 더 낫다.

처음 판단할 때는 "재시도로 성공률을 올리나?"보다 "재시도로 결과 해석이 더 또렷해지나?"를 먼저 묻는 편이 안전하다.

## 초보자용 4문항 체크리스트

아래 4개 중 **3개 이상이 예**면 `1회 짧은 retry`를 고려할 수 있다.

1. 같은 key/같은 멱등 요청의 바로 직전 경쟁처럼 보이는가?
2. retry가 새 트랜잭션 폭증이 아니라 짧은 확인 1회 수준인가?
3. 한 번 더 보면 성공 또는 `already exists`로 해석이 더 또렷해질 가능성이 큰가?
4. retry 횟수를 `1회`로 고정하고, 실패 시 바로 `busy`로 끝낼 수 있는가?

하나라도 강하게 아니오가 나오면, 초보자 기본값은 그냥 fail fast다.

## 자주 쓰는 판단 요약

| 신호 | beginner 기본 선택 | 이유 |
|---|---|---|
| `Connection is not available`, `threads awaiting connection` | fail fast | 풀 혼잡은 한 번 더 때려도 같은 입구에서 막히기 쉽다 |
| `lock timeout` on same key, winner가 거의 끝날 것 같음 | 1회 짧은 retry 가능 | 재시도 후 `already exists`나 성공으로 바뀔 여지가 있다 |
| `deadlock`, `40001` | 이 카드의 대상 아님 | 이것은 `busy`보다 `retryable` 규칙으로 본다 |
| blocker 원인이 긴 외부 I/O / 장기 트랜잭션 | fail fast | 한 번 더 시도해도 줄이 금방 풀릴 가능성이 낮다 |

`NOWAIT`나 아주 짧은 `lock timeout`처럼 애초에 "오래 기다리지 않겠다"는 lock budget이 들어간 경로를 따로 떼어 보고 싶으면 [`NOWAIT`와 짧은 `lock timeout`은 왜 자동 retry보다 `busy`에 더 가깝게 볼까?](./nowait-vs-short-lock-timeout-busy-guide.md)를 같이 보면 된다.

## 흔한 오해

- "`busy`면 일단 여러 번 재시도해도 된다"
  - 아니다. 초보자 기본값은 `0회` 또는 많아야 `1회`다.
- "`busy` 재시도는 `retryable`과 같다"
  - 아니다. `retryable`은 보통 새 트랜잭션 전체 재시도이고, 여기서 말하는 것은 짧은 확인성 retry다.
- "`lock timeout`이면 무조건 재시도 이득이 있다"
  - 아니다. hot row가 길게 막힌 상황이면 한 번 더 해도 똑같이 막힐 수 있다.
- "응답을 부드럽게 만들려면 retry를 많이 넣는 편이 낫다"
  - 아니다. 혼잡 구간에서 blind retry는 큐를 더 길게 만들 수 있다.

- "`busy`와 `40001`은 어차피 둘 다 다시 해보면 되는 것 아닌가요?"
  - 아니다. `busy`는 보통 fail-fast 또는 1회 짧은 확인이고, `40001`은 새 트랜잭션 whole retry 쪽 규칙이다.

## 한 줄 가이드

- 같은 요청의 winner가 **곧 확정될 가능성**이 높으면: 짧은 `1회` retry
- 그 외 대부분의 `busy`는: 바로 `busy`로 fail fast

## 다음에 이어서 볼 문서

- `busy` / `retryable` / `already exists` 전체 번역표는 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- `busy`를 pool 대기와 lock 대기로 다시 나누려면 [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- retry를 메서드 안 while문이 아니라 바깥 envelope로 거는 이유는 [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- retry를 트랜잭션 boundary 바깥에서 감싸는 이유를 Spring 코드로 보면 [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)

## 한 줄 정리

`busy`의 기본값은 무한 retry가 아니라 **빠른 실패**이고, "곧 풀릴 가능성이 높고 같은 요청을 한 번 더 확인하는 비용이 작다"는 조건일 때만 **짧은 1회 재시도**를 붙인다.
