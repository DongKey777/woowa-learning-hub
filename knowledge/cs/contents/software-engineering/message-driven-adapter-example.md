# Message-Driven Adapter Example

> 한 줄 요약: HTTP controller, message consumer, batch job는 먼저 "같은 일을 여는 서로 다른 입구인가?"를 보고 하나의 유스케이스 경계를 공유할지 판단하면 되고, 그다음에 inbound adapter 같은 용어를 붙이면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: message driven adapter example, inbound adapter examples, http controller vs message consumer vs batch job, same use case boundary beginner, controller batch consumer same service, 같은 유스케이스 경계, batch도 같은 service 써야 하나, consumer도 controller service 같이 쓰나, entrypoint boundary primer, inbound adapter beginner, what is inbound adapter, multi entrypoint use case, beginner hexagonal entrypoint
<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 한 문장으로 이해하기](#먼저-한-문장으로-이해하기)
- [먼저 용어 없이 경계부터 고르기](#먼저-용어-없이-경계부터-고르기)
- [같은 유스케이스를 세 가지 입력으로 여는 예시](#같은-유스케이스를-세-가지-입력으로-여는-예시)
- [HTTP controller adapter는 무엇을 맡나](#http-controller-adapter는-무엇을-맡나)
- [Message consumer adapter는 무엇을 맡나](#message-consumer-adapter는-무엇을-맡나)
- [Scheduled job adapter는 무엇을 맡나](#scheduled-job-adapter는-무엇을-맡나)
- [무엇이 같고 무엇이 다른가](#무엇이-같고-무엇이-다른가)
- [자주 하는 실수](#자주-하는-실수)

</details>

> 관련 문서:
> - [Software Engineering README: Message-Driven Adapter Example](./README.md#message-driven-adapter-example)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
> - [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Design Pattern: Command Handler Pattern](../design-pattern/command-handler-pattern.md)
> - [Design Pattern: Process Manager Deadlines and Timeouts](../design-pattern/process-manager-deadlines-timeouts.md)
> - [System Design: Job Queue 설계](../system-design/job-queue-design.md)
> - [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md)
> - [System Design: Workflow Orchestration + Saga 설계](../system-design/workflow-orchestration-saga-design.md)
>
> retrieval-anchor-keywords:
> - message-driven adapter example
> - inbound adapter examples
> - http controller vs message consumer vs scheduled job
> - message consumer hexagonal architecture
> - scheduled job inbound adapter
> - primary adapter examples
> - same use case different triggers
> - controller adapter vs consumer adapter
> - cron job adapter hexagonal
> - batch job scope hexagonal architecture
> - scheduled job loop existing use case
> - batch-oriented application service
> - webhook inbound adapter
> - webhook vs broker consumer
> - http callback vs message broker consumer
> - inbound adapter acknowledgment semantics
> - idempotent consumer adapter
> - message handler slice test
> - message consumer integration test
> - message adapter contract test
> - inbound adapter testing matrix
> - controller consumer scheduler test matrix
> - scheduled job integration test
> - command handler bridge
> - process manager timeout bridge
> - job queue handoff
> - distributed scheduler handoff
> - workflow orchestration bridge

입력 채널만 다른지, 아니면 command lifecycle과 timeout ownership까지 달라지는지 헷갈리면 [Design Pattern: Command Handler Pattern](../design-pattern/command-handler-pattern.md), [Design Pattern: Process Manager Deadlines and Timeouts](../design-pattern/process-manager-deadlines-timeouts.md)로 내려가면 된다.
같은 HTTP inbound adapter라도 사용자 요청 controller와 외부 webhook receiver는 delivery semantics가 다르고, 이를 broker consumer와 나란히 보고 싶다면 [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)를 바로 이어서 보면 된다.
같은 inbound adapter를 테스트에서 어디까지 slice로 자를지 고민한다면 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)가 바로 다음 읽기 순서다.
controller, message consumer, scheduled job를 서로 다른 테스트 포트폴리오로 비교하려면 [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)를 이어서 보면 된다.
scheduled job가 기존 per-item 유스케이스를 반복 호출하는 thin adapter로 끝나는지, 아니면 batch window/chunk/checkpoint를 가진 전용 application service가 필요한지는 [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)에서 이어서 보면 된다.
outbox/inbox와 event contract까지 포함해 unit/integration/contract를 한 번에 나누고 싶다면 [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)를 바로 이어서 보면 된다.
재시도, backlog, misfire, long-running workflow까지 커지는 순간은 [System Design: Job Queue 설계](../system-design/job-queue-design.md), [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md), [System Design: Workflow Orchestration + Saga 설계](../system-design/workflow-orchestration-saga-design.md)가 다음 handoff다.

## 왜 이 primer가 필요한가

Hexagonal Architecture를 처음 배울 때는 controller와 repository만 떠올리기 쉽다.
그래서 아래처럼 오해하는 경우가 많다.

- HTTP controller만 inbound adapter라고 생각한다
- 메시지 consumer는 "비동기 인프라 코드"라서 구조 설명 밖에 둔다
- scheduled job은 그냥 util이나 batch 코드로 따로 둔다

하지만 세 가지 모두 바깥에서 안쪽 유스케이스를 호출하는 **입구**라는 점에서는 같은 부류다.
즉 차이는 "hexagonal이냐 아니냐"가 아니라, **어떤 채널로 유스케이스에 들어오느냐**다.

## 먼저 한 문장으로 이해하기

핵심은 단순하다.

- 유스케이스는 `무슨 일을 할지`를 결정한다
- inbound adapter는 `어떤 신호를 받아 그 유스케이스를 호출할지`를 결정한다

그래서 HTTP 요청, 메시지 이벤트, 스케줄 tick은 다르더라도 안쪽 애플리케이션 서비스는 같은 포트를 통해 재사용될 수 있다.

## 먼저 용어 없이 경계부터 고르기

처음에는 `inbound adapter`, `hexagonal` 같은 이름보다 아래 질문이 더 중요하다.

- HTTP에서 누른 버튼
- 메시지로 들어온 이벤트
- 배치가 주기적으로 찾은 대상

이 셋이 결국 **같은 비즈니스 행동을 시작하는가**?

예를 들어 셋 다 "결제 상태를 다시 맞춘다"라면 입구는 셋이지만 안쪽 유스케이스 경계는 하나로 두는 편이 자연스럽다.
반대로 HTTP는 "즉시 취소", batch는 "월말 일괄 정산 마감"처럼 성공 기준과 실패 설명이 다르면 처음부터 다른 유스케이스로 보는 편이 맞다.

짧은 결정 표로 보면 이렇다.

| 질문 | 하나의 유스케이스를 공유해도 되는 신호 | 분리된 유스케이스를 의심할 신호 |
|---|---|---|
| 사용자가 설명하는 일이 같은가 | "결제 상태 재동기화"처럼 한 문장으로 같다 | "수동 재처리"와 "월 마감 배치"처럼 결과 설명이 다르다 |
| 성공/실패를 어떻게 말하나 | item 하나 성공/실패로 설명 가능 | run 전체 상태, 마감 완료, 집계 결과가 필요하다 |
| 채널 차이가 어디에 머무나 | 인증, ack, 스케줄, 재시도 같은 입구 세부 | 도메인 규칙 자체가 채널별로 갈라진다 |

즉 처음 판단은 "HTTP냐 메시지냐 배치냐"가 아니라 **같은 일을 다른 타이밍으로 여는가**다.

## 같은 유스케이스를 세 가지 입력으로 여는 예시

예를 들어 `SyncPaymentStatusUseCase`가 있다고 하자.
이 유스케이스는 "결제 상태를 외부 결제사와 다시 맞춘다"는 하나의 비즈니스 의미를 가진다.

- 운영자는 관리자 화면에서 수동 재동기화를 누를 수 있다
- 결제 완료 이벤트를 소비한 consumer가 즉시 동기화를 요청할 수 있다
- 누락 복구를 위해 스케줄러가 주기적으로 재동기화를 돌릴 수 있다

```java
public interface SyncPaymentStatusUseCase {
    void sync(SyncPaymentStatusCommand command);
}

public record SyncPaymentStatusCommand(
    String paymentId,
    SyncTrigger trigger
) {}

public enum SyncTrigger {
    HTTP_RETRY,
    MESSAGE_EVENT,
    SCHEDULED_RECONCILIATION
}
```

```java
public class SyncPaymentStatusService implements SyncPaymentStatusUseCase {
    private final PaymentGateway paymentGateway;
    private final PaymentRepository paymentRepository;

    public SyncPaymentStatusService(
        PaymentGateway paymentGateway,
        PaymentRepository paymentRepository
    ) {
        this.paymentGateway = paymentGateway;
        this.paymentRepository = paymentRepository;
    }

    @Override
    public void sync(SyncPaymentStatusCommand command) {
        PaymentSnapshot snapshot = paymentGateway.fetch(command.paymentId());
        Payment payment = paymentRepository.get(command.paymentId());

        payment.reconcile(snapshot, command.trigger());
        paymentRepository.save(payment);
    }
}
```

중요한 점은 `SyncPaymentStatusService`가 HTTP, Kafka, cron을 직접 모른다는 것이다.
그 차이는 바깥 inbound adapter에서 처리한다.

## HTTP controller adapter는 무엇을 맡나

HTTP controller는 요청/응답 모델을 유스케이스 호출로 번역한다.

```java
@RestController
class PaymentAdminController {
    private final SyncPaymentStatusUseCase useCase;

    @PostMapping("/admin/payments/{paymentId}/sync")
    ResponseEntity<Void> sync(@PathVariable String paymentId) {
        useCase.sync(new SyncPaymentStatusCommand(paymentId, SyncTrigger.HTTP_RETRY));
        return ResponseEntity.accepted().build();
    }
}
```

controller의 책임은 보통 아래에 가깝다.

- path/query/body를 command로 변환한다
- 인증, 인가, 입력 검증을 붙인다
- 예외를 HTTP status와 response body로 번역한다

즉 controller는 비즈니스 규칙의 주인이 아니라, **웹이라는 입력 채널을 포트 호출로 바꾸는 adapter**다.

## Message consumer adapter는 무엇을 맡나

메시지 consumer도 같은 역할을 한다.
차이는 입력이 HTTP request가 아니라 broker message라는 점이다.

```java
@KafkaListener(topics = "payment-authorized")
class PaymentAuthorizedConsumer {
    private final SyncPaymentStatusUseCase useCase;

    public void handle(PaymentAuthorizedEvent event) {
        useCase.sync(new SyncPaymentStatusCommand(
            event.paymentId(),
            SyncTrigger.MESSAGE_EVENT
        ));
    }
}
```

consumer adapter가 특히 더 신경 써야 하는 것은 채널 특성이다.

- 같은 메시지가 다시 올 수 있으므로 멱등성을 확인해야 한다
- ack/nack와 재시도 정책을 정해야 한다
- poison message는 DLQ나 격리 경로를 준비해야 한다

즉 consumer는 "비동기라서 hexagonal 밖"이 아니라, **브로커 이벤트를 유스케이스 호출로 번역하는 inbound adapter**다.

## Scheduled job adapter는 무엇을 맡나

scheduled job도 바깥에서 안쪽을 호출한다는 점에서 동일하다.
단지 트리거가 사용자의 요청도, 메시지 브로커도 아니라 시간이라는 점만 다르다.

```java
@Component
class PaymentReconciliationJob {
    private final SyncPaymentStatusUseCase useCase;
    private final PaymentQueryService paymentQueryService;

    @Scheduled(cron = "0 */10 * * * *")
    void run() {
        for (String paymentId : paymentQueryService.findStalePaymentIds()) {
            useCase.sync(new SyncPaymentStatusCommand(
                paymentId,
                SyncTrigger.SCHEDULED_RECONCILIATION
            ));
        }
    }
}
```

job adapter에서는 아래 같은 운영 관심사가 커진다.

- 동시에 두 번 돌지 않도록 락이나 shard 전략이 필요한가
- 한 번에 몇 건씩 처리할지 batch size를 어떻게 잡을까
- 실패한 항목을 다음 주기에 재시도할지 별도 큐로 보낼지

scheduler도 본질은 같다.
시간 기반 신호를 받아 적절한 command를 만들고 유스케이스를 호출하는 것이다.

## 무엇이 같고 무엇이 다른가

| 항목 | HTTP controller | Message consumer | Scheduled job |
|---|---|---|---|
| 입력 신호 | 사용자/클라이언트 요청 | 브로커 이벤트 | 시간 기반 트리거 |
| adapter의 주된 번역 | request DTO -> command | event payload -> command | 조회 결과/시간 조건 -> command |
| 채널별 관심사 | 인증, 응답 코드, 지연 시간 | ack, 재시도, 멱등성, DLQ | 중복 실행 방지, batch, 백필 |
| 호출 대상 | 같은 inbound port 가능 | 같은 inbound port 가능 | 같은 inbound port 가능 |
| 핵심 오해 | controller가 곧 application이라고 착각 | consumer를 인프라 util로 취급 | job을 도메인 밖 스크립트로 분리 |

세 가지를 함께 보면 규칙은 더 선명해진다.

- 유스케이스는 채널별 세부를 모른다
- adapter는 채널별 세부를 흡수한다
- 채널이 늘어도 비즈니스 규칙은 같은 유스케이스에 남는다

즉 "HTTP용 서비스", "consumer용 서비스", "batch용 서비스"를 따로 만드는 것이 아니라, 가능하면 **하나의 유스케이스를 여러 inbound adapter가 공유**하도록 본다.
이 원칙은 "무조건 하나로 합쳐라"가 아니라, **같은 비즈니스 행동이면 경계를 복제하지 말라**는 뜻이다.

초심자용으로 더 짧게 기억하면 아래 두 문장으로 충분하다.

- 입구가 달라도 "하는 일"이 같으면 유스케이스를 먼저 공유한다.
- batch run 자체가 별도 의미를 가지기 시작하면 그때 전용 유스케이스를 올린다.

## 자주 하는 실수

- message consumer 안에서 바로 repository, 외부 API, 트랜잭션 흐름을 조립해 controller와 다른 비즈니스 규칙을 만든다
- scheduled job이 application service를 우회하고 SQL이나 스크립트로 직접 상태를 바꾼다
- 채널 이름을 따라 `AdminSyncService`, `ConsumerSyncService`, `BatchSyncService`를 따로 만들고 규칙이 조금씩 갈라진다
- HTTP controller만 테스트하고 consumer/job adapter의 매핑과 실패 처리는 검증하지 않는다
- "비동기니까 다른 아키텍처"라고 생각해 같은 도메인 규칙이 채널마다 갈라진다

한 문장으로 다시 정리하면, HTTP controller, message consumer, batch job은 모두 **같은 일을 시작하면 하나의 유스케이스로 모이고**, 그 바깥의 진입 방식만 서로 다른 inbound adapter가 된다.

## 한 줄 정리

HTTP controller, message consumer, batch job은 먼저 "같은 일을 여는 입구들인가?"를 보고 하나의 유스케이스 경계를 공유할지 판단하면 된다.
