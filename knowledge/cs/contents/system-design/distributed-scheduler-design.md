# 분산 스케줄러 설계

> 한 줄 요약: 분산 스케줄러는 시간을 기준으로 job을 배치하고, 중복 실행과 장애 전파를 막으면서 정해진 시점에 작업을 실행하는 시스템이다.

retrieval-anchor-keywords: distributed scheduler, cron job, lease, leader election, delayed job, trigger, misfire, worker heartbeat, schedule drift, timezone, exactly once execution, at-least-once execution, idempotent job, dedup run key, cutover orchestration, migration workflow

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Distributed Lock 설계](./distributed-lock-design.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)

## 핵심 개념

분산 스케줄러는 단순히 `cron`을 여러 서버에서 돌리는 것이 아니다.  
실전에서는 다음을 함께 해결해야 한다.

- 하나의 job이 한 번만 실행되도록 보장
- worker 장애 시 재할당
- 시간대와 DST 처리
- 지연 실행과 반복 실행
- backlog와 misfire 처리
- 스케줄 정의와 실제 실행 분리

즉, 스케줄러는 "언제 실행할지"와 "누가 실행할지"를 분리해서 관리하는 제어 평면이다.

## 깊이 들어가기

### 1. 어떤 스케줄을 지원할 것인가

먼저 요구사항을 나눈다.

- cron-like 반복 작업
- 특정 시각 1회 실행
- 지연 실행 delayed job
- 대량 배치 window
- per-tenant schedule

이걸 한 모델로 우기면 스케줄 정의가 실행 상태와 섞여서 운영이 어려워진다.

### 2. Capacity Estimation

예를 들어:

- tenant 10만 개
- tenant당 평균 스케줄 20개
- 전체 스케줄 수 200만 개
- 매 분 1%가 만료/실행 대상

그럼 매 분 2만 개의 due scan 또는 trigger가 발생할 수 있다.  
이때 핵심은 전체 스케줄 수보다 `due job`을 얼마나 빠르게 찾고 분배하는가다.

보는 숫자:

- due scan QPS
- lease renewal QPS
- heartbeat QPS
- misfire rate
- backlog depth

### 3. 일반적인 아키텍처

```text
Scheduler API
  -> Schedule Store
  -> Trigger Index
  -> Dispatcher
  -> Job Queue
  -> Worker Pool
```

흐름은 보통 이렇다.

1. 사용자가 schedule을 등록한다.
2. scheduler가 next run을 계산한다.
3. due trigger가 되면 dispatcher가 job을 queue에 넣는다.
4. worker가 job을 실행하고 상태를 ack한다.

### 4. leader election과 lease

모든 노드가 같은 job을 동시에 집어가면 중복 실행이 생긴다.  
그래서 두 가지가 필요하다.

- leader election: 누가 trigger scan을 책임지는가
- lease: 이 job을 누가 잠시 점유하는가

완전한 중앙집중형은 단순하지만 SPOF가 된다.  
완전한 분산형은 합의 비용이 올라간다.  
실무에서는 scan은 분산하고, execution ownership은 lease로 제어하는 식이 많다.

### 5. 시간 문제

스케줄러는 시간에 민감하다.

- clock skew
- timezone
- daylight saving time
- leap second
- scheduler drift

권장 원칙:

1. 저장은 UTC로 한다.
2. 사용자 입력만 로컬 시간대로 해석한다.
3. next run 계산 결과를 명시적으로 저장한다.
4. DST ambiguity는 UI에서 드러낸다.

### 6. misfire와 backlog

스케줄된 시점에 실행되지 못하는 경우가 있다.

원인:

- worker 부족
- 장애
- 네트워크 분리
- queue backlog

대응:

- misfire policy를 정의한다
- skip / catch-up / coalesce 중 하나를 고른다
- 오래된 job은 batch로 묶거나 버린다

이건 [Job Queue 설계](./job-queue-design.md)와 함께 봐야 한다.

### 7. 실행 보장과 idempotency

스케줄러는 at-least-once 쪽으로 설계되는 경우가 많다.  
즉, job handler는 idempotent해야 한다.

- 같은 run key면 중복 실행을 막는다
- 완료 상태를 durable하게 저장한다
- side effect는 외부 key로 dedup한다

run key를 어떤 저장소에 얼마나 오래 보관할지, 그리고 retry를 replay-safe하게 만들지는 [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)와 같이 보면 더 선명해진다.

예를 들어 알림, 정산, 리포트 배치는 중복 실행이 곧 장애로 이어질 수 있다.

## 실전 시나리오

### 시나리오 1: 매일 자정 리포트

문제:

- tenant마다 자정 리포트를 생성해야 한다
- 한꺼번에 몰리면 DB가 흔들린다

해결:

- tenant별 jitter를 둔다
- 큐에 분산시킨다
- 오래 걸리는 작업은 batch worker로 분리한다

### 시나리오 2: 예약 만료 처리

문제:

- 예약이 특정 시각에 자동 해제돼야 한다
- 만료 시간이 비슷한 예약이 많다

해결:

- delayed queue 또는 wheel timer를 쓴다
- 만료 task는 idempotent하게 만든다

### 시나리오 3: 전역 배치와 리전 장애

문제:

- 한 리전이 다운되면 스케줄이 누락된다

해결:

- 리전별 스케줄 ownership을 나눈다
- failover 시 overlap 실행을 방지한다
- multi-region에서는 lease fencing token을 쓴다

## 코드로 보기

```pseudo
function tick(now):
  dueSchedules = triggerIndex.findDue(now)
  for schedule in dueSchedules:
    if lease.acquire(schedule.id, ttl=30s):
      queue.publish(buildJob(schedule))

function execute(job):
  if dedup.exists(job.runKey):
    return
  process(job)
  dedup.save(job.runKey)
```

```java
public Instant nextRun(CronExpression cron, ZoneId zone, Instant now) {
    return cron.next(now.atZone(zone)).toInstant();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 중앙 cron 서버 | 단순하다 | 장애 지점이 된다 | 작은 시스템 |
| 분산 trigger scan | 확장성이 좋다 | lease 관리가 필요하다 | 대규모 플랫폼 |
| delayed queue 기반 | 실행 모델이 단순하다 | 긴 스케줄에 부담 | 단기 지연 작업 |
| DB polling | 구현이 쉽다 | scan 비용이 크다 | 초기 MVP |
| lease + queue | 실무 친화적이다 | 복잡도가 중간이다 | 대부분의 서비스 |

핵심은 "정해진 시간에 실행"보다 **중복 없이, 누락을 최소화하며, 장애 시에도 재개 가능한가**다.

## 꼬리질문

> Q: cron은 왜 분산에서 어려워지나요?
> 의도: 단일 서버 가정이 깨질 때의 문제 이해 확인
> 핵심: 중복 실행, 리더 선출, lease, drift 문제가 같이 생긴다.

> Q: misfire는 어떻게 처리하나요?
> 의도: backlog와 운영 정책 이해 확인
> 핵심: skip, catch-up, coalesce 중 업무 의미에 맞는 정책을 정해야 한다.

> Q: 스케줄 시간을 UTC로 저장하는 이유는 무엇인가요?
> 의도: timezone/DST 이해 확인
> 핵심: 저장은 일관되게 UTC, 표시와 입력만 지역 시간으로 처리한다.

> Q: 스케줄러와 job queue는 어떻게 다르나요?
> 의도: 제어 평면과 실행 평면 구분 확인
> 핵심: 스케줄러는 시점을 관리하고, 큐는 실행 버퍼와 전달을 담당한다.

## 한 줄 정리

분산 스케줄러는 시간 기반 트리거를 안정적으로 배치하기 위해 lease, misfire policy, idempotency, failover를 함께 설계하는 시스템이다.
