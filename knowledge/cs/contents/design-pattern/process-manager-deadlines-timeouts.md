---
schema_version: 3
title: Process Manager Deadlines and Timeouts
concept_id: design-pattern/process-manager-deadlines-timeouts
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- process-manager-deadline
- timeout-workflow
- stale-timer-guard
aliases:
- process manager deadline
- timeout workflow
- timer scheduling
- reminder pattern
- deadline exceeded event
- stale timer
- reservation expiry
- workflow owner
- approval sla
- timer version
symptoms:
- deadline 처리를 scheduler callback 하나로만 구현해 깨운 뒤 어떤 상태 전이를 할지 도메인 정책이 흩어진다
- 결제 성공 후 뒤늦게 도착한 만료 timer를 stale signal로 무시하지 못해 잘못된 expire command가 나간다
- timeout을 exception으로만 보고 미응답, reminder, expiry, manual review escalation 같은 도메인 이벤트로 모델링하지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/process-manager-state-store-recovery
- design-pattern/workflow-owner-vs-participant-context
next_docs:
- design-pattern/human-approval-manual-review-workflow-pattern
- design-pattern/escalation-reassignment-queue-ownership-pattern
- design-pattern/reservation-hold-expiry-consistency-seam
linked_paths:
- contents/design-pattern/process-manager-vs-saga-coordinator.md
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/process-manager-state-store-recovery.md
- contents/design-pattern/human-approval-manual-review-workflow-pattern.md
- contents/design-pattern/escalation-reassignment-queue-ownership-pattern.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
- contents/design-pattern/reservation-hold-expiry-consistency-seam.md
- contents/design-pattern/orchestration-vs-choreography-pattern-language.md
- contents/design-pattern/command-bus-pattern.md
- contents/design-pattern/event-envelope-pattern.md
confusable_with:
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/process-manager-state-store-recovery
- design-pattern/workflow-owner-vs-participant-context
- design-pattern/reservation-hold-expiry-consistency-seam
forbidden_neighbors: []
expected_queries:
- Process Manager에서 scheduler는 언제 깨울지를 담당하고 manager는 deadline signal을 어떻게 해석해?
- timeout은 exception이 아니라 주문 만료, reminder, manual review escalation 같은 domain event 입력일 수 있는 이유가 뭐야?
- stale timer를 막기 위해 current status와 timer version token을 함께 비교해야 하는 이유가 뭐야?
- 장기 workflow에서 payment deadline이나 approval SLA 같은 time boundary는 어느 context가 소유해야 해?
- 타이머가 늦게 오거나 중복 발행될 때 process manager는 idempotency와 상태 전이를 어떻게 보호해?
contextual_chunk_prefix: |
  이 문서는 Process Manager Deadlines and Timeouts playbook으로, long-running workflow에서
  scheduler는 wake-up signal을 만들고 process manager는 current state, deadline, timer version,
  stale signal guard를 이용해 timeout, reminder, expiry, escalation을 도메인 상태 전이로 해석하는
  방법을 설명한다.
---
# Process Manager Deadlines and Timeouts

> 한 줄 요약: Process Manager는 장기 프로세스의 deadline, timeout, reminder를 상태와 함께 관리하며, 시간을 또 하나의 도메인 이벤트처럼 다뤄 다음 명령을 결정한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Escalation, Reassignment, and Queue Ownership Pattern](./escalation-reassignment-queue-ownership-pattern.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [Orchestration vs Choreography Pattern Language](./orchestration-vs-choreography-pattern-language.md)
> - [Command Bus Pattern](./command-bus-pattern.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)

---

## 핵심 개념

짧은 workflow는 이벤트가 오자마자 다음 단계를 실행하면 충분하다.  
하지만 장기 프로세스는 시간이 흐르는 동안 아무 일도 없을 수 있다.

- 30분 안에 결제가 없으면 주문 만료
- 24시간 안에 서류가 없으면 리마인드 발송
- 3일 안에 승인 응답이 없으면 수동 검토 큐로 이동

이때 시간은 단순한 인프라 세부사항이 아니라 **도메인 의사결정의 입력**이 된다.  
Process Manager는 그 시간을 deadline, timeout, reminder 형태로 모델링한다.

### Retrieval Anchors

- `process manager deadline`
- `timeout workflow`
- `timer scheduling`
- `reminder pattern`
- `deadline exceeded event`
- `cross boundary orchestration handoff`
- `stale timer`
- `reservation expiry`
- `workflow owner`
- `workflow recovery`
- `approval sla`

---

## 깊이 들어가기

### 1. Scheduler와 Process Manager는 같은 역할이 아니다

Scheduler는 "언제 깨울 것인가"를 담당한다.  
Process Manager는 "깨운 뒤 무엇을 할 것인가"를 담당한다.

- scheduler: at 10:30, emit timeout signal
- process manager: 아직 결제가 없으면 expire command 발행

이 둘을 합치면 cron/queue 기술 세부사항이 도메인 정책 안으로 새기 쉽다.

### 2. timeout은 실패가 아니라 상태 전이 조건일 수 있다

많은 팀이 timeout을 단순한 에러로 본다.  
하지만 장기 프로세스에서는 보통 의미 있는 비즈니스 사건이다.

- 결제 미완료 -> 주문 만료
- 미응답 -> 재알림
- 승인 지연 -> 수동 검토

즉 timeout은 exception보다 **도메인 이벤트에 가까운 입력**으로 보는 편이 맞다.

### 3. deadline 기록은 idempotency와 stale timer를 함께 고려해야 한다

장기 프로세스에서 흔한 문제는 타이머가 늦게 오거나, 이미 완료된 흐름에 뒤늦게 도착하는 것이다.

- 결제 성공 후 만료 타이머가 늦게 도착
- 재시도 예약이 중복 발행
- reminder가 이미 닫힌 케이스에 발송

그래서 process manager는 보통 다음을 함께 가진다.

- 현재 상태
- 다음 deadline 시각
- 처리된 timer token 또는 version
- stale signal 무시 규칙

### 4. cross-boundary orchestration에서는 time boundary를 명시해야 한다

서비스 경계를 넘는 orchestration에서 가장 흐려지기 쉬운 것은 "누가 기다림을 소유하는가"다.

- 주문 서비스가 결제 응답 deadline을 소유하는가
- 결제 서비스가 만료 정책까지 알아야 하는가
- 알림 서비스가 reminder cadence를 결정하는가

보통은 장기 프로세스를 소유한 bounded context가 deadline 정책을 소유하는 편이 안전하다.  
외부 서비스는 응답 이벤트를 주고받고, 기다림의 정책은 process manager가 가진다.

### 5. process manager는 타이머 남발보다 상태 기계를 먼저 가져야 한다

문제가 생길 때마다 timer를 하나씩 붙이면 곧 "timer spaghetti"가 생긴다.

- 첫 리마인드
- 두 번째 리마인드
- 만료 경고
- 강제 종료

이 흐름을 잘 다루려면 timer 목록보다 먼저 상태와 전이 규칙이 있어야 한다.

- `PENDING_PAYMENT`
- `REMINDER_SENT`
- `EXPIRED`
- `UNDER_MANUAL_REVIEW`

시간 신호는 이 상태 기계에 들어오는 입력으로 두는 편이 낫다.

---

## 실전 시나리오

### 시나리오 1: 무통장 입금 주문

주문 생성 직후 30분 deadline을 등록한다.  
입금 확인 이벤트가 오면 deadline을 무효화하고, 그렇지 않으면 `ExpireOrderCommand`를 발행한다.

### 시나리오 2: KYC 서류 제출

24시간 내 미제출이면 reminder, 72시간 초과면 케이스 종료로 이어질 수 있다.  
이건 단순 saga보다 process manager의 시간 상태 관리가 더 중요하다.

### 시나리오 3: 결제 실패 재시도

1일, 3일, 7일 backoff로 재시도하면서 성공 시 나머지 deadline을 모두 폐기한다.  
여기서 stale timer 무시 규칙이 없으면 중복 청구나 잘못된 해지가 발생한다.

---

## 코드로 보기

### deadline 상태를 가진 manager

```java
public class PendingPaymentProcessManager {
    private ProcessStatus status;
    private Instant paymentDeadlineAt;
    private long timerVersion;

    public void on(OrderPlaced event) {
        status = ProcessStatus.PENDING_PAYMENT;
        paymentDeadlineAt = event.occurredAt().plus(Duration.ofMinutes(30));
        timerVersion++;
        commandBus.dispatch(new ScheduleDeadlineCommand(
            event.orderId(),
            paymentDeadlineAt,
            timerVersion
        ));
    }

    public void on(PaymentReceived event) {
        status = ProcessStatus.COMPLETED;
        timerVersion++;
    }

    public void on(PaymentDeadlineReached event) {
        if (status != ProcessStatus.PENDING_PAYMENT) {
            return;
        }
        if (event.timerVersion() != timerVersion) {
            return;
        }
        commandBus.dispatch(new ExpireOrderCommand(event.orderId()));
        status = ProcessStatus.EXPIRED;
    }
}
```

### reminder cadence 정책

```java
public class ReminderPolicy {
    public List<Duration> reminderSchedule() {
        return List.of(Duration.ofHours(24), Duration.ofHours(72));
    }
}
```

### 경계 원칙

```java
// Scheduler는 wake-up을 담당하고,
// Process Manager는 deadline signal을 도메인 상태와 함께 해석한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 scheduler + callback | 구현이 빠르다 | 상태/중복/만료 규칙이 흩어진다 | 짧은 내부 타이머 하나 정도 |
| Process Manager + deadline state | 장기 프로세스 정책이 선명하다 | 상태 저장과 운영 설계가 필요하다 | reminder, timeout, SLA가 중요한 흐름 |
| Coordinator에 타이머까지 몰기 | 한곳에서 보인다 | orchestration과 시간 정책이 비대해진다 | 작은 흐름 외에는 금방 부담이 커진다 |

판단 기준은 다음과 같다.

- 시간이 도메인 결정의 입력이면 process manager를 검토한다
- stale timer와 idempotency를 함께 설계한다
- 기다림의 정책은 장기 프로세스를 소유한 context가 가진다

---

## 꼬리질문

> Q: deadline 처리는 그냥 스케줄러 작업 하나면 되지 않나요?
> 의도: 깨우기와 의사결정의 차이를 보는 질문이다.
> 핵심: 스케줄러는 신호를 보내고, 어떤 상태 전이를 할지는 process manager가 판단해야 한다.

> Q: 타이머가 늦게 오면 어떻게 하나요?
> 의도: 장기 프로세스의 stale signal 문제를 아는지 본다.
> 핵심: 상태와 timer version/token을 함께 비교해 늦은 신호를 무시해야 한다.

> Q: 결제 deadline은 주문 서비스가 가져야 하나요, 결제 서비스가 가져야 하나요?
> 의도: cross-boundary orchestration의 정책 소유권을 보는 질문이다.
> 핵심: 보통 장기 프로세스와 만료 정책을 소유한 context가 갖는 편이 안전하다.

## 한 줄 정리

Process Manager는 deadline과 timeout을 단순 배치가 아니라 도메인 입력으로 다루며, 장기 프로세스의 시간 정책과 상태 전이를 함께 관리한다.
