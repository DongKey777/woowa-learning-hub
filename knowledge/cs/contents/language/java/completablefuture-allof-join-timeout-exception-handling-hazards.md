---
schema_version: 3
title: CompletableFuture allOf, join, Timeout, and Exception Handling Hazards
concept_id: language/completablefuture-allof-join-timeout-exception-handling-hazards
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- completablefuture
- async-error-handling
- timeout-cancellation
aliases:
- CompletableFuture allOf join timeout hazards
- CompletableFuture allOf partial failure
- join vs get CompletionException
- CompletableFuture exceptionally handle whenComplete
- orTimeout completeOnTimeout
- async fan-out fan-in failure
symptoms:
- CompletableFuture allOf가 결과를 모아 준다고 생각해 개별 future 결과와 실패 원인을 별도로 회수하지 않아
- join이 CompletionException으로 실패 원인을 감싸는 점을 놓쳐 운영 로그에서 root cause를 잃어버려
- orTimeout이나 completeOnTimeout을 내부 작업 중단으로 오해해 timeout 뒤에도 DB/HTTP 작업이 남는 문제를 만든다
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- language/completablefuture-execution-model-common-pool-pitfalls
next_docs:
- language/completablefuture-cancellation-semantics
- language/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards
- language/partial-success-fan-in-patterns
linked_paths:
- contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md
- contents/language/java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md
- contents/language/java/completablefuture-cancellation-semantics.md
- contents/language/java/partial-success-fan-in-patterns.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/threadlocal-leaks-context-propagation.md
confusable_with:
- language/completablefuture-cancellation-semantics
- language/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards
- language/partial-success-fan-in-patterns
forbidden_neighbors: []
expected_queries:
- CompletableFuture allOf는 결과를 모아 주는지 완료 합류만 하는지 설명해줘
- join과 get의 예외 wrapper 차이를 CompletionException ExecutionException 관점으로 알려줘
- orTimeout completeOnTimeout이 실제 내부 작업을 중단하지 않을 수 있는 이유가 뭐야?
- CompletableFuture exceptionally handle whenComplete를 실패 은닉 없이 어떻게 써야 해?
- fan-out fan-in에서 partial failure와 성공 결과 일부를 어떻게 집계해야 해?
contextual_chunk_prefix: |
  이 문서는 CompletableFuture allOf, join/get, timeout, exceptionally/handle/whenComplete, partial success fan-in을 error flow와 background task lifecycle 관점으로 설명하는 advanced deep dive다.
  allOf join timeout, CompletionException, orTimeout, completeOnTimeout, async fan-out fan-in, partial failure 질문이 본 문서에 매핑된다.
---
# `CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards

> 한 줄 요약: `CompletableFuture` 체인은 조합이 쉬워 보여도 `allOf`, `join`, `orTimeout`, `handle`, `exceptionally`의 의미를 섞으면 실패 원인 은닉, partial success 누락, thread starvation, timeout 후 백그라운드 작업 잔류가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Partial Success Fan-in Patterns](./partial-success-fan-in-patterns.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)

> retrieval-anchor-keywords: CompletableFuture allOf, anyOf, join vs get, CompletionException, ExecutionException, exceptionally, handle, whenComplete, timeout, orTimeout, completeOnTimeout, partial failure, fan-out fan-in, async error handling, background task leak, delayedExecutor, scheduler hop

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

`CompletableFuture`의 어려움은 "비동기 실행"보다 **실패 의미를 어디서 어떻게 회수하느냐**에 있다.

특히 자주 헷갈리는 축은 이렇다.

- `join()` vs `get()`
- `allOf()`는 완료 합류인지 결과 집계인지
- timeout은 내부 작업 중단인지 응답 deadline인지
- `exceptionally()`는 복구인지 실패 은닉인지

즉 체인을 읽을 때는 값 흐름만이 아니라 error flow를 같이 읽어야 한다.

## 깊이 들어가기

### 1. `join()`은 예외를 wrapper에 싸서 다시 던진다

`join()`은 checked exception을 피할 수 있어 많이 쓰이지만,  
실패 원인을 `CompletionException` 아래에 감싸서 올릴 수 있다.

반면 `get()`은 `ExecutionException`, `InterruptedException`, `TimeoutException` 등으로 더 명시적으로 드러난다.

즉 `join()`이 항상 더 편한 것이 아니라,  
실패 경계가 흐려질 수 있다는 비용이 있다.

### 2. `allOf()`는 결과를 모으지 않는다

`allOf(f1, f2, f3)`는 "모두 끝났는가"만 알려준다.  
각 결과는 직접 꺼내야 한다.

문제는 여기서 partial failure semantics가 자주 빠진다는 점이다.

- 하나라도 실패하면 전체를 실패로 볼 것인가
- 성공한 일부 결과는 버릴 것인가
- 개별 예외를 aggregate해서 보여줄 것인가

이 정책이 없으면 fan-out/fan-in 코드는 production에서 디버깅하기 어려워진다.

### 3. timeout은 작업 수명과 응답 수명을 분리해서 봐야 한다

`orTimeout()`이나 `completeOnTimeout()`은 future의 completion semantics를 바꿀 수 있다.  
하지만 실제 내부 작업이 멈춘다는 보장은 약하다.

즉 다음은 다른 문제다.

- 호출자가 언제 포기할지
- 내부 computation이 언제 멈출지

이 구분이 없으면 timeout 이후에도 DB/HTTP 작업이 계속 남는다.

### 4. `exceptionally`, `handle`, `whenComplete`는 역할이 다르다

- `exceptionally`: 실패를 다른 값으로 복구
- `handle`: 성공/실패를 모두 받아 변환
- `whenComplete`: 부수효과 관측, 보통 값 변환은 아님

실무에서 흔한 함정은 `exceptionally`로 너무 일찍 fallback을 넣어  
실패 원인이 사라지는 것이다.

즉 fallback은 복구 전략이 분명할 때만 넣어야 한다.

### 5. stage마다 executor와 context가 달라질 수 있다

`allOf`/`join` 조합 자체보다 더 중요한 것은  
그 앞 단계들이 어느 executor에서, 어떤 `ThreadLocal`/MDC context로 돌았는가다.

즉 fan-out/fan-in 설계는:

- 실패 집계
- timeout 정책
- context propagation
- blocking 격리

를 한 묶음으로 봐야 한다.

## 실전 시나리오

### 시나리오 1: 외부 API 세 개를 병렬 호출하는데 하나만 가끔 조용히 빠진다

`exceptionally`가 너무 앞단에 붙어 실패를 빈 객체로 바꿨다.  
결과적으로 장애는 숨겨지고 데이터만 비게 된다.

### 시나리오 2: `allOf().join()` 후 원인 파악이 어렵다

어느 future가 왜 실패했는지 집계하지 않았다.  
운영 로그에는 wrapper exception만 남고, 개별 실패 문맥이 사라진다.

### 시나리오 3: timeout은 났는데 downstream 부하는 계속 오른다

future는 timeout으로 끝났지만 실제 HTTP/DB 작업은 계속 진행 중이다.  
호출자 수명과 내부 작업 수명을 분리하지 않았기 때문이다.

### 시나리오 4: async 체인 이후 traceId가 사라진다

결과는 잘 모았지만 context propagation이 빠져  
실패 분석이 더 어려워진다.

## 코드로 보기

### 1. `allOf()` 후 결과를 명시적으로 수집

```java
CompletableFuture<Void> all = CompletableFuture.allOf(userFuture, orderFuture, pointFuture);

CompletableFuture<Dashboard> dashboardFuture = all.thenApply(ignored ->
    new Dashboard(userFuture.join(), orderFuture.join(), pointFuture.join())
);
```

여기서도 각 future의 실패 정책을 따로 정해야 한다.

### 2. timeout과 fallback 구분

```java
CompletableFuture<Response> responseFuture =
    remoteCall().orTimeout(500, java.util.concurrent.TimeUnit.MILLISECONDS);
```

이 코드는 future completion을 바꿀 뿐, 내부 작업 중단을 자동 보장하지는 않는다.

### 3. 실패를 너무 일찍 삼키지 않기

```java
future
    .whenComplete((value, error) -> logOutcome(value, error))
    .thenApply(this::transform);
```

관측과 복구를 분리하는 편이 읽기 쉽다.

### 4. 개별 실패를 모아 aggregate 만들기

```java
List<CompletableFuture<Result>> futures = List.of(f1, f2, f3);

CompletableFuture<List<Result>> allResults =
    CompletableFuture.allOf(futures.toArray(CompletableFuture[] ::new))
        .thenApply(ignored -> futures.stream()
            .map(CompletableFuture::join)
            .toList());
```

partial success를 허용한다면 `Result` 타입 자체를 성공/실패 variant로 모델링하는 편이 낫다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `join()` 위주 | 코드가 짧다 | wrapper exception 아래에서 실패 원인이 흐려질 수 있다 |
| `allOf()` fan-in | 병렬 합류를 쉽게 표현한다 | 결과 수집/partial failure 정책은 직접 설계해야 한다 |
| eager fallback | 응답을 빨리 만들 수 있다 | 장애와 데이터 손실을 조용히 숨길 수 있다 |
| timeout 분리 설계 | 응답 수명과 작업 수명을 구분할 수 있다 | 코드와 취소 정책이 더 필요하다 |

핵심은 `CompletableFuture`를 값 조합 도구가 아니라 error/timeout/context 조합 도구로 함께 읽는 것이다.

## 꼬리질문

> Q: `allOf()`는 결과를 자동으로 모아주나요?
> 핵심: 아니다. 완료 합류만 해주고 각 결과는 직접 꺼내야 한다.

> Q: `join()`이 항상 `get()`보다 좋은가요?
> 핵심: 더 간단할 수 있지만 failure wrapper 때문에 원인 경계가 흐려질 수 있다.

> Q: `orTimeout()`이면 내부 작업도 멈추나요?
> 핵심: 아니다. future completion과 실제 computation 수명은 분리해서 봐야 한다.

> Q: `exceptionally()`를 어디에 두면 되나요?
> 핵심: fallback 의미가 분명한 boundary에만 두고, 너무 앞단에서 실패를 삼키지 않는 편이 안전하다.

## 한 줄 정리

`CompletableFuture` hazard의 본질은 executor보다 error flow와 timeout semantics이므로, `allOf`, `join`, fallback, cancellation을 한 정책으로 설계해야 한다.
