# `CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards

> 한 줄 요약: `CompletableFuture.delayedExecutor()`는 "잠깐 기다렸다가 같은 흐름을 이어가는 API"가 아니라, 숨겨진 timer scheduler가 나중에 base executor로 작업 제출을 시도하는 2단계 orchestration 도구다. 이 경계를 놓치면 retry/backoff, timeout, context propagation, rejection, timer-thread hijack을 잘못 설계하게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [`CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards](./completablefuture-allof-join-timeout-exception-handling-hazards.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: CompletableFuture delayedExecutor, scheduler hop, timer thread, CompletableFutureDelayScheduler, Delayer, delayed task submission, delay starts on execute, retry backoff scheduler, timeout scheduling, orTimeout completeOnTimeout, CallerRunsPolicy timer hijack, direct executor hazard, rejected delayed submission, context propagation, timer backlog, orchestration semantics

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`delayedExecutor()`의 본질은 sleep이 아니라 **지연된 제출 경계**다.

핵심 축은 세 개다.

- delay를 세는 timer scheduler
- delay 만료 뒤 `execute()`를 호출당하는 base executor
- 그 이후 실제로 stage를 수행하는 worker thread

즉 "200ms 뒤 실행"이라는 말만으로는 부족하다.  
정확히는 **200ms 뒤 어떤 thread가 누구에게 일을 넘기는가**를 읽어야 한다.

현행 OpenJDK 구현은 delay와 timeout 지원을 위해 daemon thread 하나를 유지한다.  
이 thread는 이름이 `CompletableFutureDelayScheduler`이며, 원칙적으로는 user task를 직접 돌리기보다 "지금 제출할 때가 됐다"는 trigger 역할을 한다.

문제는 base executor의 성격에 따라 이 timer thread가 실제 user code까지 떠안을 수 있다는 점이다.

## 깊이 들어가기

### 1. delay는 executor 생성 시점이 아니라 `execute()` 호출 시점부터 시작된다

Javadoc이 말하는 핵심은 이것이다.

- `CompletableFuture.delayedExecutor(delay, unit, executor)`는 base executor 자체를 바꾸지 않는다
- 반환된 executor의 `execute()`가 호출될 때마다 새로운 countdown이 시작된다
- delay가 끝나면 그때 base executor에 task 제출을 시도한다

즉 delayed executor를 한 번 만들어 두고 여러 번 써도 "공유된 한 개 타이머"처럼 움직이지 않는다.  
각 제출이 독립된 지연을 가진다.

또한 delay가 0 이하이면 사실상 즉시 제출과 비슷한 의미가 된다.  
그래도 "누가 실행하는가"는 여전히 base executor 정책에 달려 있다.

### 2. scheduler hop과 worker hop은 같은 hop이 아니다

`delayedExecutor()`를 쓰면 보통 hop이 하나 더 생긴다.

1. 호출 스레드가 delayed executor에 task를 넘긴다
2. timer scheduler가 delay 만료를 감지한다
3. scheduler가 base executor의 `execute()`를 호출한다
4. base executor의 worker가 실제 user action을 수행한다

여기서 중요한 점은 **delay를 관리하는 thread와 실제 일을 하는 thread가 분리될 수 있다**는 것이다.

그래서 다음 질문을 따로 봐야 한다.

- traceId는 어느 경계에서 끊기는가
- backpressure는 base executor가 받는가, scheduler가 받는가
- thread dump에 보이는 thread는 "실행 중"인가 "제출 중"인가

기본 overload인 `delayedExecutor(delay, unit)`는 explicit base executor를 받지 않으므로, delay 뒤 작업은 default async executor 쪽으로 다시 제출된다.  
즉 pool 격리나 context strategy가 중요하다면 overload를 짧게 쓰기보다 base executor를 명시하는 편이 안전하다.

### 3. timer thread hazard는 "timer가 일을 한다"가 아니라 "fallback 실행 주체가 바뀐다"는 뜻이다

정상적인 thread pool을 base executor로 주면 scheduler thread는 보통 `executor.execute(...)`만 호출하고 빠진다.  
하지만 다음 경우는 다르다.

- base executor가 `Runnable::run` 같은 same-thread executor다
- base executor가 synchronous executor다
- `ThreadPoolExecutor.CallerRunsPolicy`처럼 호출자 thread가 fallback 실행을 맡는다

이 경우 delay 만료 시점의 호출자는 timer scheduler thread다.  
즉 `CompletableFutureDelayScheduler`가 user code를 직접 실행할 수 있다.

이 현상은 두 가지 의미를 가진다.

- timer lane 하나가 무거운 작업에 붙잡혀 다른 delayed action까지 밀릴 수 있다
- thread dump에서 timer thread가 애플리케이션 로직을 돌고 있어도 "JDK 버그"가 아니라 executor 정책 문제일 수 있다

`CallerRunsPolicy`는 일반 executor 문서에서는 자연스러운 backpressure처럼 보이지만, delayed submission과 섞이면 backpressure를 caller가 아니라 **timer thread**가 떠안게 된다는 점이 다르다.

### 4. rejection은 "지금 실패"가 아니라 "나중에 제출 실패"로 나타난다

`supplyAsync(..., delayedExecutor(...))`를 호출하는 순간에는 future가 이미 반환된다.  
그런데 실제 base executor 제출은 delay 뒤에 일어난다.

그래서 포인트가 어긋난다.

- 호출 시점에는 정상처럼 보인다
- delay 만료 시점에 base executor가 saturation/rejection 상태일 수 있다
- 이 실패는 timer scheduler 위에서 뒤늦게 터진다

실무에서 특히 위험한 경우는 `AbortPolicy` 같은 rejection이 delayed submit 시점에 발생하는 경우다.  
이때 surrounding future가 즉시 잘 실패하지 않고, 의도와 다르게 오래 미완료 상태로 남을 수 있다.

즉 delayed executor는 "미래 시점 제출"이므로, rejection semantics도 미래로 밀린다.  
운영 감각으로는 queue saturation을 지금 보는 것이 아니라 **delay가 끝나는 순간의 수용 능력**을 봐야 한다.

### 5. `orTimeout()`과 `completeOnTimeout()`도 같은 timer lane을 공유한다

현행 OpenJDK 구현에서 `delayedExecutor()`, `orTimeout()`, `completeOnTimeout()`은 같은 Delayer 계열 메커니즘을 사용한다.

즉 내부적으로는 다음이 한 묶음이다.

- delayed retry/backoff submission
- timeout exceptional completion
- timeout fallback completion
- 완료된 future에 대한 예약 취소

이건 public API contract라기보다 구현 디테일이지만, 운영적으로는 중요하다.

- timeout이 많아도
- retry가 많아도
- 둘 다 결국 같은 hidden timer lane을 압박할 수 있다

그래서 대량의 deadline/retry orchestration을 설계할 때는 `delayedExecutor()`를 편의 API로만 볼 게 아니라, **전역 단일 timer lane을 쓰는 기본 도구**로 생각해야 한다.  
타이머 개수, 지연 정확도, 전용 metrics가 중요하면 별도 `ScheduledExecutorService`가 더 낫다.

### 6. orchestration semantics는 세 레이어로 분리해야 한다

`CompletableFuture` 체인에서 자주 섞이는 것은 다음 세 가지다.

| 관심사 | 보통 쓰는 도구 | 의미 |
|---|---|---|
| 개별 시도 deadline | `attempt.orTimeout(...)` | 한 번의 remote call을 언제 포기할지 |
| 다음 시도까지의 backoff | `delayedExecutor(...)` | 새 작업을 언제 다시 제출할지 |
| 전체 요청 deadline | outer future의 `orTimeout(...)` | orchestration 전체를 언제 종료할지 |

여기에 cancellation/cleanup은 별도 축이다.

- timeout이 났다고 내부 작업이 자동으로 멈추는가
- retry 예약이 이미 걸려 있다면 취소되는가
- 이미 성공했는데 늦게 도착한 retry가 또 실행되는가

즉 timeout, retry, cancellation을 하나의 "delay 문제"로 뭉개면 안 된다.  
각각은 completion policy, submission policy, lifetime policy다.

### 7. scheduler hop은 context hop이기도 하다

delay 이후 재개는 시간 경과가 아니라 **실행 문맥 전환**이다.

- MDC
- `ThreadLocal`
- security context
- tracing/span context

같은 ambient state는 자동으로 이어지지 않을 수 있다.

특히 retry/backoff 체인에서는 "기존 요청 context"를 그대로 붙이는 것이 항상 맞지도 않다.

- 이미 취소된 요청인데 stale context를 다시 가져오는 경우
- 요청별 timeout이 끝났는데 trace만 남아 새 시도를 여는 경우
- transaction/request scoped state가 이미 수명을 다한 경우

즉 context propagation은 단순 capture/restore가 아니라 **어떤 boundary까지 전파할지**를 정하는 문제다.

## 실전 시나리오

### 시나리오 1: retry backoff 이후 traceId가 사라진다

delay 뒤에는 scheduler hop과 worker hop이 추가된다.  
단순 sleep처럼 생각하고 MDC 복원을 안 했기 때문에 log correlation이 끊긴다.

### 시나리오 2: thread dump에 `CompletableFutureDelayScheduler`가 business logic를 돈다

base executor가 same-thread executor이거나, saturation 시 `CallerRunsPolicy`가 발동했을 가능성이 높다.  
timer thread가 hijack된 상태라 다른 delayed action도 밀릴 수 있다.

### 시나리오 3: delayed retry가 가끔 영원히 안 끝난다

retry 시점을 예약한 것은 성공했지만, delay 만료 시 base executor가 reject했다.  
제출 실패가 surrounding future completion으로 연결되지 않으면 미완료 future처럼 보일 수 있다.

### 시나리오 4: timeout과 retry를 같이 늘렸더니 지연 특성이 같이 흔들린다

`orTimeout()`과 delayed retry가 같은 hidden timer lane을 쓰면, 대량 burst에서 둘 다 같은 scheduler pressure를 받는다.

## 코드로 보기

### 1. 같은 delayed executor를 재사용해도 delay는 호출마다 새로 시작된다

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

Executor delayedIo = CompletableFuture.delayedExecutor(
    200,
    TimeUnit.MILLISECONDS,
    ioExecutor
);

delayedIo.execute(() -> log.info("first"));
delayedIo.execute(() -> log.info("second"));
```

두 task는 "공유된 한 번의 200ms"를 기다리는 것이 아니라, 각 `execute()` 호출 시점부터 따로 200ms를 센다.

### 2. same-thread executor는 timer thread hijack을 만든다

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

Executor sameThread = Runnable::run;
Executor delayed = CompletableFuture.delayedExecutor(
    100,
    TimeUnit.MILLISECONDS,
    sameThread
);

CompletableFuture.runAsync(
    () -> System.out.println(Thread.currentThread().getName()),
    delayed
).join();
```

이런 코드는 현행 OpenJDK에서 `CompletableFutureDelayScheduler` 같은 timer thread 이름이 출력될 수 있다.  
delay scheduler가 base executor 호출자이기 때문이다.

### 3. per-attempt timeout과 retry backoff는 다른 레이어로 둔다

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;

class Client {
    private final Executor ioExecutor;
    private final Executor retryExecutor;

    Client(Executor ioExecutor, Executor retryExecutor) {
        this.ioExecutor = ioExecutor;
        this.retryExecutor = retryExecutor;
    }

    CompletableFuture<String> callWithRetry(int retriesLeft) {
        CompletableFuture<String> attempt = CompletableFuture
            .supplyAsync(this::callRemote, ioExecutor)
            .orTimeout(300, TimeUnit.MILLISECONDS);

        return attempt.handle((value, error) -> {
            if (error == null) {
                return CompletableFuture.completedFuture(value);
            }
            if (retriesLeft == 0 || !isRetryable(error)) {
                return CompletableFuture.<String>failedFuture(error);
            }

            Executor backoff = CompletableFuture.delayedExecutor(
                200,
                TimeUnit.MILLISECONDS,
                retryExecutor
            );

            return CompletableFuture
                .runAsync(() -> { }, backoff)
                .thenCompose(ignored -> callWithRetry(retriesLeft - 1));
        }).thenCompose(Function.identity());
    }

    private String callRemote() {
        return "ok";
    }

    private boolean isRetryable(Throwable error) {
        return true;
    }
}
```

여기서 attempt timeout은 "한 번의 호출"에만 적용된다.  
전체 orchestration deadline이 필요하면 `callWithRetry(...).orTimeout(...)`을 바깥에 한 번 더 둬야 한다.

### 4. delayed submit 시점의 rejection은 별도 hazard다

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

ThreadPoolExecutor saturated = new ThreadPoolExecutor(
    1,
    1,
    0L,
    TimeUnit.MILLISECONDS,
    new SynchronousQueue<>(),
    new ThreadPoolExecutor.AbortPolicy()
);

Executor delayed = CompletableFuture.delayedExecutor(
    100,
    TimeUnit.MILLISECONDS,
    saturated
);

CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> "ok", delayed);
```

이 코드는 `supplyAsync(...)` 호출 시점엔 future를 돌려주지만,  
실제 rejection은 100ms 뒤 delayed submit 시점에 일어난다.  
즉 failure timing과 orchestration timing이 어긋난다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `delayedExecutor(delay, unit, executor)` | retry/backoff를 간결하게 표현하고 worker pool을 명시적으로 분리할 수 있다 | hidden timer lane은 여전히 공유되고, rejection/context 정책을 직접 챙겨야 한다 |
| `delayedExecutor(delay, unit)` | 가장 짧게 쓸 수 있다 | delay 뒤 default async executor로 돌아가므로 pool 격리와 context 의도가 흐려질 수 있다 |
| `orTimeout()` / `completeOnTimeout()` | completion deadline을 짧게 표현한다 | 다음 시도 scheduling이나 실제 computation 중단을 대신해 주지는 않는다 |
| 별도 `ScheduledExecutorService` | timer pool, metrics, cancellation, failure translation을 더 명시적으로 다룰 수 있다 | 코드와 운영 구성이 더 늘어난다 |

핵심은 `delayedExecutor()`를 "편한 sleep 대체재"가 아니라 **scheduler와 worker를 잇는 orchestration boundary**로 읽는 것이다.

## 꼬리질문

> Q: `delayedExecutor()`는 delay 후 같은 thread에서 이어서 실행되나요?
> 핵심: 보통은 아니다. delay scheduler가 base executor에 제출하고, 실제 user code는 그 다음 executor 정책에 따라 돈다.

> Q: 왜 `CompletableFutureDelayScheduler`가 business code를 실행하죠?
> 핵심: base executor가 same-thread executor이거나 `CallerRunsPolicy`처럼 호출자 thread가 fallback 실행을 맡았기 때문이다.

> Q: `orTimeout()`과 retry backoff를 같은 문제로 보면 왜 안 되나요?
> 핵심: 전자는 completion deadline, 후자는 다음 제출 시점이며, 내부 computation lifetime과 cancellation은 또 별도 축이기 때문이다.

> Q: delayed retry에서 executor saturation이 왜 더 위험하죠?
> 핵심: rejection이 delay 뒤 submit 시점에 터지므로, failure timing이 늦어지고 surrounding future가 의도대로 완료되지 않을 수 있다.

## 한 줄 정리

`CompletableFuture.delayedExecutor()`의 핵심은 sleep이 아니라 "나중에 누구에게 제출할지"를 정하는 orchestration 경계이므로, timer scheduler, base executor, timeout, retry, rejection, context propagation을 분리해서 설계해야 한다.
