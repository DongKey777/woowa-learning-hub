---
schema_version: 3
title: True Bulk Contracts and Partial Failure Results
concept_id: software-engineering/true-bulk-contracts-partial-failure-results
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/backend
review_feedback_tags:
- bulk-contract
- partial-failure
- batch
- idempotency
aliases:
- true bulk contracts partial failure results
- named bulk contract
- bulk result type
- partial failure result
- SettlementChunk BulkSubmitResult ItemFailure
- true bulk 계약 부분 실패 결과
symptoms:
- bulk가 업무 단위인데 List<T>와 successCount, failureCount만 반환해 run, chunk, item, receipt, retry decision이 계약에서 사라져
- partial failure를 count로만 표현해 어떤 item이 왜 실패했고 retry 가능한지 운영자가 알 수 없어
intents:
- definition
- design
- troubleshooting
prerequisites:
- software-engineering/bulk-port-tradeoffs
- software-engineering/saveall-sendall-port-smells
next_docs:
- software-engineering/testing-named-bulk-contracts
- software-engineering/batch-idempotency-keys
- software-engineering/batch-partial-failure
linked_paths:
- contents/software-engineering/bulk-port-vs-per-item-use-case-tradeoffs.md
- contents/software-engineering/saveall-sendall-port-smells-safer-alternatives.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
- contents/software-engineering/batch-run-result-modeling-examples.md
- contents/software-engineering/batch-idempotency-key-boundaries.md
- contents/software-engineering/batch-job-scope-hexagonal-architecture.md
- contents/software-engineering/adapter-bulk-optimization-without-port-leakage.md
- contents/software-engineering/testing-named-bulk-contracts.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/software-engineering/domain-invariants-as-contracts.md
confusable_with:
- software-engineering/saveall-sendall-port-smells
- software-engineering/bulk-port-tradeoffs
- software-engineering/testing-named-bulk-contracts
forbidden_neighbors: []
expected_queries:
- bulk가 실제 업무 단위라면 List<T> 대신 SettlementRun, SettlementChunk, ChunkSubmitResult 같은 이름 있는 타입이 필요한 이유는?
- true bulk contract에서 runId, chunkNo, cutoffTime, schemaVersion, idempotencyKey, item id를 입력 타입에 넣어야 하는 이유는?
- BulkSubmitResult가 requestedCount, acceptedCount, failedCount뿐 아니라 failures와 retryDecision, receiptId를 가져야 하는 기준은?
- partial failure를 count로만 반환하면 retry queue와 manual review에서 어떤 정보가 사라져?
- item 단위 업무와 bulk 단위 업무를 운영자가 말하는 재시도 단위로 구분하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 bulk가 업무 단위가 되는 순간 List<T>와 count 대신 run, file, chunk, item, result에 이름을 붙이고 partial failure를 ItemFailure와 retry decision으로 표현하는 beginner primer이다.
---
# True Bulk Contracts and Partial Failure Results

> 한 줄 요약: bulk가 실제 업무 단위라면 `List<T>`와 단순 count로 숨기지 말고, `SettlementFile`, `SettlementChunk`, `BulkSubmitResult`, `ItemFailure`처럼 입력 묶음과 결과 묶음을 이름 있는 타입으로 고정해야 한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: true bulk contracts partial failure results basics, true bulk contracts partial failure results beginner, true bulk contracts partial failure results intro, software engineering basics, beginner software engineering, 처음 배우는데 true bulk contracts partial failure results, true bulk contracts partial failure results 입문, true bulk contracts partial failure results 기초, what is true bulk contracts partial failure results, how to true bulk contracts partial failure results
[Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)에서 "bulk를 애플리케이션 계약으로 올려도 되는 순간"을 봤다면, 이 문서는 그다음 질문인 "그 bulk 계약을 어떤 이름과 결과 타입으로 표현해야 하는가"를 좁혀서 본다.
`saveAll`/`sendAll` smell가 먼저 헷갈린다면 [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)를 먼저 보고 오면 된다.
장애 후 재개, retry queue, checkpoint 정책 자체는 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)에서 이어서 다룬다.
`RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`처럼 결과 모델 예시만 따로 보고 싶다면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 같이 보면 된다.
run/chunk/item idempotency key 경계가 필요하면 [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)를 같이 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 떠올릴 그림](#먼저-떠올릴-그림)
- [`List<T>`가 부족해지는 순간](#listt가-부족해지는-순간)
- [이름 붙일 대상 다섯 가지](#이름-붙일-대상-다섯-가지)
- [입력 계약에 들어갈 것](#입력-계약에-들어갈-것)
- [결과 타입에 들어갈 것](#결과-타입에-들어갈-것)
- [예시: 정산 chunk 전송](#예시-정산-chunk-전송)
- [짧은 비교 표](#짧은-비교-표)
- [자주 하는 오해](#자주-하는-오해)
- [PR 전 체크리스트](#pr-전-체크리스트)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: True Bulk Contracts and Partial Failure Results](./README.md#true-bulk-contracts-and-partial-failure-results)
> - [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
> - [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)
>
> retrieval-anchor-keywords:
> - true bulk contract
> - named batch contract
> - named chunk contract
> - named file contract
> - bulk result type
> - partial failure result
> - item failure result
> - batch receipt result
> - chunk submit result
> - file import result
> - bulk contract beginner
> - hexagonal bulk contract
> - bulk is business unit
> - settlement chunk result
> - partial success count smell
> - list based bulk contract smell
> - named bulk contract test primer
> - batch idempotency key boundaries
> - chunk-level idempotency key
> - run-level idempotency key

## 먼저 떠올릴 그림

초심자에게는 이 그림이 가장 쉽다.

- item이 업무 단위면 "37번 주문을 다시 처리한다"라고 말한다
- bulk가 업무 단위면 "4월 23일 정산 파일의 3번째 chunk를 다시 보낸다"라고 말한다

두 번째 문장이 자연스럽다면 `List<SettlementLine>`만으로는 부족하다.
운영자, 테스트, 재시도 코드가 모두 같은 단어를 써야 하므로 `SettlementFile`, `SettlementChunk`, `BulkSubmitResult` 같은 이름 있는 타입이 필요하다.

즉 true bulk contract의 핵심은 이것이다.

- **묶음의 이름**
- **묶음의 경계**
- **묶음 안 item의 식별자**
- **부분 실패를 설명하는 결과**

bulk를 이름 붙인다는 것은 단순히 `List<T>`를 record로 감싸는 일이 아니다.
"이 묶음은 왜 존재하고, 어디까지가 같은 묶음이며, 실패하면 무엇을 다시 볼 것인가"를 타입으로 남기는 일이다.

## `List<T>`가 부족해지는 순간

아래 계약은 처음에는 간단해 보인다.

```java
public interface SettlementSubmitPort {
    int submitAll(List<SettlementLine> lines);
}
```

하지만 이 계약만 보면 중요한 질문에 답하기 어렵다.

| 질문 | `List<T>`와 count만 있을 때 생기는 빈칸 |
|---|---|
| 왜 이 묶음인가 | 어떤 run, 어떤 정산일, 어떤 partner 기준인지 보이지 않는다 |
| 어디서 다시 시작하나 | chunk 번호나 source file 위치가 없다 |
| 일부 실패를 어떻게 설명하나 | 실패한 item id, 실패 코드, retry 가능 여부가 없다 |
| 중복 제출은 어떻게 막나 | run/chunk idempotency key가 없다 |
| 외부 시스템이 무엇을 받았나 | receipt id나 accepted 상태가 없다 |

이 빈칸이 운영 질문으로 올라오기 시작하면 bulk가 이미 업무 단위가 된 것이다.
이때는 더 빠른 `saveAll`을 찾기보다 먼저 계약 이름을 올려야 한다.

## 이름 붙일 대상 다섯 가지

true bulk에서는 보통 다섯 가지에 이름을 붙인다.

| 대상 | 예시 이름 | 역할 |
|---|---|---|
| run/batch | `SettlementRun`, `ImportRun` | 전체 실행의 기준 시점과 소유자를 잡는다 |
| file | `PartnerSettlementFile`, `CatalogImportFile` | 외부와 주고받는 문서 또는 논리 파일을 표현한다 |
| chunk | `SettlementChunk`, `ImportChunk` | 재시도와 checkpoint가 가능한 작은 묶음이다 |
| item entry | `SettlementLine`, `ImportRow` | 묶음 안 한 건의 식별자와 원본 위치를 가진다 |
| result | `BulkSubmitResult`, `ChunkImportResult` | 성공, 부분 실패, 거절, receipt를 설명한다 |

항상 다섯 가지 타입을 전부 만들어야 하는 것은 아니다.
하지만 run, file, chunk, item, result 중 운영자가 말하는 단위가 있다면 그 단위는 이름으로 드러내는 편이 안전하다.

## 입력 계약에 들어갈 것

bulk 입력 타입은 "여러 item"보다 "왜 같은 묶음인지"를 보여 줘야 한다.

| 필드 | 왜 필요한가 |
|---|---|
| `runId` | 같은 실행을 로그, 결과, 재시도에서 추적한다 |
| `chunkNo` / `fileId` | 다시 실행하거나 외부 receipt와 맞출 단위를 고정한다 |
| `cutoffTime` / `settlementDate` | 어떤 데이터 snapshot을 대상으로 삼았는지 설명한다 |
| `schemaVersion` | file/import/export 계약이 바뀔 때 해석 기준을 남긴다 |
| `idempotencyKey` | 같은 chunk를 다시 제출했을 때 중복 부작용을 줄인다 |
| `items` | 실제 처리 대상이다. 이 안의 item도 각자 식별자를 가져야 한다 |
| `maxSize` 같은 불변식 | 너무 큰 chunk, 빈 chunk, 섞이면 안 되는 partner를 막는다 |

초심자 코드에서는 특히 `items`만 있고 나머지가 없는 경우가 많다.
하지만 true bulk에서는 `items`보다 `runId`, `chunkNo`, `cutoffTime` 같은 묶음 정보가 더 중요해질 때가 많다.

## 결과 타입에 들어갈 것

bulk 결과 타입은 "몇 건 성공"보다 "이 묶음을 다음에 어떻게 다룰 것인가"를 말해야 한다.

| 결과 필드 | 의미 |
|---|---|
| `status` | 전체 성공, 부분 성공, 전체 거절, 접수 대기 같은 큰 상태 |
| `requestedCount` | 요청한 item 수. 결과 count 검증 기준이다 |
| `acceptedCount` / `failedCount` / `skippedCount` | summary와 dashboard의 기본 숫자다 |
| `receiptId` | 외부 시스템이 bulk를 받았다는 추적 키다 |
| `failures` | 실패 item id, source line, reason code, retry 가능 여부를 담는다 |
| `retryDecision` | 바로 재시도, 수동 확인, retry queue 이동 같은 다음 경로를 드러낸다 |
| `nextCheckpoint` | 긴 run을 이어서 재개해야 할 때의 진행 지점이다 |

여기서 가장 흔한 냄새는 `successCount`, `failureCount`만 반환하는 것이다.
count는 summary일 뿐이다.
partial failure를 실제로 다루려면 실패한 item이 무엇이고, 왜 실패했고, 다시 시도해도 되는지를 알아야 한다.

## 예시: 정산 chunk 전송

정산 전송이 아래 조건을 가진다고 하자.

- 하루 정산 run을 partner별로 만든다
- 500건씩 chunk로 보낸다
- 파트너 API는 bulk receipt id를 돌려준다
- 일부 line은 validation 문제로 거절될 수 있다

### 덜 안전한 계약

```java
public interface SettlementSubmitPort {
    BulkSubmitResult submit(List<SettlementLine> lines);
}

public record BulkSubmitResult(
        int successCount,
        int failureCount
) {
}
```

이 타입은 bulk처럼 보이지만 true bulk 계약으로는 약하다.
어떤 run인지, 몇 번째 chunk인지, 실패한 line이 무엇인지, partner receipt가 무엇인지 알 수 없다.

### 더 안전한 계약

```java
public record SettlementChunk(
        SettlementRunId runId,
        PartnerId partnerId,
        LocalDate settlementDate,
        int chunkNo,
        int totalChunkCount,
        String idempotencyKey,
        List<SettlementLine> lines
) {
    public SettlementChunk {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("SettlementChunk must not be empty");
        }
        if (lines.size() > 500) {
            throw new IllegalArgumentException("SettlementChunk is too large");
        }
    }
}

public record SettlementLine(
        SettlementLineId lineId,
        int sourceLineNo,
        Money amount
) {
}

public interface SettlementSubmitPort {
    ChunkSubmitResult submit(SettlementChunk chunk);
}
```

결과 타입도 묶음과 item을 같이 설명해야 한다.

## 예시: 정산 chunk 전송 (계속 2)

```java
public record ChunkSubmitResult(
        SettlementRunId runId,
        int chunkNo,
        BulkResultStatus status,
        String partnerReceiptId,
        int requestedCount,
        int acceptedCount,
        int failedCount,
        List<ItemFailure> failures,
        RetryDecision retryDecision
) {
}

public record ItemFailure(
        SettlementLineId lineId,
        int sourceLineNo,
        FailureCode code,
        boolean retryable,
        String message
) {
}

public enum BulkResultStatus {
    ACCEPTED,
    PARTIALLY_ACCEPTED,
    REJECTED
}
```

이제 계약이 아래 질문에 답한다.

- 같은 chunk를 다시 보냈는가?
- 파트너가 어떤 receipt로 받았는가?
- 실패한 line은 무엇인가?
- 실패가 validation 문제인지 일시 장애인지 구분되는가?
- 이 결과는 바로 재시도할 것인가, retry queue로 보낼 것인가?

이 정도 정보가 있어야 partial failure result라고 부를 수 있다.

## 짧은 비교 표

| 상황 | 약한 계약 | 더 나은 계약 |
|---|---|---|
| 묶음이 단순 반복이다 | `for` loop + item use case | 그대로 둔다. bulk 계약으로 올리지 않는다 |
| 조회만 묶고 싶다 | `processAll(List<Id>)` | `findByIds`, `fetchStatuses` 같은 helper port |
| chunk가 재시도 단위다 | `submitAll(List<Line>)` | `SettlementChunk` + `ChunkSubmitResult` |
| 외부 파일이 계약이다 | `importRows(List<Row>)` | `ImportFile` + `ImportResult` + `RowFailure` |
| 결과가 count뿐이다 | `successCount`, `failureCount` | 실패 item, reason code, retry decision 포함 |

짧게 말하면:

- **성능 묶음**은 adapter나 helper에 숨긴다
- **업무 묶음**은 이름 있는 입력과 결과로 드러낸다

## 자주 하는 오해

- "record로 `List<T>`를 감싸면 named contract다"
  - 아니다. run id, chunk/file 경계, 불변식, 결과 의미가 같이 들어와야 한다.
- "partial failure는 count만 있으면 충분하다"
  - 아니다. 실패 item을 다시 찾고 분류할 수 없으면 운영 가능한 partial failure가 아니다.
- "file contract는 실제 파일 업로드에서만 필요하다"
  - 아니다. 외부가 file id나 document unit으로 이해하면 논리 파일도 file contract가 될 수 있다.
- "bulk result는 화면에 보여 주려고 만드는 DTO다"
  - 아니다. retry, 감사, receipt 매핑, 후속 queue 이동을 위한 애플리케이션 결과 타입이다.
- "named bulk contract를 만들면 adapter 최적화는 못 한다"
  - 아니다. port가 `SettlementChunk`를 받더라도 adapter 안에서는 HTTP bulk, JDBC batch, file upload를 자유롭게 선택할 수 있다.

## PR 전 체크리스트

bulk 계약을 올리기 전에 아래 질문에 답해 본다.

- 이 묶음의 이름을 기획자나 운영자도 같은 단어로 부르는가?
- 같은 item 목록이라도 run id, cutoff time, partner가 다르면 다른 묶음인가?
- 한 item 실패 시 전체 실패인지, 부분 성공인지, 전체 거절인지 정해져 있는가?
- 실패 item을 id나 source line으로 다시 찾을 수 있는가?
- 결과 타입이 retry queue, 수동 확인, checkpoint 중 다음 경로를 설명하는가?
- 외부 receipt id와 내부 run/chunk id를 함께 추적할 수 있는가?
- 중복 제출을 줄일 idempotency key가 run 기준인지 chunk 기준인지 정해져 있는가?

여기서 세 개 이상 답이 흐리면 `List<T>` 기반 bulk port를 만들기 전에 계약 이름부터 다시 잡는 편이 좋다.

## 기억할 기준

초심자용으로는 네 문장만 기억하면 충분하다.

1. **bulk가 진짜 업무 단위면 `List<T>`가 아니라 run/chunk/file 이름을 만든다.**
2. **입력 타입은 왜 같은 묶음인지와 어디서 다시 시작할지를 보여 줘야 한다.**
3. **결과 타입은 count만이 아니라 실패 item, reason, retry decision을 담아야 한다.**
4. **adapter bulk 최적화와 application bulk 계약은 다른 문제다.**

테스트 관점에서 이 계약을 어떻게 고정할지 이어서 보려면 [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)를 보면 된다.

## 한 줄 정리

bulk가 실제 업무 단위라면 `List<T>`와 단순 count로 숨기지 말고, `SettlementFile`, `SettlementChunk`, `BulkSubmitResult`, `ItemFailure`처럼 입력 묶음과 결과 묶음을 이름 있는 타입으로 고정해야 한다.
