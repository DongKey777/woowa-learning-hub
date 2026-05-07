---
schema_version: 3
title: Batch Fixture Builder vs Factory Smells
concept_id: software-engineering/batch-fixture-builder
canonical: true
category: software-engineering
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/payment
review_feedback_tags:
- batch-testing
- fixture-design
- readable-tests
aliases:
- Batch Fixture Builder vs Factory Smells
- batch test data builder decision
- fixture factory smell beginner
- named fixture vs builder
- batch helper smell
- test fixture builder 언제
symptoms:
- batch fixture를 재사용하려다 createDefault, caseA, fixture1 같은 opaque factory가 되어 테스트 장면 의미를 숨겨
- 값이 많다는 이유만으로 builder부터 만들고, 실제로는 named fixture 하나로 충분한 beginner batch test를 복잡하게 만들어
- 같은 장면의 변형이 반복되는 경우와 서로 다른 도메인 장면을 하나의 generic factory로 뭉치는 smell을 구분하지 못해
intents:
- design
- comparison
- troubleshooting
prerequisites:
- software-engineering/batch-result-fixtures
- software-engineering/readable-code-layering-test-feedback-loop-primer
next_docs:
- software-engineering/batch-result-testing
- software-engineering/runsummary-fixture-naming
- software-engineering/testing-named-bulk-contracts
linked_paths:
- contents/software-engineering/batch-result-fixture-design-primer.md
- contents/software-engineering/batch-run-result-modeling-examples.md
- contents/software-engineering/batch-result-testing-checklist.md
- contents/software-engineering/testing-named-bulk-contracts.md
- contents/software-engineering/readable-code-layering-test-feedback-loop-primer.md
- contents/software-engineering/refactoring-basics.md
- contents/software-engineering/runsummary-fixture-naming-mini-primer.md
confusable_with:
- software-engineering/batch-result-fixtures
- software-engineering/runsummary-fixture-naming
- software-engineering/testing-named-bulk-contracts
forbidden_neighbors: []
expected_queries:
- batch 테스트 fixture는 언제 named fixture로 두고 언제 builder를 얇게 올려야 해?
- createDefaultBatchResult나 caseA 같은 fixture factory smell이 테스트 의미를 숨기는 이유가 뭐야?
- product sync chunk timeout 실패 같은 장면 이름을 fixture에 남기는 게 왜 beginner 테스트에 좋아?
- 같은 장면에서 3개 이상 속성만 반복 변경될 때 builder가 정당화되는 기준을 알려줘
- batch fixture helper가 너무 커졌을 때 run chunk retry checkpoint로 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 batch 테스트 fixture에서 named fixture, thin builder, opaque factory smell을 구분해 readable test setup을 유지하는 beginner bridge다.
---
# Batch Fixture Builder vs Factory Smells

> 한 줄 요약: batch 테스트에서 fixture helper는 먼저 작은 이름 있는 장면으로 유지하고, 같은 장면을 여러 축으로 반복 바꿔야 할 때만 얇은 builder를 올리면 초심자도 읽기 쉬움과 수정 편의성을 같이 지킬 수 있다.

**난이도: 🟢 Beginner**

batch 테스트를 쓰다 보면 금방 이런 갈림길이 온다.
"`failedChunk()` 같은 작은 fixture 몇 개면 충분한가?" 아니면 "`BatchResultBuilder`나 `FixtureFactory`를 만들어야 하나?"
이 문서는 그 판단을 초심자 눈높이에서 좁혀서 설명한다.
[Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)에서 작은 fixture 조립의 기본을 먼저 잡았다면, 여기서는 **언제 그 상태를 유지하고 언제 builder/factory가 정당화되는지**만 본다.
테스트 전략 전체를 먼저 보고 싶다면 [Test Strategy Basics](./test-strategy-basics.md), batch 결과 타입을 먼저 익히고 싶다면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 이어서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 그림](#먼저-잡을-그림)
- [용어를 아주 작게 정리](#용어를-아주-작게-정리)
- [언제 작은 named fixture로 남겨야 하나](#언제-작은-named-fixture로-남겨야-하나)
- [언제 builder가 정당화되나](#언제-builder가-정당화되나)
- [factory smell은 언제 생기나](#factory-smell은-언제-생기나)
- [예시 1: 작은 fixture로 충분한 경우](#예시-1-작은-fixture로-충분한-경우)
- [예시 2: builder가 필요한 경우](#예시-2-builder가-필요한-경우)
- [짧은 결정표](#짧은-결정표)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

관련 문서:

- [Batch Result Fixture Design Primer](./batch-result-fixture-design-primer.md)
- [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
- [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
- [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
- [Readable Code Layering Test Feedback Loop Primer](./readable-code-layering-test-feedback-loop-primer.md)
- [Refactoring Basics](./refactoring-basics.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: batch fixture builder vs factory smells, batch test data builder decision, fixture factory smell beginner, named fixture vs builder, small fixture vs object mother, batch helper smell readable code, when to use test builder, batch testing helper design, fixture factory anti pattern, readable batch test fixture, thin builder over named fixtures, batch result builder beginner, fixture helper smell primer, batch test readable code, builder justified by variation

## 먼저 잡을 그림

초심자는 아래 세 줄만 먼저 기억하면 된다.

- 이름 있는 작은 fixture는 "지금 테스트가 어떤 장면인지" 바로 보여 주는 카드다.
- builder는 "같은 장면에서 바뀌는 축이 많을 때" 수정을 덜 아프게 하는 조절판이다.
- factory smell은 "편하게 만들었지만 무슨 장면인지 숨겨 버린 helper"다.

그래서 첫 선택은 보통 builder가 아니다.
대부분의 입문 테스트는 아래 순서가 더 안전하다.

1. 장면 이름이 보이는 작은 fixture를 만든다.
2. 같은 장면을 여러 테스트에서 조금씩 바꾸는 반복이 생기는지 본다.
3. 그 반복이 진짜 쌓였을 때만 builder를 얇게 추가한다.

## 용어를 아주 작게 정리

| 용어 | 이 문서에서의 뜻 |
|---|---|
| named fixture | `failedProductSyncChunk(2)`처럼 장면 이름이 드러나는 작은 helper |
| builder | 기본 장면 위에서 `withReasonCode`, `withChunkNo`처럼 일부 값만 바꾸는 조립 도구 |
| factory smell | `createCaseA()`, `defaultResult()`, `batchFixture()`처럼 뜻이 숨겨진 큰 helper |

핵심은 패턴 이름보다 읽기 경험이다.
테스트를 처음 읽는 사람이 "이 데이터가 왜 필요한지" 바로 이해되면 좋은 쪽에 가깝고, helper 내부를 열어 봐야 뜻이 보이면 smell 쪽에 가깝다.

## 언제 작은 named fixture로 남겨야 하나

아래 신호가 보이면 builder로 가지 말고 작은 fixture를 유지하는 편이 낫다.

| 신호 | 왜 작은 fixture가 더 낫나 |
|---|---|
| 테스트마다 장면이 거의 고정돼 있다 | 이름만으로 테스트 의도가 읽힌다 |
| 바뀌는 값이 1~2개뿐이다 | 메서드 체인보다 인자 1~2개가 더 직접적이다 |
| 초심자가 처음 보는 도메인이다 | helper 이름이 설명 역할을 대신한다 |
| assertion이 도메인 문장처럼 읽혀야 한다 | `timeoutRetryCandidate(item-491)`가 `builder().withRetryable(true)`보다 뜻이 선명하다 |

예를 들면 이런 경우다.

- "`2번째 chunk에서 timeout 실패가 retry 후보로 가는가`"만 검증한다
- "`mixed partner lines`를 거부하는가`"만 검증한다
- "`receiptId`와 `chunkNo`가 같이 유지되는가`"만 검증한다

이 정도면 helper를 일반화하기보다 장면 이름을 유지하는 쪽이 더 읽기 쉽다.

## 언제 builder가 정당화되나

builder가 필요해지는 순간은 "값이 많다"보다 "같은 장면의 변형이 반복된다"에 가깝다.

아래 조건이 겹치면 builder를 고려할 만하다.

| 조건 | builder가 주는 이점 |
|---|---|
| 기본 장면은 같고 3개 이상 속성만 자주 바뀐다 | 중복 setup을 줄이면서 장면 기준점은 유지할 수 있다 |
| 같은 타입 변형이 4개 이상 테스트에 반복된다 | 수정 지점을 한 곳으로 모을 수 있다 |
| 기본 fixture 인자 순서가 길어져 실수하기 쉽다 | `withXxx`가 값 의미를 더 분명히 보여 준다 |
| "정상 기본값 + 특정 한 축만 바꾸기"가 핵심이다 | diff가 작아져 어떤 조건을 바꿨는지 잘 보인다 |

단, 이때도 builder는 보통 **named fixture 위에 얇게** 두는 편이 안전하다.

예를 들어:

- 좋은 출발: `productSyncChunkBuilder().withChunkNo(3).withReasonCode("partner-timeout")`
- 덜 좋은 출발: `new GenericBatchFixtureFactory().create("CASE_A")`

앞쪽은 무엇을 바꾸는지 읽히고, 뒤쪽은 내부 구현을 열어 봐야 장면이 보인다.

## factory smell은 언제 생기나

초심자 테스트에서 흔한 smell은 "재사용"보다 "의미 은닉"에서 온다.

| smell | 왜 문제인가 |
|---|---|
| `createDefaultBatchResult()` 후 여기저기 수정 | 기본 상태가 무엇인지 테스트마다 다시 해석해야 한다 |
| `caseA()`, `caseB()`, `fixture1()` 같은 이름 | 장면이 아니라 번호만 남는다 |
| 하나의 factory가 run/chunk/retry/checkpoint를 전부 만든다 | 서로 다른 질문이 한 helper에 섞인다 |
| factory가 무작위 id, 현재 시각, 긴 목록을 자동 생성한다 | 테스트가 왜 중요한지보다 잡음이 더 커진다 |
| 작은 차이를 숨기려고 boolean 인자를 늘린다 | `true, false, true`가 무엇을 뜻하는지 잊기 쉽다 |

특히 아래 냄새가 나면 거의 factory smell이다.

- helper를 안 열어 보면 어떤 도메인 장면인지 모르겠다
- 테스트 이름보다 helper 이름이 더 추상적이다
- 수정하려면 factory 내부 조건문부터 읽어야 한다

## 예시 1: 작은 fixture로 충분한 경우

상황을 하나로 고정하자.

- 상품 동기화 batch의 2번째 chunk에서 `item-491`이 timeout으로 실패했다
- 이 실패가 retry backlog로 가는지만 검증하고 싶다

이때는 작은 named fixture가 더 읽기 쉽다.

```java
@Test
void timeout_failure_becomes_retry_candidate() {
    ChunkResult failedChunk = failedProductSyncChunk(
            2,
            itemFailure("item-491", "partner-timeout")
    );

    RetryCandidate candidate = toRetryCandidate(failedChunk.failures().get(0));

    assertThat(candidate.itemId()).isEqualTo("item-491");
    assertThat(candidate.retryable()).isTrue();
    assertThat(candidate.nextAction()).isEqualTo("retry-later");
}
```

여기서 builder를 넣으면 오히려 읽기가 길어질 수 있다.

```java
ChunkResult failedChunk = chunkResultBuilder()
        .withRunId("product-sync-2026-04-27-09")
        .withChunkNo(2)
        .withFailure(itemFailureBuilder()
                .withItemId("item-491")
                .withReasonCode("partner-timeout")
                .build())
        .build();
```

틀린 코드는 아니지만, 초심자 기준에서는 "2번째 chunk timeout 실패"라는 장면이 한눈에 덜 잡힌다.

## 예시 2: builder가 필요한 경우

이제 상황이 달라졌다고 하자.

- 같은 `ChunkResult`를 여러 테스트에서 재사용한다
- 테스트마다 바뀌는 축이 `chunkNo`, `reasonCode`, `retryable`, `acceptedCount`, `receiptId`처럼 많다
- 생성자 인자가 길어져 같은 장면을 매번 다시 쓰는 비용이 커졌다

이때는 builder가 정당화된다.
다만 시작점은 generic factory가 아니라 **이름 있는 기본 fixture + 얇은 builder**가 좋다.

```java
ChunkResult chunk = productSyncChunkBuilder()
        .secondChunkTimeoutFailure()
        .withReceiptId("rcpt-240427-02")
        .withAcceptedCount(299)
        .withRetryable(true)
        .build();
```

이 방식의 장점은 두 층이 분리된다는 점이다.

- `secondChunkTimeoutFailure()`가 기본 장면을 설명한다
- `withReceiptId`, `withAcceptedCount`가 이번 테스트의 차이를 설명한다

반대로 아래처럼 모든 것을 한 factory에 몰면 smell이 커진다.

```java
ChunkResult chunk = batchFixtureFactory.createFailureCase(
        "product-sync",
        2,
        true,
        true,
        "CASE_TIMEOUT"
);
```

이 코드는 호출은 짧아 보여도, 초심자가 읽을 때는 각 인자의 의미와 기본값을 계속 되짚어야 한다.

## 짧은 결정표

| 질문 | 더 안전한 첫 선택 |
|---|---|
| 장면이 1~2개고 반복 수정이 적은가 | 작은 named fixture |
| 같은 장면에서 바뀌는 축이 여러 개 반복되는가 | 얇은 builder |
| helper 이름만 보고 장면이 읽히는가 | 유지 |
| helper 내부를 열어 봐야 뜻이 보이는가 | smell 의심 |
| builder를 만들더라도 출발 장면 이름을 남길 수 있는가 | 만들 가치가 있다 |
| run/chunk/retry/checkpoint를 한 helper가 다 먹고 있는가 | 분리부터 먼저 |

## practice loop

초심자는 아래 순서로 리팩터링하면 과한 추상화를 덜 한다.

1. 먼저 장면 이름이 보이는 fixture 2~3개만 만든다.
2. 세 번째 테스트를 쓰면서 복붙되는 값이 무엇인지 표시한다.
3. 같은 타입에서 3개 이상 속성 변경이 반복되면 builder 후보로 올린다.
4. builder를 만들 때도 `timeoutFailureChunk()` 같은 기본 장면 메서드를 먼저 둔다.
5. builder가 run/chunk/retry/checkpoint를 한꺼번에 다루기 시작하면 다시 쪼갠다.

## 자주 하는 오해

| 오해 | 더 안전한 첫 판단 |
|---|---|
| 값이 많으면 바로 builder를 써야 한다 | 값 개수보다 변형 반복이 더 중요한 신호다 |
| builder를 쓰면 항상 더 읽기 쉽다 | 장면 이름이 사라지면 오히려 읽기 어려워진다 |
| factory는 재사용성이 높으니 좋은 추상화다 | 장면을 숨기면 재사용보다 오해 비용이 더 커진다 |
| `defaultFixture()` 하나면 확장하기 쉽다 | 기본 상태를 숨기면 수정할수록 추론 비용이 커진다 |
| 작은 fixture는 중복이라 나쁘다 | 초심자 테스트에서는 설명 가능한 중복이 종종 더 낫다 |

## 한 줄 정리

batch 테스트 helper의 첫 선택은 보통 작은 named fixture이고, 같은 장면을 여러 축으로 반복 변형해야 할 때만 그 위에 얇은 builder를 올리며, 장면 이름을 숨기는 큰 factory는 대부분 초심자에게 smell이 된다.
