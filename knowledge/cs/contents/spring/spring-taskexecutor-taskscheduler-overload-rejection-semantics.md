---
schema_version: 3
title: Spring TaskExecutor TaskScheduler Overload Queue Rejection Semantics
concept_id: spring/taskexecutor-taskscheduler-overload-rejection-semantics
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- taskexecutor-taskscheduler-overload
- rejection-semantics
- taskexecutor-overload
- taskscheduler-rejection-semantics
aliases:
- TaskExecutor overload
- TaskScheduler rejection semantics
- async executor queue
- scheduler drift rejection
- task pool backpressure
- RejectedExecutionHandler Spring
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/spring/spring-scheduler-async-boundaries.md
- contents/spring/spring-async-context-propagation-restclient-http-interface-clients.md
- contents/spring/spring-transactional-async-composition-traps.md
- contents/spring/spring-distributed-scheduling-cron-drift-leader-election-patterns.md
- contents/spring/spring-applicationeventmulticaster-internals.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
symptoms:
- @Async 작업이 밀려 request thread는 빨라 보여도 background backlog가 계속 증가한다.
- scheduler가 cron cadence를 못 맞추고 drift되거나 같은 작업이 겹친다.
- queue가 가득 찼을 때 caller가 backpressure를 맞는지 task가 버려지는지 불명확하다.
expected_queries:
- Spring TaskExecutor queue size와 rejection policy는 어떤 운영 계약이야?
- @Async overload에서 무엇을 버리고 무엇을 기다리게 할지 어떻게 정해?
- TaskScheduler cron drift와 overlap은 thread pool과 queue 때문에 생길 수 있어?
- RejectedExecutionHandler를 Spring async scheduler에서 어떻게 해석해야 해?
contextual_chunk_prefix: |
  이 문서는 Spring TaskExecutor와 TaskScheduler를 단순 실행기가 아니라 overload 때 queue,
  rejection, caller backpressure, drift, overlap, resource isolation을 결정하는 운영 계약으로
  설명한다.
---
# Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics

> 한 줄 요약: Spring의 `TaskExecutor`와 `TaskScheduler`는 단순 실행 도구가 아니라, overload 시 무엇을 버리고 무엇을 밀어두고 누가 backpressure를 대신 맞을지 정하는 운영 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring Distributed Scheduling, Cron Drift, and Leader-Election Patterns](./spring-distributed-scheduling-cron-drift-leader-election-patterns.md)
> - [Spring ApplicationEventMulticaster Internals](./spring-applicationeventmulticaster-internals.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

retrieval-anchor-keywords: TaskExecutor, TaskScheduler, ThreadPoolTaskExecutor, ThreadPoolTaskScheduler, queue capacity, rejection policy, CallerRunsPolicy, fixedRate overlap, fixedDelay, scheduler thread pool, overload semantics

## 핵심 개념

Spring에서 비동기/스케줄링 코드를 붙일 때 가장 흔한 오해는 아래다.

- 스레드 풀만 하나 만들면 된다
- 큐는 넉넉할수록 안전하다
- `@Scheduled`는 알아서 순서대로 잘 돈다
- executor가 바쁘면 그냥 조금 느려질 뿐이다

실제로는 아니다.

`TaskExecutor`와 `TaskScheduler`는 overload 시 서비스가 어떤 식으로 망가질지 결정한다.

- 즉시 거절할지
- 호출자 스레드가 대신 실행할지
- 큐에 쌓이며 지연을 키울지
- 스케줄 작업이 겹칠지

즉 풀 크기와 큐는 성능 튜닝 파라미터가 아니라, **실패 모델과 backpressure 계약**이다.

## 깊이 들어가기

### 1. executor는 throughput보다 failure mode를 먼저 정한다

`ThreadPoolTaskExecutor`를 볼 때 흔히 core/max/queue부터 손댄다.

하지만 운영 의미는 이렇게 읽는 편이 낫다.

- core size: 평소 얼마나 많은 동시 작업을 흡수할지
- max size: 순간 폭주를 얼마나 더 받아줄지
- queue capacity: 작업을 기다리게 할지 즉시 압력을 돌려보낼지
- rejection policy: 더 못 받을 때 누가 대가를 치를지

즉 설정의 핵심은 "몇 개 돌릴까"보다, **포화 시 어떤 방식으로 망가질까**다.

### 2. 큰 queue는 안전해 보이지만 지연을 숨기기도 한다

queue가 크면 일단 reject는 덜 난다.

하지만 대가가 있다.

- 작업이 큐에서 오래 대기한다
- end-to-end latency가 조용히 커진다
- 이미 의미가 없는 작업도 뒤늦게 실행될 수 있다
- 운영자는 에러보다 지연으로만 장애를 보게 된다

즉 reject가 없다고 건강한 것이 아니다.

특히 알림, cache refresh, index update 같은 작업은 "늦게라도 하면 된다"와 "지금 아니면 의미 없다"가 다르다.

### 3. rejection policy는 비즈니스 의미를 바꾼다

대표 감각:

- `AbortPolicy`: 즉시 실패시켜 압력이 보이게 한다
- `CallerRunsPolicy`: 호출자 스레드가 대신 실행해서 상류에 backpressure를 건다
- discard 계열: 일부 작업 유실을 감수한다

예를 들어 API 요청 스레드에서 `@Async` 작업이 포화되어 `CallerRunsPolicy`가 작동하면, "비동기라 빨라야 할" 요청이 오히려 느려질 수 있다.

반대로 `AbortPolicy`는 실패가 빨리 드러나지만, 호출자가 예외/재시도를 설계해야 한다.

즉 rejection policy는 단순 기술 옵션이 아니라, **과부하를 어디에 전가할지 정하는 선택**이다.

### 4. `TaskScheduler`는 실행 지연뿐 아니라 겹침(overlap)도 본다

스케줄러에서 중요한 질문은 다음이다.

- 이전 실행이 안 끝났는데 다음 tick이 오면 어떻게 되는가
- 단일 scheduler thread인가, pool인가
- `fixedRate`인가 `fixedDelay`인가

감각적으로:

- `fixedRate`: 시작 간격을 맞추려 해 겹침 압력이 생기기 쉽다
- `fixedDelay`: 이전 실행 종료 후 delay를 쉬므로 누적 지연이 생길 수 있다

즉 스케줄 작업은 "주기적으로 돈다"가 아니라, **느려졌을 때 겹칠지 밀릴지**를 설계해야 한다.

### 5. scheduler와 executor를 같은 풀로 섞으면 디버깅이 어려워진다

한 풀에서 다음을 같이 돌리면 운영 해석이 어려워진다.

- API 보조 비동기 작업
- 이벤트 fan-out
- 스케줄 작업
- warmup/background job

이유:

- 큐가 누구 때문에 밀리는지 알기 어렵다
- 우선순위가 없는 상태에서 서로 간섭한다
- scheduler 지연이 async worker 포화 때문인지 분리하기 어렵다

즉 서로 다른 실패 모델을 가진 작업은, 가능하면 **서로 다른 executor/scheduler 경계**를 두는 편이 낫다.

### 6. 관측 포인트가 없으면 "executor는 살아 있는데 시스템이 느리다"만 보인다

최소한 아래는 봐야 한다.

- active thread 수
- queue depth
- task rejection 수
- schedule drift / actual start lag
- task duration p95/p99

그래야 "풀이 작다"와 "작업이 느리다"와 "큐가 너무 크다"를 구분할 수 있다.

## 실전 시나리오

### 시나리오 1: `@Async`는 성공인데 알림이 몇 분 뒤에나 간다

reject가 안 나도 queue가 과도하게 커서 지연이 숨어 있을 수 있다.

### 시나리오 2: 포화 시 `CallerRunsPolicy` 때문에 API p99가 급등한다

비동기 부담이 상류 요청 스레드로 되돌아온 것이다.

이건 의도일 수도 있지만, 모르고 쓰면 "비동기인데 왜 느리지?"라는 착시가 생긴다.

### 시나리오 3: `@Scheduled(fixedRate=...)` 작업이 겹쳐 데이터를 두 번 만진다

작업 시간이 주기보다 길거나 scheduler pool 구성이 겹침을 허용했을 수 있다.

### 시나리오 4: 이벤트 리스너와 배치 작업이 같은 executor를 써서 서로 밀린다

풀 분리가 안 되어 서로의 overload가 전파된 것이다.

## 코드로 보기

### executor 설정

```java
@Bean(name = "notificationExecutor")
public ThreadPoolTaskExecutor notificationExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(8);
    executor.setMaxPoolSize(16);
    executor.setQueueCapacity(200);
    executor.setThreadNamePrefix("notify-");
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    executor.initialize();
    return executor;
}
```

### scheduler 설정

```java
@Bean
public ThreadPoolTaskScheduler relayScheduler() {
    ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
    scheduler.setPoolSize(4);
    scheduler.setThreadNamePrefix("relay-scheduler-");
    scheduler.initialize();
    return scheduler;
}
```

### `fixedDelay` vs `fixedRate`

```java
@Scheduled(fixedDelay = 1000)
public void pollSafely() {
}

@Scheduled(fixedRate = 1000)
public void riskOverlap() {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 작은 queue + 빠른 reject | 압력이 빨리 드러난다 | 실패 처리를 더 많이 설계해야 한다 | latency 민감, 드랍/백프레셔 선호 |
| 큰 queue | 순간 폭주를 흡수한다 | 지연이 조용히 누적된다 | 지연 허용적 백그라운드 작업 |
| `CallerRunsPolicy` | 상류에 backpressure를 전달한다 | 호출자 latency를 악화시킨다 | 비동기보단 처리 보장이 더 중요할 때 |
| executor/scheduler 분리 | 장애 해석이 쉬워진다 | 설정과 운영 포인트가 늘어난다 | 작업 의미가 다를 때 |

핵심은 풀 크기보다, **포화와 지연을 어떤 방식으로 시스템에 드러낼지**를 먼저 정하는 것이다.

## 꼬리질문

> Q: queue를 크게 잡는 것이 왜 항상 안전하지 않은가?
> 의도: 지연 숨김 이해 확인
> 핵심: reject는 줄지만 대기 시간이 커지고 오래된 작업이 뒤늦게 실행될 수 있기 때문이다.

> Q: `CallerRunsPolicy`는 무엇을 하는가?
> 의도: overload 전가 방향 이해 확인
> 핵심: 더 못 받을 때 호출자 스레드가 작업을 실행해 상류에 backpressure를 건다.

> Q: `fixedRate`와 `fixedDelay`의 운영 차이는 무엇인가?
> 의도: scheduler overlap 이해 확인
> 핵심: 전자는 겹침 압력이 크고, 후자는 누적 지연이 커질 수 있다.

> Q: 왜 작업 종류별로 executor를 분리하는 편이 좋은가?
> 의도: 장애 격리와 관측성 이해 확인
> 핵심: 서로 다른 실패 모델과 부하 패턴이 같은 큐/풀에서 섞이지 않게 하기 위해서다.

## 한 줄 정리

Spring의 executor/scheduler 설정은 성능 옵션이 아니라, 과부하와 지연이 어떤 형태로 드러날지 결정하는 운영 계약이다.
