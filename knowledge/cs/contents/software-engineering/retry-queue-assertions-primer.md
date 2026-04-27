# Primer On Retry Queue Assertions

> 한 줄 요약: `ItemFailure`를 받았다면 초심자 테스트는 "retryable인가", "manual review인가", "terminal failure인가", "원래 item을 잃지 않았는가" 네 질문부터 고정하면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: retry queue assertions primer basics, retry queue assertions primer beginner, retry queue assertions primer intro, software engineering basics, beginner software engineering, 처음 배우는데 retry queue assertions primer, retry queue assertions primer 입문, retry queue assertions primer 기초, what is retry queue assertions primer, how to retry queue assertions primer
`ItemFailure`, `RetryCandidate`, `manual review`, `terminal failure`라는 이름을 이미 보고도 테스트를 어디서 시작해야 할지 막막하다면, 이 문서는 그 첫 묶음만 좁혀서 설명한다.
[Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)에서 `retryable`, `manual-review`, `permanent` 분류표를 먼저 잡았다면, 여기서는 그 분류가 테스트에서 어떤 assertion으로 보이는지 이어서 읽으면 된다.
[Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)에서 failure mapping 자체를 봤다면, 여기서는 그다음 단계인 "실패를 다음 경로로 제대로 번역했는가"만 다룬다.
batch 정책을 먼저 익히고 싶다면 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md), 결과 타입 전체를 보고 싶다면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md), 더 넓은 결과 체크리스트가 필요하면 [Batch Result Testing Checklist](./batch-result-testing-checklist.md)를 이어서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 그림](#먼저-잡을-그림)
- [왜 이 네 assertion부터 필요한가](#왜-이-네-assertion부터-필요한가)
- [먼저 쓰는 분류 체크리스트](#먼저-쓰는-분류-체크리스트)
- [최소 테스트 1: retryable failure는 retry candidate가 된다](#최소-테스트-1-retryable-failure는-retry-candidate가-된다)
- [최소 테스트 2: manual-review failure는 queue에 섞이지 않는다](#최소-테스트-2-manual-review-failure는-queue에-섞이지-않는다)
- [최소 테스트 3: terminal failure는 retry queue와 manual review에 섞이지 않는다](#최소-테스트-3-terminal-failure는-retry-queue와-manual-review에-섞이지-않는다)
- [최소 테스트 4: 원래 item 식별자를 잃지 않는다](#최소-테스트-4-원래-item-식별자를-잃지-않는다)
- [짧은 비교 표](#짧은-비교-표)
- [작은 예시](#작은-예시)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

> 관련 문서:
> - [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
> - [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
> - [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)
>
> retrieval-anchor-keywords:
> - retry queue assertions primer
> - item failure to retry candidate test
> - item failure manual review bucket test
> - terminal failure classification checklist
> - retry candidate assertion beginner
> - manual review bucket assertion
> - batch retry queue mapping test
> - item failure classification test
> - retryable vs manual review vs terminal assertion
> - item failure next action mapping
> - retry queue beginner primer
> - manual review backlog beginner
> - terminal failure no retry assertion
> - stable item id retry candidate
> - batch failure routing assertions
> - retry queue contract test
> - item failure to queue translation
> - batch retry reason classification checklist
> - retryable manual-review terminal failure example
> - batch failure triage beginner

## 먼저 잡을 그림

초심자는 retry queue assertion을 아래 한 장면으로 기억하면 충분하다.

- `ItemFailure`는 "실패 영수증"이다
- `RetryCandidate`는 "나중에 다시 처리할 카드"다
- `manual review`는 "사람이 먼저 봐야 해서 queue에 바로 넣지 않는 상태"다
- `terminal failure`는 "이번 run에서는 끝난 실패"다

즉 테스트는 "실패가 있었다"로 끝나면 안 된다.
**그 실패가 다음에 어디로 가야 하는지**를 고정해야 한다.

가장 흔한 회귀는 네 가지다.

- timeout도 validation도 전부 retry queue로 들어간다
- manual-review 대상이 queue에 섞여 운영자가 전체 재시도를 눌러 버린다
- 이미 종료해야 할 terminal failure가 manual review나 retry queue로 흘러 들어간다
- queue에는 들어갔는데 원래 `itemId`가 아니라 임시 index만 남아 나중에 다른 item을 재처리한다

## 왜 이 네 assertion부터 필요한가

초심자 테스트는 모든 reason code를 한 번에 다 잠글 필요가 없다.
먼저 아래 네 질문이 지켜지면 retry queue 설계의 중심이 선다.

| 먼저 잠글 질문 | 왜 중요한가 |
|---|---|
| retryable failure만 retry queue로 가는가 | 자동 재시도 폭주를 막기 위해 |
| manual-review failure가 queue에 섞이지 않는가 | 사람이 볼 backlog를 지키기 위해 |
| terminal failure가 다음 경로 없이 종료되는가 | 이미 끝난 실패를 다시 흔들지 않기 위해 |
| retry 후보가 원래 item을 정확히 가리키는가 | 잘못된 재처리를 막기 위해 |

이 네 assertion은 프레임워크와 무관하다.
Spring Batch, message queue, plain service 코드 모두 같은 질문으로 읽을 수 있다.

## 먼저 쓰는 분류 체크리스트

초심자는 reason code taxonomy 전체보다 아래 체크리스트부터 붙잡는 편이 낫다.

| 체크 질문 | yes면 보통 가는 곳 | beginner 예시 |
|---|---|---|
| 잠깐 기다리면 같은 입력으로 다시 성공할 가능성이 큰가 | retry queue | `partner-timeout`, `temporary-network-error` |
| 입력값 보정이나 사람 판단이 먼저 필요한가 | manual review | `missing-required-field`, `invalid-account` |
| 같은 입력으로 다시 돌려도 결과가 바뀌지 않는가 | terminal failure | `unsupported-country`, `deleted-user`, `duplicate-closed-order` |

빠르게 읽는 법은 이것이다.

- **retryable**: 시스템 상태가 바뀌면 다시 해볼 가치가 있다
- **manual review**: 사람이나 운영 절차가 먼저 움직여야 한다
- **terminal**: 이번 정책에서는 더 진행하지 않고 종료한다

여기서 terminal은 "심각해서 무조건 장애"라는 뜻이 아니다.
"이 item은 현재 정책상 자동 retry도, manual review backlog도 만들지 않는다"는 종료 분류에 가깝다.

## 최소 테스트 1: retryable failure는 retry candidate가 된다

가장 먼저 잠글 것은 분류 기준이다.
예를 들어 `partner-timeout`, `temporary-network-error` 같은 transient failure는 retry queue 후보가 될 수 있다.

여기서 최소 assertion은 보통 네 줄이면 충분하다.

- `reasonCode`가 retryable policy로 번역된다
- `RetryCandidate`가 생성된다
- `nextAction`이 retry를 가리킨다
- 같은 item의 추적 키가 남아 있다

```text
given ItemFailure(itemId=line-19, reasonCode=partner-timeout)
when classify failure
then retryCandidates contains line-19
and manualReviewBucket is empty
and retryCandidates[0].nextAction == retry
```

핵심은 queue 시스템 호출 여부보다 **실패 분류 결과가 다음 행동으로 바뀌는가**다.

## 최소 테스트 2: manual-review failure는 queue에 섞이지 않는다

두 번째 테스트는 더 중요할 때가 많다.
자동 재시도보다 "자동 재시도하면 안 되는 실패를 막는 것"이 더 큰 안전장치이기 때문이다.

예를 들어 아래 같은 실패는 보통 manual review에 남긴다.

- `invalid-account`
- `missing-required-field`
- `policy-violation`

이 테스트에서는 아래를 같이 본다.

- manual-review reason code가 retryable로 잘못 번역되지 않는다
- retry queue 후보 수가 늘지 않는다
- manual review bucket에 원래 item과 이유가 남는다

```text
given ItemFailure(itemId=line-21, reasonCode=missing-required-field)
when classify failure
then retryCandidates does not contain line-21
and manualReviewBucket contains line-21
and manualReviewBucket[0].reasonCode == missing-required-field
```

이 assertion이 없으면 timeout과 validation 오류가 한 bucket에 섞여, 운영자는 "실패했으니 다시 돌리자"로 오해하기 쉽다.

## 최소 테스트 3: terminal failure는 retry queue와 manual review에 섞이지 않는다

세 번째 테스트는 "아무 bucket에도 넣지 않는 것도 의도된 결과일 수 있다"를 고정한다.
terminal failure를 빼먹으면 초심자 코드는 종종 아래 둘 중 하나로 미끄러진다.

- "실패니까 일단 retry queue"
- "queue로 안 보내면 불안하니 manual review"

하지만 아래 같은 경우는 보통 terminal 쪽이 더 단순하다.

- `unsupported-country`
- `deleted-user`
- `duplicate-closed-order`

이 테스트에서는 아래를 같이 본다.

- terminal reason code가 retryable로 번역되지 않는다
- manual review bucket도 늘지 않는다
- 결과에 "이번 run에서 종료"라는 설명이 남는다

```text
given ItemFailure(itemId=line-25, reasonCode=unsupported-country)
when classify failure
then retryCandidates does not contain line-25
and manualReviewBucket does not contain line-25
and terminalFailures contains line-25
and terminalFailures[0].nextAction == drop
```

핵심은 "놓쳤다"가 아니라 "의도적으로 종료했다"가 구분되는가다.
이 구분이 있어야 운영자는 retry backlog와 종료 backlog를 같은 눈금으로 보지 않는다.

## 최소 테스트 4: 원래 item 식별자를 잃지 않는다

네 번째 테스트는 count보다 중요하다.
retry queue가 만들어져도 원래 item 식별자가 깨지면 다음 재시도는 잘못된 대상에 붙을 수 있다.

초심자 기준으로는 아래 정도를 먼저 잠그면 충분하다.

- `sourceIndex`만 남지 않고 stable `itemId`나 `itemKey`가 남는다
- retry candidate, manual-review, terminal 항목 모두 원래 item 식별자를 유지한다
- 같은 failure reason이 있어도 item별로 분리되어 남는다

```text
given rejected sourceIndex=2 maps to itemId=line-19
when retry candidate is created
then candidate.itemId == line-19
and candidate.sourceChunkNo == 3
and candidate.reasonCode == partner-timeout
```

이 테스트는 특히 retry payload가 재정렬될 수 있을 때 중요하다.
index는 바뀔 수 있지만 `itemId`는 바뀌면 안 된다.

## 짧은 비교 표

| failure 종류 | 기대 결과 | 테스트에서 먼저 볼 assertion |
|---|---|---|
| timeout, temporary outage | retry queue 후보 | `retryCandidates`에 들어간다 |
| validation, policy error | manual review backlog | `manualReviewBucket`에만 남는다 |
| unsupported rule, already-closed case | terminal failure | `terminalFailures`에만 남는다 |
| stable id 누락 | 잘못된 분류 결과 | `itemId` 또는 `itemKey`가 유지된다 |

## 작은 예시

상품 동기화 chunk에서 네 건이 실패했다고 하자.

- `line-17`: `partner-timeout`
- `line-18`: `partner-timeout`
- `line-19`: `missing-required-field`
- `line-20`: `unsupported-country`

이때 초심자용 최소 기대는 아래와 같다.

| bucket | 기대 item |
|---|---|
| retry queue | `line-17`, `line-18` |
| manual review | `line-19` |
| terminal failures | `line-20` |

이 예시에서 count만 보면 `failedCount=4`로 충분해 보인다.
하지만 실제로 중요한 것은 4건의 실패가 아니라 **2건은 자동 재시도, 1건은 사람 검토, 1건은 종료**라는 다음 행동이다.

## practice loop

입문자는 아래 순서로 작은 테스트 묶음을 만드는 편이 가장 읽기 쉽다.

1. timeout 한 건이 retry queue 후보로 가는 테스트를 만든다.
2. validation 한 건이 manual review bucket으로 가는 테스트를 만든다.
3. unsupported-country 같은 종료 케이스 한 건이 terminal bucket으로 가는 테스트를 만든다.
4. 세 실패를 한 chunk에 같이 넣고 bucket 분리가 유지되는지 확인한다.
5. 마지막으로 `itemId`나 `itemKey`가 끝까지 남는지 assertion을 추가한다.

이 순서가 좋은 이유는 한 번에 모든 failure taxonomy를 외우지 않아도 되기 때문이다.
먼저 "retryable vs manual-review vs terminal" 경계를 고정하고, 그다음 "누구의 실패인가"를 잠그면 된다.

## 자주 하는 오해

| 오해 | 더 안전한 첫 판단 |
|---|---|
| 실패면 모두 retry queue에 넣으면 된다 | retry queue는 다음 경로이고, validation 오류는 manual review가 먼저일 수 있다 |
| retry도 아니면 전부 manual review다 | 사람 개입이 필요 없는 종료 사유라면 terminal로 닫는 편이 더 명확하다 |
| queue에 message만 생기면 테스트는 끝이다 | 어떤 item이 왜 queue에 갔는지까지 남아야 한다 |
| `failedCount`만 맞으면 분류도 맞다 | count와 bucket 분리는 다른 질문이다 |
| `sourceIndex`가 맞으면 충분하다 | retry에서는 stable `itemId`나 `itemKey`가 더 중요하다 |
| manual review는 운영 문서 문제라 테스트와 무관하다 | 코드에서 bucket 분리가 안 되면 runbook도 바로 흔들린다 |

## 한 줄 정리

retry queue assertion의 최소 세트는 "retryable은 queue", "manual-review는 사람 backlog", "terminal은 종료 bucket", "세 경로 모두 원래 item 식별자를 잃지 않는다"다.
