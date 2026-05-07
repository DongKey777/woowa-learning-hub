---
schema_version: 3
title: Primer On Retry Queue Assertions
concept_id: software-engineering/retry-queue-assertions
canonical: true
category: software-engineering
difficulty: beginner
doc_role: playbook
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/backend
review_feedback_tags:
- retry
- batch-testing
- failure-classification
- queue
aliases:
- retry queue assertions primer
- item failure assertion basics
- retry candidate assertion beginner
- manual review assertion
- terminal failure assertion
- 재시도 큐 테스트 기초
symptoms:
- retryable, manual-review, terminal failure를 같은 assertion으로만 검사해서 다음 행동 경로가 섞여도 테스트가 통과해
- RetryCandidate에 원래 itemId나 sourceIndex가 빠져 재처리 시 어떤 item을 다시 다뤄야 하는지 잃어버려
- manual review 대상이 retry queue에 들어가거나 terminal failure가 재시도 후보가 되는 회귀를 테스트가 잡지 못해
intents:
- troubleshooting
- design
- drill
prerequisites:
- software-engineering/retry-reason-taxonomy
- software-engineering/testing-named-bulk-contracts
next_docs:
- software-engineering/batch-result-testing
- software-engineering/batch-recovery-runbook
- software-engineering/bulk-idempotency-keys
linked_paths:
- contents/software-engineering/testing-named-bulk-contracts.md
- contents/software-engineering/retry-reason-taxonomy-primer.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
- contents/software-engineering/batch-run-result-modeling-examples.md
- contents/software-engineering/batch-result-testing-checklist.md
- contents/software-engineering/batch-recovery-runbook-bridge.md
- contents/software-engineering/bulk-idempotency-keys-for-named-contracts.md
- contents/software-engineering/http-coalescing-failure-mapping.md
confusable_with:
- software-engineering/retry-reason-taxonomy
- software-engineering/batch-result-testing
- software-engineering/batch-partial-failure
forbidden_neighbors: []
expected_queries:
- retry queue 테스트에서 retryable, manual-review, terminal failure를 각각 어떤 assertion으로 고정해야 해?
- ItemFailure가 RetryCandidate가 될 때 stable itemId나 sourceIndex를 잃지 않는지 왜 검증해야 해?
- manual review failure가 retry queue에 섞이지 않는다는 테스트는 어떻게 작성해?
- terminal failure가 자동 재시도 후보가 되지 않도록 어떤 beginner assertion을 먼저 둬야 해?
- batch 실패를 다음 경로로 번역하는 테스트에서 fake, mock, stub은 어떻게 고르면 돼?
contextual_chunk_prefix: |
  이 문서는 ItemFailure를 retryable, manual-review, terminal failure와 stable item identifier 관점에서 검증하는 beginner batch testing playbook이다.
---
# Primer On Retry Queue Assertions

> 한 줄 요약: `ItemFailure`를 받았다면 초심자 테스트는 "retryable인가", "manual review인가", "terminal failure인가", "원래 item을 잃지 않았는가" 네 질문부터 고정하면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
- [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)


retrieval-anchor-keywords: retry queue assertions primer, retry queue assertion beginner, retry queue 테스트 뭐부터, item failure assertion 기초, manual review assertion 왜 따로, terminal failure assertion 기초, retryable failure assertion 예시, retry queue stable item id example, sourceindex stable itemid retry drift, batch failure routing assertion basics
`ItemFailure`, `RetryCandidate`, `manual review`, `terminal failure`라는 이름을 이미 보고도 테스트를 어디서 시작해야 할지 막막하다면, 이 문서는 그 첫 묶음만 좁혀서 설명한다.
첫 질문이 `retry queue 테스트 뭐부터 만들어요`, `manual review는 왜 queue에 넣지 않아요`, `terminal failure assertion은 뭘 봐요`처럼 테스트 첫 단추를 묻는 단계라면 이 primer가 먼저 맞다.
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
- [외부 api retry 분기에서 test double 고르기](#외부-api-retry-분기에서-test-double-고르기)
- [bridge example: `sourceIndex -> stable itemId`를 retry queue까지 이어서 본다](#bridge-example-sourceindex---stable-itemid를-retry-queue까지-이어서-본다)
- [짧은 비교 표](#짧은-비교-표)
- [작은 예시](#작은-예시)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

> 관련 문서:
> - [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
> - [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)
> - [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
> - [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)
>
> retrieval-anchor-keywords:
> - retry queue assertions primer
> - retry queue 테스트 뭐부터
> - retry queue 테스트 처음 뭐부터
> - item failure assertion 뭐부터
> - retryable failure assertion 예시
> - manual review assertion 왜 따로
> - terminal failure assertion 뭘 보나요
> - retry queue가 뭐예요 테스트에서
> - batch 실패 다음 경로 assertion
> - retry queue stable item id 왜 중요해요
> - 처음 배우는데 retry queue assertion
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
> - external api retry mock stub fake
> - retry branch test double choice

## 먼저 잡을 그림

초심자는 retry queue assertion을 아래 한 장면으로 기억하면 충분하다.

- `ItemFailure`는 "실패 영수증"이다
- `RetryCandidate`는 "나중에 다시 처리할 카드"다
- `manual review`는 "사람이 먼저 봐야 해서 queue에 바로 넣지 않는 상태"다
- `terminal failure`는 "이번 run에서는 끝난 실패"다

즉 테스트는 "실패가 있었다"로 끝나면 안 된다.
**그 실패가 다음에 어디로 가야 하는지**를 고정해야 한다.

짧은 횟수 표기도 여기서 같이 맞춰 두면 덜 헷갈린다.

- 이 문서에서는 **`총 N회 시도 = 첫 시도 1회 + 재시도 N-1회`**로 읽는다.
- 따라서 `재시도 2회`는 "실패 후 두 번 더"이고, `총 3회 시도`와 같은 장면이다.
- `attemptCount`가 있다면 "현재까지 총 몇 번 시도했는가"인지, "몇 번 더 retry 가능한가"인지 테스트 이름과 필드 설명에서 같이 드러내는 편이 안전하다.

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

## `attemptCount`를 읽는 최소 기준

초심자는 `attemptCount=3`을 봤을 때 "재시도 3번인가, 총 3번인가?"에서 자주 막힌다.
이 문서에서는 아래처럼 고정해서 읽는다.

| 표기 | 뜻 | 같은 장면 예시 |
|---|---|---|
| `재시도 2회` | 첫 실패 뒤 추가로 2번 더 시도 | `attemptCount=3`, `maxAttempts=3` |
| `총 3회 시도` | 첫 시도 1회 + 재시도 2회 | `attemptCount`가 3에 도달하면 중단 |

테스트 이름과 payload 필드가 둘 다 있다면 한쪽만 믿지 말고 둘이 같은 기준을 쓰는지 같이 본다.
예를 들어 메서드명은 `총_3회_시도_후_중단한다`인데 queue payload 설명은 `retryCount=3`이라고 쓰면, 운영자와 개발자가 서로 다른 숫자를 떠올리기 쉽다.

## 외부 API retry 분기에서 test double 고르기

외부 API retry 테스트에서 초심자가 가장 자주 헷갈리는 부분은 "가짜를 뭘로 둘까"다.
핵심은 **무엇을 확인하려는지 먼저 고르고 그에 맞는 더블을 붙이는 것**이다.

| 확인하려는 것 | 먼저 쓰기 쉬운 더블 | 왜 이게 맞나 |
|---|---|---|
| timeout이 오면 retryable로 분류되는가 | stub | 고정 응답 1개만 있으면 분기 확인이 되기 때문 |
| 1차 timeout 뒤 2차 성공처럼 재시도 흐름이 이어지는가 | fake | 호출 횟수에 따라 응답을 바꾸는 작은 상태를 담기 쉽기 때문 |
| 정말 3번 호출했는가, 마지막에는 더 안 불렀는가 | mock | 호출 횟수와 상호작용 자체가 검증 목표이기 때문 |

작은 mental model은 이렇게 잡으면 된다.

- **stub**: "이번 테스트에서는 timeout을 돌려주는 버튼"
- **fake**: "간단한 메모리를 가진 작은 가짜 서버"
- **mock**: "몇 번 불렀는지 검사하는 감시 카메라"

예를 들어 `PartnerClient`가 첫 호출은 timeout, 둘째 호출은 성공을 반환해야 한다면 stub 두 개를 순서대로 엮기보다 fake 하나가 읽기 쉽다.
반대로 "3회 초과 호출 금지"가 핵심이면 fake 결과보다 mock의 호출 횟수 assertion이 더 직접적이다.

```text
stub: 항상 timeout 반환 -> retryable 분류 테스트
fake: 1회 timeout, 2회 success 저장 -> retry success 흐름 테스트
mock: send()가 3번 호출됐는지 검증 -> backoff/중단 조건 테스트
```

처음에는 "retry 분류는 stub, retry 흐름은 fake, 호출 횟수 제한은 mock"으로 시작하면 대부분의 외부 API 분기를 무리 없이 나눌 수 있다.

## bridge example: `sourceIndex -> stable itemId`를 retry queue까지 이어서 본다

[Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)에서 본 장면을 그대로 가져와 보자.
첫 요청에서는 vendor가 `sourceIndex=2`를 실패로 돌려줬고, 우리 쪽 원본 line은 `line-19`였다.

| 시점 | vendor가 준 값 | 우리 쪽에 남겨야 하는 값 |
|---|---|---|
| 첫 bulk 요청 | `sourceIndex=2` | `itemId=line-19` |
| retry payload 재구성 후 | `sourceIndex=0`으로 다시 압축될 수 있음 | 여전히 `itemId=line-19` |

초심자 테스트에서 여기서 잠글 것은 count가 아니다.
retry queue entry가 첫 실패 때의 `sourceIndex=2`를 그대로 저장하는지보다, **두 번째 요청에서도 같은 `line-19`를 가리키는가**가 더 중요하다.

```text
given first rejection sourceIndex=2 maps to itemId=line-19
and retry payload is rebuilt as [line-19, line-24]
when vendor rejects sourceIndex=0 on retry
then retryQueueEntry.itemId == line-19
and retryQueueEntry does not store stale sourceIndex=2 as identity
```

이 bridge 예시는 "failure mapping 테스트"와 "retry queue assertion 테스트"가 실제로 한 줄로 이어진다는 뜻이다.
mapping에서 stable id로 번역하지 못하면, queue 테스트가 초록이어도 엉뚱한 item을 다시 처리할 수 있다.
vendor index를 stable id로 다시 고정하는 더 자세한 그림은 [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)의 retry drift 예시를 이어서 보면 된다.

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
