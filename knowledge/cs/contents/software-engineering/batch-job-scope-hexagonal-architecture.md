---
schema_version: 3
title: Batch Job Scope In Hexagonal Architecture
concept_id: software-engineering/batch-job-scope
canonical: true
category: software-engineering
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 92
mission_ids:
- missions/payment
review_feedback_tags:
- hexagonal-architecture
- batch-application-service
- scheduler-boundary
aliases:
- Batch Job Scope In Hexagonal Architecture
- scheduled job loop existing use case
- batch-oriented application service
- scheduler adapter vs application service
- batch window checkpoint resume
- batch run application capability
symptoms:
- scheduled job라는 이유만으로 application service를 새로 만들거나, 반대로 batch window/checkpoint/partial failure 의미가 있는데도 adapter for-loop 안에 숨겨
- job adapter, per-item use case, batch-oriented application service의 책임을 섞어 @Scheduled 메서드가 window 계산과 chunk loop, checkpoint 저장까지 떠안아
- batch run 자체의 입력 계약과 실패 의미가 생겼는데도 단건 use case 반복으로만 처리해 run summary와 recovery 설명이 비어
intents:
- design
- comparison
- troubleshooting
prerequisites:
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/ddd-hexagonal-consistency
next_docs:
- software-engineering/batch-partial-failure
- software-engineering/bulk-port-tradeoffs
- system-design/job-queue-design
linked_paths:
- contents/software-engineering/message-driven-adapter-example.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
- contents/software-engineering/bulk-port-vs-per-item-use-case-tradeoffs.md
- contents/software-engineering/ddd-hexagonal-consistency.md
- contents/software-engineering/inbound-adapter-testing-matrix.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/system-design/job-queue-design.md
confusable_with:
- software-engineering/batch-partial-failure
- software-engineering/bulk-port-tradeoffs
- software-engineering/message-driven-adapter
forbidden_neighbors: []
expected_queries:
- scheduled job가 기존 use case를 loop해도 되는 경우와 batch-oriented application service가 필요한 경우를 구분해줘
- batch window, snapshot, checkpoint, partial failure policy가 application semantics가 되는 순간은 언제야?
- @Scheduled job adapter 안에 chunk loop와 checkpoint 저장이 길어지면 왜 hexagonal boundary smell이야?
- batch run 자체가 비즈니스 의미를 가지면 RunSummary와 dedicated service를 왜 둬야 해?
- batch job scope와 bulk port, per-item use case tradeoff를 같이 판단하는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 hexagonal architecture에서 scheduled job adapter, existing per-item use case loop, dedicated batch-oriented application service를 batch window, checkpoint, chunk, partial failure policy 기준으로 고르는 chooser다.
---
# Batch Job Scope In Hexagonal Architecture

> 한 줄 요약: scheduled job가 기존 유스케이스를 반복 호출하는 thin inbound adapter로 끝나도 되는 경우는 "한 건 처리 의미"가 그대로 재사용될 때고, batch window, checkpoint, chunk, partial failure policy 자체가 application 의미가 되면 dedicated batch-oriented application service를 따로 둬야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: batch job scope hexagonal architecture basics, batch job scope hexagonal architecture beginner, batch job scope hexagonal architecture intro, software engineering basics, beginner software engineering, 처음 배우는데 batch job scope hexagonal architecture, batch job scope hexagonal architecture 입문, batch job scope hexagonal architecture 기초, what is batch job scope hexagonal architecture, how to batch job scope hexagonal architecture
[30분 후속 분기표로 돌아가기](./common-confusion-wayfinding-notes.md#자주-헷갈리는-3개-케이스)

[Message-Driven Adapter Example](./message-driven-adapter-example.md)에서 scheduled job도 inbound adapter라는 감각을 잡았다면, 이 문서는 그다음 질문인 "그 job이 기존 유스케이스를 `for` loop로 호출하면 충분한가, 아니면 배치 전용 application service가 필요한가"만 좁혀서 본다.
여기까지 이해한 뒤 "실패 정책을 언제 pure per-item retry에서 chunk summary/retry queue/checkpoint로 올려야 하나?"가 궁금하면 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)를 먼저 보면 된다.
그다음 "batch 전용 서비스까지는 아닌데 outbound port를 `List` 기반 bulk port로 바꿔야 하나?"가 고민이라면 [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)를 이어서 보면 된다.
스케줄링 인프라, 분산 락, 큐 handoff까지 커지는 경우는 [System Design: Job Queue 설계](../system-design/job-queue-design.md), [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md)로 넘기면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 구분이 필요한가](#왜-이-구분이-필요한가)
- [먼저 경계부터 잡기](#먼저-경계부터-잡기)
- [기존 use case를 loop해도 되는 경우](#기존-use-case를-loop해도-되는-경우)
- [dedicated batch-oriented application service가 필요한 경우](#dedicated-batch-oriented-application-service가-필요한-경우)
- [결정 표로 빠르게 판단하기](#결정-표로-빠르게-판단하기)
- [설계 예시 1: thin job adapter + 기존 use case loop](#설계-예시-1-thin-job-adapter--기존-use-case-loop)
- [설계 예시 2: dedicated batch application service](#설계-예시-2-dedicated-batch-application-service)
- [자주 생기는 실수](#자주-생기는-실수)

</details>

> 관련 문서:
> - [Software Engineering README: Batch Job Scope In Hexagonal Architecture](./README.md#batch-job-scope-in-hexagonal-architecture)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [System Design: Job Queue 설계](../system-design/job-queue-design.md)
> - [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md)
>
> retrieval-anchor-keywords:
> - batch job scope hexagonal architecture
> - scheduled job loop existing use case
> - batch-oriented application service
> - dedicated batch application service
> - cron job use case loop
> - scheduler adapter vs application service
> - batch window checkpoint resume
> - chunked batch application service
> - per-item use case vs batch run
> - bulk port vs per-item use case
> - batch partial failure policy
> - chunk summary retry queue checkpoint
> - bulk processing use case
> - batch orchestration hexagonal
> - scheduled reconciliation batch service
> - run-scoped idempotency
> - batch progress checkpoint

## 왜 이 구분이 필요한가

실무에서 scheduled job은 자주 두 극단으로 무너진다.

- 이미 있는 단건 use case를 무조건 `for` loop로 돌리다가, 실제로는 batch window, checkpoint, backfill 정책이 필요한데 그 로직이 adapter 안으로 번진다
- 반대로 "배치니까 예외"라고 생각하고 SQL bulk update나 임시 스크립트가 application layer를 우회한다

둘 다 hexagonal에서 경계를 흐린다.

- 첫 번째는 **application 의미가 adapter로 새는 문제**
- 두 번째는 **도메인 규칙이 인프라 최적화에 먹히는 문제**

핵심 질문은 이것이다.

- 이 job은 단지 **같은 유스케이스를 다른 트리거로 여는가**
- 아니면 **batch run 자체가 별도의 application capability인가**

## 먼저 경계부터 잡기

scheduled job이라는 사실만으로 batch application service가 자동 생성되지는 않는다.
먼저 책임을 세 층으로 나누면 판단이 쉬워진다.

| 위치 | 주로 맡는 책임 | 여기서 비대해지면 보이는 신호 |
|---|---|---|
| job adapter | 언제 실행할지, 분산 락, trigger translation, 운영용 entrypoint | `@Scheduled` 메서드 안에 window 계산, chunk loop, checkpoint 저장이 길어진다 |
| 기존 per-item use case | 한 건 단위 비즈니스 규칙, 상태 전이, 단건 side effect | trigger 종류별 `if` 분기가 도메인 규칙을 오염시킨다 |
| batch-oriented application service | batch window, candidate snapshot, chunking, checkpoint, partial failure policy, run summary | 별도 run id, backfill 범위, 재개 정책, 운영자 재실행 기능이 필요해진다 |

즉 판단 기준은 "동기냐 비동기냐", "cron이냐 queue냐"가 아니다.
**한 번의 batch run이 독자적인 입력 계약과 실패 의미를 갖는가**가 기준이다.

## 기존 use case를 loop해도 되는 경우

아래 조건이 맞으면 scheduled job은 보통 thin adapter로 남기고 기존 use case를 반복 호출하면 충분하다.

### 1. 배치가 아니라 "같은 단건 행위의 다른 트리거"다

- 관리자 수동 재처리
- 메시지 consumer의 즉시 반응
- scheduler의 주기적 누락 복구

세 경우가 결국 같은 `ReconcilePayment(paymentId)` 의미라면, batch는 새 유스케이스가 아니라 **같은 유스케이스의 추가 진입 채널**에 가깝다.

### 2. 아이템 간 결합이 약하다

- 한 건 실패가 다른 건의 정합성을 바꾸지 않는다
- 처리 순서가 correctness를 바꾸지 않는다
- 한 건 커밋 경계가 자연스럽다

이 경우 batch run은 사실상 "안전한 단건 처리의 반복"이다.

### 3. 실패와 재시도가 아이템 단위로 닫힌다

- 다시 돌려도 멱등하게 안전하다
- 전체 run 상태를 영속 저장하지 않아도 된다
- 운영자는 "몇 건 실패했는지" 정도만 보면 된다

즉 observability는 필요해도 **run 자체의 도메인 상태**는 필요하지 않다.

### 4. 성능 비용이 아직 channel concern 수준이다

- 한 건씩 port를 타는 비용이 허용 가능하다
- 외부 API rate limit, DB lock time, transaction duration이 아이템 단위 처리로 감당된다
- candidate 조회도 복잡한 business snapshot보다는 단순한 "처리 대상 찾기"에 가깝다

이 정도면 batch 최적화가 아니라 adapter 운영 문제다.

## dedicated batch-oriented application service가 필요한 경우

아래 중 두세 가지가 같이 보이면 batch를 별도 application service로 올리는 편이 맞다.

### 1. batch run 자체가 비즈니스 의미를 가진다

예를 들면:

- 월말 정산 마감
- 일별 statement 생성
- 기간 기준 쿠폰 만료
- reconciliation cutoff 시점 확정

이때 중요한 것은 `merchantId` 하나가 아니라 **"2026-04-30 마감 배치"라는 run 자체**다.

### 2. batch window, snapshot, checkpoint가 correctness에 들어온다

- 같은 기준 시각으로 대상을 고정해야 한다
- 중간 실패 후 이어서 재개해야 한다
- backfill 범위를 명시적으로 다시 실행해야 한다
- cursor와 chunk 경계를 남기지 않으면 중복 처리나 누락이 생긴다

이 시점부터 chunking은 성능 옵션이 아니라 application semantics다.

### 3. partial failure policy가 per-item 재시도 이상이다

- 일부 실패를 모아 별도 review queue로 넘긴다
- 전체 run을 `SUCCEEDED_WITH_FAILURES` 같은 상태로 남긴다
- 성공/실패 집계를 run summary로 저장한다
- 완료 후 하나의 정산 리포트나 downstream event를 발행한다

이건 더 이상 adapter 안의 `for` loop가 설명할 책임이 아니다.

### 4. bulk optimization이 경계 안에서 설계되어야 한다

- 단건 use case를 `N`번 호출하면 외부 API/DB 비용이 비현실적이다
- 한 건씩 같은 aggregate를 불러오면 락과 round trip이 과하다
- candidate selection과 write path를 batch 전용 port로 재구성해야 한다

중요한 점은 여기서도 batch service가 도메인 규칙을 버리는 것은 아니라는 점이다.
**batch service가 batch 단위 orchestration을 맡고, 도메인 규칙은 여전히 안쪽에서 지킨다.**

## 결정 표로 빠르게 판단하기

| 질문 | 기존 use case loop가 잘 맞는 경우 | dedicated batch application service가 잘 맞는 경우 |
|---|---|---|
| 핵심 비즈니스 의미가 무엇인가 | 한 건 처리 | 한 번의 run 또는 기간/window 처리 |
| 트랜잭션 경계는 어디가 자연스러운가 | item 단위 | chunk/run 단위 정책이 필요 |
| 실패를 어떻게 설명하는가 | "몇 건 실패"면 충분 | run status, checkpoint, resume가 필요 |
| 처리 순서/병렬성/분할이 correctness에 영향이 있는가 | 거의 없다 | 있다 |
| 재실행 입력은 무엇인가 | 같은 item을 다시 처리 | run id, 기간, cursor, backfill 범위 |
| 성능 최적화가 어디에 필요한가 | adapter 운영 수준 | application-level bulk port와 snapshot 수준 |

짧은 판단 문장으로 바꾸면 이렇다.

- "scheduler가 같은 command를 여러 번 호출할 뿐"이면 loop
- "batch run을 하나의 command로 설명해야 한다"면 dedicated service

## 설계 예시 1: thin job adapter + 기존 use case loop

```java
public interface ReconcilePaymentUseCase {
    void reconcile(ReconcilePaymentCommand command);
}

public record ReconcilePaymentCommand(
    String paymentId,
    SyncTrigger trigger
) {}

@Component
class PaymentReconciliationJob {
    private final FindStalePaymentIdsQuery query;
    private final ReconcilePaymentUseCase useCase;

    @Scheduled(cron = "0 */10 * * * *")
    void run() {
        for (String paymentId : query.findNextPage(200)) {
            useCase.reconcile(new ReconcilePaymentCommand(
                paymentId,
                SyncTrigger.SCHEDULED_RECONCILIATION
            ));
        }
    }
}
```

이 구조가 맞는 이유:

- job은 시간 기반 trigger와 대상 조회만 맡는다
- 핵심 상태 전이는 `ReconcilePaymentUseCase` 하나에 모인다
- 관리자 수동 재처리나 consumer path도 같은 유스케이스를 재사용할 수 있다

여기서 batch는 **새 application capability가 아니라 호출 수가 많은 adapter**다.

## 설계 예시 2: dedicated batch application service

```java
public interface RunMonthlySettlementBatchUseCase {
    BatchRunResult run(MonthlySettlementBatchCommand command);
}

public record MonthlySettlementBatchCommand(
    String runId,
    LocalDate closingDate,
    int chunkSize
) {}

public final class MonthlySettlementBatchService
    implements RunMonthlySettlementBatchUseCase {

    private final SettlementBatchCandidatePort candidatePort;
    private final BatchCheckpointPort checkpointPort;
    private final SettleMerchantUseCase settleMerchantUseCase;

    @Override
    public BatchRunResult run(MonthlySettlementBatchCommand command) {
        BatchCheckpoint checkpoint = checkpointPort.loadOrStart(
            command.runId(),
            command.closingDate()
        );

        while (true) {
            List<String> merchantIds = candidatePort.findNextSlice(
                command.closingDate(),
                checkpoint.cursor(),
                command.chunkSize()
            );

            if (merchantIds.isEmpty()) {
                return checkpoint.finish();
            }

            for (String merchantId : merchantIds) {
                settleMerchantUseCase.settle(
                    new SettleMerchantCommand(merchantId, command.closingDate())
                );
            }

            checkpoint = checkpoint.advance(merchantIds.get(merchantIds.size() - 1));
            checkpointPort.save(checkpoint);
        }
    }
}
```

이 구조가 맞는 이유:

## 설계 예시 2: dedicated batch application service (계속 2)

- `closingDate`, `runId`, `chunkSize`가 run 입력 계약이다
- checkpoint 저장과 재개가 application layer 책임이다
- item 단위 정산 규칙은 여전히 `SettleMerchantUseCase`가 지킨다

즉 batch service는 도메인 규칙을 대체하지 않고, **batch 단위 orchestration을 명시적인 application 개념으로 승격**한다.

## 자주 생기는 실수

- scheduled job가 커졌는데도 "기존 use case 재사용"이라는 명분으로 adapter 안에 paging, cursor, summary, retry queue 로직을 계속 쌓는다
- dedicated batch service를 만들었다는 이유로 aggregate 규칙을 건너뛰고 bulk SQL update로 상태를 바꾼다
- 단건 use case에 `if (trigger == SCHEDULED_JOB)` 분기를 넣어 batch 전용 정책을 도메인에 섞는다
- batch가 실제로는 run 단위 의미를 갖는데도 observability만 추가하면 된다고 착각한다

한 문장으로 정리하면, scheduled job가 **같은 단건 유스케이스를 다른 타이밍으로 여는 것**이면 loop가 맞고, **batch run 자체의 입력 계약과 실패 의미가 생기면** dedicated batch-oriented application service가 맞다.

## 한 줄 정리

scheduled job가 기존 유스케이스를 반복 호출하는 thin inbound adapter로 끝나도 되는 경우는 "한 건 처리 의미"가 그대로 재사용될 때고, batch window, checkpoint, chunk, partial failure policy 자체가 application 의미가 되면 dedicated batch-oriented application service를 따로 둬야 한다.
