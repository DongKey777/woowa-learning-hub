# RunSummary Fixture Naming Mini Primer

> 한 줄 요약: `RunSummary` fixture 이름은 "이번 run이 어떤 장면인가"를 먼저 말해야 해서, 초심자 기준으로는 `green`, `partial-failure`, `duplicate-start`를 장면 이름으로 고정해 두는 편이 status 테스트를 가장 읽기 쉽게 만든다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: runsummary fixture naming mini primer basics, runsummary fixture naming mini primer beginner, runsummary fixture naming mini primer intro, software engineering basics, beginner software engineering, 처음 배우는데 runsummary fixture naming mini primer, runsummary fixture naming mini primer 입문, runsummary fixture naming mini primer 기초, what is runsummary fixture naming mini primer, how to runsummary fixture naming mini primer
`RunSummary` status 테스트를 쓰기 시작하면 fixture 이름이 금방 흐려진다.
`summary1()`, `failureCase()`, `duplicateCase()`처럼 짧게 만들면 테스트는 통과해도 "어떤 run 장면인지"를 다시 본문에서 해석해야 한다.
이 문서는 초심자 기준으로 가장 자주 나오는 세 장면만 좁혀서, fixture 이름을 어떻게 붙이면 status 테스트가 읽기 쉬워지는지 설명한다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 그림](#먼저-잡을-그림)
- [왜 이름부터 잠가 두는가](#왜-이름부터-잠가-두는가)
- [세 장면만 먼저 고정하기](#세-장면만-먼저-고정하기)
- [이름 비교표](#이름-비교표)
- [짧은 예시](#짧은-예시)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

> 관련 문서:
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
>
> retrieval-anchor-keywords:
> - runsummary fixture naming mini primer
> - run summary fixture naming
> - batch status fixture naming beginner
> - green path fixture name
> - partial failure fixture name
> - duplicate start fixture name
> - already started fixture naming
> - run summary status test readability
> - readable run summary fixture
> - batch fixture naming runsummary
> - beginner status fixture primer
> - completed partial failure duplicate start fixture
> - status test fixture naming batch
> - run summary green partial duplicate

## 먼저 잡을 그림

초심자는 `RunSummary` fixture를 "상태 enum용 데이터"로 보기보다 **run 장면 카드**로 보면 된다.

- green-path fixture: 이번 run이 문제 없이 끝난 장면
- partial-failure fixture: run은 끝났지만 후속 조치가 남은 장면
- duplicate-start fixture: 같은 run을 또 열려고 했지만 새 run을 만들지 않은 장면

핵심은 fixture 이름이 count보다 먼저 장면을 말해야 한다는 점이다.

- 더 읽기 쉬운 이름: `completedProductSyncRunSummary()`
- 덜 읽기 쉬운 이름: `runSummaryWithZeroFailures()`

두 이름 모두 성공 장면을 만들 수 있다.
하지만 첫 번째는 "이 테스트가 성공 종료 장면을 다루는구나"를 먼저 보여 주고, 두 번째는 숫자를 해석해야 뜻이 나온다.

## 왜 이름부터 잠가 두는가

status 테스트는 보통 assertion이 짧다.

```text
expect(summary.status).toBe(COMPLETED)
```

그래서 fixture 이름이 흐리면 테스트 전체도 같이 흐려진다.

| 흐린 이름 습관 | 왜 읽기 어려운가 |
|---|---|
| `summary1()` | 어떤 장면인지 전혀 안 보인다 |
| `failureCase()` | partial failure인지 terminal failure인지 모른다 |
| `duplicateCase()` | duplicate item인지 duplicate run start인지 모른다 |
| `defaultSummary()` 후 값 덮어쓰기 | 테스트마다 중요한 장면이 본문 아래로 숨어든다 |

초심자에게는 fixture 이름이 작은 주석 역할을 한다.
그래서 "무슨 값을 넣었는가"보다 "어떤 장면을 만들었는가"가 이름에 남는 편이 안전하다.

## 세 장면만 먼저 고정하기

처음부터 모든 status를 fixture로 만들 필요는 없다.
아래 세 장면만 먼저 고정해도 대부분의 beginner status 테스트가 읽힌다.

| 장면 | 추천 이름 예시 | 이름에 남겨야 할 뜻 |
|---|---|---|
| green path | `completedProductSyncRunSummary()` | 정상 종료, 새 run, 후속 조치 없음 |
| partial failure | `completedProductSyncRunSummaryWithRetryBacklog()` | run 종료, 실패 있음, 다음 조치 남음 |
| duplicate start | `alreadyStartedProductSyncRunSummary()` | 새 run 미생성, 기존 실행 재사용 또는 가리킴 |

여기서 중요한 것은 enum 철자를 이름에 그대로 넣는 일이 아니다.
초심자 문맥에서는 **운영자가 읽는 장면 이름**이 먼저고, enum 이름은 assertion에서 확인하면 충분하다.

예를 들어 아래 두 이름을 비교해 보자.

| 이름 | 초심자가 읽는 첫 의미 |
|---|---|
| `completedWithFollowUpRunSummary()` | 끝났지만 뭔가 더 해야 한다 |
| `statusThreeSummary()` | 세 번째 status인가? 세 번째 케이스인가? |

## 이름 비교표

| 덜 읽기 쉬운 이름 | 더 읽기 쉬운 이름 | 이유 |
|---|---|---|
| `successSummary()` | `completedProductSyncRunSummary()` | 어떤 업무 run인지 함께 남는다 |
| `failedSummary()` | `completedProductSyncRunSummaryWithRetryBacklog()` | run 중단인지 부분 실패인지 구분된다 |
| `duplicateSummary()` | `alreadyStartedProductSyncRunSummary()` | duplicate 대상이 "시작 요청"임이 보인다 |
| `summaryForStatus2()` | `partiallyFailedInventorySyncRunSummary()` | 숫자 대신 장면이 보인다 |
| `defaultSummary()` + override | 장면별 fixture 3개 | 중요한 차이가 이름에서 바로 드러난다 |

이름이 조금 길어져도 괜찮다.
초심자 테스트에서 더 큰 비용은 긴 이름이 아니라 **뜻이 없는 이름**이다.

## 짧은 예시

상품 동기화 run을 예로 들면 아래 세 fixture만 있어도 status 테스트가 읽힌다.

```text
completedProductSyncRunSummary()
- requestedItems: 1200
- failedItems: 0
- retryCandidateCount: 0
- status: completed
```

```text
completedProductSyncRunSummaryWithRetryBacklog()
- requestedItems: 1200
- failedItems: 3
- retryCandidateCount: 2
- manualReviewCount: 1
- status: completed-with-follow-up
```

```text
alreadyStartedProductSyncRunSummary()
- runKey: product-sync@2026-04-27T09:00
- existingRunId: product-sync-2026-04-27-09
- newRunCreated: false
- status: already-started
```

이 이름들이 좋은 이유는 assertion과 합쳤을 때 문장이 되기 때문이다.

```text
given completedProductSyncRunSummary()
then status means completed

given completedProductSyncRunSummaryWithRetryBacklog()
then status means completed with follow-up work

given alreadyStartedProductSyncRunSummary()
then status means existing run is reused
```

테스트를 읽는 사람은 본문 내부 count를 세기 전에, fixture 이름만 보고도 장면을 먼저 잡을 수 있다.

## practice loop

1. `completedProductSyncRunSummary()` 하나만 먼저 만든다.
2. 실패 count를 억지로 수정하지 말고, 새 fixture `completedProductSyncRunSummaryWithRetryBacklog()`를 만든다.
3. 중복 시작 장면이 필요해지면 `alreadyStartedProductSyncRunSummary()`를 추가한다.
4. 세 fixture 이름만 보고도 각각 "성공 종료", "부분 실패 종료", "새 run 미생성"이 읽히는지 확인한다.
5. `case1`, `case2`, `duplicateCase` 같은 예전 이름이 있으면 장면 이름으로 바꾼다.

이 순서가 좋은 이유는 "공통 default fixture 하나"를 먼저 키우지 않기 때문이다.
장면이 늘어날 때마다 이름을 하나씩 추가하는 편이 초심자 테스트에서는 훨씬 덜 흐려진다.

## 자주 하는 오해

| 오해 | 더 안전한 첫 판단 |
|---|---|
| 성공 fixture면 `successSummary()`면 충분하다 | 어떤 업무 run의 성공인지 이름에 남긴다 |
| partial failure는 그냥 `failedSummary()`라고 부르면 된다 | run 중단과 후속 조치가 남은 종료를 구분한다 |
| duplicate start는 예외 상황이니 fixture 이름도 대충 괜찮다 | duplicate item, duplicate event와 섞이지 않게 "start"를 이름에 넣는다 |
| 공통 `defaultSummary()` 하나가 제일 재사용성이 높다 | beginner 테스트에서는 장면별 fixture 3개가 더 읽기 쉽다 |
| enum 이름만 정확하면 fixture 이름은 중요하지 않다 | status assertion이 짧을수록 fixture 이름이 설명 책임을 많이 진다 |

## 한 줄 정리

`RunSummary` fixture 이름은 값 묶음 이름이 아니라 run 장면 이름이어야 하므로, 초심자 테스트에서는 `completed...`, `...WithRetryBacklog`, `alreadyStarted...`처럼 green-path, partial-failure, duplicate-start 장면을 먼저 읽히게 만드는 편이 가장 안전하다.
