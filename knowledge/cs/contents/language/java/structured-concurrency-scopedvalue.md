---
schema_version: 3
title: Structured Concurrency and ScopedValue
concept_id: language/structured-concurrency-scopedvalue
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/payment
- missions/spring-roomescape
review_feedback_tags:
- structured-concurrency
- scopedvalue
- virtual-threads
aliases:
- Structured Concurrency and ScopedValue
- StructuredTaskScope ScopedValue
- Java structured concurrency cancellation propagation
- scope-bound context vs ThreadLocal
- virtual threads structured task group
- 자바 structured concurrency ScopedValue
symptoms:
- async task를 여러 Future와 CompletableFuture chain으로 흩어 놓아 parent request lifetime, failure propagation, cancellation cleanup을 한 scope로 추적하지 못해
- ThreadLocal을 request context propagation 기본값으로 써 virtual thread나 thread reuse 경계에서 leak와 stale context 위험을 키워
- ScopedValue를 mutable thread-bound storage처럼 생각해 scope-bound read-only context 전달이라는 모델을 놓쳐
intents:
- deep_dive
- design
- comparison
prerequisites:
- language/completablefuture-execution-model-common-pool-pitfalls
- language/completablefuture-cancellation-semantics
- language/virtual-threads-project-loom
next_docs:
- language/structured-fanout-httpclient
- language/inheritablethreadlocal-vs-scopedvalue-context-propagation
- language/virtual-thread-migration-pinning
linked_paths:
- contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md
- contents/language/java/completablefuture-cancellation-semantics.md
- contents/language/java/structured-fanout-httpclient.md
- contents/language/java/threadlocal-leaks-context-propagation.md
- contents/language/java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/virtual-threads-project-loom.md
confusable_with:
- language/completablefuture-cancellation-semantics
- language/threadlocal-leaks-context-propagation
- language/inheritablethreadlocal-vs-scopedvalue-context-propagation
forbidden_neighbors: []
expected_queries:
- structured concurrency는 여러 async task의 lifetime failure cancellation을 하나의 scope로 묶는다는 뜻이 뭐야?
- ScopedValue는 ThreadLocal과 달리 scope-bound read-only context라는 점에서 어떤 차이가 있어?
- StructuredTaskScope를 쓰면 한 task 실패 시 sibling task cancellation을 어떻게 구조화할 수 있어?
- virtual threads와 structured concurrency를 같이 쓰면 callback chain보다 어떤 점이 단순해져?
- request context propagation에서 InheritableThreadLocal 대신 ScopedValue를 고려하는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 structured concurrency와 ScopedValue를 scope-bound task lifetime, failure/cancellation propagation, read-only context propagation, virtual threads 관점에서 설명하는 advanced deep dive다.
  structured concurrency, StructuredTaskScope, ScopedValue, ThreadLocal, virtual threads 질문이 본 문서에 매핑된다.
---
# Structured Concurrency and `ScopedValue`

> 한 줄 요약: structured concurrency는 여러 async 작업을 하나의 scope로 묶어 취소와 실패를 정리하게 해주고, `ScopedValue`는 그 scope 안에서만 보이는 읽기 전용 context를 제공한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Structured Fan-out With `HttpClient`](./structured-fanout-httpclient.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
> - [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)

> retrieval-anchor-keywords: structured concurrency, StructuredTaskScope, ScopedValue, scope-bound context, cancellation propagation, virtual threads, async task group, structured lifetime, context propagation, preview API, InheritableThreadLocal, structured fan-out HttpClient, request-scoped task group

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

structured concurrency는 관련 있는 여러 async task를 하나의 scope 안에서 관리하는 방식이다.  
중요한 것은 "비동기"가 아니라 **수명과 실패를 구조화한다**는 점이다.

`ScopedValue`는 scope-bound, 읽기 전용 context 전달을 위한 도구다.  
`ThreadLocal`보다 scope 중심의 모델에 잘 맞는다.

## 깊이 들어가기

### 1. 왜 structured concurrency가 필요한가

기존 async 코드는 task가 여기저기 흩어지기 쉽다.

- 누가 언제 끝나는지 모른다
- 실패 전파가 분산된다
- 취소와 cleanup이 어렵다

structured concurrency는 이걸 하나의 scope로 모아서 다룬다.

### 2. `ScopedValue`는 ThreadLocal의 대안적 감각이다

`ThreadLocal`은 thread에 붙는다.  
`ScopedValue`는 코드 scope에 붙는다.

이 차이는 크다.

- thread reuse에 덜 취약하다
- 읽기 전용 context 전달에 더 자연스럽다
- async task group과 함께 생각하기 좋다

### 3. 실패와 취소를 scope 안에서 정리한다

한 task가 실패하면 다른 task를 더 이상 의미 있게 돌릴 필요가 없을 수 있다.  
structured concurrency는 이런 취소 전파를 구조적으로 하게 돕는다.

### 4. virtual threads와 잘 맞는다

blocking 코드를 유지하면서도 structured task group으로 관리하면,  
이전의 callback hell이나 scattered future chaining을 줄일 수 있다.

## 실전 시나리오

### 시나리오 1: 여러 외부 API를 병렬로 호출한다

각 호출을 하나의 scope에서 묶고, 실패 시 나머지를 정리하는 방식이 자연스럽다.

### 시나리오 2: request context를 전달해야 한다

`ThreadLocal`보다 `ScopedValue`가 더 잘 맞는 경우가 있다.  
특히 scope-bound로 읽기만 하면 되는 context에 적합하다.

### 시나리오 3: 취소와 timeout을 한꺼번에 다루고 싶다

structured concurrency는 task group 단위로 취소 정책을 적용하기 쉬워진다.

## 코드로 보기

### 1. scope 중심 감각

```java
// 여러 task를 하나의 scope에서 시작하고,
// 결과와 실패를 같은 수명 안에서 정리한다.
```

### 2. ScopedValue 감각

```java
// 읽기 전용 context를 scope에 묶어 전달한다.
```

### 3. ThreadLocal과 대비

```java
// ThreadLocal은 thread에 붙고,
// ScopedValue는 scope에 붙는다.
```

### 4. virtual thread 조합

```java
// blocking 코드를 유지하면서도 scope 기반 관리가 가능하다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| structured concurrency | 수명과 실패가 구조화된다 | 새로운 API와 사고방식이 필요하다 |
| CompletableFuture chain | 익숙하고 널리 쓰인다 | 흐름이 분산되기 쉽다 |
| ThreadLocal | 간단하다 | pool reuse와 전파 문제가 있다 |
| ScopedValue | scope-bound context에 좋다 | 읽기 전용 설계에 맞는다 |

핵심은 async를 개별 task의 집합이 아니라 하나의 수명 구조로 보는 것이다.

## 꼬리질문

> Q: structured concurrency가 해결하는 핵심 문제는 무엇인가요?
> 핵심: 여러 async task의 수명, 실패, 취소를 하나의 구조로 묶는 것이다.

> Q: ScopedValue는 ThreadLocal과 어떻게 다른가요?
> 핵심: ThreadLocal은 thread에, ScopedValue는 scope에 context를 묶는다.

> Q: virtual threads가 있으면 structured concurrency가 필요 없나요?
> 핵심: 아니다. 실행 비용이 낮아져도 task 수명과 실패 구조화 문제는 남는다.

## 한 줄 정리

structured concurrency는 async task의 수명과 취소를 구조화하고, `ScopedValue`는 scope-bound context를 전달하는 더 자연스러운 방식이다.
