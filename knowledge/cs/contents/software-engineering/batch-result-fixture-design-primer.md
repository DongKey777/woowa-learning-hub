---
schema_version: 3
title: Batch Result Fixture Design Primer
concept_id: software-engineering/batch-result-fixtures
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 89
mission_ids:
- missions/payment
review_feedback_tags:
- batch-testing
- fixture-design
- readable-tests
aliases:
- Batch Result Fixture Design Primer
- batch result fixture
- run summary fixture
- chunk result fixture
- retry candidate fixture
- checkpoint fixture
- 배치 결과 테스트 fixture
symptoms:
- batch 테스트 fixture가 run, chunk, retry, checkpoint 의미를 모두 숨기는 giant helper가 되어 테스트에서 다음 행동을 읽을 수 없어
- fixture를 전혀 두지 않아 runId, chunkNo, itemId, reasonCode, checkpoint setup이 반복돼 테스트 의도가 묻혀
- product sync 2번째 chunk 실패 같은 도메인 장면 이름을 남기지 않고 caseA, defaultResult 같은 이름으로 의미를 잃어
intents:
- definition
- design
- troubleshooting
prerequisites:
- software-engineering/batch-result-modeling
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/batch-fixture-builder
- software-engineering/runsummary-fixture-naming
- software-engineering/batch-result-testing
linked_paths:
- contents/software-engineering/batch-run-result-modeling-examples.md
- contents/software-engineering/batch-result-testing-checklist.md
- contents/software-engineering/runsummary-fixture-naming-mini-primer.md
- contents/software-engineering/retry-queue-assertions-primer.md
- contents/software-engineering/testing-named-bulk-contracts.md
- contents/software-engineering/batch-fixture-builder-vs-factory-smells.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
- contents/software-engineering/batch-recovery-runbook-bridge.md
- contents/software-engineering/batch-idempotency-key-boundaries.md
confusable_with:
- software-engineering/batch-fixture-builder
- software-engineering/batch-result-modeling
- software-engineering/batch-result-testing
forbidden_neighbors: []
expected_queries:
- batch 결과 fixture를 RunSummary ChunkResult RetryCandidate Checkpoint 네 조각으로 나누는 이유가 뭐야?
- batch 테스트 fixture 이름에 product sync 2번째 chunk timeout 같은 도메인 의미를 남겨야 하는 이유를 알려줘
- createFailureCaseA 같은 흐린 fixture보다 partnerTimeoutRetryCandidate item491이 읽기 쉬운 이유는 뭐야?
- batch result fixture를 작게 재사용하면서도 테스트 장면을 숨기지 않는 방법을 알려줘
- run fixture chunk fixture retry fixture checkpoint fixture는 각각 어떤 테스트 질문에 대응해?
contextual_chunk_prefix: |
  이 문서는 batch result test fixture를 RunSummary, ChunkResult, RetryCandidate, Checkpoint 조각으로 나누고 domain scene 이름을 보존하는 beginner primer다.
---
# Batch Result Fixture Design Primer

> 한 줄 요약: batch 결과 fixture는 `run`, `chunk`, `retry`, `checkpoint`를 작게 나누어 재사용하되, `상품 동기화 2번째 chunk 실패` 같은 도메인 뜻이 이름에 그대로 남아 있어야 초심자 테스트가 덜 흐려진다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: batch result fixture design primer, batch fixture beginner, batch result test fixture, runsummary fixture example, chunkresult fixture example, retrycandidate fixture example, checkpoint fixture example, batch fixture naming, 배치 fixture 처음, 배치 결과 테스트 fixture 뭐부터, runsummary fixture 어떻게 만들지, fixture 이름 왜 길어도 되나요, fixture가 의미를 숨겨요, 테스트 fixture가 너무 거대해요, 처음 배우는데 batch fixture
`RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint` 같은 결과 타입 이름은 알겠는데 테스트 fixture를 어떻게 만들지 막막하다면, 이 문서는 그 첫 설계를 좁혀서 설명한다.
특히 `배치 결과 테스트 fixture 뭐부터 만들지`, `RunSummary/ChunkResult fixture를 왜 나누지`, `retry 후보 fixture 이름을 어떻게 짓지` 같은 첫 질문을 이 문서가 바로 받도록 맞춰 둔다.
[Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)에서 결과 타입 역할을 먼저 잡았다면, 여기서는 그 타입들을 테스트에서 **작게 재사용하면서도 도메인 의미를 숨기지 않는 방법**만 본다.
더 넓은 결과 검증 질문은 [Batch Result Testing Checklist](./batch-result-testing-checklist.md), retry 후보 분류 assertion은 [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md), bulk 계약 경계 자체 테스트는 [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)를 이어서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 그림](#먼저-잡을-그림)
- [왜 fixture 설계가 따로 필요한가](#왜-fixture-설계가-따로-필요한가)
- [fixture를 네 조각으로 나누기](#fixture를-네-조각으로-나누기)
- [좋은 fixture와 흐린 fixture 비교](#좋은-fixture와-흐린-fixture-비교)
- [예시: 상품 동기화 batch fixture](#예시-상품-동기화-batch-fixture)
- [작게 재사용하는 조립 순서](#작게-재사용하는-조립-순서)
- [짧은 비교 표](#짧은-비교-표)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

> 관련 문서:
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [RunSummary Fixture Naming Mini Primer](./runsummary-fixture-naming-mini-primer.md)
> - [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)
> - [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
> - [Batch Fixture Builder vs Factory Smells](./batch-fixture-builder-vs-factory-smells.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
> - [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
>
> retrieval-anchor-keywords:
> - batch result fixture design primer
> - batch fixture design beginner
> - run chunk retry checkpoint fixture
> - batch fixture naming primer
> - reusable batch test fixture
> - readable batch fixture
> - domain meaning fixture
> - batch test data builder primer
> - run summary fixture example
> - chunk result fixture example
> - retry candidate fixture example
> - checkpoint fixture example
> - batch fixture without hiding domain meaning
> - fixture helper naming batch
> - product sync batch fixture
> - small reusable fixture for batch test
> - opaque fixture helper smell
> - batch test builder readable code
> - fixture composition run chunk retry checkpoint
> - beginner batch testing fixtures
> - batch fixture builder vs factory smells
> - run summary fixture naming
> - 배치 fixture 뭐부터 만들지
> - 배치 결과 테스트 fixture 뭐부터
> - 처음 배우는데 배치 fixture
> - RunSummary fixture 어떻게 만들지
> - ChunkResult fixture 어떻게 만들지
> - RetryCandidate fixture 어떻게 만들지
> - Checkpoint fixture 어떻게 만들지
> - fixture 이름이 너무 길어도 되나요
> - fixture helper가 의미를 숨겨요
> - 테스트 fixture가 너무 거대해요

## 먼저 잡을 그림

초심자는 batch fixture를 아래 네 장의 카드로 기억하면 충분하다.

- `run fixture`: 이번 실행 전체 상황 카드
- `chunk fixture`: 몇 번째 묶음에서 무슨 일이 있었는지 카드
- `retry fixture`: 실패 item의 다음 행동 카드
- `checkpoint fixture`: 어디서 다시 시작할지 카드

`RunSummary` status fixture 이름을 `green-path`, `partial-failure`, `duplicate-start` 장면으로 먼저 고정하는 더 작은 naming 규칙은 [RunSummary Fixture Naming Mini Primer](./runsummary-fixture-naming-mini-primer.md)에서 바로 이어서 볼 수 있다.

핵심은 fixture가 "값 많이 채워 주는 도우미"가 아니라는 점이다.
fixture는 **테스트가 읽어야 할 장면을 짧게 꺼내는 도구**다.

그래서 아래 둘의 차이가 중요하다.

- 좋은 fixture: `partnerTimeoutRetryCandidate(item-491)`
- 흐린 fixture: `createFailureCaseA()`

둘 다 테스트를 통과시킬 수는 있다.
하지만 두 번째는 "왜 실패했고 다음에 무엇을 해야 하는가"를 이름에서 잃는다.

## 왜 fixture 설계가 따로 필요한가

batch 결과 테스트는 값이 많아지기 쉽다.
`runId`, `chunkNo`, `itemId`, `reasonCode`, `attemptCount`, `lastCompletedChunkNo`가 한 테스트에 같이 나오기 시작하면 초심자는 금방 길을 잃는다.

이때 흔히 두 극단으로 간다.

| 극단 | 문제 |
|---|---|
| fixture가 전혀 없다 | 같은 setup이 반복돼 테스트가 길어진다 |
| fixture가 모든 의미를 숨긴다 | 테스트가 짧아져도 무엇을 검증하는지 읽기 어려워진다 |

이 문서의 목표는 가운데 지점이다.

- 반복은 줄인다
- 하지만 run/chunk/retry/checkpoint 의미는 이름에 남긴다

즉 fixture는 "짧지만 설명 가능한 테스트 데이터"를 만드는 쪽이 좋다.

## fixture를 네 조각으로 나누기

결과 타입을 한 giant fixture로 합치지 말고, 질문 단위로 나누면 읽기 쉬워진다.

| fixture 조각 | 주로 담는 뜻 | 테스트가 주로 묻는 질문 |
|---|---|---|
| `runFixture` | 이번 실행 전체 상태 | 전체 상태와 count가 맞는가 |
| `chunkFixture` | 특정 chunk의 처리 결과 | 실패가 몇 번째 묶음의 것인가 |
| `retryFixture` | 재시도/수동 확인 분류 | 이 실패를 다음에 어디로 보낼까 |
| `checkpointFixture` | 재개 지점 | 어디서 다시 시작해야 하나 |

작게 나누는 이유는 재사용 범위를 줄이기 위해서다.

- chunk 테스트는 chunk fixture만 주로 읽는다
- retry 분류 테스트는 retry fixture만 집중해서 읽는다
- resume 테스트는 checkpoint fixture가 중심이 된다

한 fixture가 네 질문을 모두 대신하면, 이름은 짧아져도 테스트 뜻은 오히려 흐려진다.

## 좋은 fixture와 흐린 fixture 비교

아래처럼 비교하면 감이 빨리 온다.

| 흐린 형태 | 더 읽기 쉬운 형태 | 이유 |
|---|---|---|
| `Fixtures.failedRun()` | `productSyncRunWithRetryCandidates()` | 어떤 run인지 드러난다 |
| `Fixtures.chunk2()` | `failedProductSyncChunk(2)` | 실패 의미와 chunk 번호가 같이 남는다 |
| `Fixtures.retryCase()` | `partnerTimeoutRetryCandidate(item-491)` | reason과 대상 item이 드러난다 |
| `Fixtures.savedCheckpoint()` | `checkpointAfterChunk(2)` | 재개 지점이 바로 읽힌다 |
| `Fixtures.defaultResult()` 후 수동 수정 | 작은 기본 fixture 조합 | 어떤 값이 중요한지 테스트마다 보인다 |

fixture 이름이 길어지는 것이 항상 나쁜 것은 아니다.
초심자 문맥에서는 `chunk2FailureAfterPartnerTimeout`처럼 뜻이 남는 이름이 `caseA`보다 훨씬 낫다.

## 예시: 상품 동기화 batch fixture

예시 상황을 하나로 고정하자.

- 오전 9시 상품 동기화 run이 있다
- 300개씩 chunk를 보낸다
- 2번째 chunk에서 `item-491`이 partner timeout으로 실패했다
- 같은 run은 2번째 chunk 뒤에서 재개할 수 있어야 한다

이때 fixture를 아래처럼 작게 만들 수 있다.

```text
run fixture
- runId: product-sync-2026-04-27-09
- status: completed-with-retry-candidates
- requestedItems: 1200
- succeededItems: 1199
- failedItems: 1
```

```text
chunk fixture
- runId: product-sync-2026-04-27-09
- chunkNo: 2
- requestedItems: 300
- succeededItems: 299
- failedItems: 1
```

```text
retry fixture
- itemId: item-491
- sourceChunkNo: 2
- reasonCode: partner-timeout
- retryable: true
- nextAction: retry-later
```

```text
checkpoint fixture
- runId: product-sync-2026-04-27-09
- lastCompletedChunkNo: 2
- nextCursor: product-id > item-600
- resumeMode: continue same snapshot
```

이 네 조각은 각자 작다.
하지만 조립하면 "상품 동기화 run의 2번째 chunk에서 timeout이 났고, 실패 item은 retry backlog로 가며, 같은 snapshot 기준으로 chunk 3부터 재개한다"라는 문장이 만들어진다.

바로 이 문장이 테스트에서 보여야 할 도메인 의미다.

## 작게 재사용하는 조립 순서

처음부터 거대한 builder를 만들기보다, 아래 순서로 늘리는 편이 읽기 쉽다.

### 1. 가장 평범한 녹색 경로를 만든다

```text
completedProductSyncRun()
successfulProductSyncChunk(1)
checkpointAfterChunk(1)
```

이 단계에서는 "정상 흐름의 기본 그림"만 만든다.

### 2. 실패 의미를 별도 fixture로 더한다

```text
failedProductSyncChunk(2)
partnerTimeoutRetryCandidate(item-491)
```

여기서 중요한 점은 실패를 `failedRun()` 한 줄로 덮지 않는 것이다.
실패 이유와 대상 item을 따로 드러내면 assertion도 읽기 쉬워진다.

### 3. checkpoint는 실패 backlog와 분리한다

```text
checkpointAfterChunk(2)
manualReviewCandidate(item-492)
```

checkpoint는 진행 위치고, retry/manual-review fixture는 실패 후속 경로다.
둘을 한 helper에 같이 넣으면 "어디까지 끝났는가"와 "무엇을 다시 볼까"가 뒤섞인다.

### 4. 조립 함수가 있더라도 뜻을 숨기지 않는다

조립 helper가 필요하다면 아래처럼 의미를 유지하는 쪽이 낫다.

```text
productSyncRunAfterChunk2Timeout()
```

다만 이 helper도 내부에서 다시 작은 fixture를 조립하는 편이 안전하다.
그래야 어떤 테스트는 `retry fixture`만 바꾸고, 어떤 테스트는 `checkpoint fixture`만 바꾸는 식으로 수정할 수 있다.
builder나 factory로 더 올라가야 하는지 자체가 헷갈리면 [Batch Fixture Builder vs Factory Smells](./batch-fixture-builder-vs-factory-smells.md)에서 "작은 fixture 유지"와 "얇은 builder 정당화" 기준을 바로 이어서 볼 수 있다.

## 짧은 비교 표

| 설계 질문 | 더 안전한 첫 선택 |
|---|---|
| fixture를 하나로 만들까 여러 개로 나눌까 | run/chunk/retry/checkpoint 질문별로 나눈다 |
| 이름을 짧게 할까 뜻을 남길까 | 초심자 문서에서는 뜻을 남긴다 |
| 모든 기본값을 한 helper에 넣을까 | 작은 기본 fixture를 조합한다 |
| checkpoint와 retry backlog를 같이 넣을까 | 진행 위치와 실패 후속 경로를 분리한다 |
| builder가 필요할까 | 반복이 생길 때만, 작은 fixture 위에 얇게 둔다 |

## practice loop

입문자는 아래 순서로 fixture를 늘리면 과하게 추상화하지 않게 된다.

1. 전체 성공 run 하나를 표현하는 `completedProductSyncRun()`을 만든다.
2. 2번째 chunk 실패를 표현하는 `failedProductSyncChunk(2)`를 추가한다.
3. timeout 실패 한 건을 나타내는 `partnerTimeoutRetryCandidate(item-491)`를 만든다.
4. 재개 지점을 나타내는 `checkpointAfterChunk(2)`를 만든다.
5. 마지막으로 네 fixture를 함께 써서 "2번째 chunk 실패 후 retry 후보 생성 + chunk 3부터 재개" 테스트를 만든다.

이 순서가 좋은 이유는 한 번에 모든 helper를 일반화하지 않기 때문이다.
먼저 장면을 하나 만들고, 반복이 보일 때만 다음 fixture를 추가하면 된다.

## 자주 하는 오해

| 오해 | 더 안전한 첫 판단 |
|---|---|
| fixture는 짧을수록 무조건 좋다 | 짧아도 도메인 뜻이 사라지면 오히려 읽기 어렵다 |
| builder 하나면 모든 테스트가 편해진다 | 큰 builder는 보통 중요한 차이를 숨긴다 |
| checkpoint에 retry 후보도 같이 넣는 편이 편하다 | 진행 위치와 실패 후속 경로는 다른 질문이다 |
| `defaultRun()` 같은 이름이면 충분하다 | 어떤 업무 run인지 이름에 남는 편이 초심자에게 안전하다 |
| fixture는 setup용이라 assertion 읽기와 무관하다 | fixture 이름이 흐리면 assertion도 왜 중요한지 흐려진다 |

## 한 줄 정리

좋은 batch 결과 fixture는 `run`, `chunk`, `retry`, `checkpoint`를 작은 조각으로 나누고, `상품 동기화 2번째 chunk timeout` 같은 도메인 뜻을 이름에 남겨 테스트가 짧아져도 의미는 숨기지 않는다.
