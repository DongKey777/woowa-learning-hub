# Batch Run Result Modeling Examples

> 한 줄 요약: 배치 결과 모델은 "이번 실행 영수증", "이번 chunk 영수증", "나중에 다시 볼 후보", "이어 달릴 책갈피"를 각각 `RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`로 나누면 초심자도 실패 정책을 설명하기 쉬워진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Software Engineering README](./README.md#batch-run-result-modeling-examples)
- [Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)
- [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
- [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)
- [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
- [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
- [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
- [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
- [System Design: Job Queue 설계](../system-design/job-queue-design.md)

retrieval-anchor-keywords: batch run result modeling, run summary example, chunk result example, retry candidate example, checkpoint type example, batch result type basics, batch status model beginner, 배치 결과 모델링 처음, chunk retry checkpoint intro, run summary what is, batch idempotency key boundaries, item-level idempotency key, chunk-level idempotency key, run-level idempotency key, terminal failure in batch result, terminal failure count summary, terminal failure vs retry backlog, batch terminal result modeling, terminal failure beginner primer

## 핵심 개념

배치 결과 모델링은 먼저 "무엇을 기억해야 다음 행동을 정할 수 있는가"를 나누는 일이다.

- `RunSummary`는 실행 전체의 영수증이다.
- `ChunkResult`는 작은 묶음 하나의 영수증이다.
- `RetryCandidate`는 main run에서 분리해 나중에 다시 볼 대상이다.
- `Checkpoint`는 같은 run을 어디서 다시 시작할지 알려 주는 책갈피다.

이 네 타입은 특정 프레임워크의 클래스 이름이 아니다.
언어에 따라 record, class, struct, JSON message가 될 수 있지만, 초심자에게 중요한 것은 "역할이 다르므로 한 타입에 뭉치지 않는다"는 점이다.

## 한눈에 보기

| 타입 | 한 문장 비유 | 주로 답하는 질문 |
|---|---|---|
| `RunSummary` | 실행 전체 영수증 | 이번 run은 성공인가, 부분 성공인가, 운영자가 다음에 무엇을 봐야 하나 |
| `ChunkResult` | chunk 하나의 영수증 | 이 chunk에서 몇 건이 처리됐고 어떤 실패가 생겼나 |
| `RetryCandidate` | 나중에 다시 볼 후보 카드 | 이 item은 왜 실패했고 바로 재시도해도 되나 |
| `Checkpoint` | 이어 달릴 책갈피 | 장애 후 같은 run을 어디서 다시 시작해야 하나 |

count만 반환하면 네 질문이 한데 섞인다.
그래서 `successCount=1180, failureCount=20`만으로는 재개, 재시도, 수동 확인, 운영 보고를 안정적으로 분리하기 어렵다.

## 예시 상황

상품 1,200개를 파트너 검색 서비스에 동기화한다고 하자.
한 번의 run은 오전 9시 snapshot을 대상으로 하고, 300개씩 네 chunk로 나누어 보낸다.

운영자가 알고 싶은 말은 네 가지다.

- "오전 9시 동기화 run은 전체적으로 어떤 상태인가?"
- "2번째 chunk에서만 왜 7건이 실패했나?"
- "그 7건 중 바로 재시도할 대상과 사람이 봐야 할 대상은 무엇인가?"
- "서버가 3번째 chunk 뒤에서 죽었다면 어디서 다시 시작하나?"

이 질문에 맞춰 타입을 나누면 결과 모델이 과하게 커지는 대신, 각 타입의 책임이 작고 읽기 쉬워진다.

## 타입별 초심자 예시

아래 예시는 구조를 보여 주기 위한 중립적인 모양이다.
특정 언어의 문법이나 프레임워크 annotation으로 읽지 않아도 된다.

```text
RunSummary
- runId: product-sync-2026-04-23-09
- status: completed-with-retry-candidates
- totalChunks: 4
- requestedItems: 1200
- succeededItems: 1188
- failedItems: 12
- retryCandidateCount: 9
- manualReviewCount: 3
- terminalFailureCount: 0
- latestCheckpoint: after chunk 4
```

```text
ChunkResult
- runId: product-sync-2026-04-23-09
- chunkNo: 2
- requestedItems: 300
- succeededItems: 293
- failedItems: 7
- retryCandidates: item-491, item-492, item-499
- terminalFailures: none
- nextCheckpoint: after chunk 2
```

```text
RetryCandidate
- itemId: item-491
- sourceChunkNo: 2
- reasonCode: partner-timeout
- retryable: true
- attemptCount: 1
- nextAction: retry later with same idempotency key
```

```text
Checkpoint
- runId: product-sync-2026-04-23-09
- snapshotTime: 2026-04-23 09:00
- lastCompletedChunkNo: 2
- nextCursor: product-id > item-600
- resumeMode: continue same snapshot
```

## 작은 follow-up: terminal failure는 retry backlog가 아니다

초심자가 가장 많이 헷갈리는 지점은 이것이다.

- `RetryCandidate`는 "나중에 다시 처리할 카드"다
- terminal failure는 "이번 정책에서는 여기서 종료하는 실패"다

둘 다 실패이지만, 다음 행동이 다르다.
그래서 terminal failure를 retry backlog 수에 섞으면 운영자가 "나중에 다시 돌릴 12건"으로 오해하게 된다.

### 가장 쉬운 판단

| 분류 | 다음 행동 | 결과 타입에서 보통 어디에 남기나 |
|---|---|---|
| retryable failure | 자동 또는 지연 재시도 | `RetryCandidate` + `retryCandidateCount` |
| manual review failure | 사람이 먼저 확인 | `manualReviewCount` 또는 별도 review bucket |
| terminal failure | 이번 run에서 종료 | `terminalFailureCount` 또는 `terminalFailures` |

terminal failure는 "실패를 숨긴다"가 아니다.
오히려 summary와 chunk result에 **명시적으로 남기되 retry backlog와 분리**하는 것이 핵심이다.

### 같은 run을 terminal failure까지 포함해 다시 써 보면

예를 들어 12건 실패 중 9건은 timeout, 2건은 잘못된 상품 코드, 1건은 지원하지 않는 국가라고 하자.

- timeout 9건: retry backlog로 보낸다
- 잘못된 상품 코드 2건: manual review로 보낸다
- 지원하지 않는 국가 1건: terminal failure로 종료한다

이 장면을 `RunSummary`에 적으면 아래처럼 읽힌다.

```text
RunSummary
- runId: product-sync-2026-04-23-09
- status: completed-with-follow-up
- requestedItems: 1200
- succeededItems: 1188
- failedItems: 12
- retryCandidateCount: 9
- manualReviewCount: 2
- terminalFailureCount: 1
```

중요한 점은 `failedItems=12`와 `retryCandidateCount=9`가 같을 필요가 없다는 것이다.
실패 전체와 retry backlog는 같은 숫자가 아니다.

`ChunkResult`도 같은 원칙으로 읽는다.

```text
ChunkResult
- chunkNo: 2
- failedItems: 3
- retryCandidates: item-491
- manualReviewItems: item-492
- terminalFailures: item-493
```

이렇게 남기면 운영자는 바로 구분할 수 있다.

- `item-491`은 다시 돌릴 수 있다
- `item-492`는 사람이 먼저 본다
- `item-493`는 이번 정책상 종료된 실패다

### 자주 하는 혼동

| 흔한 표현 | 왜 위험한가 | 더 안전한 표현 |
|---|---|---|
| `failedItems` 전부를 retry backlog로 본다 | 종료 실패까지 재시도 대상으로 오해한다 | `failedItems`와 `retryCandidateCount`를 따로 둔다 |
| terminal failure는 summary에서 뺀다 | 실패가 사라져 운영 보고가 흐려진다 | summary에는 남기되 retry 수와 분리한다 |
| checkpoint에 terminal item 목록을 같이 넣는다 | 진행 위치와 실패 결과가 섞인다 | checkpoint는 위치만, terminal은 result/summary에 둔다 |

초심자는 아래 한 문장으로 기억하면 충분하다.

- **retry backlog는 "다시 볼 일감", terminal failure는 "끝난 실패 기록"이다**

## 흔한 오해와 함정

| 오해 | 더 안전한 첫 판단 |
|---|---|
| `RunSummary`가 있으면 `ChunkResult`는 필요 없다 | 전체 보고와 chunk 원인 분석은 질문이 다르다 |
| `Checkpoint`에 실패 item을 다 넣으면 된다 | checkpoint는 진행 위치이고 실패 backlog는 `RetryCandidate`가 맡는다 |
| `RetryCandidate`는 무조건 즉시 재시도 대상이다 | validation 실패처럼 수동 확인 후 재시도해야 하는 후보도 있다 |
| terminal failure도 retry backlog count에 포함하면 편하다 | 실패 총수와 retry backlog는 다른 숫자여야 운영 해석이 맞다 |
| `ChunkResult`는 로그로 충분하다 | 후속 queue 이동이나 운영 판단에 쓰이면 결과 계약으로 남겨야 한다 |
| 네 타입을 만들면 무조건 무겁다 | run 의미가 있는 배치에서는 오히려 책임이 작아져 테스트와 설명이 쉬워진다 |

핵심은 타입 수를 늘리는 것이 아니라 질문을 섞지 않는 것이다.
작고 독립적인 batch라면 실패 item id 목록만으로 충분할 수 있다.
하지만 run/chunk/retry/resume 질문이 동시에 나오면 네 이름을 분리하는 편이 초심자에게도 더 명확하다.

## 실무에서 쓰는 흐름

처리 흐름은 보통 아래처럼 읽으면 된다.

1. run을 시작할 때 `RunSummary` 초안을 만들고 snapshot 기준을 고정한다.
2. chunk 하나를 처리한 뒤 `ChunkResult`를 남긴다.
3. 실패 item 중 다시 볼 대상은 `RetryCandidate`로 분리하고, terminal failure는 result에 종료 기록으로 남긴다.
4. 안전하게 완료한 지점은 `Checkpoint`로 저장한다.
5. 마지막에 chunk 결과들을 모아 최종 `RunSummary`를 갱신한다.

이 흐름은 job scheduler, message queue, HTTP 관리 버튼 중 무엇으로 시작하든 크게 달라지지 않는다.
프레임워크는 실행 트리거를 제공할 뿐이고, 네 타입은 애플리케이션이 실패와 재개를 설명하는 언어다.

테스트 fixture를 만들 때도 같은 분리가 도움이 된다.
`RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`를 한 giant helper로 뭉치기보다, 각 타입 뜻이 보이는 작은 fixture로 나누는 예시는 [Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)에서 이어서 볼 수 있다.

## 더 깊이 가려면

이 문서는 타입 이름을 잡는 초심자용 예시다.
정책 판단이 먼저 필요하면 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)에서 per-item retry, retry queue, checkpoint의 차이를 먼저 본다.
terminal failure를 retry queue assertion과 어떻게 분리해 테스트할지 바로 보고 싶다면 [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)를 이어서 본다.
재시도와 resume에서 어떤 idempotency key를 재사용해야 하는지는 [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)에서 item/chunk/run 경계로 나눠 본다.
테스트 데이터를 어떻게 읽기 쉽게 재사용할지 고민되면 [Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)에서 fixture naming과 조립 순서를 먼저 좁혀 볼 수 있다.
result count와 bucket 분리를 실제 assertion으로 잠그는 순서는 [Batch Result Testing Checklist](./batch-result-testing-checklist.md)에서 이어서 볼 수 있다.
bulk 입력/결과 계약까지 커졌다면 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)에서 run/chunk/file 이름 붙이기를 이어서 보면 된다.
실제 재시도 backlog가 별도 worker나 queue로 넘어가면 [System Design: Job Queue 설계](../system-design/job-queue-design.md)로 책임을 넘겨 읽는다.

## 한 줄 정리

`RunSummary`는 전체 실행, `ChunkResult`는 작은 묶음, `RetryCandidate`는 실패 item의 다음 경로, `Checkpoint`는 run 재개 지점을 설명한다.
