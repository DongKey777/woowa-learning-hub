# Thread Interruption and Cooperative Cancellation Playbook

> 한 줄 요약: Java의 interrupt는 스레드를 강제로 죽이는 기능이 아니라 협력적 취소 신호다. `InterruptedException`을 삼키거나 interrupt status를 잃어버리면 shutdown, timeout, request cancel이 조용히 망가진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Structured Concurrency and `ScopedValue`](./structured-concurrency-scopedvalue.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [ForkJoinPool Work-Stealing](./forkjoinpool-work-stealing.md)

> retrieval-anchor-keywords: interrupt, InterruptedException, interruption status, Thread.interrupt, Thread.interrupted, isInterrupted, cooperative cancellation, graceful shutdown, shutdownNow, Future.cancel, blocking call, sleep, join, lockInterruptibly, virtual thread, cancellation token, servlet request cancel, servlet async timeout, client disconnect, request timeout, virtual thread request interrupt

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

interrupt는 "지금 당장 멈춰"가 아니라 "멈출 수 있으면 멈춰 달라"는 요청이다.

이 요청은 보통 두 형태로 나타난다.

- interrupt flag를 세운다
- 일부 blocking API가 `InterruptedException`으로 깨어난다

그래서 취소가 제대로 동작하려면 호출자와 작업 코드가 같은 규칙을 지켜야 한다.

- blocking 지점은 interrupt를 존중한다
- catch한 쪽은 신호를 잃어버리지 않는다
- CPU loop는 `isInterrupted()`나 별도 token을 확인한다

핵심 오해는 interrupt를 예외 처리 세부사항으로 보는 것이다.  
실무에서는 interrupt가 곧 shutdown protocol이다.

## 깊이 들어가기

### 1. interrupt는 상태이자 협력 신호다

`Thread#interrupt()`는 대상 스레드의 interrupt status를 세운다.  
스레드가 `sleep`, `wait`, `join`, `BlockingQueue#take`, `lockInterruptibly()` 같은 interruptible blocking call에 있으면 깨어날 수 있다.

하지만 모든 blocking call이 즉시 멈추는 것은 아니다.

- 일부 I/O는 resource close나 driver-specific cancel이 더 중요하다
- native call이나 외부 라이브러리는 interrupt를 느리게 반영할 수 있다
- 이미 CPU loop 안에 있으면 코드가 flag를 직접 확인해야 한다

즉 interrupt는 kill signal이 아니라 cooperation contract다.

### 2. `InterruptedException`을 잡으면 status가 지워질 수 있다

많은 interruptible API는 `InterruptedException`을 던지면서 현재 스레드의 interrupt status를 clear한다.  
그래서 catch 후 그냥 로그만 남기고 계속 가면, 상위 호출자는 취소 신호가 있었는지 모르게 된다.

규칙은 단순하다.

- 가능하면 `InterruptedException`을 그대로 다시 던진다
- 못 던지면 `Thread.currentThread().interrupt()`로 status를 복구한다
- 취소를 정상 종료로 볼지, 예외로 볼지 boundary에서 일관되게 정한다

### 3. `Thread.interrupted()`와 `isInterrupted()`는 다르다

- `Thread.currentThread().isInterrupted()`: 상태를 읽기만 한다
- `Thread.interrupted()`: 현재 스레드 상태를 읽고 clear한다

`Thread.interrupted()`를 무심코 쓰면 cancellation signal을 소비해버릴 수 있다.  
retry loop, polling loop, batch worker에서 특히 조심해야 한다.

### 4. interrupt만으로 충분하지 않은 경우가 있다

interrupt는 강력한 기본 신호지만, 다음 경우엔 추가 설계가 필요하다.

- 긴 CPU loop: 주기적으로 flag 체크 필요
- 외부 API 호출: 소켓 timeout, JDBC cancel, HTTP client cancel도 같이 설계
- async graph 전체 취소: interrupt 외에 cancellation token이나 parent scope 필요

즉 interrupt는 바닥 신호이고, 상위 수준 취소 모델은 별도로 있을 수 있다.

특히 servlet request timeout이나 client disconnect는 "thread를 interrupt한다"보다 "response/request lifetime이 끝났다"에 가깝다.  
그래서 Spring MVC나 virtual-thread request handling에서는 timeout/disconnect를 interrupt로 착각하지 말고, app task cancel과 downstream timeout을 별도로 연결해야 한다.

### 5. executor, future, virtual thread와의 관계

`ExecutorService#shutdownNow()`는 대기 중 task 반환과 worker interrupt를 시도한다.  
`Future#cancel(true)`도 interrupt를 기대하게 만들지만, 실제 작업이 interrupt를 존중해야 효과가 있다.

virtual thread에서도 원칙은 같다.

- blocking 자체는 저렴해질 수 있다
- 하지만 취소 협약은 여전히 필요하다
- `InterruptedException`을 삼키면 structured cancellation도 흐려진다

즉 Loom이 interrupt discipline을 없애주지는 않는다.

## 실전 시나리오

### 시나리오 1: 서버 종료가 오래 걸린다

worker가 queue에서 `take()` 하다 interrupt를 받았는데 catch 후 무시하고 다시 loop를 돌면,  
`shutdownNow()`는 성공한 것처럼 보여도 스레드는 계속 살아남는다.

이때 문제는 executor가 아니라 worker contract다.

### 시나리오 2: timeout은 지났는데 DB 작업이 계속 돈다

상위 future는 timeout으로 실패했지만, 실제 JDBC 호출은 계속 진행될 수 있다.  
interrupt만 걸고 끝내면 부족할 수 있다.

확인할 것:

- driver가 interrupt를 어떻게 다루는가
- statement timeout이 있는가
- connection close나 cancel API가 있는가

### 시나리오 3: 배치 루프가 취소되지 않는다

CPU-bound loop가 interruptible blocking point 없이 오래 돌면,  
interrupt status를 주기적으로 확인하지 않는 한 끝나지 않는다.

### 시나리오 4: 취소 신호가 중간 계층에서 사라진다

library code가 `InterruptedException`을 catch해서 로그만 남기고 빈 값을 반환하면,  
호출자는 "정상 종료"와 "취소"를 구분할 수 없게 된다.

이 패턴은 request cancel, graceful shutdown, 배치 stop을 모두 어렵게 만든다.

## 코드로 보기

### 1. `InterruptedException`을 복구하며 빠져나오기

```java
public void runWorker() {
    try {
        queue.take();
        processNext();
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        return;
    }
}
```

### 2. CPU loop에서 interrupt 확인하기

```java
public void indexAll(List<Job> jobs) {
    for (Job job : jobs) {
        if (Thread.currentThread().isInterrupted()) {
            return;
        }
        index(job);
    }
}
```

### 3. interrupt와 별도 stop token 함께 쓰기

```java
import java.util.concurrent.atomic.AtomicBoolean;

public final class Worker {
    private final AtomicBoolean stop = new AtomicBoolean();

    public void requestStop() {
        stop.set(true);
    }

    public void run() {
        while (!stop.get() && !Thread.currentThread().isInterrupted()) {
            doUnitOfWork();
        }
    }
}
```

### 4. executor 종료 절차

```java
executor.shutdown();
if (!executor.awaitTermination(5, java.util.concurrent.TimeUnit.SECONDS)) {
    executor.shutdownNow();
}
```

이 패턴도 worker가 interrupt를 존중하지 않으면 의미가 약해진다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| interrupt 중심 취소 | JDK 유틸리티와 자연스럽게 맞물린다 | 코드가 협력하지 않으면 효과가 약하다 |
| 별도 stop flag | CPU loop 제어가 단순하다 | blocking call을 깨우지 못한다 |
| cancellation token 객체 | async graph에 의도를 명시적으로 전달한다 | plumbing 코드가 늘어난다 |
| `shutdownNow()` 의존 | 중앙에서 멈추기 쉽다 | best-effort일 뿐 실제 중단을 보장하지 않는다 |

핵심은 "무엇으로 신호를 보낼지"보다 "누가 그 신호를 존중하는지"다.

## 꼬리질문

> Q: interrupt는 스레드를 강제로 종료하나요?
> 핵심: 아니다. 협력적 취소 신호이며 코드와 API가 이를 존중해야 멈춘다.

> Q: `InterruptedException`을 catch하면 무엇을 가장 조심해야 하나요?
> 핵심: interrupt status를 잃어버리지 않는 것이다. 못 던지면 다시 `interrupt()` 해야 한다.

> Q: `Thread.interrupted()`와 `isInterrupted()` 차이는 무엇인가요?
> 핵심: 전자는 읽으면서 clear하고, 후자는 읽기만 한다.

> Q: interrupt만 걸면 외부 API 호출도 같이 멈추나요?
> 핵심: 항상 그렇지 않다. timeout, cancel, close 같은 별도 메커니즘을 함께 봐야 한다.

## 한 줄 정리

interrupt는 Java 취소 모델의 공용 언어이므로, `InterruptedException`을 삼키지 않고 status를 보존하는 습관이 shutdown과 timeout 설계의 기본이다.
