# CompletableFuture Cancellation Semantics

> 한 줄 요약: `CompletableFuture.cancel()`은 작업 중단 신호라기보다 exceptional completion에 가깝고, 실제 computation을 멈추는 보장은 없으므로 cancellation propagation과 timeout 전략을 따로 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [ForkJoinPool Work-Stealing](./forkjoinpool-work-stealing.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: CompletableFuture cancellation, cancel, CancellationException, exceptional completion, timeout, propagation, interrupt, completion stage, dependent stage, mayInterruptIfRunning, `completeExceptionally`

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

`CompletableFuture`의 cancellation은 `FutureTask`의 interrupt-driven cancellation과 성격이 다르다.  
Javadoc은 `cancel()`이 `completeExceptionally(new CancellationException())`과 같은 효과를 가진다고 설명한다.

즉 cancel은 "반드시 실행 중인 작업을 멈춘다"가 아니다.

## 깊이 들어가기

### 1. cancellation은 상태 전환이다

`CompletableFuture`는 cancellation을 exceptional completion으로 본다.  
그래서 downstream stage는 `CompletionException` 또는 `CancellationException` 흐름을 따라가게 된다.

### 2. mayInterruptIfRunning은 기대를 낮춰야 한다

`CompletableFuture.cancel(true)`가 있어도, 구현상 interrupt로 실제 계산을 멈추는 보장은 약하다.  
특히 async stage가 common pool이나 별도 executor에서 이미 돌아가면 더 그렇다.

### 3. downstream propagation이 필요하다

한 stage가 취소되었다고 해서 모든 관련 작업이 자동으로 멈추지는 않는다.  
부모와 자식 future의 전파 규칙을 직접 설계해야 한다.

### 4. timeout은 cancellation과 비슷하지만 다르다

- timeout: 시간 제한에 의해 실패를 만듦
- cancel: 명시적인 중단 신호

둘을 혼동하면 재시도와 cleanup 로직이 어긋날 수 있다.

## 실전 시나리오

### 시나리오 1: 사용자 요청이 취소됐는데 백그라운드 작업은 계속 돈다

이때 `CompletableFuture` 취소만으로는 부족할 수 있다.  
작업 자체가 cooperative cancellation을 지원해야 한다.

### 시나리오 2: timeout 후에도 downstream이 움직인다

상위 future가 실패해도 이미 시작된 다른 future는 계속 실행될 수 있다.  
그래서 shared resource를 쓰는 작업은 별도 중단 신호가 필요하다.

### 시나리오 3: cancel된 future를 join할 때 예외가 헷갈린다

취소는 exceptional completion이므로, `join()`과 `get()`에서 보이는 예외 타입을 구분해서 읽어야 한다.

## 코드로 보기

### 1. cancel 호출

```java
CompletableFuture<String> future = new CompletableFuture<>();
future.cancel(true);
```

### 2. timeout과 같이 쓰는 예

```java
CompletableFuture<String> future = CompletableFuture
    .supplyAsync(this::work)
    .orTimeout(3, java.util.concurrent.TimeUnit.SECONDS);
```

### 3. cooperative cancellation

```java
public String work(java.util.concurrent.atomic.AtomicBoolean stop) {
    while (!stop.get()) {
        // keep working
    }
    return "stopped";
}
```

### 4. downstream 예외 처리

```java
future
    .thenApply(this::step)
    .exceptionally(ex -> "fallback");
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `cancel()` | 신호를 명시할 수 있다 | 실제 중단 보장은 약하다 |
| timeout | 응답 SLA를 지키기 쉽다 | 내부 작업은 계속 남을 수 있다 |
| cooperative flag | 실행 중단을 직접 설계할 수 있다 | 작업 코드 수정이 필요하다 |
| interrupt 기반 작업 | 전통적인 중단이 가능하다 | `CompletableFuture`와는 결이 다를 수 있다 |

핵심은 cancel을 "작업을 죽이는 버튼"이 아니라 "실패 상태를 전파하는 신호"로 보는 것이다.

## 꼬리질문

> Q: `CompletableFuture.cancel()`은 작업을 반드시 멈추나요?
> 핵심: 아니다. exceptional completion에 가깝고, 실제 computation 중단은 별도 설계가 필요하다.

> Q: timeout과 cancel 차이는 무엇인가요?
> 핵심: timeout은 시간 조건 실패이고 cancel은 명시적 중단 신호다.

> Q: 취소 전파를 왜 따로 설계해야 하나요?
> 핵심: 이미 시작된 dependent stage나 shared executor 작업은 자동으로 멈추지 않을 수 있기 때문이다.

## 한 줄 정리

`CompletableFuture`의 cancellation은 실행 중단 보장이 아니라 exceptional completion이므로, timeout과 cooperative cancellation을 함께 설계해야 한다.
