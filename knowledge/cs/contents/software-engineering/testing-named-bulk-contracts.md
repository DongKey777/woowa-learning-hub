# Testing Named Bulk Contracts

> 한 줄 요약: named bulk contract 테스트는 "이 chunk가 계약을 지키는가", "실패가 맞는 item에 붙는가", "영수증이 같은 묶음을 가리키는가" 세 질문을 먼저 고정하면 초심자도 bulk adapter 회귀를 빠르게 잡을 수 있다.

**난이도: 🟢 Beginner**

`SettlementChunk`, `ItemFailure`, `ChunkSubmitResult` 같은 이름 있는 bulk 계약을 이미 올렸다면, 다음 질문은 "무엇을 테스트해야 진짜 안심할 수 있나"가 된다.
이 문서는 그 답을 chunk invariant, item-failure mapping, receipt correlation 세 축으로만 좁혀서 설명한다.
bulk 계약 자체를 먼저 잡고 싶다면 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)부터 보고, run/chunk/item 결과 이름을 먼저 익히고 싶다면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 같이 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 그림](#먼저-잡을-그림)
- [왜 이 세 축부터 테스트하나](#왜-이-세-축부터-테스트하나)
- [핵심 검증축 1: chunk invariants](#핵심-검증축-1-chunk-invariants)
- [핵심 검증축 2: item-failure mapping](#핵심-검증축-2-item-failure-mapping)
- [핵심 검증축 3: receipt correlation](#핵심-검증축-3-receipt-correlation)
- [예시: 정산 chunk submit adapter](#예시-정산-chunk-submit-adapter)
- [테스트 레벨을 어떻게 나누나](#테스트-레벨을-어떻게-나누나)
- [자주 하는 오해](#자주-하는-오해)
- [최소 체크리스트](#최소-체크리스트)

</details>

관련 문서:

- [Software Engineering README: Testing Named Bulk Contracts](./README.md#testing-named-bulk-contracts)
- [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
- [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
- [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
- [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)
- [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
- [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
- [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: testing named bulk contracts, named bulk adapter test, chunk invariants test, item failure mapping test, receipt correlation test, bulk adapter contract testing, chunk submit result assertions, item failure result mapping, batch receipt correlation beginner, bulk partial failure test primer, run chunk item test boundary, settlement chunk adapter test, adapter receipt to item correlation, bulk contract test checklist, testing named bulk contracts basics

## 먼저 잡을 그림

초심자에게는 bulk adapter를 아래 세 장면으로 기억하면 된다.

- 입력 묶음이 계약을 지키는가
- 실패한 item이 누구인지 결과가 정확히 가리키는가
- 외부 영수증과 내부 결과가 같은 chunk를 말하는가

이 세 장면을 놓치면 흔히 이런 일이 생긴다.

- 비어 있는 chunk나 partner가 섞인 chunk가 조용히 통과한다
- `failureCount=2`는 맞는데 어느 line이 실패했는지 뒤바뀐다
- `receiptId`는 저장됐는데 다른 `runId`나 `chunkNo`에 붙어 운영 추적이 깨진다

즉 named bulk contract 테스트는 "bulk API가 호출됐는가"보다 먼저, **묶음의 경계, 실패의 귀속, 영수증의 상관관계**를 검증하는 일이다.

## 왜 이 세 축부터 테스트하나

`List<T>` 대신 `SettlementChunk`, `ChunkSubmitResult`, `ItemFailure` 같은 이름을 만든 이유는 운영 질문을 숨기지 않기 위해서다.
테스트도 같은 질문을 따라가면 된다.

| 검증축 | 테스트가 답해야 하는 질문 | 놓치면 생기는 회귀 |
|---|---|---|
| chunk invariants | "이 묶음은 애초에 유효한가?" | 빈 chunk, oversized chunk, 다른 owner가 섞인 chunk가 흘러간다 |
| item-failure mapping | "실패가 정확히 어느 item의 것인가?" | index 오프셋 오류, line 번호 뒤바뀜, 잘못된 retry 대상 생성 |
| receipt correlation | "이 영수증이 바로 이 chunk의 것인가?" | 다른 run/chunk receipt 오염, 운영 summary와 실제 downstream receipt 불일치 |

초심자 테스트에서는 이 세 축이 count assertion보다 신호가 훨씬 크다.
`acceptedCount=98`만 맞는 테스트는 쉽게 초록이 되지만, 실제 운영 장애는 대개 누구의 실패인지와 어느 묶음의 영수증인지에서 난다.

## 핵심 검증축 1: chunk invariants

먼저 "받아도 되는 묶음인가"를 확인한다.
이 부분은 bulk adapter 바깥의 생성자, validator, adapter preflight 어디에 있든 테스트로 고정해야 한다.

자주 보는 invariant는 아래 정도면 충분하다.

| invariant | 왜 중요한가 |
|---|---|
| chunk가 비어 있지 않다 | 빈 요청을 성공처럼 기록하지 않기 위해 |
| 최대 크기를 넘지 않는다 | downstream limit과 timeout 폭발을 막기 위해 |
| 같은 partner/run/file 경계를 공유한다 | 다른 업무 묶음이 한 chunk에 섞이지 않게 하기 위해 |
| item 식별자가 비어 있지 않다 | 실패 mapping과 retry 생성의 기준점을 잃지 않기 위해 |

여기서 핵심은 모든 테스트가 invariant를 반복 검증하는 것이 아니다.
초심자 기준으로는 **계약 자체의 집중 테스트 1개 묶음**과 **adapter가 invalid input을 조용히 삼키지 않는 경로 1개**면 충분하다.

## 핵심 검증축 2: item-failure mapping

partial failure가 있는 bulk adapter라면 count보다 mapping을 먼저 본다.

예를 들어 partner 응답이 아래처럼 왔다고 하자.

```text
receiptId = rcpt-2026-04-24-03
accepted = [line-11, line-12]
rejected = [
  { sourceIndex = 2, code = "INVALID_AMOUNT" },
  { sourceIndex = 4, code = "DUPLICATE_REFERENCE" }
]
```

우리 adapter 테스트는 단순히 `failedCount=2`를 보는 데서 끝나면 안 된다.
반드시 아래를 같이 본다.

- `sourceIndex=2`가 정말 `line-13`인지
- `ItemFailure`가 `lineId`, `sourceLineNo`, `reasonCode`를 잃지 않는지
- retryable 여부가 reason code에 맞게 번역되는지

즉 item-failure mapping 테스트의 핵심은 이것이다.
**외부 응답의 위치 정보나 vendor code를, 우리 계약의 item 식별자와 실패 이유로 안정적으로 번역하는가**

특히 vendor가 `sourceIndex`만 주는 경우에는 한 줄 더 확인하는 편이 안전하다.
retry에서 실패 item만 다시 보내면 index는 다시 `0, 1, 2`로 압축될 수 있으므로, 테스트도 "옛 index를 저장했는가"가 아니라 "stable item id로 번역했는가"를 봐야 한다.

| 추가 질문 | 왜 필요한가 |
|---|---|
| 첫 요청의 `sourceIndex=2`가 retry queue에서는 `line-19` 같은 stable id로 남는가 | retry payload 재정렬 뒤에도 같은 item을 다시 찾기 위해 |
| retry payload에서 새 index `0`이 다시 `line-19`로 연결되는가 | vendor index drift가 domain drift로 번지는 것을 막기 위해 |
| 같은 retry에서 기존 `itemKey`를 재사용하는가 | 같은 부작용을 새 일처럼 오해하지 않기 위해 |

이 장면이 더 헷갈리면 [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)의 "vendor index를 stable item id로 다시 고정" 섹션을 같이 보면 된다.

## 핵심 검증축 3: receipt correlation

receipt correlation은 "영수증이 존재한다"가 아니라 "영수증이 같은 묶음을 가리킨다"를 확인하는 테스트다.

아래 필드를 함께 묶어서 보는 습관이 좋다.

| 같이 묶어 볼 값 | 확인 이유 |
|---|---|
| `runId` + `chunkNo` + `receiptId` | receipt가 다른 실행에 섞이지 않았는지 확인한다 |
| `requestedCount` + `acceptedCount` + `failures.size()` | summary 숫자가 실제 결과와 맞는지 확인한다 |
| `receiptId` + `partnerId` 또는 `fileId` | downstream 영수증이 다른 source와 섞이지 않았는지 확인한다 |

특히 adapter가 HTTP bulk endpoint나 JDBC batch 결과를 번역할 때는, 기술 응답 하나를 여러 domain 결과로 퍼뜨리는 과정에서 correlation이 깨지기 쉽다.
그래서 receipt correlation 테스트는 "값이 하나 들어왔다"보다 "그 값이 어디에 붙었는가"를 본다.

## 예시: 정산 chunk submit adapter

상황을 하나로 고정해 보자.

- `SettlementChunk`는 같은 `runId`, `partnerId`, `fileId`를 가진 3번째 chunk다
- line 17과 line 19가 downstream validation 실패를 받는다
- downstream은 `receiptId=rcpt-240424-03`을 돌려준다

이때 초심자용 최소 테스트는 아래 세 개면 된다.

### 1. chunk invariant test

```java
@Test
void rejects_chunk_with_mixed_partner_lines() {
    SettlementChunk invalidChunk = SettlementChunk.of(
            runId,
            fileId,
            chunkNo(3),
            List.of(lineOf("partner-a", 17), lineOf("partner-b", 18))
    );

    assertThatThrownBy(() -> validator.validate(invalidChunk))
            .isInstanceOf(InvalidChunkException.class);
}
```

### 2. item-failure mapping test

```java
@Test
void maps_partner_rejections_back_to_original_lines() {
    partnerApi.willReturn(partialFailure(
            "rcpt-240424-03",
            rejected(index(0), "INVALID_AMOUNT"),
            rejected(index(2), "DUPLICATE_REFERENCE")
    ));

    ChunkSubmitResult result = adapter.submit(validChunk(
            lineId("line-17"),
            lineId("line-18"),
            lineId("line-19")
    ));

    assertThat(result.failures()).extracting(ItemFailure::lineId)
            .containsExactly(lineId("line-17"), lineId("line-19"));
    assertThat(result.failures()).extracting(ItemFailure::reasonCode)
            .containsExactly("INVALID_AMOUNT", "DUPLICATE_REFERENCE");
}
```

### 3. receipt correlation test

## 예시: 정산 chunk submit adapter (계속 2)

```java
@Test
void keeps_run_chunk_and_receipt_correlated() {
    partnerApi.willReturn(successReceipt("rcpt-240424-03"));

    ChunkSubmitResult result = adapter.submit(chunk3);

    assertThat(result.runId()).isEqualTo(chunk3.runId());
    assertThat(result.chunkNo()).isEqualTo(chunk3.chunkNo());
    assertThat(result.receiptId()).isEqualTo("rcpt-240424-03");
    assertThat(result.requestedCount())
            .isEqualTo(result.acceptedCount() + result.failures().size());
}
```

여기서 중요한 것은 프레임워크가 아니라 assertion의 방향이다.
초심자라면 "호출 횟수"보다 "경계가 유지됐는가"를 먼저 읽는 편이 훨씬 안전하다.

## 테스트 레벨을 어떻게 나누나

세 축을 한 테스트에 다 몰아넣기보다 책임에 따라 나누면 읽기 쉬워진다.

| 테스트 레벨 | 주로 보는 것 | 이 문서의 세 축 중 무엇을 덮나 |
|---|---|---|
| 계약/unit test | 생성자, validator, small mapper | chunk invariants |
| adapter integration test | 외부 응답 번역, 부분 실패, receipt 저장 | item-failure mapping, receipt correlation |
| end-to-end smoke | wiring, serialization, transaction 경계 | 한 번의 녹색 경로 확인 |

초심자에게 특히 중요한 규칙은 하나다.
**count 검증은 보조 신호고, named field 검증이 주 신호다.**

예를 들어 `failedCount=2`만 보면 초록이지만, 실제로는 `line-17`과 `line-19`가 뒤바뀌어 retry queue가 잘못 생성될 수 있다.

## 자주 하는 오해

| 오해 | 더 안전한 첫 판단 |
|---|---|
| 성공/실패 count만 맞으면 충분하다 | partial failure에서는 어느 item이 실패했는지가 더 중요하다 |
| vendor index가 맞으면 item mapping도 맞은 것이다 | index는 임시 좌표일 수 있으니 stable `itemId`와 `itemKey`까지 확인해야 한다 |
| receiptId가 null이 아니면 correlation도 검증된 것이다 | `runId`, `chunkNo`, `partnerId`와 함께 맞물리는지 봐야 한다 |
| invariant는 생성자에서 막으니 테스트할 필요가 없다 | 계약이 중요한 만큼 한 번은 고정 테스트로 남겨 두는 편이 안전하다 |
| adapter test는 mock 호출 횟수만 보면 된다 | bulk adapter는 번역 결과와 상관관계가 더 핵심이다 |
| 모든 실패 이유를 end-to-end에서만 보자 | reason mapping은 adapter integration test가 더 빠르고 읽기 쉽다 |

## 최소 체크리스트

PR에서 named bulk adapter를 볼 때는 아래 다섯 줄만 먼저 체크해도 품질이 많이 올라간다.

1. invalid chunk를 거부하는 테스트가 있는가
2. partial failure가 원래 item 식별자로 돌아오는 테스트가 있는가
3. `receiptId`가 `runId`와 `chunkNo`에 올바르게 붙는 테스트가 있는가
4. `requestedCount == acceptedCount + failures + skippedCount` 같은 기본 합계 검증이 있는가
5. count assertion만 있고 `lineId`, `sourceLineNo`, `reasonCode` 검증이 빠지지 않았는가

## 더 깊이 가려면

named bulk 계약 자체를 더 단단하게 보고 싶다면 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)에서 run/file/chunk/result 이름을 먼저 고정한다.
retry와 rerun에서 어떤 key를 재사용해야 할지는 [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)로 이어 읽으면 된다.
HTTP bulk endpoint의 vendor 응답을 per-item 실패로 번역하는 더 깊은 사례는 [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)에서 이어지고, seam 자체를 test portfolio로 확장하려면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)와 [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)를 같이 보면 된다.

## 한 줄 정리

named bulk contract 테스트의 첫 출발점은 "유효한 chunk인가, 실패가 맞는 item에 붙는가, 영수증이 같은 묶음을 가리키는가" 이 세 질문을 각기 다른 assertion으로 고정하는 것이다.
