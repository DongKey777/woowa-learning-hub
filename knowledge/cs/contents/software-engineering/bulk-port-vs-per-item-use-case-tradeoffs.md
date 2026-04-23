# Bulk Port vs Per-Item Use Case Tradeoffs

> 한 줄 요약: 성능이 걱정된다고 곧바로 bulk port를 노출하기보다, 먼저 "애플리케이션이 정말 묶음 단위로 생각해야 하는가"를 보고, 아니라면 per-item 유스케이스를 유지한 채 조회 경로나 adapter 최적화만 묶는 편이 더 안전하다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 헷갈리는가](#왜-이-주제가-헷갈리는가)
- [먼저 세 가지 모양부터 기억하기](#먼저-세-가지-모양부터-기억하기)
- [1. strict per-item execution이 맞는 경우](#1-strict-per-item-execution이-맞는-경우)
- [2. per-item 유스케이스는 유지하고 bulk helper port만 두는 경우](#2-per-item-유스케이스는-유지하고-bulk-helper-port만-두는-경우)
- [3. bulk-oriented outbound port를 도입하는 편이 맞는 경우](#3-bulk-oriented-outbound-port를-도입하는-편이-맞는-경우)
- [짧은 결정 표](#짧은-결정-표)
- [예시 1: 메일 재전송은 per-item으로 남긴다](#예시-1-메일-재전송은-per-item으로-남긴다)
- [예시 2: 운송장 조회는 bulk helper port로만 묶는다](#예시-2-운송장-조회는-bulk-helper-port로만-묶는다)
- [예시 3: 정산 전송은 bulk use case와 bulk port가 같이 간다](#예시-3-정산-전송은-bulk-use-case와-bulk-port가-같이-간다)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: Bulk Port vs Per-Item Use Case Tradeoffs](./README.md#bulk-port-vs-per-item-use-case-tradeoffs)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
>
> retrieval-anchor-keywords:
> - bulk port vs per-item use case
> - bulk-oriented outbound port
> - per-item use case execution
> - hexagonal bulk port tradeoff
> - batch port vs single item port
> - per-item command with bulk read port
> - bulk helper port
> - bulk query helper port
> - bulk write port hexagonal
> - strict per-item execution
> - loop use case vs bulk port
> - true bulk contract
> - bulk result type
> - partial failure result
> - adapter optimization vs application bulk contract
> - adapter bulk optimization without port leakage
> - JPA batch inside adapter
> - HTTP bulk endpoint adapter
> - saveAll port smell
> - findByIds port hexagonal
> - bulk api boundary

## 왜 이 주제가 헷갈리는가

실무에서는 처리량 문제가 보이기 시작하면 두 극단으로 가기 쉽다.

- "느리니까 다 `List`로 바꾸자"며 `saveAll`, `sendAll`, `syncAll` 같은 bulk port를 빠르게 늘린다
- 반대로 "hexagonal은 무조건 한 건씩"이라고 생각하고, 수천 건을 항상 같은 유스케이스로만 호출해 round trip 비용을 방치한다

둘 다 절반만 맞다.

- 첫 번째는 **성능 걱정을 애플리케이션 계약으로 너무 빨리 끌어올린다**
- 두 번째는 **애플리케이션 의미는 그대로인데 조회/연결 비용을 줄일 기회도 함께 버린다**

초심자 기준으로는 먼저 이 질문 하나로 정리하면 된다.

- 지금 문제는 **한 건 판단을 많이 반복하는 것**인가
- 아니면 **묶음 자체가 하나의 의미를 가지는 것**인가

## 먼저 세 가지 모양부터 기억하기

이 주제는 사실 두 가지가 아니라 세 가지 선택지로 보면 훨씬 덜 헷갈린다.

| 모양 | 애플리케이션이 생각하는 단위 | 보통의 신호 |
|---|---|---|
| strict per-item execution | 한 건 | 실패, 재시도, 감사 로그가 item 단위로 닫힌다 |
| per-item use case + bulk helper port | 판단은 한 건, 조회/준비만 묶음 | 외부 조회나 candidate 로딩 round trip이 많다 |
| bulk use case + bulk-oriented outbound port | run/chunk/파일/묶음 | chunk 결과, partial failure, checkpoint가 의미가 된다 |

가장 중요한 포인트는 이것이다.

- **성능 문제 = 곧바로 bulk use case**는 아니다
- 중간 단계인 **bulk helper port**가 먼저 맞는 경우가 많다

## 1. strict per-item execution이 맞는 경우

아래 상황이면 유스케이스와 outbound port를 한 건 기준으로 유지하는 편이 좋다.

### 한 건마다 규칙과 실패 의미가 독립적이다

- 한 사용자의 메일 발송 실패가 다른 사용자 결정에 영향을 주지 않는다
- 한 주문 취소 실패가 다른 주문 취소 결과를 바꾸지 않는다
- 운영자도 "37번만 다시 실행"처럼 item 단위로 다루면 충분하다

### 감사, 멱등성, 재시도가 item 단위로 닫힌다

- idempotency key도 item 기준이다
- 실패 이력과 보상 처리도 item 기준이다
- "batch run 상태"를 따로 저장하지 않아도 운영 설명이 된다

### 외부 시스템도 사실상 단건 의미에 가깝다

- bulk endpoint가 없거나
- 있더라도 "여러 건을 한 번에 보내는 편의 기능" 정도이고
- 성공/실패와 rate limit 판단은 결국 item 단위로 다시 봐야 한다

이 경우에는 port를 무리하게 `List` 기반으로 바꾸기보다, per-item 흐름을 유지하는 편이 설계와 운영이 더 단순하다.

## 2. per-item 유스케이스는 유지하고 bulk helper port만 두는 경우

초심자가 가장 많이 놓치는 안전한 중간 단계가 이것이다.

핵심은:

- **결정과 상태 전이는 item 단위로 유지한다**
- 대신 **조회나 준비 작업만 묶어서 가져온다**

예를 들면:

- 외부 API에서 500건 상태를 한 번에 조회할 수 있다
- DB에서 처리 대상 ID를 한 번에 읽어 오는 편이 훨씬 싸다
- reference data를 건건이 조회하면 N round trip이 너무 크다

이때는 `SyncThingUseCase.sync(itemId)` 같은 per-item 유스케이스를 유지하면서,
그 앞단에 bulk query/helper port를 둘 수 있다.

대표적인 예:

- `CarrierStatusBulkQueryPort.fetchStatuses(List<ShipmentId>)`
- `UserContactQueryPort.findByIds(List<UserId>)`
- `ProductSnapshotPort.fetchByIds(List<ProductId>)`

이 구조가 좋은 이유:

- 도메인 규칙은 여전히 한 건씩 검증된다
- 실패와 재시도 단위도 item으로 남는다
- 성능 병목이 조회 fan-out이라면 가장 작은 변화로 개선된다

즉 "성능 때문에 묶음이 필요하다"와 "비즈니스 의미가 묶음이다"를 분리할 수 있다.

## 3. bulk-oriented outbound port를 도입하는 편이 맞는 경우

반대로 아래 신호가 보이면 bulk port를 애플리케이션 계약으로 끌어올리는 편이 맞다.

### 묶음 자체가 설명 가능한 입력이다

- "2026-04 정산 전송"
- "이번 run의 500건 chunk"
- "검색 인덱스 bulk upsert 요청"
- "파트너사 일괄 등록 파일"

이때는 `itemId` 하나보다 **run id, chunk size, cutoff time, file unit**이 더 중요한 입력이다.

### 성공/실패를 묶음 단위로 설명해야 한다

- 500건 중 17건 실패를 chunk summary로 남겨야 한다
- 일부 실패를 별도 review queue로 옮겨야 한다
- 외부 시스템이 batch receipt id나 file id를 돌려준다
- 재개는 item 재시도보다 run checkpoint 기준으로 해야 한다

### 외부 의존도 자체가 bulk-native다

- 외부 시스템이 bulk submit 결과를 한 번에 반환한다
- 대량 upsert, 파일 생성, bulk ack처럼 묶음 호출이 본래 계약이다
- 단건 호출로 쪼개면 rate limit, 비용, latency가 구조적으로 감당되지 않는다

이 상황이면 bulk port는 단순 최적화가 아니라 **실제 애플리케이션 경계**가 된다.
이때 run/chunk/file 입력 타입과 partial failure 결과 타입을 어떻게 이름 붙일지는 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)에서 이어서 보면 된다.

## 짧은 결정 표

| 질문 | strict per-item 유지 | bulk helper port만 추가 | bulk port를 도입 |
|---|---|---|---|
| 유스케이스가 설명하는 단위는? | item | item | run/chunk/file |
| 실패를 어떻게 설명하나? | item 재시도 | item 재시도 | partial failure summary, checkpoint |
| 성능 병목은 어디 있나? | 아직 크지 않다 | 조회/준비 fan-out | 실제 쓰기/전송 계약 자체 |
| 멱등성과 감사 로그 단위는? | item | item | item + run/chunk 둘 다 필요 |
| 첫 번째 개선책은? | 그대로 둔다 | bulk query/helper port | dedicated bulk use case + bulk port |

짧게 외우면 이렇다.

- **한 건을 잘 많이 처리하면 되는 문제**면 per-item
- **한 건 판단은 그대로인데 조회만 비싸다**면 bulk helper port
- **묶음 자체가 일이다**면 bulk port

## 예시 1: 메일 재전송은 per-item으로 남긴다

관리자가 휴면 해제 안내 메일을 200명에게 다시 보내야 한다고 하자.

- 각 사용자마다 수신 동의 확인이 필요하다
- 각 사용자마다 중복 발송 방지 키가 다르다
- 실패해도 1명만 다시 보내면 된다

이 경우 핵심 use case는 여전히 `ResendWelcomeMail(userId)`다.

```java
public interface ResendWelcomeMailUseCase {
    void resend(UserId userId);
}

public interface MailSender {
    void send(WelcomeMail mail);
}
```

`MailSender.sendAll(...)`로 급히 바꾸면 오히려 한 사용자 실패가 전체 결과 설명을 흐릴 수 있다.
이 경우에는 strict per-item이 더 자연스럽다.

## 예시 2: 운송장 조회는 bulk helper port로만 묶는다

야간 동기화 job이 300개의 운송장 상태를 다시 확인한다고 하자.

- 운송장 상태 판단과 저장은 shipment 하나씩 하면 된다
- 하지만 택배사 API는 100건 조회 endpoint를 제공한다
- 병목은 상태 조회 fan-out이지, 도메인 규칙 자체가 아니다

이때는 use case를 bulk로 바꾸기보다 조회 port만 묶는 편이 좋다.

```java
public interface SyncShipmentStatusUseCase {
    void sync(ShipmentId shipmentId, CarrierStatusSnapshot snapshot);
}

public interface CarrierStatusBulkQueryPort {
    Map<ShipmentId, CarrierStatusSnapshot> fetchStatuses(List<ShipmentId> shipmentIds);
}
```

```java
class ShipmentSyncJob {
    private final FindTargetShipmentIdsPort targetPort;
    private final CarrierStatusBulkQueryPort carrierPort;
    private final SyncShipmentStatusUseCase useCase;

    void run() {
        List<ShipmentId> ids = targetPort.findNextBatch(300);
        Map<ShipmentId, CarrierStatusSnapshot> snapshots = carrierPort.fetchStatuses(ids);

        for (ShipmentId id : ids) {
            useCase.sync(id, snapshots.get(id));
        }
    }
}
```

여기서 bulk는 **준비 작업의 효율화**다.
애플리케이션이 설명하는 핵심 행위는 여전히 shipment 한 건 동기화다.

## 예시 3: 정산 전송은 bulk use case와 bulk port가 같이 간다

반대로 파트너 정산을 하루 한 번 500건씩 전송한다고 하자.

- 파트너 API가 bulk submit만 지원한다
- 결과도 batch receipt id로 돌아온다
- 일부 실패를 별도 재처리 큐로 보내야 한다
- 운영자는 "4월 23일 오전 run의 3번째 chunk"를 기준으로 재개한다

이 경우에는 묶음 자체가 일이다.

```java
public interface RunSettlementDeliveryUseCase {
    SettlementBatchResult run(SettlementBatchCommand command);
}

public interface PartnerSettlementBulkPort {
    BulkSubmitResult submit(SettlementChunk chunk);
}
```

이제 bulk port는 단순한 `List` 최적화가 아니라:

- run/chunk 단위 입력 계약
- chunk 결과 집계
- partial failure 처리
- checkpoint 재개

를 함께 설명하는 애플리케이션 경계가 된다.

## 자주 하는 오해

- `findAllById()`가 있다고 해서 유스케이스 전체가 bulk가 되는 것은 아니다.
- `saveAll()`을 포트에 바로 노출하면 aggregate 규칙 검증이 한 번에 뭉개질 수 있다.
- bulk port를 만들었다고 해서 도메인 규칙을 건너뛰고 SQL bulk update로 바로 상태를 바꿔도 된다는 뜻은 아니다.
- per-item 설계를 유지한다고 해서 성능 개선을 포기해야 하는 것은 아니다. 조회/query/helper 경로부터 묶을 수 있다.
- batch job가 있다고 해서 항상 bulk port가 필요한 것은 아니다. [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)처럼 run 의미가 먼저 있어야 한다.

## 기억할 기준

초심자용으로는 세 문장만 기억하면 충분하다.

1. **행위가 한 건이면 유스케이스도 한 건으로 남긴다.**
2. **조회 fan-out만 문제면 bulk helper port부터 본다.**
3. **run/chunk/file이 비즈니스 입력이 되면 bulk port를 애플리케이션 계약으로 올린다.**
