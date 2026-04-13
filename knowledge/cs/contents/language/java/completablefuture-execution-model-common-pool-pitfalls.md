# CompletableFuture Execution Model and Common Pool Pitfalls

> 한 줄 요약: `CompletableFuture`는 조합 API처럼 보이지만 실제로는 어떤 executor에서 어떤 단계가 실행되는지까지 이해해야 하며, default `commonPool`에 기대면 blocking과 starvation 문제가 쉽게 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ForkJoinPool Work-Stealing](./forkjoinpool-work-stealing.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)

> retrieval-anchor-keywords: CompletableFuture, common pool, default executor, async stage, thenApply, thenCompose, supplyAsync, runAsync, allOf, anyOf, blocking stage, starvation, ForkJoinPool, thread hopping, exceptional completion

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

`CompletableFuture`는 비동기 작업을 조합하는 API다.  
하지만 실제 성능과 안정성은 "어느 stage가 어느 executor에서 돌았는가"에 달려 있다.

기본적으로 async 메서드는 executor를 명시하지 않으면 common pool을 사용할 수 있다.  
그래서 편하지만, 동시에 공유 자원이다.

### 왜 이게 문제인가

- blocking I/O가 섞이면 worker가 묶인다
- 같은 common pool을 다른 코드도 쓸 수 있다
- stage가 thread를 옮겨 다니며 context가 사라질 수 있다

## 깊이 들어가기

### 1. stage마다 실행 모델이 다르다

`CompletableFuture`는 단계별로 실행 형태가 조금씩 다르다.

- `thenApply`: 앞 단계와 같은 thread에서 이어질 수 있다
- `thenApplyAsync`: executor를 타고 비동기로 갈 수 있다
- `thenCompose`: 중첩 future를 평탄화한다
- `allOf`: 여러 future 완료를 기다린다
- `anyOf`: 먼저 끝난 결과를 받는다

즉 "체인"이라고 해서 항상 같은 실행 흐름은 아니다.

### 2. common pool은 default이지만 safe default는 아니다

common pool은 여러 라이브러리와 기능이 함께 쓰는 공유 pool이다.  
이곳에서 다음 일이 생기면 문제가 커진다.

- DB 호출
- HTTP 호출
- 긴 lock wait
- 오래 걸리는 계산

ForkJoinPool은 work-stealing에 강하지만 blocking에는 약하다.  
즉 `CompletableFuture`를 common pool에만 기대면 starvation이 생길 수 있다.

### 3. blocking stage는 별도 executor가 안전하다

비동기 조합보다 더 중요한 것은 경계다.

- CPU-bound 단계
- blocking I/O 단계
- 외부 API 호출 단계
- 긴 후처리 단계

이런 단계를 같은 pool에 넣지 않는 편이 좋다.

### 4. 예외는 조합의 일부다

`CompletableFuture`는 실패를 감춘다기보다 흘려 보낸다.  
따라서 예외 처리도 체인의 일부로 설계해야 한다.

- `exceptionally`
- `handle`
- `whenComplete`

를 언제 쓰는지 분명해야 한다.

## 실전 시나리오

### 시나리오 1: async인데 느리다

비동기라서 빨라지는 것은 아니다.  
common pool에서 blocking 작업을 돌리면 worker가 묶여 오히려 느려질 수 있다.

### 시나리오 2: 로그에 context가 자꾸 사라진다

stage hop이 발생하면 `ThreadLocal` 기반 context가 이어지지 않을 수 있다.  
이때는 wrapper나 명시적 전달이 필요하다.

### 시나리오 3: `allOf`를 썼는데 실패 원인을 못 찾는다

`allOf`는 완료 합류에 편하지만, 개별 실패를 자동으로 다 정리해 주지는 않는다.  
각 future의 결과와 예외를 따로 모아야 한다.

## 코드로 보기

### 1. executor를 명시하는 기본 패턴

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

public class ProfileService {
    private final Executor ioExecutor;

    public ProfileService(Executor ioExecutor) {
        this.ioExecutor = ioExecutor;
    }

    public CompletableFuture<String> loadProfile(String userId) {
        return CompletableFuture
            .supplyAsync(() -> fetchUser(userId), ioExecutor)
            .thenApply(this::enrich)
            .thenApplyAsync(this::render, ioExecutor);
    }

    private String fetchUser(String userId) {
        return "user:" + userId;
    }

    private String enrich(String value) {
        return value + ":enriched";
    }

    private String render(String value) {
        return value + ":rendered";
    }
}
```

### 2. common pool에 기대는 코드의 냄새

```java
CompletableFuture.supplyAsync(() -> {
    // blocking I/O
    return loadFromDatabase();
});
```

이 코드는 executor를 명시하지 않아 default pool에 묶일 수 있다.

### 3. 실패를 다루는 체인

```java
CompletableFuture<String> result = task
    .thenApply(this::step1)
    .thenApply(this::step2)
    .exceptionally(ex -> "fallback");
```

### 4. allOf 결과 모으기

```java
CompletableFuture<Void> all = CompletableFuture.allOf(f1, f2, f3);
all.join();
```

`allOf` 자체는 결과를 모으지 않으므로, 각 future에서 값을 꺼내는 후처리가 필요하다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| default async + common pool | 코드가 짧다 | blocking과 경쟁이 생긴다 |
| executor 명시 | 격리가 된다 | pool 설계가 필요하다 |
| stage별 executor 분리 | 병목을 줄인다 | 코드가 길어진다 |
| virtual threads로 단순화 | blocking 코드 유지가 쉽다 | 조합 모델은 여전히 설계가 필요하다 |

핵심은 `CompletableFuture`를 "마법의 비동기"가 아니라 "executor를 끼는 조합 API"로 보는 것이다.

## 꼬리질문

> Q: `thenApply`와 `thenApplyAsync` 차이는 무엇인가요?
> 핵심: `thenApply`는 이어지는 thread에서 실행될 수 있고, `thenApplyAsync`는 executor를 타며 스케줄링 경계가 생긴다.

> Q: common pool을 왜 조심해야 하나요?
> 핵심: shared pool이라 blocking 작업이 섞이면 다른 async 작업까지 느려질 수 있다.

> Q: `allOf`가 끝났는데 결과가 안 보이는 이유는 무엇인가요?
> 핵심: `allOf`는 완료 합류만 제공하고 각 결과는 직접 모아야 한다.

## 한 줄 정리

`CompletableFuture`는 stage 조합만이 아니라 executor 선택이 핵심이고, default common pool에 blocking을 섞지 않는 것이 안정성의 출발점이다.
