# ThreadLocal Leaks and Context Propagation

> 한 줄 요약: `ThreadLocal`은 thread에 붙는 상태라 thread pool 재사용에서 쉽게 누수되고, async 경계에서는 자동 전파되지 않으므로 `remove()`와 capture/restore 패턴이 필수다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: ThreadLocal, InheritableThreadLocal, leak, thread pool reuse, remove, request context, MDC, context propagation, capture/restore, transmittable context, virtual thread, executor wrapper

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

`ThreadLocal`은 "스레드별로 따로 가진 변수"다.  
JDK 문서도 각 thread가 자기 복사본을 가진다고 설명한다.

문제는 thread의 수명이 아니다. thread pool에서는 thread가 오래 살아남는다.  
그래서 `ThreadLocal.set()`만 하고 `remove()`를 빼먹으면 다음 작업까지 값이 남을 수 있다.

또 하나의 문제는 context 전파다.

- `ThreadLocal`은 thread 경계를 넘지 않는다
- `InheritableThreadLocal`은 thread 생성 시점에만 복사된다
- executor, async, callback hop에서는 자동 전파가 아니다

## 깊이 들어가기

### 1. 왜 pool에서 누수가 잘 생기나

thread pool의 thread는 요청마다 생성되지 않는다.  
하나의 worker가 여러 request를 처리한다.

그러면 다음과 같은 일이 생긴다.

1. request A가 `ThreadLocal`에 값을 넣는다
2. request A가 끝났지만 `remove()`를 안 한다
3. 같은 worker가 request B를 처리한다
4. B는 A의 값이 남아 있는 상태를 만난다

이건 기능 버그이면서 동시에 메모리 버그다.

### 2. `InheritableThreadLocal`은 만능이 아니다

이 타입은 자식 thread 생성 시 값을 넘기는 데 도움을 준다.  
하지만 thread pool에서는 worker가 이미 생성되어 있기 때문에 기대한 전파가 되지 않는다.

즉 "자식 thread에 자동 전달"과 "executor task에 자동 전달"은 전혀 다르다.

### 3. context propagation은 capture/restore 문제다

실무에서 필요한 것은 보통 다음이다.

- 제출 시점의 context를 캡처한다
- 실행 시점에 복원한다
- 끝나면 반드시 원복하거나 제거한다

이 패턴이 없으면 request ID, auth 정보, locale, tracing 정보가 섞인다.

### 4. virtual threads가 와도 cleanup은 남는다

virtual thread는 짧게 생겼다가 사라지는 경향이 있어 pool 재사용 문제를 줄일 수 있다.  
하지만 `ThreadLocal`의 생명주기 관리 자체가 사라지는 것은 아니다.

또한 async hop이 생기면 여전히 context 전파 전략이 필요하다.

## 실전 시나리오

### 시나리오 1: 로그에 request ID가 섞인다

증상:

- 한 request의 traceId가 다른 request 로그에 나온다
- 비슷한 부하에서만 재현된다

원인 후보:

- `ThreadLocal.remove()` 누락
- worker 재사용
- 비동기 작업에서 context 복원 누락

### 시나리오 2: 메모리가 천천히 늘어난다

증상:

- request가 끝났는데 객체가 계속 남는다
- heap dump에서 thread 관련 root가 보인다

이건 classloader leak과 비슷한 형태로 보일 수 있다.  
실제로는 thread가 오래 살면서 context 객체를 붙잡고 있는 경우가 많다.

### 시나리오 3: async 이후 context가 사라진다

예:

- web request에서 traceId를 세팅
- `CompletableFuture`나 executor로 작업 넘김
- downstream 로그에는 traceId가 없다

이 경우는 전파를 직접 설계해야 한다.

## 코드로 보기

### 1. 기본 cleanup 패턴

```java
public class RequestContext {
    private static final ThreadLocal<String> TRACE_ID = new ThreadLocal<>();

    public void handle(String traceId, Runnable work) {
        TRACE_ID.set(traceId);
        try {
            work.run();
        } finally {
            TRACE_ID.remove();
        }
    }

    public static String currentTraceId() {
        return TRACE_ID.get();
    }
}
```

### 2. capture/restore wrapper

```java
public final class ContextAware {
    private static final ThreadLocal<String> TRACE_ID = new ThreadLocal<>();

    public static Runnable wrap(Runnable task) {
        String captured = TRACE_ID.get();
        return () -> {
            String previous = TRACE_ID.get();
            TRACE_ID.set(captured);
            try {
                task.run();
            } finally {
                if (previous == null) {
                    TRACE_ID.remove();
                } else {
                    TRACE_ID.set(previous);
                }
            }
        };
    }
}
```

이 패턴은 context propagation의 핵심을 보여준다.  
누가 세팅했는지, 언제 복원하는지, 언제 제거하는지를 명시해야 한다.

### 3. executor에 감싸서 넘기기

```java
executor.execute(ContextAware.wrap(() -> {
    // work with traceId
}));
```

### 4. 제거를 잊기 쉬운 코드의 냄새

```java
TRACE_ID.set(traceId);
work.run();
```

이 코드는 `finally`가 없어서 누수의 시작점이 되기 쉽다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `ThreadLocal` | 호출이 간단하다 | cleanup을 놓치기 쉽다 |
| `InheritableThreadLocal` | child thread에 복사된다 | pool 재사용 전파에는 약하다 |
| explicit parameter passing | 가장 명확하다 | 함수 시그니처가 길어진다 |
| capture/restore wrapper | async 전파가 가능하다 | 구현과 규율이 필요하다 |

핵심은 "편해서 썼다"가 아니라 "수명과 전파 규칙을 설계했다"가 되어야 한다는 점이다.

## 꼬리질문

> Q: `ThreadLocal`을 왜 pool 환경에서 조심해야 하나요?
> 핵심: worker thread가 재사용되므로 값을 지우지 않으면 다음 작업까지 남을 수 있다.

> Q: `InheritableThreadLocal`이면 충분한가요?
> 핵심: 아니다. thread 생성 시점 복사만 다루고 executor task 전파는 해결하지 못한다.

> Q: context propagation 대신 더 단순한 해법은 없나요?
> 핵심: 가능하면 explicit parameter passing이 가장 안전하고, 그게 어렵다면 wrapper나 전파 라이브러리를 쓴다.

## 한 줄 정리

`ThreadLocal`은 thread-local이지 request-local이 아니므로, pool 재사용에서는 `remove()`가 필수이고 async 경계에서는 capture/restore로 context propagation을 직접 설계해야 한다.
