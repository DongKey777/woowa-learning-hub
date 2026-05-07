---
schema_version: 3
title: saveAll/sendAll Port Smells and Safer Alternatives
concept_id: software-engineering/saveall-sendall-port-smells
canonical: true
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/backend
review_feedback_tags:
- ports-and-adapters
- batch
- bulk-contract
- invariants
aliases:
- saveAll port smell
- sendAll port smell
- bulk port smell
- per item port vs bulk port
- named bulk contract
- saveAll 포트 냄새
symptoms:
- outbound port에 saveAll이나 sendAll을 그대로 노출해서 item 단위 불변식, 실패 정책, idempotency 단위가 계약에서 사라져
- List를 받는 bulk port가 한 건 실패 시 전체 실패인지 partial success인지 결과 타입으로 설명하지 않아
- JPA batch나 외부 SDK bulk endpoint 같은 adapter 최적화 이유가 application port 이름으로 승격돼
- true bulk 업무인데 SettlementChunk, NotificationBatch, BulkSubmitResult 같은 named contract 없이 단순 List로만 표현돼
intents:
- symptom
- troubleshooting
- design
prerequisites:
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/bulk-port-tradeoffs
next_docs:
- software-engineering/true-bulk-contracts-partial-failure-results
- software-engineering/adapter-bulk-optimization
- software-engineering/jpa-batch-config-pitfalls
linked_paths:
- contents/software-engineering/jpa-batch-config-pitfalls.md
- contents/software-engineering/bulk-port-vs-per-item-use-case-tradeoffs.md
- contents/software-engineering/adapter-bulk-optimization-without-port-leakage.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
- contents/software-engineering/true-bulk-contracts-partial-failure-results.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/software-engineering/batch-job-scope-hexagonal-architecture.md
- contents/software-engineering/message-driven-adapter-example.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/software-engineering/domain-invariants-as-contracts.md
confusable_with:
- software-engineering/bulk-port-tradeoffs
- software-engineering/true-bulk-contracts-partial-failure-results
- software-engineering/jpa-batch-config-pitfalls
forbidden_neighbors: []
expected_queries:
- saveAll이나 sendAll을 outbound port로 바로 올리면 item 단위 invariant와 실패 정책이 왜 숨어?
- bulk 처리는 언제 adapter 내부 최적화이고 언제 named bulk contract로 port에 올라와야 해?
- per-item port를 유지하면서 JDBC batch나 외부 bulk API 최적화를 adapter에 숨기는 방법을 알려줘
- partial failure가 필요한 bulk 업무는 List 반환 대신 어떤 result type을 둬야 해?
- saveAll을 쓰면 JPA batch가 자동으로 잘 되는지와 port 설계 문제를 어떻게 분리해서 봐야 해?
contextual_chunk_prefix: |
  이 문서는 saveAll/sendAll 같은 bulk helper 이름이 outbound port 계약으로 새어 item invariant, partial failure, idempotency 경계를 숨기는 증상을 다루는 beginner symptom router이다.
---
# saveAll/sendAll Port Smells and Safer Alternatives

> 한 줄 요약: `saveAll`/`sendAll`를 outbound port로 바로 노출하면 "무엇을 한 번에 처리하는가"보다 "일단 묶어서 빠르게 보낸다"만 계약에 남아, item 단위 불변식과 실패 정책이 숨어 버리기 쉽다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: saveall port smell basics, sendall port smell basics, saveall을 port에 올려도 되나요, sendall을 port에 올려도 되나요, bulk port vs per item port, 왜 saveall이 adapter detail인가요, list 받는 port 왜 위험해요, batch 성능 때문에 port를 bulk로 바꿔야 하나요, true bulk contract 뭐예요, saveall 언제 진짜 계약이 되나요, 처음 hexagonal bulk 헷갈림, beginner bulk port primer, per item invariant bulk smell, named bulk contract first question
<details>
<summary>Table of Contents</summary>

- [먼저 한 문장으로 잡기](#먼저-한-문장으로-잡기)
- [왜 saveAll/sendAll이 쉽게 생기나](#왜-saveallsendall이-쉽게-생기나)
- [왜 smell로 보는가](#왜-smell로-보는가)
- [무엇이 숨어 버리나](#무엇이-숨어-버리나)
- [더 안전한 세 가지 대안](#더-안전한-세-가지-대안)
- [예시 1: 저장 port는 단건 계약을 유지한다](#예시-1-저장-port는-단건-계약을-유지한다)
- [예시 2: bulk는 helper port에만 맡긴다](#예시-2-bulk는-helper-port에만-맡긴다)
- [예시 3: bulk가 진짜 일이라면 이름을 올린다](#예시-3-bulk가-진짜-일이라면-이름을-올린다)
- [짧은 비교 표](#짧은-비교-표)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: saveAll/sendAll Port Smells and Safer Alternatives](./README.md#saveallsendall-port-smells-and-safer-alternatives)
> - [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
> - [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)
>
> retrieval-anchor-keywords:
> - saveAll port smell
> - sendAll port smell
> - bulk port smell
> - outbound port hides invariants
> - hidden invariant batch contract
> - per-item port vs bulk port
> - bulk helper port
> - saveAll repository port smell
> - sendAll notification port smell
> - partial failure bulk contract
> - named batch contract
> - true bulk contract
> - bulk result type
> - item failure result
> - hexagonal bulk write smell
> - junior hexagonal bulk primer
> - persistence batch boundary
> - no saveAll port leak
> - saveAll as adapter detail
> - adapter internal bulk api
> - saveAll batching misconception
> - saveAll 다음에 jpa batch config pitfalls
> - saveAll 성능 오해 어디서 푸나

## 먼저 한 문장으로 잡기

초심자 기준으로는 이것만 먼저 기억하면 된다.

- **port는 성능 트릭 이름이 아니라, 애플리케이션이 약속하는 일의 단위**다

만약 "`saveAll()`을 쓰면 JPA batch가 자동으로 잘 걸리는 것 아닌가?"라는 질문부터 시작했다면, 이 문서만 붙잡기보다 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)로 바로 넘어가 `batch_size`, `flush()`, `GenerationType.IDENTITY`를 먼저 확인하는 편이 빠르다.

그래서 `saveAll(List<Order>)`, `sendAll(List<Mail>)` 같은 이름이 보이면 먼저 이렇게 물어보면 된다.

- 정말로 "묶음"이 하나의 일인가?
- 아니면 한 건 규칙을 여러 번 실행하는데, 조회나 전송 효율만 걱정되는가?

이 질문이 흐리면 bulk API 편의 함수가 곧바로 애플리케이션 계약이 된다.

## 왜 saveAll/sendAll이 쉽게 생기나

실무에서는 아래 이유 때문에 이 이름들이 너무 자연스럽게 올라온다.

- JPA, JDBC, 외부 SDK가 이미 `saveAll`, `sendAll`, `bulkSend` 같은 메서드를 제공한다
- 배치 job 입력이 `List`처럼 보이니 port도 그대로 `List`를 받고 싶어진다
- round trip 비용이 보여서 "묶으면 빨라질 것 같다"는 압력이 생긴다

특히 첫 번째 이유 때문에 초심자는 "`Spring Data`에 `saveAll`이 있으니 우리 port도 `saveAll`이면 맞다"라고 생각하기 쉽다. 이 오해가 핵심이면 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)의 "`saveAll` 포트 승격 오해: before / after" 섹션으로 바로 이어 읽는 것이 가장 빠르다.

하지만 이 셋은 대부분 **adapter 구현 이유**다.

- ORM이 편한가
- 외부 API가 bulk endpoint를 주는가
- 네트워크 호출 수를 줄이고 싶은가

이 이유만으로 port를 bulk로 올리면, 애플리케이션이 실제로 지켜야 할 규칙이 이름에서 사라진다.

## 왜 smell로 보는가

`saveAll`/`sendAll`이 항상 틀린 것은 아니다.
다만 초심자 코드에서는 자주 이런 식으로 나온다.

```java
public interface OrderPersistencePort {
    void saveAll(List<Order> orders);
}

public interface NotificationGateway {
    void sendAll(List<Notification> notifications);
}
```

이 계약만 보면 중요한 질문에 답하기 어렵다.

- 일부만 저장되거나 전송되어도 되는가?
- 한 건 실패 시 나머지를 계속 처리하는가?
- 중복 방지는 item 기준인가, run 기준인가?
- 순서가 중요한가?
- 감사 로그와 재시도는 어디 단위로 남기는가?

즉 문제는 `List` 그 자체보다, **묶음의 의미가 이름과 타입에 드러나지 않는 것**이다.

## 무엇이 숨어 버리나

| 숨어 버리는 것 | `saveAll`/`sendAll`에선 왜 흐려지나 | 보통 필요한 질문 |
|---|---|---|
| 판단 단위 | 메서드 이름이 "전부 처리"만 말한다 | 한 건 규칙을 독립적으로 적용하는가? |
| 실패 정책 | `void`나 단순 count 반환이면 partial failure 설명이 없다 | 한 건 실패 시 전체 실패인가, 일부 성공인가? |
| 멱등성 | 중복 방지 키가 묶음인지 item인지 드러나지 않는다 | 재시도 시 무엇을 중복으로 볼 것인가? |
| 순서와 묶음 경계 | `List`는 순서만 보여 주고 왜 이 묶음인지 설명하지 못한다 | run id, chunk id, cutoff time이 필요한가? |
| 감사와 운영 | 나중에 "무엇을 다시 돌릴지" 설명이 약하다 | item 재시도인지 batch 재개인지 분리되는가? |

초심자에게 중요한 감각은 이것이다.

- `saveAll`은 대개 **"빠르게 처리하고 싶다"**를 말한다
- 좋은 port 이름은 **"무엇을 어떤 규칙으로 처리한다"**를 말한다

## 더 안전한 세 가지 대안

이 문제는 bulk를 금지해서 푸는 게 아니라, bulk를 **올바른 층에 올리는 것**으로 푼다.

### 1. item 규칙이 중심이면 단건 port를 유지한다

- 각 item이 독립적으로 검증된다
- 실패와 재시도가 item 단위로 닫힌다
- 운영자도 "42번만 다시 실행"처럼 설명한다

이때는 `save(order)`, `send(notification)`가 더 정직하다.

### 2. bulk는 helper/query port로만 제한한다

- 규칙은 item 단위다
- 하지만 조회, reference data 로딩, 상태 조회만 묶는 편이 싸다

이때는 `findByIds`, `fetchStatuses`, `loadSnapshots`처럼 **무엇을 bulk로 묶는지**를 이름에 적는다.

### 3. bulk가 진짜 일이라면 묶음 자체를 타입으로 드러낸다

- run/chunk/file가 비즈니스 의미를 가진다
- partial failure summary가 필요하다
- 외부 시스템도 batch receipt, file id, chunk result를 돌려준다

이때는 `List<T>`보다 `SettlementChunk`, `NotificationBatch`, `BulkSubmitResult`처럼 이름 있는 계약이 낫다.

## 예시 1: 저장 port는 단건 계약을 유지한다

주문 저장에서 각 주문은 버전 충돌, 상태 검증, 감사 로그가 독립적이라고 하자.

### 덜 안전한 계약

```java
public interface OrderRepository {
    void saveAll(List<Order> orders);
}
```

이 이름만으로는 아래가 보이지 않는다.

- 주문 하나가 version conflict면 전체를 롤백해야 하는가
- 이미 저장된 주문은 어떻게 구분하는가
- 재시도는 어느 주문부터 다시 하는가

### 더 안전한 계약

```java
public interface OrderRepository {
    void save(Order order);
}
```

배치 job는 바깥에서 이렇게 조합하면 된다.

```java
for (Order order : orders) {
    orderRepository.save(order);
}
```

adapter 내부에서는 필요하면 JDBC batch나 ORM 최적화를 사용할 수 있다.
핵심은 그 최적화가 **port 계약이 아니라 구현 세부**라는 점이다.

## 예시 2: bulk는 helper port에만 맡긴다

알림 전송 정책은 사용자마다 다르지만, 연락처 조회는 한 번에 묶는 편이 싸다고 하자.

### 덜 안전한 계약

```java
public interface NotificationGateway {
    void sendAll(List<Notification> notifications);
}
```

이 계약은 "누가 왜 전송 가능한지"보다 "한꺼번에 보내자"만 강조한다.

### 더 안전한 분리

```java
public interface UserContactQueryPort {
    Map<UserId, ContactSnapshot> findByIds(List<UserId> userIds);
}

public interface NotificationGateway {
    void send(Notification notification);
}
```

그러면 흐름은 이렇게 된다.

1. `UserContactQueryPort.findByIds(...)`로 준비 데이터를 bulk 조회한다.
2. 각 사용자 규칙을 item 단위로 확인한다.
3. `NotificationGateway.send(...)`를 item 단위로 호출한다.

즉 bulk는 **준비 작업 최적화**로만 쓰고, 판단과 실패 설명은 item 단위로 유지한다.

## 예시 3: bulk가 진짜 일이라면 이름을 올린다

정산 파일 업로드처럼 "이번 500건 chunk"가 업무 단위인 경우는 다르다.

- run id가 필요하다
- 부분 실패 건수를 남겨야 한다
- 외부 시스템이 batch receipt id를 반환한다

이때는 단순 `sendAll(List<SettlementLine>)`보다 아래가 낫다.

```java
public record SettlementChunk(
        SettlementRunId runId,
        int sequence,
        List<SettlementLine> lines
) {
}

public record BulkSubmitResult(
        String receiptId,
        int successCount,
        int failureCount
) {
}

public interface SettlementBulkSubmitPort {
    BulkSubmitResult submit(SettlementChunk chunk);
}
```

이 계약은 적어도 다음을 숨기지 않는다.

- 왜 이 묶음이 존재하는가
- 어떤 단위로 다시 시작할 수 있는가
- 결과를 어떤 단위로 기록해야 하는가

즉 bulk 자체가 문제라기보다, **이름 없는 bulk**가 문제다.
run/chunk/file 이름과 partial failure result를 더 구체적으로 잡는 방법은 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)에서 이어서 보면 된다.

## 짧은 비교 표

| 상황 | 더 나은 선택 | 이유 |
|---|---|---|
| 주문, 메일, 쿠폰처럼 item 규칙이 독립적이다 | `save(order)`, `send(notification)` | 실패와 재시도 설명이 명확하다 |
| 판단은 item인데 조회 fan-out만 비싸다 | `findByIds`, `fetchStatuses` 같은 helper port | 규칙은 안 흐리고 성능만 개선한다 |
| 정산 chunk, 업로드 파일, bulk submit 자체가 일이다 | `SettlementChunk`, `BulkSubmitResult` 같은 named batch contract | run/chunk invariants와 partial failure를 드러낸다 |

## 자주 하는 오해

- "`Spring Data`에 `saveAll`이 있으니 port도 `saveAll`이면 된다"
  - 아니다. adapter 구현이 `saveAll`을 쓸 수는 있지만, port는 애플리케이션 의미를 먼저 말해야 한다. 왜 이 오해가 JPA batch 설정 착시와 연결되는지는 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)에서 바로 확인할 수 있다.
- "배치 job가 `List`를 받으니 use case와 port도 `List`여야 한다"
  - 아니다. scheduler adapter가 item loop를 돌릴 수 있고, bulk helper port만 따로 둘 수도 있다.
- "그럼 bulk port는 항상 안 좋은가"
  - 아니다. batch/run/file가 진짜 업무 단위라면 오히려 명시적으로 올려야 한다.
- "`saveAll`을 없애면 성능을 포기하는 것 아닌가"
  - 아니다. bulk 최적화는 adapter 내부, query helper, named batch contract 중 맞는 위치에 두면 된다.

## 기억할 기준

- port는 "몇 번 호출을 줄일까"보다 "무슨 단위의 일을 약속하나"를 말해야 한다
- `saveAll`/`sendAll`이 보이면 item 규칙, partial failure, idempotency가 어디에 숨어 있는지 먼저 본다
- item 규칙이 중심이면 단건 port가 기본이다
- 조회/준비만 bulk면 helper port로 한정한다
- bulk가 진짜 업무 단위라면 `List<T>`가 아니라 이름 있는 batch 타입과 결과 타입을 만든다

## 한 줄 정리

`saveAll`/`sendAll`를 outbound port로 바로 노출하면 "무엇을 한 번에 처리하는가"보다 "일단 묶어서 빠르게 보낸다"만 계약에 남아, item 단위 불변식과 실패 정책이 숨어 버리기 쉽다.
