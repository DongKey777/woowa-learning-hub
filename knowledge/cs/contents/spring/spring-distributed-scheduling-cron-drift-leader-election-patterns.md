---
schema_version: 3
title: Spring Distributed Scheduling, Cron Drift, and Leader-Election Patterns
concept_id: spring/distributed-scheduling-cron-drift-leader-election-patterns
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 82
review_feedback_tags:
- distributed-scheduling-cron
- drift-leader-election
- distributed-scheduling
- cron-drift
aliases:
- distributed scheduling
- cron drift
- leader election
- scheduler duplicate execution
- fixedRate overlap
- distributed lock scheduler
- missed tick
- schedule lag
- fencing token
intents:
- design
- troubleshooting
symptoms:
- 멀티 인스턴스에서 @Scheduled job이 중복 실행된다.
- GC pause, scheduler pool saturation, clock skew 때문에 cron tick이 밀리거나 겹친다.
- 장애 후 missed window를 skip, catch-up, coalesce 중 어떻게 처리할지 불명확하다.
linked_paths:
- contents/spring/spring-scheduler-async-boundaries.md
- contents/spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md
- contents/spring/spring-startup-runner-smartlifecycle-readiness-warmup.md
- contents/spring/spring-delivery-reliability-retryable-resilience4j-outbox-relay.md
- contents/spring/spring-batch-chunk-retry-skip.md
- contents/system-design/distributed-scheduler-design.md
- contents/system-design/distributed-lock-design.md
expected_queries:
- Spring @Scheduled를 멀티 인스턴스에서 돌리면 왜 중복 실행돼?
- distributed scheduler에서 leader election과 distributed lock은 어떻게 달라?
- cron drift와 schedule lag를 어떻게 관측해야 해?
- missed tick은 skip catch-up coalesce 중 어떻게 정책을 정해?
contextual_chunk_prefix: |
  이 문서는 Spring @Scheduled가 로컬 JVM scheduler라는 전제에서 출발해
  multi-instance duplicate execution, cron drift, leader election, lease,
  distributed lock, checkpoint/watermark, catch-up/coalesce/misfire policy,
  fencing token을 설계하는 advanced playbook이다.
---
# Spring Distributed Scheduling, Cron Drift, and Leader-Election Patterns

> 한 줄 요약: `@Scheduled`는 기본적으로 로컬 JVM 스케줄러이므로 멀티 인스턴스 환경에서는 duplicate execution, cron drift, missed window를 먼저 가정해야 하고, leader election, lease, checkpoint, catch-up policy를 함께 설계해야 장애 후에도 설명 가능한 스케줄링이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
> - [Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup](./spring-startup-runner-smartlifecycle-readiness-warmup.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)
> - [Spring Batch Chunk / Retry / Skip](./spring-batch-chunk-retry-skip.md)
> - [분산 스케줄러 설계](../system-design/distributed-scheduler-design.md)
> - [Distributed Lock 설계](../system-design/distributed-lock-design.md)

retrieval-anchor-keywords: distributed scheduling, cron drift, leader election, scheduler duplicate execution, fixedRate overlap, distributed lock scheduler, lease-based leader, missed tick, schedule lag, misfire policy, checkpoint, watermark, catch-up semantics, coalescing, fencing token, multi-instance scheduled job

## 핵심 개념

Spring의 `@Scheduled`는 각 JVM 안에서 개별적으로 돈다.

멀티 인스턴스에서 중요한 것은 단순히 "tick을 만든다"가 아니라 아래 네 가지를 분리해 보는 것이다.

- 어떤 시각이 실행 대상인가 (`scheduledAt`)
- 지금 누가 그 시각의 작업 소유자인가 (`leader` / `lease`)
- 어디까지 완료했는가 (`checkpoint` / `watermark`)
- 늦어진 tick을 어떻게 처리할 것인가 (`skip`, `catch-up`, `coalesce`)

즉 분산 환경의 스케줄링은 "주기를 맞춘다"보다, **중복 실행, 지연, 누락, 승계, backlog를 어떤 방식으로 허용할지 정하는 것**이 핵심이다.

## 깊이 들어가기

### 1. 로컬 scheduler와 분산 scheduler는 전제가 다르다

단일 인스턴스에선 `@Scheduled`만으로 충분할 수 있다.

하지만 멀티 인스턴스에선 각 인스턴스가 독립적으로 같은 cron을 계산한다.

- 각 인스턴스가 같은 작업을 모두 돌릴 수 있다
- clock skew, GC pause, CPU saturation으로 실행 시각이 흔들릴 수 있다
- 작업 시간이 길면 다음 tick과 겹치거나 밀릴 수 있다
- 장애 후 재기동 시 missed window를 어떻게 다룰지 애플리케이션이 스스로 결정해야 한다

즉 `@Scheduled` 자체보다, **로컬 주기 실행 도구를 분산 coordination 없이 운영 환경에 올리는 것**이 문제다.

### 2. cron drift는 `scheduledAt`과 `startedAt`을 분리해 보게 만든다

cron 표현식은 "이상적으로 언제 돌고 싶었는가"만 표현한다.

실전에서는 최소한 아래 시각을 따로 보는 편이 낫다.

- `scheduledAt`: 원래 돌아야 했던 시각
- `claimedAt`: leader나 lock이 실행권을 잡은 시각
- `startedAt`: 실제 작업 본문이 시작된 시각
- `completedAt`: side effect가 끝난 시각

drift가 커지는 흔한 원인은 이렇다.

- scheduler thread가 바빴다
- JVM pause가 있었다
- host clock가 튀었다
- 이전 작업이 길었다
- scheduler pool이 다른 background task와 섞여 있었다

그래서 분산 scheduling에선 cron 표현보다 **schedule lag(`startedAt - scheduledAt`)와 overlap 여부**가 더 중요한 지표가 된다.

### 3. 분산 락과 leader election은 비슷해 보여도 ownership 모델이 다르다

대표 감각은 이렇다.

- 분산 락/lease: 각 tick마다 "이번 실행권"을 경쟁해서 잡는다
- leader election: 한 인스턴스가 일정 기간 스케줄 family의 소유권을 가진다

둘 다 "한 번만 돌게 하자"처럼 보이지만 의미가 다르다.

- per-run lock은 개별 작업에는 단순하지만 소유권이 매번 흔들린다
- leader election은 여러 작업을 묶기 쉽지만 failover gap을 설계해야 한다
- hybrid 패턴은 leader가 due window를 스캔하고, 실제 실행은 queue/worker로 넘긴다

즉 coordination 기법은 구현 취향이 아니라, **소유권 모델을 어떻게 표현할지**의 문제다.

### 4. leader handoff는 lease TTL만이 아니라 heartbeat와 fencing token까지 봐야 한다

leader election 패턴은 보통 이렇게 이해하면 된다.

- 현재 leader만 due window를 스캔한다
- leader는 lease를 주기적으로 renew한다
- leader가 죽거나 renew를 놓치면 다른 인스턴스가 승계한다

이때 trade-off가 바로 생긴다.

- lease가 너무 짧으면 GC pause나 일시 네트워크 지연에도 false failover가 난다
- lease가 너무 길면 recovery가 늦어진다
- warmup이 덜 된 노드가 곧바로 leader가 되면 restart 직후 부하가 몰릴 수 있다

특히 오래된 leader가 뒤늦게 깨어나 쓰기를 이어가는 stale owner 문제가 있다.

그래서 중요한 작업은 [Distributed Lock 설계](../system-design/distributed-lock-design.md)에서 말하는 것처럼:

- compare-and-delete 해제
- monotonic leader epoch 또는 fencing token
- readiness 이후에만 leader 후보 참여

를 함께 보는 편이 안전하다.

즉 leader election은 단순 중복 방지가 아니라, **장애 후 얼마나 빨리, 얼마나 안전하게 다른 노드가 넘겨받을지 정하는 정책**이다.

### 5. checkpoint가 있어야 "다시 돌기"가 아니라 "이어 돌기"가 된다

분산 스케줄링에서 lock이나 leader는 "누가 지금 한다"만 알려준다.

반면 checkpoint는 "어디까지 끝났는가"를 알려준다.

예를 들면 checkpoint는 이런 모습일 수 있다.

- 마지막으로 성공한 minute window의 end time
- 마지막으로 처리한 주문 ID high-water mark
- tenant별 마지막 집계 cursor

이게 없으면 새 leader는 항상 애매해진다.

- 방금 전 window가 이미 끝났는지
- publish만 하고 아직 worker가 안 끝났는지
- 장애 직전 어느 구간까지 성공했는지

즉 checkpoint는 스케줄링의 부가 메타데이터가 아니라, **failover 후 해석 가능성을 만드는 진짜 상태**다.

checkpoint를 둘 때는 다음 원칙이 중요하다.

- side effect가 durable하게 끝난 뒤에만 checkpoint를 전진시킨다
- checkpoint와 run key를 분리해 "완료 여부"와 "진행 위치"를 둘 다 남긴다
- checkpoint 저장소는 leader 프로세스 메모리가 아니라 DB 같은 durable storage여야 한다

checkpoint를 너무 일찍 올리면 crash 후 조용한 skip이 생기고, 너무 늦게 올리면 replay 양이 커진다.

### 6. catch-up semantics는 기술 옵션이 아니라 misfire 정책이다

서비스가 20분 내려가 있었고 작업 주기가 1분이라고 하자.

재기동 후 "20개 missed tick을 어떻게 처리할까"는 구현 디테일이 아니라 업무 계약이다.

| 정책 | 의미 | 장점 | 위험 / 어울리는 경우 |
|---|---|---|---|
| `skip` | 오래된 tick을 버리고 현재 시점부터 시작 | backlog 폭주를 막는다 | 데이터 공백을 허용해야 한다 |
| `catch-up` | 놓친 window를 하나씩 모두 재생 | per-window 정합성이 선명하다 | backlog storm, 장시간 replay가 생긴다 |
| `coalesce` | 놓친 여러 window를 한 번의 넓은 범위 처리로 합친다 | 회복이 빠르다 | 각 window 단위 SLA나 알림 의미가 흐려진다 |
| `bounded catch-up` | 최대 N개까지만 replay하고 그 이상은 coalesce/alert | 부하와 정합성 균형을 잡기 쉽다 | 정책이 복잡해진다 |

핵심은 catch-up 정책을 checkpoint와 같이 정의하는 것이다.

- `checkpoint -> now` 범위를 window로 잘라 replay할지
- backlog가 너무 크면 coalesce할지
- 일정 임계치를 넘기면 운영자에게 alert만 올리고 수동 개입할지

이걸 정하지 않으면 장애 후 복구가 "왜 20번 돌았지?" 혹은 "왜 20분이 비었지?"로 보이게 된다.

### 7. cron / fixedRate / fixedDelay 선택도 catch-up 모양을 바꾼다

- cron: calendar window가 선명해서 checkpoint와 catch-up을 붙이기 쉽다
- fixedRate: 이상적인 시작 간격을 유지하려 해 backlog나 overlap 압력이 커진다
- fixedDelay: 이전 실행 종료 후 delay를 쉬므로 "missed tick replay" 개념이 약하고, backlog보단 자연스러운 throttle에 가깝다

예를 들어:

- "매 분 집계"처럼 window 의미가 중요하면 cron + checkpoint가 읽기 쉽다
- "이전 run이 끝난 뒤 N초 후 다시 polling"이면 fixedDelay가 더 자연스럽다
- fixedRate는 부하 실험이나 heartbeat처럼 간격 그 자체가 중요할 때만 신중히 쓴다

즉 trigger 타입은 문법 취향이 아니라, **drift와 catch-up을 어떤 형태로 드러낼지 정하는 선택**이다.

### 8. 실무 패턴은 `@Scheduled`를 coordinator tick으로 제한하는 편이 낫다

운영에서 자주 안정적인 패턴은 이렇다.

1. `@Scheduled`는 짧은 주기로 due window를 확인하는 coordinator 역할만 한다
2. leader/lease가 scan ownership을 정한다
3. checkpoint를 기준으로 overdue window를 계산한다
4. 각 window를 idempotent run key로 queue나 worker에 넘긴다
5. worker가 성공 후 run key와 checkpoint를 durable하게 남긴다

이렇게 하면 다음 이점이 있다.

- planning과 execution이 분리돼 drift 원인 해석이 쉬워진다
- leader가 바뀌어도 checkpoint 기준으로 다시 계산할 수 있다
- 긴 작업이 scheduler thread를 오래 붙잡지 않는다

반대로 scheduled 메서드 안에서 모든 일을 다 하면, drift, overlap, failover 해석이 한 메서드에 엉겨 붙는다.

## 실전 시나리오

### 시나리오 1: 배포 후 같은 배치가 두 번 실행된다

인스턴스가 늘었는데 로컬 `@Scheduled`만 쓰고 있을 가능성이 높다.

중복 방지를 락으로 할지, 아예 leader ownership으로 모델링할지부터 정해야 한다.

### 시나리오 2: cron은 정각인데 실제 실행은 계속 몇 초씩 밀린다

drift 자체는 자연스러울 수 있다.

중요한 건 drift를 허용할지, scheduler pool 포화인지, 작업 시간이 길어지는지 구분해 보는 것이다.

즉 cron 식보다 schedule lag 메트릭이 더 먼저다.

### 시나리오 3: leader가 죽은 뒤 한동안 작업이 비어 있다

leader election/lease 설계상 failover gap일 수 있다.

버그라기보다 lease TTL, heartbeat 간격, readiness gating 선택 결과일 수 있다.

### 시나리오 4: 서비스가 40분 내려갔다가 올라온 뒤 작업이 40번 연속 돈다

업무가 catch-up을 허용한다면 정상일 수 있다.

하지만 backlog storm이 문제라면 bounded catch-up이나 coalesce 정책이 필요하다.

### 시나리오 5: 장애 후 일부 window가 영영 비어 있다

checkpoint를 실제 완료보다 먼저 올렸을 가능성을 의심해야 한다.

이 경우 중복보다 더 위험한 것은 "조용한 누락"이다.

## 코드로 보기

### 로컬 스케줄 작업

```java
@Scheduled(cron = "0 * * * * *")
public void minuteJob() {
    settlementService.runCurrentMinute();
}
```

멀티 인스턴스에선 이 코드만으로는 "지금 누가 실행권을 갖는가"와 "어디까지 완료했는가"가 비어 있다.

### coordinator tick + leader lease + checkpoint

```java
@Component
@RequiredArgsConstructor
public class SettlementCoordinator {

    private final LeaderLeaseService leaderLeaseService;
    private final JobCheckpointRepository checkpointRepository;
    private final SettlementRunPublisher runPublisher;
    private final Clock clock;

    @Scheduled(fixedDelayString = "PT10S")
    public void coordinate() {
        if (!leaderLeaseService.tryAcquire("settlement-minute")) {
            return;
        }

        Instant now = clock.instant().truncatedTo(ChronoUnit.MINUTES);
        Instant checkpoint = checkpointRepository
                .load("settlement-minute")
                .orElse(now.minus(1, ChronoUnit.MINUTES));

        for (TimeWindow window : TimeWindowPlanner.windows(checkpoint, now, 10)) {
            runPublisher.publish("settlement:" + window.start(), window);
        }
    }
}
```

핵심은 scheduled 메서드가 "이번에 직접 다 처리한다"가 아니라, **지금 처리해야 할 window를 계산하고 실행을 위임한다**는 점이다.

### bounded catch-up planner 감각

```java
public final class TimeWindowPlanner {

    public static List<TimeWindow> windows(
            Instant checkpointExclusive,
            Instant nowInclusive,
            int maxCatchUpWindows
    ) {
        List<TimeWindow> windows = enumerateMinuteWindows(checkpointExclusive, nowInclusive);
        if (windows.size() <= maxCatchUpWindows) {
            return windows;
        }
        return List.of(TimeWindow.coalesced(
                windows.get(0).start(),
                windows.get(windows.size() - 1).end()
        ));
    }
}
```

이 planner가 바로 catch-up 정책을 코드로 표현하는 지점이다.

### run key + checkpoint advance

```java
@Transactional
public void process(TimeWindow window) {
    String runKey = "settlement:" + window.start();
    if (runRepository.exists(runKey)) {
        return;
    }

    settlementService.settle(window);
    runRepository.markDone(runKey);
    checkpointRepository.advance("settlement-minute", window.end());
}
```

중요한 포인트는 checkpoint를 **side effect 성공 이후**에만 올리는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 인스턴스 로컬 `@Scheduled` | 가장 단순하다 | 멀티 인스턴스에서 중복/누락/재기동 공백에 취약하다 | 작은 서비스, 단일 노드 |
| per-run 분산 락 | 개별 작업에 붙이기 쉽다 | ownership이 매 tick 흔들리고 stale owner 방어가 필요하다 | 독립적인 소수 배치 |
| leader election + checkpointed coordinator | 소유권과 failover 해석이 선명하다 | lease, heartbeat, checkpoint 관리가 늘어난다 | 여러 주기 작업, 운영 중요도 높음 |
| 모든 missed window catch-up | 누락된 구간이 남지 않는다 | backlog storm과 recovery 지연이 크다 | 정산, 집계, billing처럼 window 손실이 치명적일 때 |
| coalesce / skip 위주 복구 | 회복이 빠르고 부하를 제어하기 쉽다 | per-window 의미가 흐려질 수 있다 | cache refresh, derived stats, 보조성 작업 |
| 외부 전용 스케줄러 | 운영 제어가 강하고 ownership이 분리된다 | 시스템이 하나 더 늘어난다 | 중요한 배치, 대규모 플랫폼 |

핵심은 분산 scheduling을 "중복 방지"만으로 보지 않고, **ownership, checkpoint, catch-up을 함께 가진 운영 설계**로 보는 것이다.

## 꼬리질문

> Q: 멀티 인스턴스에서 `@Scheduled`만 쓰면 가장 먼저 생기는 문제는 무엇인가?
> 의도: 로컬 scheduler 한계 이해 확인
> 핵심: 동일 작업의 중복 실행 가능성과 missed window 해석 부재다.

> Q: cron drift를 볼 때 가장 먼저 분리해서 봐야 할 시각은 무엇인가?
> 의도: 설정 시각과 실제 실행 분리 확인
> 핵심: `scheduledAt`, `claimedAt`, `startedAt`을 분리해 schedule lag를 봐야 한다.

> Q: leader election과 분산 락의 차이는 무엇인가?
> 의도: coordination 모델 구분 확인
> 핵심: 전자는 일정 기간 ownership 모델, 후자는 각 실행 시점 lock 모델에 더 가깝다.

> Q: checkpoint는 왜 run key와 별개로 필요한가?
> 의도: 완료 여부와 진행 위치 분리 확인
> 핵심: run key는 중복 실행 방지, checkpoint는 어디까지 끝났는지 표현한다.

> Q: 서비스가 내려가서 30개의 tick을 놓쳤다면 무엇을 먼저 정해야 하는가?
> 의도: catch-up semantics 이해 확인
> 핵심: `skip`, `catch-up`, `coalesce`, `bounded catch-up` 중 어떤 업무 계약을 택할지 먼저 정해야 한다.

## 한 줄 정리

분산 환경의 스케줄링은 "언제 돌까"보다 "누가 소유하고, 어디까지 끝났고, 늦어진 tick을 어떻게 복구할까"를 먼저 설계해야 한다.
